export interface Geography {
  id: string;
  name: string;
  district: string;
  state: string;
  latitude?: number;
  longitude?: number;
  market_type: string;
}

export interface Commodity {
  id: string;
  name: string;
  variety: string;
  unit: string;
  alert_threshold: number;
  crisis_threshold: number;
}

export interface MarketObservation {
  id: number;
  commodity_id: string;
  geography_id: string;
  date: string;
  min_price: number;
  modal_price: number;
  max_price: number;
  arrivals_mt: number;
  source_id: string;
  quality_flags: string;
  is_demo_data: boolean;
}

export interface MarketAnalytics {
  summary: {
    latest_date: string;
    latest_modal_price: number;
    latest_min_price: number;
    latest_max_price: number;
    latest_arrivals_mt: number;
    wow_price_change_pct: number;
    wow_arrivals_change_pct: number;
    current_volatility: number;
    period_min: number;
    period_max: number;
    period_mean: number;
  };
  series: Array<{
    date: string;
    modal_price: number;
    arrivals_mt: number;
    ma_7: number;
    ma_14: number;
    ma_30: number;
    volatility: number;
  }>;
  anomalies: Array<{
    date: string;
    price: number;
    z_score: number;
    dod_change_pct: number;
    severity: string;
    reason: string;
  }>;
  arrival_price_correlation: number;
}

export interface ForecastPoint {
  date: string;
  predicted_modal: number;
  lower_80: number;
  upper_80: number;
  lower_95: number;
  upper_95: number;
}

export interface ForecastRun {
  id: string;
  commodity_id: string;
  geography_id: string;
  run_date: string;
  model_name: string;
  model_version: string;
  horizon_days: number;
  status: string;
  data_cutoff_date: string;
  forecast_series: ForecastPoint[];
  metrics: {
    mae: number;
    rmse: number;
    wape: number;
    interval_coverage: number;
    sample_count: number;
  };
  advisory?: string;
}

export interface RiskDriver {
  driver: string;
  impact_pct: number;
  detail: string;
}

export interface RiskAssessment {
  id: string;
  commodity_id: string;
  geography_id: string;
  assessment_date: string;
  horizon_days: number;
  spike_probability: number;
  threshold_level: string;
  primary_drivers: RiskDriver[];
  narrative: string;
}

export interface ScenarioRun {
  id: string;
  name: string;
  commodity_id: string;
  geography_id: string;
  baseline_forecast_id?: string;
  intervention_type: string;
  release_quantity_mt: number;
  target_districts: string[];
  timing_days: number;
  logistics_mode: string;
  cost_per_kg_subsidy: number;
  total_budget_cr: number;
  simulated_price_path: Array<{
    date: string;
    baseline_price?: number;
    simulated_price: number;
    savings_per_kg?: number;
  }>;
  expected_price_mitigation_pct: number;
  stock_depletion_mt: number;
  stock_remaining_mt: number;
  is_constraint_violated: boolean;
  violation_reason?: string;
  created_at: string;
}

export interface DecisionReview {
  id: string;
  scenario_id: string;
  title: string;
  summary: string;
  state: "DRAFT" | "SUBMITTED" | "IN_REVIEW" | "APPROVED" | "REJECTED";
  current_reviewer_role: string;
  comments: Array<{
    author: string;
    role: string;
    action?: string;
    timestamp: string;
    text: string;
  }>;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface ConnectorHealth {
  connector_id: string;
  name: string;
  family: string;
  status: string;
  freshness_hours: number;
  records_count: number;
  quality_score: number;
  mode_label: string;
  last_sync: string;
}

export interface AuditEvent {
  id: number;
  timestamp: string;
  actor_id: string;
  actor_role: string;
  action: string;
  target_type: string;
  target_id: string;
  outcome: string;
  details: Record<string, any>;
  correlation_id?: string;
}

export interface AgentStreamEvent {
  correlation_id: string;
  timestamp: string;
  stage: string;
  agent: string;
  status: "running" | "completed" | "failed";
  payload: any;
}
