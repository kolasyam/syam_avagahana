"""
Scenario Simulation API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
from datetime import datetime, timezone
from app.core.database import get_db
from app.domain.models import ScenarioRun, ForecastRun
from app.domain.schemas import ScenarioCreateRequest, ScenarioOut
from app.simulation.scenario_engine import run_scenario_simulation
from app.core.audit import log_audit_event

router = APIRouter()

@router.get("", response_model=List[ScenarioOut])
def get_scenarios(db: Session = Depends(get_db)):
    scenarios = db.query(ScenarioRun).order_by(ScenarioRun.created_at.desc()).all()
    results = []
    for s in scenarios:
        results.append({
            "id": s.id,
            "name": s.name,
            "commodity_id": s.commodity_id,
            "geography_id": s.geography_id,
            "baseline_forecast_id": s.baseline_forecast_id,
            "intervention_type": s.intervention_type,
            "release_quantity_mt": s.release_quantity_mt,
            "target_districts": json.loads(s.target_districts_json),
            "timing_days": s.timing_days,
            "logistics_mode": s.logistics_mode,
            "cost_per_kg_subsidy": s.cost_per_kg_subsidy,
            "total_budget_cr": s.total_budget_cr,
            "simulated_price_path": json.loads(s.simulated_price_path_json),
            "expected_price_mitigation_pct": s.expected_price_mitigation_pct,
            "stock_depletion_mt": s.stock_depletion_mt,
            "stock_remaining_mt": s.stock_remaining_mt,
            "is_constraint_violated": s.is_constraint_violated,
            "violation_reason": s.violation_reason,
            "created_at": s.created_at
        })
    return results

@router.post("/simulate", response_model=ScenarioOut)
def create_scenario(req: ScenarioCreateRequest, db: Session = Depends(get_db)):
    # Retrieve baseline forecast for market
    latest_fc = db.query(ForecastRun).filter(
        ForecastRun.commodity_id == req.commodity_id,
        ForecastRun.geography_id == req.geography_id
    ).order_by(ForecastRun.run_date.desc()).first()

    baseline_points = json.loads(latest_fc.forecast_series_json) if latest_fc else []

    sim_res = run_scenario_simulation(
        name=req.name,
        commodity_id=req.commodity_id,
        geography_id=req.geography_id,
        release_quantity_mt=req.release_quantity_mt,
        timing_days=req.timing_days,
        logistics_mode=req.logistics_mode,
        cost_per_kg_subsidy=req.cost_per_kg_subsidy,
        target_districts=req.target_districts,
        baseline_forecast=baseline_points
    )

    scen_id = f"scen_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    scenario = ScenarioRun(
        id=scen_id,
        name=req.name,
        commodity_id=req.commodity_id,
        geography_id=req.geography_id,
        baseline_forecast_id=latest_fc.id if latest_fc else None,
        intervention_type=req.intervention_type,
        release_quantity_mt=req.release_quantity_mt,
        target_districts_json=json.dumps(req.target_districts),
        timing_days=req.timing_days,
        logistics_mode=req.logistics_mode,
        cost_per_kg_subsidy=req.cost_per_kg_subsidy,
        total_budget_cr=sim_res["total_budget_cr"],
        simulated_price_path_json=json.dumps(sim_res["simulated_price_path"]),
        expected_price_mitigation_pct=sim_res["expected_price_mitigation_pct"],
        stock_depletion_mt=sim_res["stock_depletion_mt"],
        stock_remaining_mt=sim_res["stock_remaining_mt"],
        is_constraint_violated=sim_res["is_constraint_violated"],
        violation_reason=sim_res["violation_reason"]
    )
    db.add(scenario)
    db.commit()

    log_audit_event(
        db=db,
        actor_id="officer_demo",
        actor_role="Analyst",
        action="SIMULATE_SCENARIO",
        target_type="SCENARIO_RUN",
        target_id=scen_id,
        details={
            "quantity_mt": req.release_quantity_mt,
            "budget_cr": sim_res["total_budget_cr"],
            "violated": sim_res["is_constraint_violated"]
        }
    )

    return {
        "id": scen_id,
        "name": req.name,
        "commodity_id": req.commodity_id,
        "geography_id": req.geography_id,
        "baseline_forecast_id": latest_fc.id if latest_fc else None,
        "intervention_type": req.intervention_type,
        "release_quantity_mt": req.release_quantity_mt,
        "target_districts": req.target_districts,
        "timing_days": req.timing_days,
        "logistics_mode": req.logistics_mode,
        "cost_per_kg_subsidy": req.cost_per_kg_subsidy,
        "total_budget_cr": sim_res["total_budget_cr"],
        "simulated_price_path": sim_res["simulated_price_path"],
        "expected_price_mitigation_pct": sim_res["expected_price_mitigation_pct"],
        "stock_depletion_mt": sim_res["stock_depletion_mt"],
        "stock_remaining_mt": sim_res["stock_remaining_mt"],
        "is_constraint_violated": sim_res["is_constraint_violated"],
        "violation_reason": sim_res["violation_reason"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
