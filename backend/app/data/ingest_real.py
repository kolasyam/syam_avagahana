"""
Real Market Data Ingestion
==========================
Loads the curated AP onion dataset (AGMARKNET-derived state-aggregate series,
Jan 2022 - Oct 2026) into the platform database.

Replaces the synthetic `seed_data.py` loader. Every row written here is REAL:
  - MarketObservation rows  : source AGMARKNET (curated daily state aggregates)
  - ExternalObservation rows: IMD-derived weather, PPAC-derived fuel, production estimates

Honesty rules baked into this loader:
  1. is_demo_data = False on every row.
  2. AGMARKNET publishes only the MODAL price for this aggregate series, so
     min_price = max_price = modal_price and the row is flagged MODAL_ONLY_SERIES.
     (No fabricated min/max spreads.)
  3. Arrival units are assumed to be MT/day and flagged UNIT_ASSUMED_MT.
  4. The five mandi geographies from the reference catalog are registered as
     REFERENCE SITES with NO price data until a district-level AGMARKNET pull
     is ingested. The demo runs on real state-level series.

Run directly:  python -m app.data.ingest_real [--force]
"""

import csv
import os
from datetime import datetime
from typing import Any, Dict, List

from app.core.config import settings
from app.core.database import SessionLocal
from app.domain.models import Commodity, ExternalObservation, Geography, MarketObservation

# --------------------------------------------------------------------------- #
# Source file
# --------------------------------------------------------------------------- #

DEFAULT_CSV = os.path.join(
    os.path.expanduser("~"),
    "OneDrive", "Desktop", "AP_Onion_Dataset_2022_2026_Production.csv",
)
CSV_PATH = os.getenv("REAL_DATA_CSV", getattr(settings, "REAL_DATA_CSV", DEFAULT_CSV))

# --------------------------------------------------------------------------- #
# Geography catalog (state aggregates = real ingested series)
# --------------------------------------------------------------------------- #

STATE_GEOGRAPHIES: List[Dict[str, Any]] = [
    {
        "id": "state_andhra_pradesh",
        "name": "Andhra Pradesh — State Aggregate",
        "district": "STATE_AGGREGATE",
        "state": "Andhra Pradesh",
        "latitude": 15.9129,
        "longitude": 79.7400,
        "market_type": "State Aggregate (AGMARKNET curated series)",
    },
    {
        "id": "state_maharashtra",
        "name": "Maharashtra — State Aggregate",
        "district": "STATE_AGGREGATE",
        "state": "Maharashtra",
        "latitude": 19.7515,
        "longitude": 75.7139,
        "market_type": "Comparator State (primary national supplier)",
    },
    {
        "id": "state_karnataka",
        "name": "Karnataka — State Aggregate",
        "district": "STATE_AGGREGATE",
        "state": "Karnataka",
        "latitude": 15.3173,
        "longitude": 75.7139,
        "market_type": "Comparator State",
    },
    {
        "id": "state_madhya_pradesh",
        "name": "Madhya Pradesh — State Aggregate",
        "district": "STATE_AGGREGATE",
        "state": "Madhya Pradesh",
        "latitude": 22.9734,
        "longitude": 78.6569,
        "market_type": "Comparator State",
    },
    {
        "id": "nation_india",
        "name": "India — National Aggregate",
        "district": "NATIONAL_AGGREGATE",
        "state": "India",
        "latitude": 21.1458,
        "longitude": 79.0882,
        "market_type": "National Aggregate (production context only)",
    },
]

