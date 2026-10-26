"""
LLM Client (provider-agnostic: OSS-20B API primary, local Ollama fallback)
==========================================================================
Routes chat to a configured LLM backend via the OpenAI-compatible API, with
honest status reporting:

  PRIMARY   = an open-weight OSS model (default gpt-oss-20b) over any
              OpenAI-compatible /chat/completions endpoint (OpenAI, OpenRouter,
              Together, vLLM, ...). Configured by OPENAI_API_BASE / _KEY / _MODEL.
  FALLBACK  = the locally served Ollama model (settings.OLLAMA_MODEL) — engaged
              automatically when the primary API errors/times out, so the demo
              keeps working if the API hiccups. Disable with
              LLM_FALLBACK_TO_OLLAMA=false.
  LAST RESORT = the orchestrator's deterministic RULE-BASED FALLBACK path
              (labelled, never pretends to be LLM-generated).

Provider selection is a single knob (settings.LLM_PROVIDER): "openai_api" or
"ollama". Force local-only for an offline rehearsal with LLM_PROVIDER=ollama.
"""

import json
import time
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

CHAT_TIMEOUT_SECONDS = 240.0  # API cold starts / long generations


class OllamaUnavailableError(RuntimeError):
    """Raised when NO LLM backend (primary or fallback) could answer.

    Kept under its historical name so the orchestrator's except-clause and the
    rule-based fallback path stay stable across the provider swap.
    """
    pass


# ---------------------------------------------------------------------------
# Provider resolution
# ---------------------------------------------------------------------------
def _use_api() -> bool:
    """True when the primary backend is the OpenAI-compatible API."""
    return settings.LLM_PROVIDER.strip().lower() == "openai_api"


def _primary_base() -> str:
    return settings.OPENAI_API_BASE.rstrip("/")


def _primary_model() -> str:
    return settings.OPENAI_MODEL


def _ollama_base() -> str:
    return settings.OLLAMA_HOST.rstrip("/")


def active_backend_label() -> str:
    """Human-readable label for the configured primary backend (for UI/audit)."""
    if _use_api():
        return f"{_primary_model()} (OSS API)"
    return f"{settings.OLLAMA_MODEL} (local Ollama)"


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
def check_health() -> Dict[str, Any]:
    """Verifies the ACTIVE LLM backend (and reports the fallback's status too)."""
    primary = _check_primary()
    result: Dict[str, Any] = dict(primary)
    # Always surface the local Ollama status so a demo operator can see whether
    # the safety-net fallback is warm before the audience arrives.
    if _use_api():
        result["fallback"] = _check_ollama()
    return result


def _check_primary() -> Dict[str, Any]:
    if _use_api():
        base, model = _primary_base(), _primary_model()
        if not settings.OPENAI_API_KEY:
            return {
                "status": "NO_API_KEY", "host": base, "model": model,
                "hint": "Set OPENAI_API_KEY (and LLM_PROVIDER=openai_api).",
            }
        try:
            # OpenAI-compatible servers expose /models; use it as a cheap probe.
            resp = httpx.get(
                f"{base}/models",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                timeout=10.0,
            )
            resp.raise_for_status()
            ids = [m.get("id") for m in resp.json().get("data", [])]
            ok = (not ids) or any(model == i or str(i).endswith(model) for i in ids)
            return {
                "status": "READY" if ok else "MODEL_NOT_LISTED",
                "host": base, "model": model,
                "available_models": ids[:20],
                "hint": None if ok else f"Check OPENAI_MODEL='{model}' exists on {base}",
            }
        except httpx.HTTPError as exc:
            return {
                "status": "OFFLINE", "host": base, "model": model, "error": str(exc)[:200],
                "hint": "Check OPENAI_API_BASE / network; Ollama fallback will cover.",
            }
    return _check_ollama()


def _check_ollama() -> Dict[str, Any]:
    base, target = _ollama_base(), settings.OLLAMA_MODEL
    try:
        resp = httpx.get(f"{base}/api/tags", timeout=5.0)
        resp.raise_for_status()
        models = [m.get("name") for m in resp.json().get("models", [])]
        ok = any(m == target or (m and m.split(":")[0] == target.split(":")[0]) for m in models)
        return {
            "status": "READY" if ok else "MODEL_NOT_PULLED",
            "host": base, "model": target, "available_models": models,
            "hint": None if ok else f"Run: ollama pull {target}",
        }
    except httpx.HTTPError as exc:
        return {
            "status": "OFFLINE", "host": base, "model": target, "error": str(exc)[:200],
            "hint": "Start Ollama: `ollama serve` then pull the model.",
        }


