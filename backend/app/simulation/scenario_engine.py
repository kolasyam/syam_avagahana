"""
Deterministic Scenario Simulation and Sensitivity Engine
Computes stock depletion, budget arithmetic, logistics feasibility constraints,
price trajectory mitigation, and sensitivity analysis.
"""

from typing import List, Dict, Any, Optional
import math
from datetime import datetime, timedelta

TOTAL_STATE_BUFFER_STOCK_MT = 28500.0 # NAFED / AP PSF Stock Reserve
MAX_TRUCK_CONVOY_DAILY_MT = 3500.0
MAX_RAIL_FREIGHT_DAILY_MT = 6000.0

def run_scenario_simulation(
    name: str,
    commodity_id: str,
    geography_id: str,
    release_quantity_mt: float,
    timing_days: int = 3,
    logistics_mode: str = "TRUCK_CONVOY",
    cost_per_kg_subsidy: float = 8.50,
    target_districts: Optional[List[str]] = None,
    baseline_forecast: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Executes a deterministic what-if intervention scenario.
    Validates physical constraints and returns simulated price trajectory and sensitivity.
    """
    if target_districts is None:
        target_districts = ["Kurnool", "Kadapa", "Vijayawada", "Tirupati"]

    # 1. Constraint Verification
    # A. Stock constraint
    if release_quantity_mt > TOTAL_STATE_BUFFER_STOCK_MT:
        return {
            "is_constraint_violated": True,
            "violation_reason": (
                f"Requested release of {release_quantity_mt:,.0f} MT exceeds total available AP buffer reserve "
                f"of {TOTAL_STATE_BUFFER_STOCK_MT:,.0f} MT."
            ),
            "simulated_price_path": [],
            "expected_price_mitigation_pct": 0.0,
            "total_budget_cr": 0.0,
            "stock_depletion_mt": 0.0,
            "stock_remaining_mt": TOTAL_STATE_BUFFER_STOCK_MT
        }

    # B. Logistics throughput constraint
    daily_required_flow = release_quantity_mt / max(timing_days, 1)
    max_flow = MAX_RAIL_FREIGHT_DAILY_MT if logistics_mode == "RAILWAY_FREIGHT" else MAX_TRUCK_CONVOY_DAILY_MT
    if daily_required_flow > max_flow:
        return {
            "is_constraint_violated": True,
            "violation_reason": (
                f"Logistics bottleneck: {daily_required_flow:,.0f} MT/day exceeds maximum daily throughput "
                f"of {max_flow:,.0f} MT/day for mode '{logistics_mode}'. Extend timing days or select Rail freight."
            ),
            "simulated_price_path": [],
            "expected_price_mitigation_pct": 0.0,
            "total_budget_cr": 0.0,
            "stock_depletion_mt": 0.0,
            "stock_remaining_mt": TOTAL_STATE_BUFFER_STOCK_MT
        }

    # 2. Budget Arithmetic
    # (Quantity MT * 1,000 kg/MT * ₹ subsidy) / 10,000,000 (Cr)
    total_budget_cr = round((release_quantity_mt * 1000.0 * cost_per_kg_subsidy) / 10000000.0, 2)
    stock_remaining = round(TOTAL_STATE_BUFFER_STOCK_MT - release_quantity_mt, 1)

    # 3. Price Trajectory Calculation
    # Elasticity coefficient: 10,000 MT release in AP lowers mandi modal by ~22-26%
    mitigation_factor = min(0.38, (release_quantity_mt / 25000.0) * 0.42)
    mitigation_pct = round(mitigation_factor * 100, 1)

    simulated_path = []
    lead_time = 2 if logistics_mode == "TRUCK_CONVOY" else 4
    
    if baseline_forecast:
        for idx, pt in enumerate(baseline_forecast):
            base_p = pt["predicted_modal"]
            day_num = idx + 1
            if day_num <= lead_time:
                # Still in transit, minor anticipation dampening
                p_sim = base_p - (0.2 * day_num)
            else:
                # Injection takes effect
                days_active = day_num - lead_time
                ramp = min(1.0, days_active / float(timing_days))
                p_sim = base_p * (1.0 - (mitigation_factor * ramp))
            
            simulated_path.append({
                "date": pt["date"],
                "baseline_price": base_p,
                "simulated_price": round(max(p_sim, 22.0), 2),
                "savings_per_kg": round(base_p - max(p_sim, 22.0), 2)
            })

    # 4. Sensitivity Analysis Matrix (±20% volume vs ±15% subsidy)
    sensitivity = []
    for qty_mult in [0.75, 1.0, 1.25]:
        test_qty = release_quantity_mt * qty_mult
        test_budget = round((test_qty * 1000.0 * cost_per_kg_subsidy) / 10000000.0, 2)
        test_mitigation = round(min(0.38, (test_qty / 25000.0) * 0.42) * 100, 1)
        sensitivity.append({
            "volume_mt": test_qty,
            "budget_cr": test_budget,
            "mitigation_pct": test_mitigation,
            "cost_effectiveness_ratio": round(test_mitigation / max(test_budget, 0.1), 2)
        })

    return {
        "is_constraint_violated": False,
        "violation_reason": None,
        "name": name,
        "release_quantity_mt": release_quantity_mt,
        "total_budget_cr": total_budget_cr,
        "stock_depletion_mt": release_quantity_mt,
        "stock_remaining_mt": stock_remaining,
        "expected_price_mitigation_pct": mitigation_pct,
        "target_districts": target_districts,
        "timing_days": timing_days,
        "logistics_mode": logistics_mode,
        "simulated_price_path": simulated_path,
        "sensitivity_analysis": sensitivity
    }
