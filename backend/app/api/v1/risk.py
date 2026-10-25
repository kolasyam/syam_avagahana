"""
Price Spike Risk API Endpoints
==============================
Computes risk LIVE from the latest real forecast (Chronos-2 quantile ladder)
plus data-derived drivers. No stored pseudo-random or hardcoded rows.
"""

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
import pandas as pd

from app.core.config import settings
from app.core.database import get_db
from app.domain.models import ExternalObservation, ForecastRun, MarketObservation
from app.domain.schemas import RiskAssessmentOut
from app.forecasting.chronos_adapter import probability_sheet
from app.forecasting.tabular_model import AutoregressiveCovariateModel

from app.api.v1.forecast import _predict_with_champion_or_fallback

router = APIRouter()


def _arrival_dynamics(db: Session, geography_id: str, window_days: int = 30) -> Dict[str, Any]:
    """Data-derived arrival momentum for the drivers list (real numbers only)."""
    rows = db.query(MarketObservation).filter(
        MarketObservation.commodity_id == settings.PILOT_COMMODITY_ID,
        MarketObservation.geography_id == geography_id,
    ).order_by(MarketObservation.date.desc()).limit(window_days * 2).all()

    if len(rows) < window_days + 5:
        return {}

    recent = rows[:window_days]
    prior = rows[window_days: window_days * 2]
    arrivals_now = sum(r.arrivals_mt for r in recent) / max(1, len(recent))
    arrivals_prior = sum(r.arrivals_mt for r in prior) / max(1, len(prior))
    price_change = (
        (recent[0].modal_price - prior[0].modal_price) / prior[0].modal_price * 100.0
        if prior[0].modal_price else 0.0
    )
    return {
        "arrivals_recent_avg_mt": round(arrivals_now, 1),
        "arrivals_prior_avg_mt": round(arrivals_prior, 1),
        "arrivals_change_pct": round((arrivals_now - arrivals_prior) / arrivals_prior * 100.0, 1) if arrivals_prior else 0.0,
        "price_change_pct_window": round(price_change, 1),
    }


def _weather_context(db: Session, geography_id: str, window_days: int = 14) -> Optional[Dict[str, Any]]:
    rows = db.query(ExternalObservation).filter(
        ExternalObservation.geography_id == geography_id,
        ExternalObservation.variable_name.in_(["precipitation_mm", "vpd_kpa"]),
    ).order_by(ExternalObservation.date.desc()).limit(window_days * 2).all()
    if not rows:
        return None
    rain = [r.value for r in rows if r.variable_name == "precipitation_mm"]
    vpd = [r.value for r in rows if r.variable_name == "vpd_kpa"]
    return {
        "cum_rain_14d_mm": round(sum(rain[:window_days]), 1),
        "avg_vpd_kpa": round(sum(vpd[:window_days]) / max(1, len(vpd[:window_days])), 3),
    }


def _build_drivers(db: Session, geography_id: str, risk: Dict[str, Any]) -> List[Dict[str, Any]]:
    drivers: List[Dict[str, Any]] = []
    dyn = _arrival_dynamics(db, geography_id)
    weather = _weather_context(db, geography_id)

    if dyn:
        if dyn["arrivals_change_pct"] < -10:
            drivers.append({
                "factor": "Arrival contraction",
                "direction": "UPWARD_PRICE_PRESSURE",
                "evidence": f"Average arrivals {dyn['arrivals_recent_avg_mt']} MT/day vs "
                            f"{dyn['arrivals_prior_avg_mt']} MT/day in prior window ({dyn['arrivals_change_pct']:+.1f}%)."
            })
        elif dyn["arrivals_change_pct"] > 10:
            drivers.append({
                "factor": "Arrival expansion",
                "direction": "DOWNWARD_PRICE_PRESSURE",
                "evidence": f"Average arrivals {dyn['arrivals_recent_avg_mt']} MT/day "
                            f"({dyn['arrivals_change_pct']:+.1f}% vs prior window)."
            })
        drivers.append({
            "factor": "Recent price momentum",
            "direction": "UPWARD_PRICE_PRESSURE" if dyn["price_change_pct_window"] > 1
                         else "DOWNWARD_PRICE_PRESSURE" if dyn["price_change_pct_window"] < -1
                         else "NEUTRAL",
            "evidence": f"Modal price moved {dyn['price_change_pct_window']:+.1f}% across the last ~30 days."
        })
    if weather:
        if weather["cum_rain_14d_mm"] > 100:
            drivers.append({
                "factor": "Elevated rainfall",
                "direction": "UPWARD_PRICE_PRESSURE",
                "evidence": f"Cumulative 14-day precipitation {weather['cum_rain_14d_mm']} mm "
                            "(harvest/logistics disruption risk in producing belts)."
            })
        else:
            drivers.append({
                "factor": "Weather normal",
                "direction": "NEUTRAL",
                "evidence": f"Cumulative 14-day precipitation {weather['cum_rain_14d_mm']} mm; "
                            f"avg VPD {weather['avg_vpd_kpa']} kPa."
            })
    drivers.append({
        "factor": "Forecast distribution (Chronos-2)",
        "direction": "UPWARD_PRICE_PRESSURE" if risk.get("alert_exceedance", {}).get("max_within_30d", 0) > 0.2
                     else "NEUTRAL",
        "evidence": "Exceedance probabilities derived from the zero-shot forecast "
                    "distribution (quantile-ladder interpolation)."
    })
    return drivers