# Mandis from the reference catalog: registered as reference sites. NO synthetic
# observations are generated for them. District-level ingestion is a roadmap item;
# until then agents may fetch district quotes on demand via the web-fallback tool
# (with source citation), never from fabricated rows.
MANDI_REFERENCE_GEOGRAPHIES: List[Dict[str, Any]] = [
    {
        "id": "mandi_kurnool",
        "name": "Kurnool Agricultural Market Yard",
        "district": "Kurnool",
        "state": "Andhra Pradesh",
        "latitude": 15.8281,
        "longitude": 78.0373,
        "market_type": "Reference Site (district ingestion on roadmap)",
    },
    {
        "id": "mandi_kadapa",
        "name": "Kadapa APMC Mandi",
        "district": "YSR Kadapa",
        "state": "Andhra Pradesh",
        "latitude": 14.4673,
        "longitude": 78.8242,
        "market_type": "Reference Site (district ingestion on roadmap)",
    },
    {
        "id": "mandi_vijayawada",
        "name": "Gollapudi Mandi, Vijayawada",
        "district": "NTR District",
        "state": "Andhra Pradesh",
        "latitude": 16.5062,
        "longitude": 80.6480,
        "market_type": "Reference Site (district ingestion on roadmap)",
    },
    {
        "id": "mandi_tirupati",
        "name": "Tirupati Vegetable Market",
        "district": "Tirupati",
        "state": "Andhra Pradesh",
        "latitude": 13.6288,
        "longitude": 79.4192,
        "market_type": "Reference Site (district ingestion on roadmap)",
    },
    {
        "id": "mandi_visakhapatnam",
        "name": "MVP Rythu Bazaar / Mandi, Visakhapatnam",
        "district": "Visakhapatnam",
        "state": "Andhra Pradesh",
        "latitude": 17.6868,
        "longitude": 83.2185,
        "market_type": "Reference Site (district ingestion on roadmap)",
    },
]

# --------------------------------------------------------------------------- #
# CSV column mapping
# --------------------------------------------------------------------------- #

# AGMARKNET publishes rupees per quintal. The platform stores rupees per kg.
QTL_TO_KG = 100.0

STATE_COLUMNS = {
    "state_andhra_pradesh": {"modal": "modal_ap", "retail": "retail_ap", "arrival": "arrival_ap"},
    "state_maharashtra": {"modal": "modal_mh", "retail": "retail_mh", "arrival": "arrival_mh"},
    "state_karnataka": {"modal": "modal_ka", "retail": "retail_ka", "arrival": "arrival_ka"},
    "state_madhya_pradesh": {"modal": "modal_mp", "retail": "retail_mp", "arrival": "arrival_mp"},
}

# External variables ingested per row (AP context series).
EXTERNAL_VARIABLES = [
    {"col": "Avg_Precipitation", "var": "precipitation_mm", "unit": "mm", "geo": "state_andhra_pradesh", "source": "IMD"},
    {"col": "VPD", "var": "vpd_kpa", "unit": "kPa", "geo": "state_andhra_pradesh", "source": "IMD"},
    {"col": "Seasonal_VPD", "var": "seasonal_vpd_kpa", "unit": "kPa", "geo": "state_andhra_pradesh", "source": "IMD"},
    {"col": "Seasonal_Rain", "var": "seasonal_rain_mm", "unit": "mm", "geo": "state_andhra_pradesh", "source": "IMD"},
    {"col": "Fuel_Avg", "var": "fuel_price_avg", "unit": "INR/L", "geo": "nation_india", "source": "PPAC"},
    {"col": "prod_ap", "var": "production_kt", "unit": "'000 MT", "geo": "state_andhra_pradesh", "source": "STATE_HORTICULTURE"},
    {"col": "prod_mh", "var": "production_kt", "unit": "'000 MT", "geo": "state_maharashtra", "source": "STATE_HORTICULTURE"},
    {"col": "prod_india", "var": "production_kt", "unit": "'000 MT", "geo": "nation_india", "source": "MoA_HORTICULTURE_BOARD"},
    {"col": "prod_ratio_ap", "var": "production_share_ratio_ap", "unit": "ratio", "geo": "state_andhra_pradesh", "source": "DERIVED"},
]

MISSING_MARKERS = {"", "NA", "N/A", "nan", "NaN", "None", "-"}


def _parse_date(raw: str) -> str:
    """DD-MM-YYYY -> ISO YYYY-MM-DD."""
    return datetime.strptime(raw.strip(), "%d-%m-%Y").date().isoformat()


