"""
Precompute cached forecast runs for the demo (instant /forecast/latest).
Runs the real Chronos-2 model once per (geography, horizon) and persists
ForecastRun rows with status CHRONOS2_REAL.

    python scripts/precompute_forecasts.py           # pilot geography, 7..90d
    python scripts/precompute_forecasts.py --all     # all four state aggregates
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8")  # Windows console: allow ₹/unicode

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.database import SessionLocal  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.domain.models import ForecastRun, MarketObservation  # noqa: E402
from app.forecasting.chronos_adapter import (
    Chronos2FoundationModel,
    ChronosUnavailableError,
    probability_sheet,
)  # noqa: E402
from app.forecasting.tabular_model import AutoregressiveCovariateModel  # noqa: E402

HORIZONS = settings.DEFAULT_FORECAST_HORIZONS  # [7, 14, 30, 60, 90]


def load_df(db, geography_id: str):
    rows = db.query(MarketObservation).filter(
        MarketObservation.commodity_id == settings.PILOT_COMMODITY_ID,
        MarketObservation.geography_id == geography_id,
        MarketObservation.is_demo_data == False,  # noqa: E712
    ).order_by(MarketObservation.date.asc()).all()
    import pandas as pd
    return pd.DataFrame([{
        "date": r.date,
        "modal_price": r.modal_price,
        "arrivals_mt": r.arrivals_mt,
    } for r in rows])


def sweep_existing(db, geography_id: str, horizon: int):
    return db.query(ForecastRun).filter(
        ForecastRun.commodity_id == settings.PILOT_COMMODITY_ID,
        ForecastRun.geography_id == geography_id,
        ForecastRun.horizon_days == horizon,
        ForecastRun.status == "CHRONOS2_REAL",
        ForecastRun.data_cutoff_date == _latest_cutoff(db, geography_id),
    ).first()


def _latest_cutoff(db, geography_id: str):
    latest = db.query(MarketObservation.date).filter(
        MarketObservation.commodity_id == settings.PILOT_COMMODITY_ID,
        MarketObservation.geography_id == geography_id,
    ).order_by(MarketObservation.date.desc()).first()
    return latest[0] if latest else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    geographies = (
        ["state_andhra_pradesh", "state_maharashtra", "state_karnataka", "state_madhya_pradesh"]
        if args.all else [settings.PILOT_MARKET_ID]
    )

    db = SessionLocal()
    try:
        try:
            adapter = Chronos2FoundationModel()
            adapter.get_pipeline()  # force load now, outside the loop
        except ChronosUnavailableError as exc:
            print(f"CHRONOS-2 UNAVAILABLE -> {exc}")
            print("Falling back to AR-Lag runs (labeled honestly), no fake Chronos rows written.")
            adapter = None

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        for geo in geographies:
            df = load_df(db, geo)
            if len(df) < 30:
                print(f"[skip] {geo}: only {len(df)} rows")
                continue
            cutoff = df["date"].max()
            for h in HORIZONS:
                if sweep_existing(db, geo, h) is not None:
                    print(f"[cached] {geo} h={h}")
                    continue
                if adapter is not None:
                    points = adapter.predict(df, h, item_id=f"onion_{geo}")
                    model_name = "Amazon Chronos-2 (pretrained, zero-shot)"
                    model_version = "chronos-2 / apache-2.0"
                    status = "CHRONOS2_REAL"
                else:
                    points = AutoregressiveCovariateModel().predict(df, h)
                    model_name = "AR-Lag Tabular (Ridge) — FALLBACK: Chronos-2 unavailable"
                    model_version = "v1-tabular-fallback"
                    status = "ARLAG_FALLBACK"

                risk = probability_sheet(
                    points, alert=settings.ONION_ALERT_THRESHOLD, crisis=settings.ONION_CRISIS_THRESHOLD
                )
                run = ForecastRun(
                    id=f"fc_{geo}_{h}d_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                    commodity_id=settings.PILOT_COMMODITY_ID,
                    geography_id=geo,
                    run_date=today,
                    model_name=model_name,
                    model_version=model_version,
                    horizon_days=h,
                    forecast_series_json=json.dumps(points),
                    metrics_json=json.dumps({"risk_projection": risk, "status_note": "precomputed"}),
                    data_cutoff_date=cutoff,
                    status=status,
                )
                db.add(run)
                db.commit()
                last = points[-1]["predicted_modal"]
                print(f"[done]  {geo} h={h:>2}  cutoff={cutoff}  end_forecast=₹{last}/kg  status={status}")
    finally:
        db.close()
    print("\nAll cached. /api/v1/forecast/latest will now serve instantly.")


if __name__ == "__main__":
    main()
