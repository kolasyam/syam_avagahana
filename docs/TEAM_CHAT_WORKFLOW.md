# Agentic Chat — End-to-End Workflow (Team Explainer)

> How a user question becomes a grounded, cited answer — the routing, the DB
> fallback, the web-search trust gate, and the forecast/scenario tools.
> All numbers below are receipts from live runs (cutoff 2026-10-15).

---

## 1. The 60-second overview

```
User question (browser SSE)
   → Router  = local LLM (Ollama, qwen2.5:3b-instruct) reading a system prompt
               + tool schemas → decides WHICH agent/tool handles the question
   → Agents  = thin labels the orchestrator attaches to each tool family:
               Market Agent / Forecast Agent / Analysis Agent → Response Agent
   → Tools   = 7 real functions that hit the DB, the cached model, Tavily, or
               an isolated compute worker. Every number a tool returns is real.
   → Response Agent streams the final answer token-by-token with a source list,
     and the orchestrator closes with an audit frame (model, tools, agents used)
```

Nothing is staged. If a component is missing (no Ollama, no Tavily key, no
cached scenario), the answer **says so** instead of inventing numbers.

## 2. Components and models

| Piece | What it is | Model / tech |
|---|---|---|
| Router | Reads the question + tool schemas, returns tool calls (JSON) | `qwen2.5:3b-instruct` on local **Ollama** (OpenAI-compatible endpoint `:11434`) |
| Agents | Named stages shown as chips in the UI; each maps to a tool family | Orchestrator labels (no extra models) |
| Tools | 7 grounded functions (`app/chat/tools.py`) | SQLAlchemy / pandas / Chronos-2 / Tavily |
| Forecast engine | Time-series foundation model, quantile outputs | **Amazon Chronos-2** (local weights only, downloaded once) |
| Web search | Fallback when local DB is stale | **Tavily API** + trust whitelist (`app/tools/web_trust.py`) |
| Transport | Server-Sent Events streaming | FastAPI `StreamingResponse`, strict JSON frames |

The LLM is a *router and narrator*, not a data source: it chooses tools and
phrases their results. **Every price/forecast number comes from a tool result
over the wire** — the system prompt forbids inventing data, and the tool
results embed anti-hallucination instructions (`presentation_hints`,
`answer_protocol`) that a small local model echoes verbatim.

### Guardrails (L0 → L1 → L2 → L3 — every stage audited)

Implemented in `app/chat/guardrails.py` (pure rules, no LLM dependency):
- **L0 Input guard** (`classify_input`) — sensitive/political/medical/legal/personal-data/injection/off-topic messages refused **before any LLM token is spent**. Live receipts confirmed: INJECTION, PII, POLITICAL, OTHER_COMMODITY, OFF_TOPIC all blocked at 0.0 s, `GUARDRAIL_*` audit rows.
- **L1 Prompt scope** (`SYSTEM_PROMPT`) — onion-only commodity scope; weather as forecasting covariate only; citation-only rule hard-coded.
- **L2 Tool guards** (`web_topic_guard` = agriculture/market/weather only; `sanitize_horizon` clamps to 1..90; `check_factor_value` clamps scenario values) — prevents web tool from being abused as general search.
- **L3 Output guard** (`StreamingGuard`, sliding window) — scans composed stream; any fabricated ingestion claim (`"web data ingested"`), commodity drift (`rice`, `wheat`, `potato`), or injection echo replaces the stream with the refusal text.
Every trip yields an `audit` SSE frame (`guardrail_events`, `input_guard`) — visible in the audit DB (`audit_events`).

## 3. The tool map (agent → tool → data path)

| Agent | Tool | Data path |
|---|---|---|
| Market Agent | `search_local_prices` | SQLite `market_observations` (AGMARKNET-derived, real ingest) — 60-day avg, WoW change, arrivals |
| Market Agent | `latest_price` | Same table, most recent row; attaches `stale` + `recommend_web_fallback` flags |
| Market Agent | `get_regions` | Geography registry (AP primary; MH/KA/MP comparators; mandis = reference) |
| Market Agent | `web_lookup` | **Tavily** → trust-whitelist classification → citation-only (never auto-ingested) |
| Forecast Agent | `run_forecast` | Cache-first: all 20 pre-computed runs (AP/MH/KA/MP × 5 horizons). Cache miss → live Chronos-2 |
| Forecast Agent | `forecast_with_factor` | Conversational what-if: cache of pre-computed scenarios, else **isolated subprocess** re-forecast with Chronos-2 conditioned on the factor |
| Analysis Agent | `get_risk` | Alert/crisis thresholds + quantile-ladder breach probabilities (`probability_sheet`) |

## 4. Question → routing walk-throughs (with tonight's receipts)

### A. History question (DB hit)
> "What is the average onion modal price over the last 60 days in Andhra Pradesh?"

1. Router sees the answer is in the local series → calls `search_local_prices(state_andhra_pradesh, 60)`.
2. SQL: filter `commodity = onion`, `geography = state_andhra_pradesh`, order by date desc, take window.
3. Tool returns **₹35.69/kg** (60d avg) + change vs previous 30 days (+/- %).
4. Response Agent: "…was **₹35.69/kg** …" → source frame: `DB_OR_MODEL, ingested: true`.
Live: 20 s end-to-end.

### B. Today's price (stale local → web fallback)
> "What is the onion price today?"

1. Router → `latest_price(state_andhra_pradesh)` → latest real row ₹36.91/kg @ **2026-10-15**, flag `recommend_web_fallback: true` (data is N days old).
2. **Governance is enforced in code, not hoped for from the model:** the
   orchestrator *deterministically* auto-runs `web_lookup` in the same turn
   (frame shows `"reason": "staleness escalation"`) — a small local model can
   forget this step; the pipeline never does.
