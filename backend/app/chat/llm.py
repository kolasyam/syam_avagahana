"""
Ollama LLM Client (local, OpenAI-compatible)
============================================
Talks to the locally served Ollama model (settings.OLLAMA_MODEL — qwen2.5:3b-instruct)
via the OpenAI-compatible endpoints, with honest status reporting:

  - model reachable  → normal operation
  - model missing / offline → OLLAMA_UNAVAILABLE status; orchestrator falls
    back to deterministic templated answers labeled "RULE-BASED FALLBACK"
    (never pretends to be LLM-generated).
"""

import json
import time
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

CHAT_TIMEOUT_SECONDS = 240.0  # cold model load can take minutes on a tight RAM box


class OllamaUnavailableError(RuntimeError):
    pass


def _base_url() -> str:
    return settings.OLLAMA_HOST.rstrip("/")


def check_health() -> Dict[str, Any]:
    """Verifies the local LLM service and the configured model availability."""
    try:
        resp = httpx.get(f"{_base_url()}/api/tags", timeout=5.0)
        resp.raise_for_status()
        models = [m.get("name") for m in resp.json().get("models", [])]
        target = settings.OLLAMA_MODEL
        ok = any(m == target or m and m.split(":")[0] == target.split(":")[0] for m in models)
        return {
            "status": "READY" if ok else "MODEL_NOT_PULLED",
            "host": _base_url(),
            "model": target,
            "available_models": models,
            "hint": None if ok else f"Run: ollama pull {target}",
        }
    except httpx.HTTPError as exc:
        return {
            "status": "OFFLINE",
            "host": _base_url(),
            "model": settings.OLLAMA_MODEL,
            "error": str(exc),
            "hint": "Start Ollama: `ollama serve` then pull the model.",
        }


def chat_completion(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    stream: bool = False,
    temperature: float = 0.2,
    _retries: int = 1,
):
    """
    OpenAI-compatible completion against local Ollama.
    Retries once on transient failures (covers cold model-load timeouts).
    """
    payload: Dict[str, Any] = {
        "model": settings.OLLAMA_MODEL,
        "messages": messages,
        "temperature": temperature,
        "stream": stream,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    try:
        if stream:
            req = httpx.build_request(
                "POST", f"{_base_url()}/v1/chat/completions", json=payload, timeout=CHAT_TIMEOUT_SECONDS
            )
            return httpx.Client().send(req, stream=True)
        resp = httpx.post(
            f"{_base_url()}/v1/chat/completions",
            json=payload,
            timeout=CHAT_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.TimeoutException) as exc:
        if _retries > 0:
            time.sleep(3.0)
            return chat_completion(messages, tools, stream, temperature, _retries - 1)
        raise OllamaUnavailableError(f"Ollama at {_base_url()} failed: {exc}") from exc


def warm_model(keep_alive_minutes: int = 15) -> Dict[str, Any]:
    """
    Pre-loads the configured model into RAM (demo pre-warm).
    Cold 14B/3B loads can exceed request timeouts; call this before the
    audience arrives. Uses Ollama's native endpoint.
    """
    try:
        resp = httpx.post(
            f"{_base_url()}/api/chat",
            json={
                "model": settings.OLLAMA_MODEL,
                "messages": [{"role": "user", "content": "ready?"}],
                "stream": False,
                "keep_alive": f"{keep_alive_minutes}m",
                "options": {"num_predict": 3},
            },
            timeout=CHAT_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        return {"status": "WARMED", "model": settings.OLLAMA_MODEL,
                "sample": str(resp.json().get("message", {}).get("content", ""))[:40]}
    except (httpx.HTTPError, httpx.TimeoutException) as exc:
        return {"status": "WARM_FAILED", "error": str(exc)[:200]}


__all__ = ["check_health", "chat_completion", "warm_model", "OllamaUnavailableError"]
