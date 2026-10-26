# LLM Backend Swap — OSS-20B via API (with Ollama fallback)

The agentic chat no longer depends solely on the local Ollama model. It now runs a
**provider-agnostic LLM layer** (`app/chat/llm.py`):

```
PRIMARY   = openai/gpt-oss-20b over Groq (https://api.groq.com/openai/v1, ~1000 tps)
FALLBACK  = local Ollama (qwen2.5:3b-instruct) — engaged automatically if the API errors
LAST      = deterministic RULE-BASED FALLBACK (honest, labelled, never fake)
```

If the Groq API hiccups mid-demo, the chat silently continues on local Ollama. Only if
BOTH are down does it drop to the labelled rule-based path. Nothing is ever invented.

---

## 1. Provide the API key (Groq)

Set these before launching the backend (same pattern as the Tavily key — `setx` does
NOT reach child processes of the current shell, so set inline in the launch shell):

```powershell
$env:OPENAI_API_KEY   = '<PASTE-YOUR-GROQ-KEY-HERE>'   # also reads GROQ_API_KEY
$env:OPENAI_API_BASE  = 'https://api.groq.com/openai/v1'   # default
$env:OPENAI_MODEL     = 'openai/gpt-oss-20b'               # default
$env:LLM_PROVIDER     = 'openai_api'                       # default; 'ollama' forces local-only
$env:LLM_FALLBACK_TO_OLLAMA = 'true'                       # keep the safety net (default)
```

Then start from the `backend/` folder:

```powershell
cd "C:\Users\syamm\OneDrive\Desktop\Avagahana Dattha\AP_Onion_Commodity\backend"
$env:PYTHONPATH='.'; python -m uvicorn app.main:app --port 8000
```

## 2. Using a non-Groq provider (OpenAI / OpenRouter / Together / vLLM / Fireworks)

`gpt-oss-20b` is open-weight and served by several OpenAI-compatible hosts. Just change
the base URL + model id:

| Provider | OPENAI_API_BASE | OPENAI_MODEL |
|---|---|---|
| **Groq (default)** | `https://api.groq.com/openai/v1` | `openai/gpt-oss-20b` |
| OpenAI | `https://api.openai.com/v1` | `gpt-oss-20b` |
| OpenRouter | `https://openrouter.ai/api/v1` | `openai/gpt-oss-20b` |
| Together | `https://api.together.xyz/v1` | `openai/gpt-oss-20b` |
| Fireworks | `https://api.fireworks.ai/inference/v1` | `accounts/fireworks/models/gpt-oss-20b` |
| Self-hosted vLLM | `http://<host>:8000/v1` | the served model id |

## 3. Verify before the demo

```powershell
# Health — expect status READY, model gpt-oss-20b (OSS API), plus a "fallback" block for Ollama
Invoke-RestMethod http://127.0.0.1:8000/api/v1/chat/health | ConvertTo-Json -Depth 4

# Warm (1-token probe confirms reachability)
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/v1/chat/warm
```

The Router agent chip in the UI now reads `LLM: gpt-oss-20b (OSS API)` instead of
`local Ollama`, and the audit frame logs the active backend label.

## 4. Offline rehearsal (force local-only)

```powershell
$env:LLM_PROVIDER='ollama'   # bypass the API entirely, use local Ollama
```

## 5. What changed

- `app/core/config.py` — added `LLM_PROVIDER`, `OPENAI_API_BASE/_KEY/_MODEL`,
  `LLM_FALLBACK_TO_OLLAMA`. `OLLAMA_*` retained as the fallback.
- `app/chat/llm.py` — rewritten as provider-agnostic. `check_health()` probes the active
  backend (and reports the Ollama fallback status). `chat_completion()` routes primary →
  fallback → raise. `warm_model()` warms whichever backend is active.
  `OllamaUnavailableError` name kept stable (raised only when NO backend answers).
- `app/chat/orchestrator.py` — Router detail + audit `model` field now use
  `active_backend_label()` so the UI/audit show the real backend.
