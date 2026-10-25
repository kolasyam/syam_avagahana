# DEMO CLAIMS CHEAT SHEET — Schezzer / CEO Presentation (Wed Oct 28, 2026)

All numbers below are REAL and traceable to artifacts. Rehearse with these;
do NOT use the old fabricated numbers anywhere.

---

## 1. The honest headline (use exactly this framing)

> "Foundation-model price forecasting **on real four-year AGMARKNET-derived data**
> (Jan 2022 → Oct 2026, 6,851 market rows), validated by a rolling-origin backtest,
> served live through a governed agentic workflow — with **zero synthetic data**."

**Accuracy claim (safe, true):**
- 14-day horizon: **WAPE 13.9%** (Chronos-2 champion, MAE ₹4.95/kg, 80% band covers 98.2%) on AP state aggregate → **"≥86% level accuracy at the two-week tactical horizon."**
- 30-day horizon: **WAPE 19.5%** (MAE ₹7.16/kg, 80% band covers 92.5%) → **"≥80% level accuracy at the one-month horizon."**
- Across all four validated states, h=30 WAPE ranges **13.2% − 21.4%**; best case Maharashtra **MAE ₹4.83/kg (13.2%)**.

**Legacy claim to retire (was on old slide):** ~~"4.1% WAPE / 96% accuracy / MAE 1.42 / spike prob 0.88 / Kurnool ₹48.50"~~ — none of these exist in the real system.

## 2. Full validated backtest matrix (real artifact `forecast_metrics.json`)

| State | h=14 MAE / WAPE | h=30 MAE / WAPE | h=30 80% coverage |
|---|---|---|---|
| Andhra Pradesh | ₹4.95 / 13.85% | ₹7.16 / 19.46% | 92.5% |
| Maharashtra | ₹2.97 / 8.28% | ₹4.83 / 13.16% | 93.3% |
| Karnataka | ₹4.63 / 12.47% | ₹8.17 / 21.40% | 59.2% ⚠ |
| Madhya Pradesh | ₹2.50 / 9.15% | ₹5.92 / 21.21% | 55.8% ⚠ |

- Beat the seasonal-naive baseline by **+9.2% MAE at h=14** on the pilot state; at h=30 the naive baseline is competitive — and we say so.
- **Methodology:** 4 rolling-origin folds per bucket, 56–120 real eval points per model, errors in ₹/kg.
- The UI table itself printed all rows + an auto-generated honesty note; if asked about the dip: *"Karnataka/MP 30-day bands under-cover in this fold mix; our protocol plans on the 95% band for that horizon until district-level features enable retraining."*

## 3. Data integrity lines (we proactively disclose these)

- 6,851 price rows (AP 1,749 / KA 1,640 / MP 1,734 / MH 1,728) + 22,591 context rows, Jan 2022 → Oct 15 2026, **random-synthetic purge runs on every ingest**; `is_demo_data=False` on all rows.
- AGMARKNET limit disclosed: state rows are **modal-price-only** (min=max=modal) → flagged `MODAL_ONLY_SERIES`; arrivals unit assumed MT.
- Mandi sites shown as **"Reference Site — district ingestion on roadmap"** (no price rows fabricated for them).
- Model context is regularized (missing market-holiday days forward-filled) — **DB keeps raw gaps; only the model input is regularized** (documented in code).

## 4. Live numbers for the demo script (cutoff 2026-10-15, cached instant)

- Latest AP modal: **₹36.91/kg**; last-60d avg ₹35.69/kg; WoW +7.6%; arrivals 242 MT/day (+30% vs prior 14d).
- AP 30-day forecast: **₹32.00/kg** horizon-end (peak day-1 ₹34.98), trend down ≈ −4.7%.
- Breach risk (₹35 alert): chat + exec tile both show **max-30d 49.8%** (day-7 48.1%, day-30 43.0%) — one number, quantile-ladder from real Chronos-2 bands. Crisis ₹50: max-30d ≈ 9.7%.
- Comparator forecasts (all real Chronos-2, cached): MH 30d ₹30.54 · KA 30d ₹31.72 · MP 30d ₹24.94.
- Chat grounding demo: "> **What is the onion price today?**" → tool trace → **₹35.69/kg grounded answer with source + audit trail**.
- Governance: every investigation writes a **real** DecisionReview + ScenarioRun + AuditEvent rows (e.g. `brief_state_andhra_pradesh_20261025063155`, audit #29+). No approval UI in demo — by design, conversational only.

## 5. Architecture one-liners (if probed)

- Forecast: **Amazon Chronos-2 zero-shot** (real inference, local weights, offline-safe), AR-Lag Ridge as honest fallback chain, labels on screen.
- Chat: **local `qwen2.5:3b-instruct` via Ollama** (npx-style warm endpoint pre-loads at page open; 10–15 min keep_alive) — no cloud LLM tokens leave the machine.
- Web fallback: **Tavily, citation-only** — results are shown with trust badges, **never auto-ingested**; ingestion stays under the source whitelist. (Key provisioning pending; offline the tool honestly reports `WEB_SEARCH_UNAVAILABLE`.)
- Demo survives offline: cached forecasts serve instantly, model weights local, chat works rule-based-fallback if the LLM is down.

## 6. Do NOT claim (audit-excluded)

1. ~~"96–97% forecast accuracy"~~ → real: ≥86% (14d) / ≥80% (30d) level accuracy.
2. ~~"MAE 1.42 / WAPE 4.1%"~~ → real table above.
3. ~~"Spike probability 88%"~~ → real quantile-ladder numbers (49.8% max-30d).
4. ~~"Kurnool ₹48.50 / 26.4% projected / ₹8.50 Cr plan from Oct 2026 brief"~~ → scenario engine computes −16.8% mitigation for a 10,000 MT release in-run; see live screen.
5. ~~"We ingest min/max prices"~~ → modal-only disclosure (line 3).
6. Any mandi-specific price for the 5 reference sites.

## 7. Remaining open items (status)

- [ ] **Tavily API key** → set `TAVILY_API_KEY` env, then `web_lookup` demo works (everything else verified offline).
- [ ] Deck: replace slide claim block with §1–§2 numbers.
- [ ] Tuesday: 2× dress rehearsal of the 5 scripted questions + offline drill + add-factor conversational re-forecast check.