@router.get("/latest", response_model=RiskAssessmentOut)
def get_latest_risk(
    commodity_id: str = Query("onion"),
    geography_id: str = Query(settings.PILOT_MARKET_ID),
    db: Session = Depends(get_db)
):
    """Live risk from the newest cached real forecast; computes a fresh
    forecast only if no cached run exists."""
    run: Optional[ForecastRun] = db.query(ForecastRun).filter(
        ForecastRun.commodity_id == commodity_id,
        ForecastRun.geography_id == geography_id,
        ForecastRun.status.in_(["CHRONOS2_REAL", "ARLAG_FALLBACK"]),
    ).order_by(ForecastRun.run_date.desc(), ForecastRun.id.desc()).first()

    if run is not None:
        points = json.loads(run.forecast_series_json)
        horizon = run.horizon_days
        model_name = run.model_name
    else:
        obs = db.query(MarketObservation).filter(
            MarketObservation.commodity_id == commodity_id,
            MarketObservation.geography_id == geography_id,
        ).order_by(MarketObservation.date.asc()).all()
        if len(obs) < 14:
            raise HTTPException(status_code=404, detail="No forecast history available for risk computation.")
        df = pd.DataFrame([{"date": o.date, "modal_price": o.modal_price} for o in obs])
        result = _predict_with_champion_or_fallback(df, 30)
        points = result["points"]
        horizon = 30
        model_name = result["model_name"]

    risk = probability_sheet(
        points, alert=settings.ONION_ALERT_THRESHOLD, crisis=settings.ONION_CRISIS_THRESHOLD
    )
    spike_prob = float(risk.get("alert_exceedance", {}).get("max_within_30d", 0.0))
    drivers = _build_drivers(db, geography_id, risk)

    threshold = risk.get("first_median_breach_day_alert")
    narrative = (
        f"Based on {model_name} ({horizon}-day horizon), the probability that AP modal price "
        f"exceeds the alert threshold ₹{settings.ONION_ALERT_THRESHOLD}/kg within 30 days is "
        f"{spike_prob*100:.0f}%. "
        + (f"Median path first crosses the alert threshold on day {threshold}. "
           if threshold is not None else
           "The median forecast path does not cross the alert threshold in this horizon. ")
        + f"Crisis threshold ₹{settings.ONION_CRISIS_THRESHOLD}/kg exceedance within 30 days: "
        f"{risk.get('crisis_exceedance', {}).get('max_within_30d', 0.0)*100:.0f}%."
    )

    return {
        "id": f"risk_{geography_id}_{run.id if run else 'live'}",
        "commodity_id": commodity_id,
        "geography_id": geography_id,
        "assessment_date": run.data_cutoff_date if run else points[-1]["date"],
        "horizon_days": horizon,
        "spike_probability": spike_prob,
        "threshold_level": f"ALERT_{int(settings.ONION_ALERT_THRESHOLD)}",
        "primary_drivers": drivers,
        "narrative": narrative,
    }
