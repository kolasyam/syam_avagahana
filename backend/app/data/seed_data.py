"""
Deterministic Realistic Seed Data Generator
Populates historical daily mandi observations, external indicators, reference catalogs,
and baseline evaluations matching the AP Onion Pilot specification.
All data strictly English-only.
"""

from datetime import datetime, timedelta
import math
import json
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, Base, engine
from app.domain.models import (
    Geography, Commodity, MarketObservation, ExternalObservation,
    ForecastRun, RiskAssessment, ScenarioRun, DecisionReview
)
from app.data.reference_catalog import GEOGRAPHIES, COMMODITIES

def seed_database(db: Session = None):
    should_close = False
    if db is None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        should_close = True

    try:
        # 1. Geographies
        for geo_data in GEOGRAPHIES:
            existing = db.query(Geography).filter(Geography.id == geo_data["id"]).first()
            if not existing:
                geo = Geography(
                    id=geo_data["id"],
                    name=geo_data["name"],
                    district=geo_data["district"],
                    state=geo_data["state"],
                    latitude=geo_data.get("latitude"),
                    longitude=geo_data.get("longitude"),
                    market_type=geo_data.get("market_type", "APMC Mandi")
                )
                db.add(geo)

        # 2. Commodities
        for comm_data in COMMODITIES:
            existing = db.query(Commodity).filter(Commodity.id == comm_data["id"]).first()
            if not existing:
                comm = Commodity(
                    id=comm_data["id"],
                    name=comm_data["name"],
                    variety=comm_data.get("variety", "Standard Red / Hybrid"),
                    unit=comm_data.get("unit", "₹/kg"),
                    alert_threshold=comm_data.get("alert_threshold", 35.0),
                    crisis_threshold=comm_data.get("crisis_threshold", 50.0)
                )
                db.add(comm)
        
        db.commit()

        # Check if observations already seeded
        obs_count = db.query(MarketObservation).count()
        if obs_count > 0:
            print(f"Database already has {obs_count} observations. Skipping raw data generation.")
            return

        print("Generating realistic AP daily market observations...")
        
        end_date = datetime(2026, 10, 23)
        start_date = end_date - timedelta(days=180)
        
        # Generation configuration per market
        # Kurnool is the primary pilot focus with acute recent spike matching Slide 8 (Modal ~₹40.88)
        market_configs = {
            "mandi_kurnool": {"base_price": 24.0, "spike_factor": 1.70, "base_arrivals": 380.0},
            "mandi_kadapa": {"base_price": 25.5, "spike_factor": 1.55, "base_arrivals": 210.0},
            "mandi_vijayawada": {"base_price": 27.0, "spike_factor": 1.62, "base_arrivals": 420.0},
            "mandi_tirupati": {"base_price": 26.5, "spike_factor": 1.58, "base_arrivals": 260.0},
            "mandi_visakhapatnam": {"base_price": 28.5, "spike_factor": 1.50, "base_arrivals": 350.0},
        }

        curr = start_date
        day_idx = 0
        total_days = (end_date - start_date).days

        while curr <= end_date:
            date_str = curr.strftime("%Y-%m-%d")
            
            # Simulated unseasonal rain event occurring 20 to 10 days ago in supply basins
            days_ago = (end_date - curr).days
            rain_shock = 0.0
            if 10 <= days_ago <= 22:
                rain_shock = math.exp(-((days_ago - 16) ** 2) / 10.0) * 45.0 # mm unseasonal rain

            for geo_id, cfg in market_configs.items():
                # Normal seasonal sine wave + recent shock ramp in last 30 days
                seasonal = math.sin(day_idx / 25.0) * 2.5
                
                # Supply crunch factor in last 30 days
                shock = 0.0
                if days_ago <= 30:
                    shock = (1.0 - (days_ago / 30.0)) * (cfg["base_price"] * (cfg["spike_factor"] - 1.0))
                
                # Daily micro noise
                noise = math.sin(day_idx * 1.7 + hash(geo_id) % 10) * 0.8
                modal = round(cfg["base_price"] + seasonal + shock + noise, 2)
                
                # Calibrate exact current price for Kurnool on final day to match Slide 8 (₹40.88/kg)
                if geo_id == "mandi_kurnool" and days_ago == 0:
                    modal = 40.88
                
                min_price = round(modal * 0.88, 2)
                max_price = round(modal * 1.14, 2)
                
                # Arrivals inversely correlated with price shock
                arrival_mult = 1.0 - (shock / (cfg["base_price"] * 2.0))
                arrivals = max(round(cfg["base_arrivals"] * arrival_mult + math.sin(day_idx) * 25.0, 1), 60.0)
                
                obs = MarketObservation(
                    commodity_id="onion",
                    geography_id=geo_id,
                    date=date_str,
                    min_price=min_price,
                    modal_price=modal,
                    max_price=max_price,
                    arrivals_mt=arrivals,
                    source_id="AGMARKNET",
                    source_record_id=f"AGM-{geo_id}-{date_str}",
                    quality_flags="VERIFIED",
                    is_demo_data=True
                )
                db.add(obs)

                # Seed weather external observation for each market
                if days_ago % 2 == 0: # sample every 2 days
                    rain_val = max(round(math.sin(day_idx * 0.5) * 3.0 + (rain_shock * 0.6 if geo_id in ["mandi_kurnool", "mandi_kadapa"] else 0.0), 1), 0.0)
                    temp_val = round(31.0 + math.cos(day_idx * 0.2) * 3.5, 1)
                    
                    db.add(ExternalObservation(
                        variable_name="rainfall_mm",
                        geography_id=geo_id,
                        date=date_str,
                        value=rain_val,
                        unit="mm",
                        source_id="IMD",
                        quality_flags="VERIFIED",
                        is_demo_data=True
                    ))
                    db.add(ExternalObservation(
                        variable_name="max_temp_c",
                        geography_id=geo_id,
                        date=date_str,
                        value=temp_val,
                        unit="°C",
                        source_id="IMD",
                        quality_flags="VERIFIED",
                        is_demo_data=True
                    ))

            curr += timedelta(days=1)
            day_idx += 1

        db.commit()

        # Seed initial Baseline Forecast for Kurnool Onion
        forecast_points = []
        base_f_date = end_date
        f_val = 40.88
        for i in range(1, 15):
            f_date = (base_f_date + timedelta(days=i)).strftime("%Y-%m-%d")
            # Unmitigated price trajectory expected to rise toward ₹49.50/kg
            f_val += 0.62 - (i * 0.02)
            f_val_r = round(f_val, 2)
            uncertainty_80 = round(1.2 + (i * 0.25), 2)
            uncertainty_95 = round(2.0 + (i * 0.45), 2)
            forecast_points.append({
                "date": f_date,
                "predicted_modal": f_val_r,
                "lower_80": round(f_val_r - uncertainty_80, 2),
                "upper_80": round(f_val_r + uncertainty_80, 2),
                "lower_95": round(f_val_r - uncertainty_95, 2),
                "upper_95": round(f_val_r + uncertainty_95, 2),
            })

        forecast_run = ForecastRun(
            id="fc_kurnool_onion_14d_curr",
            commodity_id="onion",
            geography_id="mandi_kurnool",
            run_date="2026-10-23",
            model_name="AR-Lag Tabular + Weather Covariates",
            model_version="v1.2.4",
            horizon_days=14,
            forecast_series_json=json.dumps(forecast_points),
            metrics_json=json.dumps({
                "mae": 1.42,
                "rmse": 1.86,
                "wape": 4.1,
                "interval_coverage": 91.5,
                "sample_count": 180
            }),
            data_cutoff_date="2026-10-23",
            status="DEMO_EVALUATED"
        )
        db.add(forecast_run)

        # Seed Risk Assessment
        risk = RiskAssessment(
            id="risk_kurnool_onion_curr",
            commodity_id="onion",
            geography_id="mandi_kurnool",
            assessment_date="2026-10-23",
            horizon_days=14,
            spike_probability=0.88,
            threshold_level="HIGH_ALERT",
            primary_drivers_json=json.dumps([
                {"driver": "Arrival Deficit", "impact_pct": 42.0, "detail": "Kurnool arrivals down 58% WoW (110 MT vs 380 MT normal)"},
                {"driver": "Monsoon Interruption in Nashik/Karnataka", "impact_pct": 28.0, "detail": "Late unseasonal rains damaged curing sheds & harvest logistics"},
                {"driver": "Inter-state Inflow Compression", "impact_pct": 18.0, "detail": "Truck freight inward rates up 24%, cross-border supply throttled"},
                {"driver": "Festival / Urban Demand Surge", "impact_pct": 12.0, "detail": "Pre-Diwali consumption ramp creating local supply buffer depletion"}
            ]),
            narrative="High probability (88%) of modal onion prices in Kurnool breaching the crisis threshold of ₹50.00/kg within the next 11 days unless buffer stock release is initiated."
        )
        db.add(risk)

        # Seed Default Policy Scenario (Slide 9 - 10,000 MT Buffer Release)
        sim_path = []
        sim_val = 40.88
        for i in range(1, 15):
            sim_date = (base_f_date + timedelta(days=i)).strftime("%Y-%m-%d")
            # Intervention drops price back toward ₹31.50
            if i <= 3:
                sim_val += 0.20 # lead time delay
            else:
                sim_val = max(sim_val - 1.10, 31.50)
            sim_path.append({"date": sim_date, "simulated_price": round(sim_val, 2)})

        scenario = ScenarioRun(
            id="scen_kurnool_10k_release",
            name="Targeted 10,000 MT NAFED Buffer Release (Rayalaseema & Coastal AP)",
            commodity_id="onion",
            geography_id="mandi_kurnool",
            baseline_forecast_id="fc_kurnool_onion_14d_curr",
            intervention_type="BUFFER_RELEASE",
            release_quantity_mt=10000.0,
            target_districts_json=json.dumps(["Kurnool", "Kadapa", "Vijayawada", "Tirupati"]),
            timing_days=3,
            logistics_mode="TRUCK_CONVOY",
            cost_per_kg_subsidy=8.50,
            total_budget_cr=8.50,
            simulated_price_path_json=json.dumps(sim_path),
            expected_price_mitigation_pct=26.4,
            stock_depletion_mt=10000.0,
            stock_remaining_mt=18500.0,
            is_constraint_violated=False,
            violation_reason=None
        )
        db.add(scenario)

        # Seed Initial Decision Review Brief
        review = DecisionReview(
            id="brief_kurnool_onion_001",
            scenario_id="scen_kurnool_10k_release",
            title="Pre-emptive 10,000 MT Onion Stabilisation via Rythu Bazaars & APMC Yards",
            summary="Executive recommendation: Authorize emergency allocation of 10,000 MT from PSF buffer stock at ₹28.00/kg through Rythu Bazaars across Kurnool, Kadapa, and Vijayawada. Projected to suppress modal spike from ₹48.50 down to ₹32.00/kg within 7 days.",
            state="SUBMITTED",
            current_reviewer_role="Director of Civil Supplies",
            comments_json=json.dumps([
                {"author": "Senior Price Intelligence Analyst", "role": "Analyst", "timestamp": "2026-10-23T18:45:00Z", "text": "Forecast validated against 180-day backtest. Arrival deficit verified across AGMARKNET and e-NAM logs. Ready for Director review."}
            ]),
            version=1
        )
        db.add(review)

        db.commit()
        print("Database successfully seeded with realistic AP pilot records!")
    finally:
        if should_close:
            db.close()

if __name__ == "__main__":
    seed_database()
