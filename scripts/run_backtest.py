"""
Rolling-origin backtest on REAL data -> forecast_metrics.json
Run after real-data ingestion and after Chronos-2 weights are cached:
    python scripts/run_backtest.py            # AP state series, h=14 & 30
    python scripts/run_backtest.py --all      # all four state aggregates

Writes: backend/app/forecasting/forecast_metrics.json
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
from app.domain.models import MarketObservation  # noqa: E402
from app.forecasting.backtest import evaluate_models_backtest  # noqa: E402

STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "app", "forecasting", "forecast_metrics.json")


def load_series(db, geography_id: str):
    rows = db.query(MarketObservation).filter(
        MarketObservation.commodity_id == settings.PILOT_COMMODITY_ID,
        MarketObservation.geography_id == geography_id,
        MarketObservation.is_demo_data == False,  # noqa: E712
    ).order_by(MarketObservation.date.asc()).all()
    return [{
        "date": r.date,
        "modal_price": r.modal_price,
        "arrivals_mt": r.arrivals_mt,
    } for r in rows]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Backtest all state geographies")
    parser.add_argument("--horizons", default="14,30", help="Comma-separated horizon buckets")
    args = parser.parse_args()

    horizons = [int(h) for h in args.horizons.split(",") if h.strip()]
    geographies = (
        ["state_andhra_pradesh", "state_maharashtra", "state_karnataka", "state_madhya_pradesh"]
        if args.all else [settings.PILOT_MARKET_ID]
    )

    store = {"generated_at": datetime.now(timezone.utc).isoformat(), "by_geography": {}}
    db = SessionLocal()
    try:
        for geo in geographies:
            series = load_series(db, geo)
            if len(series) < 100:
                print(f"[skip] {geo}: only {len(series)} real rows")
                continue
            store["by_geography"][geo] = {}
            for h in horizons:
                print(f"[backtest] {geo} h={h} ({len(series)} real rows) ...", flush=True)
                report = evaluate_models_backtest(series, horizon=h, use_chronos=True)
                store["by_geography"][geo][str(h)] = report
                for m in report["models"]:
                    print(f"    {m['model_name']:<32} MAE={m['mae']:>6} RMSE={m['rmse']:>6} "
                          f"WAPE={m['wape_pct']:>6}%  cov80={m.get('interval_80_coverage_pct')}")
                if report.get("note"):
                    print(f"    note: {report['note']}")
    finally:
        db.close()

    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
    with open(STORE_PATH, "w", encoding="utf-8") as fh:
        json.dump(store, fh, indent=2)
    print(f"\nSaved -> {os.path.abspath(STORE_PATH)}")


if __name__ == "__main__":
    main()
