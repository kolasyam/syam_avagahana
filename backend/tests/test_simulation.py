"""
Unit Tests for Scenario Engine and Constraint Verification
"""

import pytest
from app.simulation.scenario_engine import run_scenario_simulation, TOTAL_STATE_BUFFER_STOCK_MT

def test_scenario_valid_run():
    baseline = [{"date": f"2026-11-{i:02d}", "predicted_modal": 45.0 + i} for i in range(1, 15)]
    res = run_scenario_simulation(
        name="Test 10k Release",
        commodity_id="onion",
        geography_id="mandi_kurnool",
        release_quantity_mt=10000.0,
        timing_days=3,
        logistics_mode="TRUCK_CONVOY",
        cost_per_kg_subsidy=8.50,
        baseline_forecast=baseline
    )
    assert res["is_constraint_violated"] is False
    assert res["total_budget_cr"] == 8.50 # 10000 * 1000 * 8.5 / 10^7
    assert res["stock_remaining_mt"] == TOTAL_STATE_BUFFER_STOCK_MT - 10000.0
    assert res["expected_price_mitigation_pct"] > 15.0
    assert len(res["simulated_price_path"]) == 14
    assert len(res["sensitivity_analysis"]) == 3

def test_scenario_stock_constraint_violation():
    # Requesting more than total state buffer reserve of 28,500 MT
    res = run_scenario_simulation(
        name="Excessive Release",
        commodity_id="onion",
        geography_id="mandi_kurnool",
        release_quantity_mt=35000.0,
        timing_days=5
    )
    assert res["is_constraint_violated"] is True
    assert "exceeds total available AP buffer reserve" in res["violation_reason"]

def test_scenario_logistics_throughput_violation():
    # Requesting 10,000 MT in 1 day via truck (exceeds 2,500 MT/day capacity)
    res = run_scenario_simulation(
        name="Bottleneck Run",
        commodity_id="onion",
        geography_id="mandi_kurnool",
        release_quantity_mt=10000.0,
        timing_days=1,
        logistics_mode="TRUCK_CONVOY"
    )
    assert res["is_constraint_violated"] is True
    assert "Logistics bottleneck" in res["violation_reason"]
