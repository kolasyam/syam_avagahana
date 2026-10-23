"""
Database Models for AP Essential Commodities Platform
Clean domain entities: Geography, Commodity, Market Observations, Forecasts, Risk, Scenarios, Reviews, and Audits.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Geography(Base):
    __tablename__ = "geographies"
    
    id = Column(String(64), primary_key=True, index=True) # e.g. mandi_kurnool
    name = Column(String(128), nullable=False)
    district = Column(String(64), nullable=False)
    state = Column(String(64), default="Andhra Pradesh")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    market_type = Column(String(32), default="APMC Mandi")

class Commodity(Base):
    __tablename__ = "commodities"
    
    id = Column(String(64), primary_key=True, index=True) # e.g. onion
    name = Column(String(128), nullable=False)
    variety = Column(String(64), default="Standard Red / Hybrid")
    unit = Column(String(32), default="₹/kg")
    alert_threshold = Column(Float, default=35.0)
    crisis_threshold = Column(Float, default=50.0)

class MarketObservation(Base):
    __tablename__ = "market_observations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    commodity_id = Column(String(64), ForeignKey("commodities.id"), index=True, nullable=False)
    geography_id = Column(String(64), ForeignKey("geographies.id"), index=True, nullable=False)
    date = Column(String(10), index=True, nullable=False) # YYYY-MM-DD
    min_price = Column(Float, nullable=False)
    modal_price = Column(Float, nullable=False)
    max_price = Column(Float, nullable=False)
    arrivals_mt = Column(Float, nullable=False)
    source_id = Column(String(64), default="AGMARKNET")
    source_record_id = Column(String(128), nullable=True)
    quality_flags = Column(String(64), default="VERIFIED")
    is_demo_data = Column(Boolean, default=True)

class ExternalObservation(Base):
    __tablename__ = "external_observations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    variable_name = Column(String(64), index=True, nullable=False) # rainfall_mm, temp_c, buffer_stock_mt
    geography_id = Column(String(64), ForeignKey("geographies.id"), index=True, nullable=False)
    date = Column(String(10), index=True, nullable=False) # YYYY-MM-DD
    value = Column(Float, nullable=False)
    unit = Column(String(32), nullable=False)
    source_id = Column(String(64), default="IMD")
    quality_flags = Column(String(64), default="VERIFIED")
    is_demo_data = Column(Boolean, default=True)

class ForecastRun(Base):
    __tablename__ = "forecast_runs"
    
    id = Column(String(64), primary_key=True, index=True)
    commodity_id = Column(String(64), nullable=False)
    geography_id = Column(String(64), nullable=False)
    run_date = Column(String(10), nullable=False)
    model_name = Column(String(64), nullable=False)
    model_version = Column(String(32), default="v1.0.0")
    horizon_days = Column(Integer, default=14)
    forecast_series_json = Column(Text, nullable=False)
    metrics_json = Column(Text, nullable=False)
    data_cutoff_date = Column(String(10), nullable=False)
    status = Column(String(32), default="DEMO_EVALUATED")

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    
    id = Column(String(64), primary_key=True, index=True)
    commodity_id = Column(String(64), nullable=False)
    geography_id = Column(String(64), nullable=False)
    assessment_date = Column(String(10), nullable=False)
    horizon_days = Column(Integer, default=14)
    spike_probability = Column(Float, nullable=False)
    threshold_level = Column(String(32), nullable=False)
    primary_drivers_json = Column(Text, nullable=False)
    narrative = Column(Text, nullable=False)

class ScenarioRun(Base):
    __tablename__ = "scenario_runs"
    
    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    commodity_id = Column(String(64), nullable=False)
    geography_id = Column(String(64), nullable=False)
    baseline_forecast_id = Column(String(64), nullable=True)
    intervention_type = Column(String(64), nullable=False)
    release_quantity_mt = Column(Float, nullable=False)
    target_districts_json = Column(Text, nullable=False)
    timing_days = Column(Integer, default=3)
    logistics_mode = Column(String(32), default="TRUCK_CONVOY")
    cost_per_kg_subsidy = Column(Float, default=8.0)
    total_budget_cr = Column(Float, nullable=False)
    simulated_price_path_json = Column(Text, nullable=False)
    expected_price_mitigation_pct = Column(Float, nullable=False)
    stock_depletion_mt = Column(Float, nullable=False)
    stock_remaining_mt = Column(Float, nullable=False)
    is_constraint_violated = Column(Boolean, default=False)
    violation_reason = Column(Text, nullable=True)
    created_at = Column(String(32), default=lambda: datetime.now(timezone.utc).isoformat())

class DecisionReview(Base):
    __tablename__ = "decision_reviews"
    
    id = Column(String(64), primary_key=True, index=True)
    scenario_id = Column(String(64), nullable=False)
    title = Column(String(256), nullable=False)
    summary = Column(Text, nullable=False)
    state = Column(String(32), default="DRAFT") # DRAFT, SUBMITTED, IN_REVIEW, APPROVED, REJECTED
    current_reviewer_role = Column(String(64), default="Analyst")
    comments_json = Column(Text, default="[]")
    version = Column(Integer, default=1)
    created_at = Column(String(32), default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at = Column(String(32), default=lambda: datetime.now(timezone.utc).isoformat())

class AuditEvent(Base):
    __tablename__ = "audit_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(String(32), default=lambda: datetime.now(timezone.utc).isoformat())
    actor_id = Column(String(64), nullable=False)
    actor_role = Column(String(64), nullable=False)
    action = Column(String(64), nullable=False)
    target_type = Column(String(64), nullable=False)
    target_id = Column(String(64), nullable=False)
    outcome = Column(String(32), default="SUCCESS")
    details_json = Column(Text, default="{}")
    correlation_id = Column(String(64), nullable=True)