# ---------------------------------------------------------------------------
# Completion (with automatic fallback primary -> ollama -> raise)
# ---------------------------------------------------------------------------
def chat_completion(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    stream: bool = False,
    temperature: float = 0.2,
    _retries: int = 1,
):
    """
    OpenAI-compatible completion against the ACTIVE backend.
    On primary failure, transparently retries once against local Ollama
    (when enabled) before raising OllamaUnavailableError (-> rule-based path).
    """
    errors: List[str] = []

    # ---- PRIMARY (OSS-20B API) ----
    if _use_api():
        try:
            return _complete_openai(
                base=_primary_base(), api_key=settings.OPENAI_API_KEY,
                model=_primary_model(), messages=messages, tools=tools,
                stream=stream, temperature=temperature,
            )
        except Exception as exc:  # noqa: BLE001 - record and fall through
            errors.append(f"api({ _primary_model() }): {str(exc)[:160]}")

    # ---- FALLBACK (local Ollama) ----
    if settings.LLM_FALLBACK_TO_OLLAMA:
        try:
            return _complete_openai(
                base=_ollama_base(), api_key="", model=settings.OLLAMA_MODEL,
                messages=messages, tools=tools, stream=stream,
                temperature=temperature, is_ollama=True,
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"ollama({settings.OLLAMA_MODEL}): {str(exc)[:160]}")

    # ---- BOTH DOWN -> orchestrator's rule-based fallback ----
    raise OllamaUnavailableError("No LLM backend available. " + " | ".join(errors))


def _complete_openai(
    base: str, api_key: str, model: str, messages, tools, stream, temperature,
    is_ollama: bool = False,
):
    """POST /chat/completions against any OpenAI-compatible base URL."""
    payload: Dict[str, Any] = {
        "model": model, "messages": messages,
        "temperature": temperature, "stream": stream,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    # Ollama serves its OpenAI-compatible API under /v1; provider base URLs
    # (Groq/OpenAI/etc.) already include /v1, so only Ollama needs the prefix.
    url = f"{base}/v1/chat/completions" if is_ollama else f"{base}/chat/completions"
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    if stream:
        req = httpx.build_request("POST", url, json=payload, headers=headers,
                                  timeout=CHAT_TIMEOUT_SECONDS)
        return httpx.Client().send(req, stream=True)

    resp = httpx.post(url, json=payload, headers=headers, timeout=CHAT_TIMEOUT_SECONDS)
    resp.raise_for_status()
    return resp.json()


def warm_model(keep_alive_minutes: int = 15) -> Dict[str, Any]:
    """
    Pre-warms the configured backend before the audience arrives.
    - OSS API: no local RAM to warm; send a 1-token probe to confirm reachability.
    - Ollama: loads the model into RAM via the native endpoint.
    """
    if _use_api():
        try:
            r = httpx.post(
                f"{_primary_base()}/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={"model": _primary_model(),
                      "messages": [{"role": "user", "content": "ready?"}],
                      "max_tokens": 3, "stream": False},
                timeout=CHAT_TIMEOUT_SECONDS,
            )
            r.raise_for_status()
            return {"status": "WARMED", "backend": active_backend_label(),
                    "sample": str(r.json()["choices"][0]["message"].get("content", ""))[:40]}
        except (httpx.HTTPError, httpx.TimeoutException, KeyError, IndexError) as exc:
            return {"status": "WARM_FAILED", "backend": active_backend_label(),
                    "error": str(exc)[:200]}
    try:
        resp = httpx.post(
            f"{_ollama_base()}/api/chat",
            json={"model": settings.OLLAMA_MODEL,
                  "messages": [{"role": "user", "content": "ready?"}],
                  "stream": False, "keep_alive": f"{keep_alive_minutes}m",
                  "options": {"num_predict": 3}},
            timeout=CHAT_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        return {"status": "WARMED", "backend": active_backend_label(),
                "sample": str(resp.json().get("message", {}).get("content", ""))[:40]}
    except (httpx.HTTPError, httpx.TimeoutException) as exc:
        return {"status": "WARM_FAILED", "backend": active_backend_label(),
                "error": str(exc)[:200]}


__all__ = [
    "check_health", "chat_completion", "warm_model",
    "OllamaUnavailableError", "active_backend_label",
]
