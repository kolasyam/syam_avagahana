"""
Smoke test: real Chronos-2 on the real ingested AP series.
    python scripts/smoke_chronos.py
Loads the last state series from SQLite, runs a 30-day real forecast,
prints quantile sanity output + breach probability against thresholds.
"""

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")  # Windows console: allow ₹/unicode

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.database import SessionLocal  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.domain.models import MarketObservation  # noqa: E402
from app.forecasting.chronos_adapter import (  # noqa: E402
    Chronos2FoundationModel,
    ChronosUnavailableError,
    probability_sheet,
)
import pandas as pd  # noqa: E402


def main():
    db = SessionLocal()
    try:
        rows = db.query(MarketObservation).filter(
            MarketObservation.commodity_id == settings.PILOT_COMMODITY_ID,
            MarketObservation.geography_id == settings.PILOT_MARKET_ID,
            MarketObservation.is_demo_data == False,  # noqa: E712
        ).order_by(MarketObservation.date.asc()).all()
    finally:
        db.close()

    print(f"real rows for {settings.PILOT_MARKET_ID}: {len(rows)}")
    df = pd.DataFrame([{"date": r.date, "modal_price": r.modal_price} for r in rows])
    print(f"cutoff: {df['date'].max()}  latest modal: ₹{df['modal_price'].iloc[-1]}/kg")

    adapter = Chronos2FoundationModel()
    try:
        points = adapter.predict(df, 30)
    except ChronosUnavailableError as exc:
        print(f"CHRONOS UNAVAILABLE: {exc}")
        sys.exit(1)

    print("\nfirst 5 forecast days:")
    for p in points[:5]:
        print(f"  {p['date']}  med=₹{p['predicted_modal']:>7}  "
              f"80%=[₹{p['lower_80']}, ₹{p['upper_80']}]  95%=[₹{p['lower_95']}, ₹{p['upper_95']}]")

    risk = probability_sheet(
        points, alert=settings.ONION_ALERT_THRESHOLD, crisis=settings.ONION_CRISIS_THRESHOLD
    )
    import json
    print("\nrisk sheet (dynamic, from quantile ladder):")
    print(json.dumps(risk, indent=2))


if __name__ == "__main__":
    main()