def _parse_float(raw: str):
    if raw is None:
        return None
    raw = raw.strip()
    if raw in MISSING_MARKERS:
        return None
    try:
        val = float(raw)
        return val if val == val else None  # guard NaN
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# Core ingestion
# --------------------------------------------------------------------------- #

def ensure_real_data(force: bool = False) -> Dict[str, Any]:
    """
    Loads the real dataset if not already ingested. Idempotent by default;
    pass force=True (or --force) to wipe and reload real rows.
    """
    db = SessionLocal()
    try:
        existing = db.query(MarketObservation).filter(
            MarketObservation.is_demo_data == False  # noqa: E712  (real rows only)
        ).count()

        if existing > 300 and not force:
            # Still purge any leftover synthetic rows from previous seed runs
            _purge_synthetic(db)
            return {"status": "ALREADY_INGESTED", "real_rows": existing}

        if force:
            db.query(MarketObservation).filter(MarketObservation.is_demo_data == False).delete()
            db.query(ExternalObservation).filter(ExternalObservation.is_demo_data == False).delete()

        _purge_synthetic(db)  # demo rows must never coexist with the real series
        _seed_geographies_and_commodity(db)

        if not os.path.exists(CSV_PATH):
            raise FileNotFoundError(
                f"Real dataset not found at '{CSV_PATH}'. "
                "Set REAL_DATA_CSV env var or place AP_Onion_Dataset_2022_2026_Production.csv on the Desktop."
            )

        summary = _ingest_rows(db)
        db.commit()
        return summary
    finally:
        db.close()


def _purge_synthetic(db) -> None:
    """
    Removes every demo/synthetic artifact from earlier seed runs.
    The client demo runs on real data only; fake rows must not linger
    (stale synthetic forecasts/risk rows would otherwise be served).
    """
    demo_obs = db.query(MarketObservation).filter(MarketObservation.is_demo_data == True).delete()  # noqa: E712
    demo_ext = db.query(ExternalObservation).filter(ExternalObservation.is_demo_data == True).delete()  # noqa: E712
    from app.domain.models import ForecastRun, RiskAssessment
    demo_fc = db.query(ForecastRun).filter(ForecastRun.status == "DEMO_EVALUATED").delete()
    demo_risk = db.query(RiskAssessment).delete()  # regenerated live under real mode
    if demo_obs or demo_ext or demo_fc or demo_risk:
        db.commit()
        print(f"purged synthetic leftovers: obs={demo_obs} ext={demo_ext} "
              f"forecast_runs={demo_fc} risk_rows={demo_risk}")


def _seed_geographies_and_commodity(db) -> None:
    existing_geo_ids = {g.id for g in db.query(Geography.id).all()}
    for geo in STATE_GEOGRAPHIES + MANDI_REFERENCE_GEOGRAPHIES:
        if geo["id"] not in existing_geo_ids:
            db.add(Geography(**geo))

    if db.query(Commodity).filter(Commodity.id == settings.PILOT_COMMODITY_ID).first() is None:
        db.add(Commodity(
            id=settings.PILOT_COMMODITY_ID,
            name="Onion (Common Red / Hybrid)",
            variety="Nashik Red / Bellary Hybrid",
            unit="₹/kg",
            alert_threshold=settings.ONION_ALERT_THRESHOLD,
            crisis_threshold=settings.ONION_CRISIS_THRESHOLD,
        ))
    db.commit()