3. `web_lookup` → **Tavily** (live API, key configured) restricted to the
   trust-whitelist domains; each result is classified:
   - `APPROVED_TRUST_SOURCE` (gov / news-of-record: agmarknet.gov.in, pib.gov.in,
     business-standard, Economic Times, Livemint, Moneycontrol …) → citable
   - `UNVERIFIED_WEB_RESULT` → still citation-only, flagged untrusted
   - **Web results are never ingested into the forecasting model** — demo keeps ingest-off hardwired.
4. Verified live: answer quotes the last ingested price first, then four
   onion-specific citations with trust labels ("Azadpur mandi falls to
   ₹30–40/kg — Business Standard", "mandi prices fell 9% in nine days —
   Moneycontrol", "govt plans ₹35/kg agency sales — Economic Times",
   "Delhi average ₹78/kg — Livemint"), then the threshold position
   ("above alert ₹35, crisis ₹50 not breached").
5. Honesty ladder: if the network is down, the tool serves the seeded
   `web_cache.json` result; if that is exhausted, `WEB_SEARCH_UNAVAILABLE`
   and the answer reports the ingested series honestly. Invented "today's
   price" is impossible by construction.

### C. Forecast + breach risk (cached model, determinism)
> "Forecast for the next 30 days; how likely are we to breach the alert threshold?"

1. Router → `run_forecast(AP, 30)` → serves the **pre-computed Chronos-2 run** (instant; 20 runs cached for AP/MH/KA/MP × 7/14/30/60/90d, cutoff 2026-10-15).
2. Tool returns medians + 80% band + quantile-ladder exceedance per day.
3. Response Agent (echo-guarded): "₹32.00/kg … 80% CI ₹18.28–₹49.07 … **49.8% chance** of breaching the ₹35.00 alert within 30 days, **9.7% chance** for the ₹50.00 crisis."
4. The same 49.8% appears in the workspace exec tile — one number, one source, everywhere.

### D. Factor what-if (real conditioned re-forecast)
> "What if rainfall next year is 150 mm over two weeks?"

1. Router → `forecast_with_factor(AP, rainfall, 150)`.
2. Tool resolves fuzzy inputs (the 3B typed `state_andhra_pr Pradesh` — auto-corrected; `rainfall_mm` → mapped to ingested `precipitation_mm`).
3. Scenario served from the **pre-computed cache** (`factor_scenarios.json`), else a **process-isolated** worker (`scripts/compute_factor_scenario.py`) runs Chronos-2 *conditioned on the covariate* and diffs against the baseline:
   **₹33.65 → ₹39.57/kg, Δ +₹5.92 (+17.6%)** — a genuine re-forecast, not a scaling of a number.
4. Any failure (worker crash, timeout, unknown factor) → tool returns
   `PARTIAL` with the reason and an instruction the model must not claim any
   numeric effect. Isolation exists because native torch under RAM pressure
   crashed the server twice on this 7.3 GB box; now a crash costs only the
   child process and the chat keeps streaming.

## 5. Frame contract (frontend ↔ backend)

Per question the SSE stream carries:

```
event: agent   data: {"agent":"Market Agent","status":"running",...}     (chips)
event: tool    data: {"tool":"latest_price","args":{...},"status":"running"|"completed","summary":"..."}
event: token   data: "…answer text piece…"     (always JSON-encoded strings)
event: sources data: [{type:"DB_OR_MODEL"|"WEB","ingested":true|false,"url":...}]
event: audit   data: {"model":"qwen2.5:3b-instruct","agents":[...],"tools":[...]}
event: done    data: {"status":"OK","duration_seconds":24.5}
```

If Ollama is down, the stream still completes with a **"RULE-BASED FALLBACK"
answer** built directly from tool data — labeled as deterministic, no fake
LLM transcript.

## 6. Where the code lives

| File | Role |
|---|---|
| `backend/app/chat/orchestrator.py` | SSE loop, tool-calling loop, deterministic web escalation, audit frame |
| `backend/app/chat/llm.py` | Ollama OpenAI-compatible client, health/warm, 240 s cold-load timeout |
| `backend/app/chat/tools.py` | The 7 tools + fuzzy geo/variable resolution + scenario cache |
| `backend/app/tools/web_trust.py` | Tavily gate, trust whitelist, cache/web_cache.json offline mode |
| `backend/app/forecasting/chronos_adapter.py` | Chronos-2 loading, gap-regularized context, quantile outputs, `probability_sheet` |
| `backend/app/forecasting/factor_scenarios.json` | Pre-computed scenario cache (rainfall 150 mm seeded) |
| `scripts/compute_factor_scenario.py` | Isolated scenario worker (crash-proof compute) |
| `scripts/precompute_forecasts.py` | The 20 cached forecast runs |

## 7. Demo-day facts

- LLM RAM footprint ≈ 2.5 GB (3B, q4) — all reasoning is local; no cloud LLM.
- Web search: `TAVILY_API_KEY` is set (user env var, permanent) → live Tavily
  calls enabled; the seeded `web_cache.json` covers the scripted offline case.
- Streaming perception: history ≈ 20 s, forecast ≈ 50 s, today's-price web
  escalation ≈ 95–130 s, factor-from-cache ≈ 2 min (text streams from ~40 s).
- Tests: 17 logic tests pass; the Chronos smoke test auto-skips under memory
  pressure (`os error 1455` = RAM/pagefile ceiling).
