"""
Web Fallback Tool with Trust Whitelist (Tavily)
===============================================
Implements the architecture's Market-Agent escalation rule:

  local DB missing / stale  →  web search via Tavily  →  trust-whitelist filter
  →  results returned WITH source citations, flagged:
       APPROVED_TRUST_SOURCE | UNVERIFIED_WEB_RESULT

Core governance rule (deck slides 16/19): web results are NEVER auto-ingested
into the forecasting model. They are advisory context + citations only. Any
use in the model pipeline requires human verification (roadmap; out of demo
scope by design decision — demo keeps ingest-off hardwired).

Honesty behavior:
  - No TAVILY_API_KEY  →  returns status WEB_SEARCH_UNAVAILABLE (no fake data).
  - Network failure    →  same, with the error surfaced.
  - Offline demo mode  →  cached demo queries from cache/web_cache.json
"""

import json
import os
import re
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

TAVILY_ENDPOINT = "https://api.tavily.com/search"
CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "web_cache.json")


def _classify_url(url: str) -> str:
    """Trust whitelist: government / news-of-record domains are approved."""
    host = (url.split("//")[-1].split("/")[0] or "").lower()
    if host.startswith("www."):
        host = host[4:]
    for domain in settings.WEB_TRUST_DOMAINS:
        if host == domain or host.endswith("." + domain):
            return "APPROVED_TRUST_SOURCE"
    return "UNVERIFIED_WEB_RESULT"


def _extract_prices(text: str) -> List[str]:
    """Pulls price-like mentions (₹/Rs + number) for quick agent triage.
    Extraction only — attribution stays attached to the source URL."""
    if not text:
        return []
    pattern = r"(?:₹|Rs\.?|INRS?)\s?(\d+(?:[.,]\d+)?)\s?(?:per|/)?\s?(kg|kilogram|quintal|qtl)?"
    hits = re.findall(pattern, text or "", flags=re.IGNORECASE)
    out = []
    for value, unit in hits[:5]:
        out.append(f"₹{value}{('/' + unit) if unit else ''}")
    return out


def _load_cache() -> Dict[str, Any]:
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            return {}
    return {}


def _save_cache(cache: Dict[str, Any]) -> None:
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as fh:
            json.dump(cache, fh, indent=2)
    except OSError:
        pass  # best-effort demo cache


def web_search_lookup(
    query: str,
    max_results: int = 5,
    hours_fresh: Optional[int] = 168,
) -> Dict[str, Any]:
    """
    Market Agent tool: escape-hatch web lookup.

    Returns a structured result envelope:
      status: WEB_RESULTS | WEB_SEARCH_UNAVAILABLE
      results: [{ title, url, snippet, trust, extracted_prices }]
      governance: { web_data_ingested_into_model: False, ... }
    """
    query = (query or "").strip()
    if not query:
        return {"status": "WEB_SEARCH_UNAVAILABLE", "error": "Empty query."}

    cache = _load_cache()
    if query in cache:
        return cache[query]

    if not settings.TAVILY_API_KEY:
        result = {
            "status": "WEB_SEARCH_UNAVAILABLE",
            "error": "TAVILY_API_KEY not configured. Web fallback disabled; "
                     "answer limited to ingested local series.",
            "results": [],
            "governance": {"web_data_ingested_into_model": False},
        }
        cache[query] = result
        _save_cache(cache)
        return result

    payload: Dict[str, Any] = {
        "api_key": settings.TAVILY_API_KEY,
        "query": query,
        "max_results": max_results,
        "search_depth": "basic",
        "include_answer": False,
        "include_raw_content": False,
        # Prefer whitelisted domains so social-media noise (FB/IG reels) never
        # crowds out citable market coverage.
        "include_domains": settings.WEB_TRUST_DOMAINS,
    }
    if hours_fresh:
        payload["topic"] = "news"
        payload["days"] = max(1, hours_fresh // 24)

    try:
        resp = httpx.post(TAVILY_ENDPOINT, json=payload, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()
        # Fallback: restricted search can return zero (gov domains rarely run
        # daily news). Retry unrestricted; everything still passes the trust
        # classifier and lands in the right tier.
        if not (data.get("results") or []):
            payload.pop("include_domains", None)
            resp = httpx.post(TAVILY_ENDPOINT, json=payload, timeout=15.0)
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, httpx.RequestError, ValueError) as exc:
        result = {
            "status": "WEB_SEARCH_UNAVAILABLE",
            "error": f"Tavily request failed: {exc}",
            "results": [],
            "governance": {"web_data_ingested_into_model": False},
        }
        cache[query] = result
        _save_cache(cache)
        return result

    results: List[Dict[str, Any]] = []
    for item in (data.get("results") or [])[:max_results]:
        snippet = item.get("content") or ""
        results.append({
            "title": item.get("title"),
            "url": item.get("url"),
            "snippet": snippet[:400],
            "trust": _classify_url(item.get("url") or ""),
            "extracted_prices": _extract_prices(snippet),
        })

    result = {
        "status": "WEB_RESULTS",
        "query": query,
        "results": results,
        "trust_summary": {
            "approved": sum(1 for r in results if r["trust"] == "APPROVED_TRUST_SOURCE"),
            "unverified": sum(1 for r in results if r["trust"] == "UNVERIFIED_WEB_RESULT"),
        },
        "governance": {
            "web_data_ingested_into_model": False,
            "note": "Web results are citation-only. Model ingestion requires "
                    "trust-whitelisted source + human verification (roadmap item).",
        },
    }
    cache[query] = result
    _save_cache(cache)
    return result


__all__ = ["web_search_lookup"]
