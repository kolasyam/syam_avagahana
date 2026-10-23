# AP Essential Commodities Price Intelligence Platform
## System Architecture & Technical Blueprint

### 1. Architectural Philosophy & Clean Decoupling

The **Andhra Pradesh Essential Commodities Price Intelligence and Autonomous Stabilisation Platform (AP-OPIS)** is built on clean architectural principles, decoupling real-time data ingestion, econometric forecasting, multi-agent orchestration, policy simulation, and modern web presentation.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                              │
│   React 19 + TypeScript + Vite 8 + Liquid Glassmorphism CSS Design    │
│   [Executive Workspace] [Market Intelligence] [Forecast & Risk]       │
│   [Scenario Lab]        [Decision Briefs]     [Data Fabric Studio]     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ REST / OpenAPI 3.1
┌───────────────────────────────────▼────────────────────────────────────┐
│                        API ROUTING & ORCHESTRATION                     │
│   FastAPI Asynchronous Gateway (Uvicorn / Starlette)                   │
│   Lifespan State Management, CORS Security, Pydantic v2 Contracts      │
└─────────┬─────────────────────────┬──────────────────────────┬─────────┘
          │                         │                          │
┌─────────▼──────────────┐ ┌────────▼─────────────┐ ┌──────────▼─────────┐
│  DATA FABRIC & AUDIT   │ │ FORECASTING ENGINES  │ │ POLICY SIMULATION  │
│  - Multi-Feed Sync     │ │ - Autoregressive GBDT│ │ - Buffer Releases  │
│  - AGMARKNET / DOCA    │ │ - Chronos Foundation │ │ - Rythu Subsidies  │
│  - Quality Checker     │ │ - Conformal Bands    │ │ - Fiscal Outlay    │
│  - SHA-256 Audit Trail │ │ - Backtest Engine    │ │ - CAG Audit Export │
└────────────────────────┘ └──────────────────────┘ └────────────────────┘
```

---

### 2. Multi-Horizon Forecasting Engine

The platform implements an ensemble multi-horizon forecasting architecture tailored for high-volatility agricultural commodities:

1. **Seasonal Naive & Exponential Smoothing Baselines:**
   - Captures intra-week market periodicity (mandi weekend closures, Sunday arrivals).
   - Establishes statistical benchmarks for candidate machine learning models.

2. **Autoregressive Covariate Regressor (GBDT / Ridge):**
   - Engineered features:
     - Lagged prices: $t-1, t-3, t-7, t-14, t-30$.
     - Rolling statistics: 7-day and 14-day rolling mean, volatility, and price momentum.
     - Mandi arrival volume ratios against historical seasonal baselines.
     - Inter-state price spreads (Lasalgaon / Solapur vs. Kurnool).

3. **Non-Parametric Conformal Prediction Interval Estimation:**
   - Computes empirical residuals on rolling backtest folds.
   - Guarantees finite-sample coverage at both 80% and 95% confidence tiers without assuming Gaussian distribution errors.

4. **Rolling-Origin Temporal Backtesting:**
   - Enforces temporal causality (no forward look-ahead bias).
   - Evaluates performance across expanding and sliding temporal test splits.

---

### 3. Quantitative Risk Scoring & Early Warning System

The risk evaluation engine continuously computes the statistical probability of acute market price spikes:
- **Price Alert Threshold:** Set at ₹35.00/kg (triggers 14-day early warning alert).
- **Crisis Threshold:** Set at ₹50.00/kg (triggers emergency buffer stock release recommendations).
- **Supply Imbalance Index:** Ratios current arrivals against historical demand coefficients.
- **Macro Drivers:** Decomposes risk drivers into weather anomalies, freight escalation, and cross-border arbitrage.

---

### 4. Policy Simulation Engine & Exchequer Sensitivity

Andhra Pradesh consumes approximately **45,000 Metric Tonnes (MT)** of onions monthly.
The economic relationship is codified mathematically:

$$\Delta \text{Fiscal Impact} = 45{,}000{,}000\text{ kg} \times (P_{\text{wholesale}} - P_{\text{subsidized}})$$

Key simulation capabilities:
1. **Buffer Stock Liquidation:** Models physical stock liquidation from 500 MT to 5,000 MT via NAFED and state warehouses.
2. **Rythu Bazaar Subsidy Disbursal:** Simulates targeted consumer relief via Aadhaar biometric authentication at ₹35.00/kg.
3. **Logistics & Procurement Throughput:** Validates storage capacity and transit constraints across districts.

---

### 5. Multi-Tier Governance & Role-Based Authorization

Algorithmic recommendations follow a strict finite-state machine to guarantee democratic and administrative accountability:
- `Draft`: Agent-generated proposal.
- `Under Review`: Assigned to Section Officer / Joint Director.
- `Approved`: Signed off by Principal Secretary / Hon. Minister.
- `Executed`: Civil Supplies Corporation issues procurement and transport tenders.
- `Rejected`: Structured rationale recorded for algorithmic recalibration.
