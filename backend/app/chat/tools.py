"""
Agent Tool Registry for the Chat Orchestrator
=============================================
The tools the LLM may invoke, mapped to the architecture diagram:

  Market Agent   → search_local_prices, latest_price, web_lookup (Tavily,
                   trust-filtered, citation-only), get_regions
  Forecast Agent → run_forecast (real Chronos-2), forecast_with_factor
                   (conversational add-factor sensitivity)
  Analysis Agent → get_risk (quantile-ladder breach probabilities)
  Response Agent → assembles citations + confidence in the orchestrator

Every tool returns a JSON-serializable dict. Any failure returns
{"status": "TOOL_ERROR", "error": ...} — the LLM never fabricates results.
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.chat.guardrails import check_factor_value, sanitize_horizon, web_topic_guard
from app.domain.models import ExternalObservation, ForecastRun, MarketObservation
from app.forecasting.chronos_adapter import probability_sheet
from app.tools.web_trust import web_search_lookup


# --------------------------------------------------------------------------- #
# Market Agent tools
# --------------------------------------------------------------------------- #

def search_local_prices(
    db: Session,
    geography_id: str = "state_andhra_pradesh",
    days: int = 60,
) -> Dict[str, Any]:
    """Local DB-1 lookup (Avagahana ingested series)."""
    rows = db.query(MarketObservation).filter(
        MarketObservation.commodity_id == settings.PILOT_COMMODITY_ID,
        MarketObservation.geography_id == geography_id,
    ).order_by(MarketObservation.date.desc()).limit(max(7, days)).all()

    if not rows:
        return {"status": "NOT_FOUND", "message": "No ingested observations for that geography.",
                "available_geographies": [settings.PILOT_MARKET_ID]}

    dates = [r.date for r in rows]
    # Price averages
    prices = [r.modal_price for r in rows]
    arrivals = [r.arrivals_mt for r in rows]
    window = min(len(rows), days)
    avg_window = sum(prices[:window]) / window
    avg_prev_30 = sum(prices[window: window + 30]) / max(1, len(prices[window: window + 30])) if len(prices) > window else None

    # Quantity / arrival averages
    avg_arr_window = sum(arrivals[:window]) / window
    avg_arr_prev_30 = sum(arrivals[window: window + 30]) / max(1, len(arrivals[window: window + 30])) if len(arrivals) > window else None

    result = {
        "status": "OK",
        "source": "Avagahana ingested series (AGMARKNET-derived, real)",
        "geography_id": geography_id,
        "cutoff_date": max(dates),
        "days_returned": len(rows),
        "latest_modal_inr_kg": round(prices[0], 2),
        "avg_modal_last_30d": round(avg_window, 2) if window <= 30 else None,
        "avg_modal_last_60d": round(avg_window, 2) if 30 < window <= 60 else None,
        "avg_modal_requested": round(avg_window, 2),
        "latest_arrivals_mt": round(arrivals[0], 2) if arrivals else None,
        "avg_arrivals_mt_requested": round(avg_arr_window, 2) if arrivals else None,
        "avg_arrivals_mt_14d": round(sum(arrivals[:min(14, len(arrivals))]) / min(14, len(arrivals)), 2) if arrivals else None,
        "avg_arrivals_mt_30d": round(sum(arrivals[:min(30, len(arrivals))]) / min(30, len(arrivals)), 2) if arrivals else None,
        "avg_prior_30d": round(avg_prev_30, 2) if avg_prev_30 else None,
        "presentation_hints": {
            "price": (
                f"Quote: average modal price ₹{avg_window:.2f}/kg (window {window}d); "
                f"latest price ₹{prices[0]:.2f}/kg on {max(dates)}."
            ),
            "quantity": (
                f"Quote: average arrivals {avg_arr_window:.2f} MT over {window} days; "
                f"latest arrivals {arrivals[0]:.2f} MT (date {max(dates)}). "
                "Arrivals are real ingested series (AGMARKNET-derived), not estimates."
            ),
        },
        "change_vs_prior": round((prices[0] - prices[-1]) / prices[-1] * 100.0, 1) if prices[-1] else None,
    }
    # explicit window averages for precise answering
    result["avg_modal_last_14d"] = round(sum(prices[:14]) / min(14, len(prices)), 2)
    return result


def latest_price(db: Session, geography_id: str = "state_andhra_pradesh") -> Dict[str, Any]:
    """Latest ingested observation + staleness assessment (drives web fallback)."""
    row = db.query(MarketObservation).filter(
        MarketObservation.commodity_id == settings.PILOT_COMMODITY_ID,
        MarketObservation.geography_id == geography_id,
    ).order_by(MarketObservation.date.desc()).first()

    if not row:
        return {"status": "NOT_FOUND"}

    today = datetime.now().strftime("%Y-%m-%d")
    stale = row.date < today
    alert = settings.ONION_ALERT_THRESHOLD
    return {
        "status": "OK",
        "source": f"Ingested real series ({row.source_id})",
        "geography_id": geography_id,
        "modal_price_inr_kg": row.modal_price,
        "arrivals_mt": row.arrivals_mt,
        "date": row.date,
        "is_today": not stale,
        "staleness_days": (datetime.now() - datetime.strptime(row.date, "%Y-%m-%d")).days,
        "recommend_web_fallback": stale,
        "alert_threshold": alert,
        "presentation_hints": {
            "alert_positioning": (
                f"Quote exactly: latest ingested price ₹{row.modal_price:.2f}/kg is "
                f"{('ABOVE' if row.modal_price >= alert else 'BELOW')} the alert "
                f"threshold of ₹{alert:.2f}/kg — use the correct direction."
            ),
            "quantity": (
                f"Quote exactly: latest ingested arrivals are {row.arrivals_mt:.2f} MT "
                f"on {row.date}. Arrivals are real ingested series, not estimates."
            ),
        },
    }


def get_regions(db: Session) -> Dict[str, Any]:
    geos = db.query(MarketObservation.geography_id).filter(
        MarketObservation.commodity_id == settings.PILOT_COMMODITY_ID,
        MarketObservation.is_demo_data == False,  # noqa: E712
    ).distinct().all()
    return {
        "status": "OK",
        "geographies_with_data": sorted({g[0] for g in geos}),
        "note": "District mandis are reference sites until district-level ingest completes.",
    }


def web_lookup(db: Session, query: str) -> Dict[str, Any]:
    """
    Market Agent escalation: Tavily web fallback (citation-only).
    GUARDRAIL (L2): the topic gate restricts the web tool to agriculture /
    market / weather queries — it cannot be used as a general search engine.
    Attaches grounding hints so the local LLM uses the citations instead of
    asking permission to search (the lookup is auto-executed upstream).
    """
    guard = web_topic_guard(query)
    if not guard["allowed"]:
        return {
            "status": "WEB_BLOCKED",
            "blocked_reason": guard["reason"],
            "allowed_topics": guard.get("allowed_topics"),
            "governance": {
                "web_data_ingested_into_model": False,
                "guardrail": "web_topic_gate (agriculture/market/weather only)",
            },
            "results": [],
            "presentation_hints": {
                "usage": (
                    "The web lookup was BLOCKED by the platform guardrail "
                    "(off-scope topic). State that the web tool only serves "
                    "agriculture, market and weather topics, and answer from "
                    "the ingested series instead. Do NOT retry the web call."
                ),
            },
        }

    result = web_search_lookup(query, hours_fresh=None)
    try:
        last = db.query(MarketObservation).filter(
            MarketObservation.commodity_id == settings.PILOT_COMMODITY_ID,
            MarketObservation.geography_id == "state_andhra_pradesh",
        ).order_by(MarketObservation.date.desc()).first()
        last_str = f"₹{last.modal_price}/kg on {last.date}" if last else "unavailable"

        if result.get("status") == "WEB_RESULTS":
            top = result.get("results") or []
            citations = "; ".join(
                f"{(r.get('title') or '')[:70]} "
                f"({(r.get('url') or '').split('//')[-1].split('/')[0]})"
                for r in top[:3] if r.get("url")
            )
            result["presentation_hints"] = {
                "usage": (
                    "The web lookup has ALREADY executed automatically. Do NOT ask the "
                    "user for permission to search, and do NOT offer to search later."
                ),
                "answer": (
                    f"Quote closely: 'The platform's last INGESTED onion price is "
                    f"{last_str} (AGMARKNET-derived) — web findings are context "
                    "citations only and are never ingested into the model.' Then "
                    "briefly summarize what the web citations say about current "
                    "onion prices, labeling each source approved-trusted or "
                    "unverified."
                ),
                "top_citations": citations,
            }
        else:
            result["presentation_hints"] = {
                "usage": (
                    "Web search is unavailable right now. State that honestly, give "
                    f"the last ingested price ({last_str}), and do NOT invent a "
                    "current price."
                ),
            }
    except Exception:
        pass  # hints are best-effort; the raw result is always intact
    return result


# --------------------------------------------------------------------------- #
# Forecast Agent tools
# --------------------------------------------------------------------------- #

def _served_forecast(db: Session, geography_id: str, horizon: int) -> Optional[Dict[str, Any]]:
    run = db.query(ForecastRun).filter(
        ForecastRun.commodity_id == settings.PILOT_COMMODITY_ID,
        ForecastRun.geography_id == geography_id,
        ForecastRun.horizon_days == horizon,
        ForecastRun.status.in_(["CHRONOS2_REAL", "ARLAG_FALLBACK"]),
    ).order_by(ForecastRun.run_date.desc(), ForecastRun.id.desc()).first()
    if run is None:
        return None
    return {
        "run": run,
        "points": json.loads(run.forecast_series_json),
    }


def run_forecast(db: Session, geography_id: str, horizon: int) -> Dict[str, Any]:
    """Serves the precomputed real forecast (fast) or computes live."""
    # GUARDRAIL (L2): horizons come from the LLM — clamp to the supported band.
    horizon = sanitize_horizon(horizon)
    served = _served_forecast(db, geography_id, horizon)
    if served is None:
        from app.api.v1.forecast import _predict_with_champion_or_fallback
        rows = db.query(MarketObservation).filter(
            MarketObservation.commodity_id == settings.PILOT_COMMODITY_ID,
            MarketObservation.geography_id == geography_id,
        ).order_by(MarketObservation.date.asc()).all()
        if len(rows) < 14:
            return {"status": "NOT_FOUND", "message": "Insufficient history."}
        import pandas as pd
        df = pd.DataFrame([{"date": r.date, "modal_price": r.modal_price} for r in rows])
        model_out = _predict_with_champion_or_fallback(df, horizon)
        points, model_name, status = model_out["points"], model_out["model_name"], model_out["status"]
    else:
        points = served["points"]
        model_name, status = served["run"].model_name, served["run"].status

    last = points[-1]
    risk = probability_sheet(points, alert=settings.ONION_ALERT_THRESHOLD, crisis=settings.ONION_CRISIS_THRESHOLD)
    first_alert = risk.get("first_median_breach_day_alert")
    return {
        "status": "OK",
        "source": f"Model: {model_name} ({status}) on real ingested data",
        "geography_id": geography_id,
        "horizon_days": horizon,
        "cutoff": points[-1]["date"] if horizon == 1 else (points[0]["date"] if points else None),
        "day1_forecast": points[0] if points else None,
        "day30_forecast": points[min(30, horizon) - 1] if horizon >= 30 else None,
        "horizon_end_forecast": last,
        "alert_breach": {
            "threshold": settings.ONION_ALERT_THRESHOLD,
            "max_exceedance_within_30d": risk.get("alert_exceedance", {}).get("max_within_30d"),
            "first_median_breach_day": first_alert,
        },
        "crisis_breach": {
            "threshold": settings.ONION_CRISIS_THRESHOLD,
            "max_exceedance_within_30d": risk.get("crisis_exceedance", {}).get("max_within_30d"),
        },
        "probability_method": risk.get("method"),
        # Pre-formatted lines for local LLMs to echo verbatim (prevents the
        # model paraphrasing a 9.7% exceedance as "no chance").
        "presentation_hints": {
            "alert": (
                f"Quote exactly: alert ₹{settings.ONION_ALERT_THRESHOLD:.2f}/kg breach "
                f"probability within the first 30 days is "
                f"{round((risk.get('alert_exceedance', {}).get('max_within_30d') or 0)*100, 1)}%."
            ),
            "crisis": (
                f"Quote exactly: crisis ₹{settings.ONION_CRISIS_THRESHOLD:.2f}/kg breach "
                f"probability within the first 30 days is "
                f"{round((risk.get('crisis_exceedance', {}).get('max_within_30d') or 0)*100, 1)}%. "
                f"Report this percentage even though it is small."
            ),
        },
    }


def _resolve_geography(db: Session, requested: str) -> Optional[str]:
    """Fuzzy geographic resolution — local models mistype ids; never fail on that."""
    candidates = [g for (g,) in db.query(MarketObservation.geography_id).distinct().all()]
    req = (requested or "").lower()
    norm = lambda s: re.sub(r"[^a-z]", "", s or "")
    if req in candidates:
        return req
    nreq = norm(req)
    if not nreq:
        return None
    for cand in candidates:
        nc = norm(cand)
        # typo-tolerant containment: 'state_andhra_pr Pradesh' -> 'stateandhrapr' ⊂ 'stateandhrapradesh'
        if nreq in nc and len(nreq) >= 5:
            return cand
        # common word hits: 'andhra' inside 'state_andhra_pradesh'
        for token in ("andhra", "karnatak", "maharashtr", "madhya"):
            if token in nreq or token in req:
                if token in cand:
                    return cand
    return None


_VARIABLE_ALIASES = None  # legacy marker kept out — resolution is in _resolve_variable


def _resolve_variable(requested: str, available: List[str]) -> Optional[str]:
    """Maps user-friendly factor names to ingested variable names."""
    req = (requested or "").lower().strip()
    if req in available:
        return req
    has = lambda *ws: any(w in req for w in ws)
    if "season" in req and has("rain"):
        cand = "seasonal_rain_mm"
    elif has("rain", "monsoon", "precip"):
        cand = "precipitation_mm"
    elif "season" in req and has("vpd", "vapor", "vapour"):
        cand = "seasonal_vpd_kpa"
    elif has("vpd", "vapor", "vapour"):
        cand = "vpd_kpa"
    elif has("fuel", "diesel", "petrol", "gas price"):
        cand = "fuel_price_avg"
    elif has("production", "harvest"):
        cand = "production_kt"
    elif has("retail"):
        cand = "retail_price_inr_kg"
    else:
        cand = req
    for a in available:
        if cand and (norm_req := re.sub(r"[^a-z0-9]", "", cand)) and norm_req in re.sub(r"[^a-z0-9]", "", a):
            return a
    return None


def forecast_with_factor(
    db: Session,
    geography_id: str,
    variable_name: str,
    future_value: float,
    horizon: int = 30,
) -> Dict[str, Any]:
    """
    Conversational 'add factor' WHAT-IF: re-runs the real Chronos-2 model with a
    user-proposed future value for a covariate (e.g. rainfall 150 mm/14d).
    Honesty: if covariate conditioning isn't supported at run time, returns a
    clear PARTIAL result (qualitative sensitivity) — no fabricated scenario data.
    Geography/variable names are fuzzy-resolved (local models mistype them),
    and every non-OK path carries anti-rumor instructions for the LLM.
    """
    HONESTY_PROTOCOL = (
        "You must NOT claim this factor had any effect on the forecast — it was "
        "NOT applied. State the reason, list the available factors, and offer to "
        "retry with one of them."
    )

    geo = _resolve_geography(db, geography_id)
    if geo is None:
        all_geos = sorted({g for (g,) in db.query(MarketObservation.geography_id).distinct().all()})
        return {"status": "NOT_FOUND", "reason": f"Unknown geography '{geography_id}'.",
                "available_geographies": all_geos, "answer_protocol": HONESTY_PROTOCOL}

    # Historical covariate series from external observations
    available = sorted({
        v for (v,) in db.query(ExternalObservation.variable_name)
        .filter(ExternalObservation.geography_id == geo).distinct().all()
    })
    variable = _resolve_variable(variable_name, available)
    if variable is None:
        return {
            "status": "NOT_FOUND",
            "reason": f"Factor '{variable_name}' is not available for {geo}.",
            "available_variables": available,
            "answer_protocol": HONESTY_PROTOCOL,
        }

    # GUARDRAIL (L2): scenario values must be sane — no negative rainfall, no
    # absurd magnitudes reaching the real model.
    value_check = check_factor_value(variable, future_value)
    if not value_check["ok"]:
        lo, hi = {"precipitation_mm": (0.0, 600.0), "temperature_c": (-5.0, 60.0)}.get(
            variable, (0.0, 100000.0))
        return {
            "status": "REJECTED",
            "reason": value_check["reason"],
            "supported_range": f"{lo} to {hi}",
            "answer_protocol": (
                "You must NOT run any re-forecast and must NOT claim the factor "
                "had any effect. Explain the supported range and ask the user "
                "to retry with a value inside it."
            ),
        }
    hist = db.query(ExternalObservation).filter(
        ExternalObservation.geography_id == geo,
        ExternalObservation.variable_name == variable,
    ).order_by(ExternalObservation.date.asc()).all()
    if not hist:
        return {"status": "NOT_FOUND", "reason": f"No history rows for {variable}.",
                "available_variables": available, "answer_protocol": HONESTY_PROTOCOL}

    # Baseline (cached) forecast for delta measurement
    served = _served_forecast(db, geo, min(horizon, 30)) or _served_forecast(db, geo, 30)
    if served is None:
        return {"status": "TOOL_ERROR", "error": "No cached baseline forecast to diff against.",
                "answer_protocol": HONESTY_PROTOCOL}

    # Attempt REAL covariate-conditioned inference — in an ISOLATED subprocess.
    # Why (demo-critical): on the 7.3 GB demo box, native torch inference under
    # RAM pressure crashed the whole uvicorn server mid-SSE. Isolated worker:
    # a crash costs only the child process; the tool reports an honest PARTIAL
    # and the chat session keeps streaming.
    resolved = {"variable": variable, "future_value": future_value, "geography_id": geo}
    try:
        import subprocess
        import sys
        import tempfile
        from pathlib import Path

        # 1) Pre-computed scenario cache (scripted demo values hit this path —
        #    instant and torch-free).
        cache_path = Path(__file__).resolve().parents[2] / "app" / "forecasting" / "factor_scenarios.json"
        key = f"{geo}|{variable}|{future_value:g}|{horizon}"
        if cache_path.exists():
            try:
                cache = json.loads(cache_path.read_text(encoding="utf-8"))
                if isinstance(cache.get(key), dict) and cache[key].get("status") == "OK":
                    result = dict(cache[key])
                    result["cached"] = True
                    result.setdefault("answer_protocol",
                                      "Pre-computed real scenario — quote its numbers verbatim.")
                    return result
            except (OSError, ValueError, KeyError):
                pass  # corrupted cache → fall through to compute

        # 2) Isolated compute worker (scripts/compute_factor_scenario.py).
        backend_root = Path(__file__).resolve().parents[2]
        runner = backend_root / "scripts" / "compute_factor_scenario.py"
        with tempfile.NamedTemporaryFile("r", encoding="utf-8", suffix=".json", delete=False) as tf:
            out_path = Path(tf.name)
        try:
            proc = subprocess.run(
                [sys.executable, str(runner),
                 "--geography", geo, "--variable", variable,
                 "--future-value", str(future_value),
                 "--horizon", str(horizon), "--out", str(out_path)],
                cwd=str(backend_root), timeout=600, capture_output=True,
            )
            try:
                result = json.loads(out_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                result = None
            if result is None:
                result = {"status": "PARTIAL",
                          "reason": f"Scenario worker produced no result (rc={proc.returncode}).",
                          **resolved,
                          "answer_protocol": "Report the PARTIAL status and reason only. You must NOT claim any numeric effect on the forecast."}
        except subprocess.TimeoutExpired:
            result = {"status": "PARTIAL", "reason": "Scenario re-forecast exceeded the compute timeout (600 s).",
                      **resolved,
                      "answer_protocol": "Report the PARTIAL status and reason only. You must NOT claim any numeric effect on the forecast."}
        finally:
            try:
                out_path.unlink(missing_ok=True)
            except OSError:
                pass

        if result.get("status") == "OK":
            # Persist for the offline demo: same question next time is instant.
            try:
                cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
            except (OSError, ValueError):
                cache = {}
            cache[key] = result
            try:
                cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
            except OSError:
                pass
            return result

        # Worker already wrote a truthful PARTIAL receipt (incl. native crash)
        if "answer_protocol" not in result:
            result.setdefault("answer_protocol",
                              "Report the PARTIAL status and reason only. You must NOT claim any numeric effect on the forecast.")
        return result

    except Exception as exc:  # safety net — tools never crash the orchestrator
        return {
            "status": "PARTIAL",
            "reason": f"Scenario tool failed ({type(exc).__name__}: {exc}).",
            **resolved,
            "answer_protocol": "Report the PARTIAL status and reason only. You must NOT claim any numeric effect on the forecast.",
        }


# --------------------------------------------------------------------------- #
# Analysis Agent tool
# --------------------------------------------------------------------------- #

def get_risk(db: Session, geography_id: str) -> Dict[str, Any]:
    rows = db.query(MarketObservation).filter(
        MarketObservation.commodity_id == settings.PILOT_COMMODITY_ID,
        MarketObservation.geography_id == geography_id,
    ).order_by(MarketObservation.date.desc()).limit(10).all()
    if not rows:
        return {"status": "NOT_FOUND"}
    return {
        "status": "OK",
        "geography_id": geography_id,
        "commodity": "onion",
        "alert_threshold": settings.ONION_ALERT_THRESHOLD,
        "crisis_threshold": settings.ONION_CRISIS_THRESHOLD,
        "latest_modal_inr_kg": rows[0].modal_price,
        "headroom_to_alert": round(settings.ONION_ALERT_THRESHOLD - rows[0].modal_price, 2),
        "risk_ladder": [
            {"date": r.date, "modal_inr_kg": r.modal_price, "arrivals_mt": r.arrivals_mt} for r in rows[:5]
        ],
        "note": "Full breach probabilities available via run_forecast (quantile ladder).",
    }


TOOL_REGISTRY = {
    "search_local_prices": search_local_prices,
    "latest_price": latest_price,
    "get_regions": get_regions,
    "web_lookup": web_lookup,
    "run_forecast": run_forecast,
    "forecast_with_factor": forecast_with_factor,
    "get_risk": get_risk,
}


OPENAI_TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_local_prices",
            "description": "Search the ingested real price series (per geography). Returns averages over requested windows, latest prices and trends. Use for historical/statistical questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "geography_id": {"type": "string", "description": "One of the available geographies, e.g. state_andhra_pradesh"},
                    "days": {"type": "integer", "description": "Window length in days (default 60)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "latest_price",
            "description": "Get the most recent ingested price observation and its staleness. If stale (>today), follow up with web_lookup for today's market news.",
            "parameters": {
                "type": "object",
                "properties": {
                    "geography_id": {"type": "string"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_lookup",
            "description": "Escape-hatch web search (citation-only, trust-filtered). Use ONLY when local data is missing/stale for the question, e.g. today's live market price.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_forecast",
            "description": "Run/serve the real Chronos-2 foundation-model forecast for a geography and horizon (7/14/30/60/90 days). Quantile bands incl. breach probabilities vs alert/crisis thresholds.",
            "parameters": {
                "type": "object",
                "properties": {
                    "geography_id": {"type": "string"},
                    "horizon": {"type": "integer", "enum": [7, 14, 30, 60, 90]},
                },
                "required": ["geography_id", "horizon"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "forecast_with_factor",
            "description": "Conversational WHAT-IF: re-run the forecast with a user-proposed future value for a factor (e.g. precipitation, fuel). Returns expected price delta vs baseline.",
            "parameters": {
                "type": "object",
                "properties": {
                    "geography_id": {"type": "string"},
                    "variable_name": {"type": "string", "description": "e.g. precipitation_mm, fuel_price_avg, production_kt"},
                    "future_value": {"type": "number"},
                    "horizon": {"type": "integer", "enum": [7, 14, 30, 60, 90]},
                },
                "required": ["geography_id", "variable_name", "future_value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_risk",
            "description": "Risk snapshot: latest price vs alert/crisis thresholds and headroom.",
            "parameters": {
                "type": "object",
                "properties": {"geography_id": {"type": "string"}},
                "required": [],
            },
        },
    },
]
