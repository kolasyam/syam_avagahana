# AP Essential Commodities Price Intelligence & Autonomous Stabilisation
## Comprehensive Visual Documentation & Screenshot Gallery

This gallery documents the **Andhra Pradesh Essential Commodities Price Intelligence and Autonomous Stabilisation Platform (AP-OPIS)**. All visual captures represent live execution with calibrated Andhra Pradesh agricultural ground truth across major AP mandi trading hubs (Kurnool, Vijayawada, Guntur, Tirupati, Visakhapatnam), Rythu Bazaar consumer networks, and the AP Civil Supplies Corporation.

---

## Gallery Index

1. [Executive Workspace & Command Center (Desktop)](#1-executive-workspace--command-center-desktop)
2. [Workspace Alert Streams, Active Interventions & Recent Decisions](#2-workspace-alert-streams-active-interventions--recent-decisions)
3. [Market Intelligence Mandi Network Explorer (Overview)](#3-market-intelligence-mandi-network-explorer-overview)
4. [Mandi Spatial Distribution, Filter Spreads & Arrivals Tracking](#4-mandi-spatial-distribution-filter-spreads--arrivals-tracking)
5. [Multi-Horizon Trajectory & Conformal Uncertainty Bounds (7d/14d/30d/60d/90d)](#5-multi-horizon-trajectory--conformal-uncertainty-bounds-7d14d30d60d90d)
6. [Autonomous Price Spike Risk Gauge & Macro-Driver Decomposition](#6-autonomous-price-spike-risk-gauge--macro-driver-decomposition)
7. [Scenario Lab Policy Simulation Studio (Buffer Stock & Aadhaar Subsidies)](#7-scenario-lab-policy-simulation-studio-buffer-stock--aadhaar-subsidies)
8. [Scenario Lab Exchequer Budget & Fiscal Sensitivity Analysis](#8-scenario-lab-exchequer-budget--fiscal-sensitivity-analysis)
9. [Autonomous Decision Briefs & Executive Strategic Recommendations](#9-autonomous-decision-briefs--executive-strategic-recommendations)
10. [Multi-Tier Governance Approval & State-Machine Workflow](#10-multi-tier-governance-approval--state-machine-workflow)
11. [Data Fabric Multi-Source Integration & Pipeline Orchestration](#11-data-fabric-multi-source-integration--pipeline-orchestration)
12. [Data Fabric Feed Latency, Provenance & Ingestion Health](#12-data-fabric-feed-latency-provenance--ingestion-health)
13. [Data Intake Client Studio & Rapid Continuous Retraining](#13-data-intake-client-studio--rapid-continuous-retraining)
14. [Tamper-Evident Run Inspector & SHA-256 Audit Trail](#14-tamper-evident-run-inspector--sha-256-audit-trail)
15. [Responsive Tablet View (768 x 1024)](#15-responsive-tablet-view-768-x-1024)
16. [Responsive Mobile View (375 x 812)](#16-responsive-mobile-view-375-x-812)

---

### 1. Executive Workspace & Command Center (Desktop)

![Executive Workspace](screenshots/01_executive_workspace_command_center.png)

- **Route / Component:** `Navbar.tsx` -> [`frontend/src/components/WorkspaceView.tsx`](../frontend/src/components/WorkspaceView.tsx)
- **Purpose:** Primary command dashboard providing state administrators, the Agriculture Marketing Minister, and civil supplies officers with unified situational awareness across key AP commodity markets.
- **Key Features Displayed:**
  - **Live Ground-Truth Status Banner:** Displays active live feed synchronization with AP Civil Supplies and APMC integrated data fabric.
  - **4 Top KPI Cards:** State Composite Price (₹38.20/kg modal), 14-Day Trajectory Projection (₹56.45/kg), 30-Day Mandi Volume Arrival (24,850 MT), and Active Intervention Count (2 Active Policies).
  - **Direct One-Click Navigation:** Immediate jump points into Forecasting, Scenario Simulation, and Governance Approvals.
- **Code References:** [`frontend/src/components/WorkspaceView.tsx`](../frontend/src/components/WorkspaceView.tsx), [`backend/app/api/v1/observations.py`](../backend/app/api/v1/observations.py), [`backend/app/core/config.py`](../backend/app/core/config.py).

---

### 2. Workspace Alert Streams, Active Interventions & Recent Decisions

![Workspace Alerts & Interventions](screenshots/02_workspace_recent_briefs_and_alerts.png)

- **Route / Component:** [`frontend/src/components/WorkspaceView.tsx`](../frontend/src/components/WorkspaceView.tsx) (Lower Pane)
- **Purpose:** Displays live agentic risk alerts, active market intervention orders, and recent ministerial decision briefs.
- **Key Features Displayed:**
  - **Price Surge Warning Stream:** Autonomous 14-day advance alert indicating Kurnool mandi onion prices crossing the ₹35.00/kg alert threshold towards ₹56.45/kg.
  - **Intervention Tracker:** Real-time progress on 2,500 MT NAFED buffer release and Rythu Bazaar subsidized sales at ₹35.00/kg.
  - **Audit Provenance Badge:** Cryptographically verifiable action logs tied to individual officers and agent recommendations.
- **Code References:** [`frontend/src/components/WorkspaceView.tsx`](../frontend/src/components/WorkspaceView.tsx), [`backend/app/agents/orchestrator.py`](../backend/app/agents/orchestrator.py).

---

### 3. Market Intelligence Mandi Network Explorer (Overview)

![Market Intelligence Overview](screenshots/03_market_intelligence_mandi_overview.png)

- **Route / Component:** [`frontend/src/components/MarketIntelligenceView.tsx`](../frontend/src/components/MarketIntelligenceView.tsx)
- **Purpose:** Comprehensive market surveillance grid covering 6 principal AP agricultural mandis: Kurnool, Vijayawada, Guntur, Tirupati, Visakhapatnam, and Anantapur.
- **Key Features Displayed:**
  - **Interactive Commodity & Geography Switchers:** Real-time dropdown toggling between commodities (Onion, Tomato, Red Chilli) and mandis.
  - **Modal, Min, and Max Spread Analysis:** Identifies trade margin disparities between farm-gate wholesale and consumer retail.
  - **Arrival Volume Heatmap:** Tracking daily arrivals in Metric Tonnes (MT) against 3-year historical modal averages.
- **Code References:** [`frontend/src/components/MarketIntelligenceView.tsx`](../frontend/src/components/MarketIntelligenceView.tsx), [`backend/app/api/v1/reference.py`](../backend/app/api/v1/reference.py).

---

### 4. Mandi Spatial Distribution, Filter Spreads & Arrivals Tracking

![Mandi Filter & Arrivals](screenshots/04_market_intelligence_filter_and_arrivals.png)

- **Route / Component:** [`frontend/src/components/MarketIntelligenceView.tsx`](../frontend/src/components/MarketIntelligenceView.tsx) (Detailed Grid)
- **Purpose:** Deep-dive tabular exploration of daily arrivals, quality inspection flags, modal price bands, and inter-mandi transport logistics.
- **Key Features Displayed:**
  - **Kurnool Mandi Pilot Benchmark:** Verified wholesale modal price of ₹38.20/kg and daily arrivals of 820 MT.
  - **Data Integrity Score:** Quality flags highlighting anomalous price reporting or missing arrival records.
  - **Export Capabilities:** Downloadable CSV/JSON audit reports for district collectors and market committee secretaries.
- **Code References:** [`frontend/src/components/MarketIntelligenceView.tsx`](../frontend/src/components/MarketIntelligenceView.tsx), [`backend/app/analytics/engine.py`](../backend/app/analytics/engine.py).

---

### 5. Multi-Horizon Trajectory & Conformal Uncertainty Bounds (7d/14d/30d/60d/90d)

![Forecast Multi-Horizon & Conformal Bands](screenshots/05_forecast_multi_horizon_conformal_bands.png)

- **Route / Component:** [`frontend/src/components/ForecastRiskView.tsx`](../frontend/src/components/ForecastRiskView.tsx) -> [`InteractiveChart.tsx`](../frontend/src/components/InteractiveChart.tsx)
- **Purpose:** Multi-horizon predictive price trajectory displaying historical actuals alongside forecast curves and non-parametric conformal uncertainty bands (80% and 95% coverage).
- **Key Features Displayed:**
  - **Multi-Horizon Selector Pills:** Synchronized forecasting across 7-day, 14-day, 30-day, 60-day, and 90-day time horizons.
  - **Conformal Uncertainty Bands:** Mathematically guaranteed confidence corridors capturing supply volatility and weather anomalies.
  - **Threshold Markers:** Clear visual markers for Baseline (₹24.50), Alert (₹35.00), and Crisis (₹50.00) levels.
- **Code References:** [`frontend/src/components/ForecastRiskView.tsx`](../frontend/src/components/ForecastRiskView.tsx), [`backend/app/forecasting/tabular_model.py`](../backend/app/forecasting/tabular_model.py), [`backend/app/forecasting/chronos_adapter.py`](../backend/app/forecasting/chronos_adapter.py).

---

### 6. Autonomous Price Spike Risk Gauge & Macro-Driver Decomposition

![Forecast Risk Gauge & Drivers](screenshots/06_forecast_risk_gauge_and_spike_probability.png)

- **Route / Component:** [`frontend/src/components/ForecastRiskView.tsx`](../frontend/src/components/ForecastRiskView.tsx) -> [`RiskGauge.tsx`](../frontend/src/components/RiskGauge.tsx)
- **Purpose:** Quantitative risk scoring engine estimating the statistical probability of acute market disruption and identifying primary econometric drivers.
- **Key Features Displayed:**
  - **Liquid Glass Risk Gauge:** Visual radial dial indicating high spike probability (78% risk rating).
  - **Primary Driver Decomposition:** Breakdown of contributory factors: Kharif harvest rainfall delays (+34%), diesel freight escalation (+22%), and inter-state export demand from Tamil Nadu/Karnataka (+18%).
  - **Rolling-Origin Backtest Metrics:** Verified Mean Absolute Error (MAE: ₹1.82) and Root Mean Square Error (RMSE: ₹2.41) across rolling validation windows.
- **Code References:** [`frontend/src/components/RiskGauge.tsx`](../frontend/src/components/RiskGauge.tsx), [`backend/app/risk/evaluator.py`](../backend/app/risk/evaluator.py), [`backend/app/forecasting/backtest.py`](../backend/app/forecasting/backtest.py).

---

### 7. Scenario Lab Policy Simulation Studio (Buffer Stock & Aadhaar Subsidies)

![Scenario Lab Policy Simulator](screenshots/07_scenario_lab_policy_simulation_studio.png)

- **Route / Component:** [`frontend/src/components/ScenarioLabView.tsx`](../frontend/src/components/ScenarioLabView.tsx)
- **Purpose:** Interactive policy simulation sandbox enabling civil servants to model the price dampening effect of government market interventions prior to capital deployment.
- **Key Features Displayed:**
  - **Buffer Stock Release Slider:** Parameterize stock liquidation from 500 MT to 5,000 MT via NAFED/NCCF reserves.
  - **Rythu Bazaar Subsidy Price Setting:** Configure Aadhaar biometric subsidized consumer price (e.g., ₹35.00/kg vs open-market ₹58.00/kg).
  - **Direct Procurement Toggle:** Model local farmer procurement to prevent distress sales while defending price floors.
- **Code References:** [`frontend/src/components/ScenarioLabView.tsx`](../frontend/src/components/ScenarioLabView.tsx), [`backend/app/simulation/scenario_engine.py`](../backend/app/simulation/scenario_engine.py).

---

### 8. Scenario Lab Exchequer Budget & Fiscal Sensitivity Analysis

![Scenario Lab Fiscal Impact](screenshots/08_scenario_lab_fiscal_exchequer_impact.png)

- **Route / Component:** [`frontend/src/components/ScenarioLabView.tsx`](../frontend/src/components/ScenarioLabView.tsx) (Impact Analysis)
- **Purpose:** Computes the fiscal cost and welfare impact on the state budget based on AP's monthly consumption rate of 45,000 Metric Tonnes.
- **Key Features Displayed:**
  - **Fiscal Sensitivity Rule:** Standardized baseline of ₹4.50 Crores / month per ₹1.00/kg price variance.
  - **Net Budget Outlay:** Dynamic projection of procurement expenditure, transport subsidy, and net consumer surplus.
  - **Price Suppression Trajectory:** Side-by-side curve comparison: Status Quo baseline vs. Policy Intervention trajectory.
- **Code References:** [`frontend/src/components/ScenarioLabView.tsx`](../frontend/src/components/ScenarioLabView.tsx), [`backend/app/simulation/scenario_engine.py`](../backend/app/simulation/scenario_engine.py).

---

### 9. Autonomous Decision Briefs & Executive Strategic Recommendations

![Decision Briefs Recommendations](screenshots/09_decision_briefs_autonomous_recommendations.png)

- **Route / Component:** [`frontend/src/components/DecisionBriefsView.tsx`](../frontend/src/components/DecisionBriefsView.tsx)
- **Purpose:** Synthesizes forecasting insights, risk signals, and inventory status into formal, executive-ready decision briefs for the Department of Agriculture and Civil Supplies.
- **Key Features Displayed:**
  - **Structured Action Plans:** Recommended intervention volumes, target distribution mandis, and fiscal outlays.
  - **Urgency & Confidence Classification:** High-priority flagging with 92% algorithmic confidence.
  - **Plain-Language Strategic Context:** Clear, non-technical executive rationale compliant with administrative standards.
- **Code References:** [`frontend/src/components/DecisionBriefsView.tsx`](../frontend/src/components/DecisionBriefsView.tsx), [`backend/app/api/v1/recommendations.py`](../backend/app/api/v1/recommendations.py).

---

### 10. Multi-Tier Governance Approval & State-Machine Workflow

![Governance Approval State Machine](screenshots/10_governance_approval_state_machine.png)

- **Route / Component:** [`frontend/src/components/DecisionBriefsView.tsx`](../frontend/src/components/DecisionBriefsView.tsx) (Workflow Panel)
- **Purpose:** Rigorous role-based authorization state machine ensuring algorithmic recommendations require human-in-the-loop sign-off before operational execution.
- **Key Features Displayed:**
  - **State Machine Progression:** `Draft` -> `Under Review` -> `Approved` / `Rejected` -> `Executed`.
  - **Role-Based Controls:** Enforces separation of duties between Analyst, Section Officer, Director of Marketing, and Secretary of Agriculture.
  - **Rejection & Feedback Loop:** Structured feedback capture for continuous refinement of agent recommendation algorithms.
- **Code References:** [`backend/tests/test_governance.py`](../backend/tests/test_governance.py), [`backend/app/domain/models.py`](../backend/app/domain/models.py).

---

### 11. Data Fabric Multi-Source Integration & Pipeline Orchestration

![Data Fabric Integration](screenshots/11_data_fabric_multi_source_orchestration.png)

- **Route / Component:** [`frontend/src/components/DataFabricView.tsx`](../frontend/src/components/DataFabricView.tsx)
- **Purpose:** Centralized pipeline monitor orchestrating 6 heterogeneous data feeds into a unified semantic commodities data fabric.
- **Key Features Displayed:**
  - **Connected Feeds:** AGMARKNET APMC Daily Arrivals, DOCA Retail Monitoring, AP Civil Supplies ERP, e-NAM Electronic Mandi Ledger, IMD Weather Radar, and IOCL Diesel Price Feed.
  - **Connection Protocols:** REST APIs, SFTP ETL pipelines, and live webhook subscriptions.
  - **Data Harmonization Status:** Standardized schema conversion to uniform quintal-to-kg units and ISO-8601 timestamps.
- **Code References:** [`frontend/src/components/DataFabricView.tsx`](../frontend/src/components/DataFabricView.tsx), [`backend/app/api/v1/sources.py`](../backend/app/api/v1/sources.py).

---

### 12. Data Fabric Feed Latency, Provenance & Ingestion Health

![Data Fabric Health](screenshots/12_data_fabric_ingestion_health_status.png)

- **Route / Component:** [`frontend/src/components/DataFabricView.tsx`](../frontend/src/components/DataFabricView.tsx) (Health Monitor)
- **Purpose:** Live surveillance of connector health, sync frequencies, network latencies, and automated schema reconciliation.
- **Key Features Displayed:**
  - **Latency Metrics:** Sub-minute synchronization confirmation across primary state mandis.
  - **Health Indicators:** Color-coded status dots (Green = Active/Healthy, Amber = Degraded, Red = Disconnected).
  - **Historical Ingestion Volumes:** Record counts tracking over 900+ verified daily mandi market observations.
- **Code References:** [`frontend/src/components/DataFabricView.tsx`](../frontend/src/components/DataFabricView.tsx), [`backend/app/core/audit.py`](../backend/app/core/audit.py).

---

### 13. Data Intake Client Studio & Rapid Continuous Retraining

![Data Intake Client Studio](screenshots/13_data_intake_client_studio_upload.png)

- **Route / Component:** [`frontend/src/components/DataIntakeView.tsx`](../frontend/src/components/DataIntakeView.tsx)
- **Purpose:** Client Data Studio allowing market inspectors and district officers to upload ad-hoc market surveys, APMC receipts, and private trader rates with instantaneous schema validation.
- **Key Features Displayed:**
  - **Drag-and-Drop Ingestion:** Accepts CSV and JSON datasets with automatic column header detection.
  - **Pre-Flight Validation Engine:** Verifies date continuity, flags missing price bounds, and detects input outliers before database insertion.
  - **Continuous Learning Loop:** Updates baseline model weights and recalibrates conformal prediction intervals in real time.
- **Code References:** [`frontend/src/components/DataIntakeView.tsx`](../frontend/src/components/DataIntakeView.tsx), [`backend/app/analytics/quality_checker.py`](../backend/app/analytics/quality_checker.py).

---

### 14. Tamper-Evident Run Inspector & SHA-256 Audit Trail

![Audit Trail Inspector](screenshots/14_audit_trail_agent_execution_inspector.png)

- **Route / Component:** [`frontend/src/components/RunInspectorView.tsx`](../frontend/src/components/RunInspectorView.tsx)
- **Purpose:** Comprehensive governance inspector providing an immutable, tamper-evident audit log of every model inference, risk alert, and administrative action.
- **Key Features Displayed:**
  - **Cryptographic Hash Verification:** Every event logged with timestamp, user/agent ID, and SHA-256 integrity signature.
  - **Agent Reasoning Traces:** Inspect full prompt traces, intermediate tool invocations, and confidence scoring.
  - **Compliance Export:** Exportable audit certificates satisfying state oversight and Comptroller and Auditor General (CAG) requirements.
- **Code References:** [`frontend/src/components/RunInspectorView.tsx`](../frontend/src/components/RunInspectorView.tsx), [`backend/app/api/v1/audit.py`](../backend/app/api/v1/audit.py), [`backend/app/core/audit.py`](../backend/app/core/audit.py).

---

### 15. Responsive Tablet View (768 x 1024)

![Tablet View](screenshots/15_responsive_tablet_view_768px.png)

- **Viewport Dimension:** 768px × 1024px (Apple iPad Air & Pro Portrait)
- **Purpose:** Field usability for district collectors, agricultural officers, and Rythu Bazaar supervisors using tablet devices during mandi inspections.
- **Key Features Displayed:**
  - **Adaptive Liquid Navigation:** Touch-optimized pill buttons with smooth horizontal scroll.
  - **Stacked Responsive Cards:** High-density metric layout without text truncation or horizontal overflow.
  - **Hardware-Accelerated Touch Charts:** Smooth pinch-to-zoom and gesture tooltips on mobile Safari and Chrome.

---

### 16. Responsive Mobile View (375 x 812)

![Mobile View](screenshots/16_responsive_mobile_view_375px.png)

- **Viewport Dimension:** 375px × 812px (Apple iPhone X / 13 / 15 Viewport)
- **Purpose:** On-the-ground mobile monitoring for mandi secretaries, civil supplies field inspectors, and citizens tracking daily price advisories.
- **Key Features Displayed:**
  - **Single-Column Flow:** Ergonomic vertical layout designed for single-thumb navigation.
  - **Touch-Friendly KPI Badges:** High-contrast price indicators with legible typography.
  - **Zero Layout Shift:** Rigid mobile viewport constraints preventing unwanted horizontal scroll.

---

*Documentation compiled and maintained for the AP Essential Commodities Price Intelligence & Autonomous Stabilisation Platform (AP-OPIS).*