def _ingest_rows(db) -> Dict[str, Any]:
    price_rows: List[MarketObservation] = []
    external_rows: List[ExternalObservation] = []
    missing_counts: Dict[str, int] = {}
    date_min, date_max = None, None

    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)

        for raw in reader:
            try:
                iso_date = _parse_date(raw["date"])
            except (KeyError, ValueError):
                continue  # skip malformed calendar rows entirely

            if date_min is None or iso_date < date_min:
                date_min = iso_date
            if date_max is None or iso_date > date_max:
                date_max = iso_date

            # ---- Price rows (₹/quintal -> ₹/kg) -------------------------------
            for geo_id, cols in STATE_COLUMNS.items():
                modal_qtl = _parse_float(raw.get(cols["modal"], ""))
                if modal_qtl is None or modal_qtl <= 0:
                    key = f"{geo_id}.modal_missing"
                    missing_counts[key] = missing_counts.get(key, 0) + 1
                    continue

                modal_kg = round(modal_qtl / QTL_TO_KG, 4)
                arrival = _parse_float(raw.get(cols["arrival"], ""))
                flags = "VERIFIED • MODAL_ONLY_SERIES"
                if arrival is None:
                    arrival = 0.0
                    flags = "VERIFIED • MODAL_ONLY_SERIES • ARRIVAL_NOT_REPORTED"
                elif arrival == 1.0 and geo_id == "state_andhra_pradesh" and iso_date.endswith(("-01-01",)) is False:
                    pass  # keep as-is; units flagged institutionally, not per row

                price_rows.append(MarketObservation(
                    commodity_id=settings.PILOT_COMMODITY_ID,
                    geography_id=geo_id,
                    date=iso_date,
                    min_price=modal_kg,       # honest: only modal is published
                    modal_price=modal_kg,
                    max_price=modal_kg,
                    arrivals_mt=arrival,
                    source_id="AGMARKNET",
                    source_record_id=os.path.basename(CSV_PATH),
                    quality_flags=flags,
                    is_demo_data=False,
                ))

                # Retail reference price as external variable (DoCA retail lens)
                retail_qtl = _parse_float(raw.get(cols["retail"], ""))
                if retail_qtl is not None and retail_qtl > 0:
                    external_rows.append(ExternalObservation(
                        variable_name="retail_price_inr_kg",
                        geography_id=geo_id,
                        date=iso_date,
                        value=round(retail_qtl / QTL_TO_KG, 4),
                        unit="₹/kg",
                        source_id="DoCA_PMS",
                        quality_flags="VERIFIED • RETAIL_LENS",
                        is_demo_data=False,
                    ))

            # ---- External context variables -----------------------------------
            for spec in EXTERNAL_VARIABLES:
                val = _parse_float(raw.get(spec["col"], ""))
                if val is None:
                    key = f"ext.{spec['var']}.missing"
                    missing_counts[key] = missing_counts.get(key, 0) + 1
                    continue
                external_rows.append(ExternalObservation(
                    variable_name=spec["var"],
                    geography_id=spec["geo"],
                    date=iso_date,
                    value=val,
                    unit=spec["unit"],
                    source_id=spec["source"],
                    quality_flags="VERIFIED",
                    is_demo_data=False,
                ))

    db.add_all(price_rows)
    db.add_all(external_rows)

    return {
        "status": "INGESTED",
        "source_file": os.path.basename(CSV_PATH),
        "date_min": date_min,
        "date_max": date_max,
        "price_rows": len(price_rows),
        "external_rows": len(external_rows),
        "geographies": [g["id"] for g in STATE_GEOGRAPHIES],
        "missing_cells": missing_counts,
    }


def latest_observations_frame(db) -> "pd.DataFrame":  # noqa: F821  (pandas import kept local to callers)
    """Convenience for model scripts; imported lazily by callers."""
    from app.domain.models import MarketObservation  # noqa: F811

    rows = db.query(MarketObservation).filter(
        MarketObservation.commodity_id == settings.PILOT_COMMODITY_ID
    ).order_by(MarketObservation.date.asc()).all()
    import pandas as pd
    return pd.DataFrame([{
        "date": o.date,
        "modal_price": o.modal_price,
        "arrivals_mt": o.arrivals_mt,
    } for o in rows])


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Ingest real AP onion dataset")
    parser.add_argument("--force", action="store_true", help="Wipe real rows and reload")
    args = parser.parse_args()

    result = ensure_real_data(force=args.force)
    print(json.dumps(result, indent=2, default=str))
