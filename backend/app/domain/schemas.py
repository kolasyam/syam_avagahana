"""
Pydantic Schemas for API Requests, Responses, and Domain Contracts
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any

class GeographyBase(BaseModel):
    id: str
    name: str
    district: str
    state: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    market_type: str

class GeographyOut(GeographyBase):
    model_config = ConfigDict(from_attributes=True)

class CommodityBase(BaseModel):
    id: str
    name: str
    variety: str
    unit: str
    alert_threshold: float
    crisis_threshold: float

class CommodityOut(CommodityBase):
    model_config = ConfigDict(from_attributes=True)

class MarketObservationOut(BaseModel):
    id: int
    commodity_id: str
    geography_id: str
    date: str
    min_price: float
    modal_price: float
    max_price: float
    arrivals_mt: float
    source_id: str
    source_record_id: Optional[str]
    quality_flags: str
    is_demo_data: bool

    model_config = ConfigDict(from_attributes=True)

class ForecastPoint(BaseModel):
    date: str
    predicted_modal: float
    lower_80: float
    upper_80: float
    lower_95: float
    upper_95: float

class ForecastMetrics(BaseModel):
    mae: float
    rmse: float
    wape: float
    interval_coverage: float
    sample_count: int

class ForecastRunOut(BaseModel):
    id: str
    commodity_id: str
    geography_id: str
    run_date: str
    model_name: str
    model_version: str
    horizon_days: int
    data_cutoff_date: str
    status: str
    forecast_series: List[ForecastPoint]
    metrics: ForecastMetrics

class RiskAssessmentOut(BaseModel):
    id: str
    commodity_id: str
    geography_id: str
    assessment_date: str
    horizon_days: int
    spike_probability: float
    threshold_level: str
    primary_drivers: List[Dict[str, Any]]
    narrative: str

class ScenarioCreateRequest(BaseModel):
    name: str
    commodity_id: str = "onion"
    geography_id: str = "mandi_kurnool"
    intervention_type: str = "BUFFER_RELEASE" # BUFFER_RELEASE, OPEN_MARKET_SALE, MOBILE_BAZAAR
    release_quantity_mt: float = Field(..., gt=0, le=50000, description="Quantity to release in MT")
    target_districts: List[str] = ["Kurnool", "Vijayawada", "Tirupati"]
    timing_days: int = Field(3, ge=1, le=30)
    logistics_mode: str = "TRUCK_CONVOY" # TRUCK_CONVOY or RAILWAY_FREIGHT
    cost_per_kg_subsidy: float = 8.0 # ₹/kg

class ScenarioOut(BaseModel):
    id: str
    name: str
    commodity_id: str
    geography_id: str
    baseline_forecast_id: Optional[str]
    intervention_type: str
    release_quantity_mt: float
    target_districts: List[str]
    timing_days: int
    logistics_mode: str
    cost_per_kg_subsidy: float
    total_budget_cr: float
    simulated_price_path: List[Dict[str, Any]]
    expected_price_mitigation_pct: float
    stock_depletion_mt: float
    stock_remaining_mt: float
    is_constraint_violated: bool
    violation_reason: Optional[str]
    created_at: str

class ReviewCreateRequest(BaseModel):
    scenario_id: str
    title: str
    summary: str

class ReviewTransitionRequest(BaseModel):
    action: str # SUBMIT, REVIEW, APPROVE, REJECT
    reviewer_role: str # Analyst, Director, Commissioner, Minister
    comment: str

class ReviewOut(BaseModel):
    id: str
    scenario_id: str
    title: str
    summary: str
    state: str
    current_reviewer_role: str
    comments: List[Dict[str, Any]]
    version: int
    created_at: str
    updated_at: str

class ConnectorHealthOut(BaseModel):
    connector_id: str
    name: str
    family: str
    status: str # HEALTHY_DEMO, VERIFIED_LIVE, EXPERIMENTAL, DEGRADED
    freshness_hours: float
    records_count: int
    quality_score: float
    mode_label: str
    last_sync: str

class AgentStepTrace(BaseModel):
    step_id: str
    agent_role: str
    status: str # queued, running, completed, warning, failed
    timestamp: str
    detail: str
    output_summary: Optional[str] = None
    confidence: Optional[str] = "HIGH"

class InvestigationRequest(BaseModel):
    query: str
    commodity_id: str = "onion"
    geography_id: str = "mandi_kurnool"
    horizon_days: int = 14
