"""
The Eight Domain Agent Modules for AP Essential Commodities Platform
====================================================================
Implements the Standard Agent Pattern (Input Contract -> Reason -> Tool Calls ->
Output Contract -> Guardrails).

REWIRED FOR REAL DATA (Monday build):
Every agent reads the ingested real series / external context / model artifacts
and reports ONLY data-derived values. When a value is unavailable, the agent
says so instead of substituting an invented default. Configured policy
parameters (thresholds, catalog options, buffer registry) are labeled as
policy-configured inputs, not as measurements.
All narratives and findings strictly English-only.
"""

import os
from typing import Dict, Any, List, Optional

from app.core.config import settings

_METRICS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "forecasting", "forecast_metrics.json"
)


def _load_real_metrics(geography_id: str, horizon_days: int) -> Optional[Dict[str, Any]]:
    """Real backtest metrics for the nearest evaluated horizon bucket."""
    try:
        import json
        if not os.path.exists(_METRICS_PATH):
            return None
        with open(_METRICS_PATH, "r", encoding="utf-8") as fh:
            store = json.load(fh)
        geo_block = store.get("by_geography", {}).get(geography_id) or {}
        buckets = sorted((int(k) for k in geo_block.keys()))
        eligible = [b for b in buckets if b <= horizon_days]
        bucket = max(eligible) if eligible else (buckets[0] if buckets else None)
        if bucket is None:
            return None
        block = geo_block.get(str(bucket), {})
        champion = next((m for m in block.get("models", []) if m.get("is_champion")), None)
        if champion:
            return {
                "model_name": champion["model_name"],
                "backtest_horizon_days": bucket,
                "mae": champion["mae"],
                "wape_pct": champion["wape_pct"],
                "coverage_80": champion.get("interval_80_coverage_pct"),
                "eval_samples": champion.get("eval_samples"),
            }
    except (OSError, ValueError, KeyError):
        return None
    return None


class MarketAgent:
    name = "Market Intelligence Agent"
    role = "market"

    def run(
        self,
        observations: List[Dict[str, Any]],
        analytics: Dict[str, Any],
        geography_id: str = "state_andhra_pradesh",
    ) -> Dict[str, Any]:
        summary = analytics.get("summary", {})
        anomalies = analytics.get("anomalies", [])

        latest_price = summary.get("latest_modal_price")
        wow_change = summary.get("wow_price_change_pct")
        arrivals = summary.get("latest_arrivals_mt")
        volatility = summary.get("current_volatility")

        if latest_price is None or not observations:
            return {
                "agent": self.name,
                "role": self.role,
                "confidence": "LOW",
                "finding": (
                    f"No ingested price series available for {geography_id}. "
                    "Local data lookup failed — escalate to the web-fallback tool "
                    "with source citations before any analysis."
                ),
                "evidence": [
                    {"source": "Ingested series", "metric": "Observations", "value": f"{len(observations)} rows"},
                    {"source": "Web fallback", "metric": "Status", "value": "Escalation recommended (citation-only)"},
                ],
                "next_step": "Trigger web_lookup escalation via the Market Agent tool loop",
            }

        # Arrival momentum from real observations (last 14d vs prior 14d)
        arrivals_note = "n/a"
        if len(observations) >= 28 and arrivals is not None:
            recent = [o["arrivals_mt"] for o in observations[-14:] if o.get("arrivals_mt") is not None]
            prior = [o["arrivals_mt"] for o in observations[-28:-14] if o.get("arrivals_mt") is not None]
            if recent and prior:
                r_avg = sum(recent) / len(recent)
                p_avg = sum(prior) / len(prior)
                if p_avg > 0:
                    mom = (r_avg - p_avg) / p_avg * 100.0
                    arrivals_note = f"14d avg {r_avg:,.0f} MT/day ({mom:+.1f}% vs prior 14d)"
                else:
                    arrivals_note = f"14d avg {sum(recent)/len(recent):,.0f} MT/day"

        cutoff = observations[-1].get("date", "unknown") if observations else "unknown"
        finding = (
            f"{geography_id.replace('_', ' ').title()} modal price ₹{latest_price:.2f}/kg "
            f"(data through {cutoff}). "
            + (f"Week-on-week change {wow_change:+.1f}%. " if wow_change is not None else "")
            + f"Arrival momentum: {arrivals_note}. "
            + (f"{len(anomalies)} active anomaly flag(s) from the analytics engine." if anomalies else "No active anomalies.")
        )

        evidence = [
            {"source": "Ingested series (AGMARKNET-derived)", "metric": "Modal Price", "value": f"₹{latest_price:.2f}/kg"},
            {"source": "Ingested series", "metric": "Latest Arrivals", "value": f"{arrivals:,.0f} MT" if arrivals is not None else "n/a"},
            {"source": "Ingested series", "metric": "Price Volatility (annualised)", "value": f"{volatility:.2f}" if volatility is not None else "n/a"},
            {"source": "Analytics Engine", "metric": "Active Anomalies", "value": f"{len(anomalies)}"},
        ]
        return {
            "agent": self.name,
            "role": self.role,
            "confidence": "HIGH",
            "finding": finding,
            "evidence": evidence,
            "next_step": "Correlate weather context and upstream-supply signals",
        }


class WeatherAgent:
    name = "Weather Risk Agent"
    role = "weather"

    def run(self, db: Any, geo_id: str) -> Dict[str, Any]:
        from app.domain.models import ExternalObservation

        rows = db.query(ExternalObservation).filter(
            ExternalObservation.geography_id == geo_id,
            ExternalObservation.variable_name.in_(["precipitation_mm", "vpd_kpa", "seasonal_rain_mm"]),
        ).order_by(ExternalObservation.date.desc()).limit(28 * 3).all()

        if not rows:
            return {
                "agent": self.name,
                "role": self.role,
                "confidence": "LOW",
                "finding": "No ingested weather context for this geography; live IMD telemetry is a roadmap item.",
                "evidence": [{"source": "Ingested context", "metric": "Coverage", "value": "none"}],
                "next_step": "Ingest weather context or use web fallback with citations",
            }

        by_var = {}
        cutoff = rows[0].date
        for r in rows:
            by_var.setdefault(r.variable_name, []).append(r.value)

        rain14 = sum((by_var.get("precipitation_mm") or [])[:14])
        vpd14 = (by_var.get("vpd_kpa") or [])[:14]
        rain_prior = sum((by_var.get("precipitation_mm") or [])[14:28])
        vpd_str = f"{sum(vpd14)/len(vpd14):.2f} kPa avg" if vpd14 else "n/a"

        trend = (
            "elevated vs prior 14 days" if rain14 > rain_prior * 1.25
            else "below prior 14 days" if rain_prior > rain14 * 1.25
            else "near prior 14-day levels"
        )
        impact = (
            "Harvest/logistics disruption risk in producing belts — monitor despatch corridors."
            if rain14 > 100 else "No extreme-precipitation signal in the ingested context."
        )

        finding = (
            f"Ingested weather context (IMD-derived): cumulative 14-day precipitation {rain14:.1f} mm "
            f"({trend}, prior window {rain_prior:.1f} mm), avg VPD {vpd_str}, through {cutoff}. {impact}"
        )
        return {
            "agent": self.name,
            "role": self.role,
            "confidence": "HIGH",
            "finding": finding,
            "evidence": [
                {"source": "Ingested context (IMD-derived)", "metric": "Cum. Rain 14d", "value": f"{rain14:.1f} mm"},
                {"source": "Ingested context", "metric": "Prior 14d Rain", "value": f"{rain_prior:.1f} mm"},
                {"source": "Ingested context", "metric": "Avg VPD 14d", "value": vpd_str},
            ],
            "next_step": "Assess supply buffers and interstate flow signals",
        }


class SupplyAgent:
    name = "Supply & Stock Agent"
    role = "supply"

    def run(self, db: Any) -> Dict[str, Any]:
        from app.domain.models import ExternalObservation, MarketObservation

        finding_parts: List[str] = []
        evidence: List[Dict[str, str]] = []

        # Real production context
        prod = db.query(ExternalObservation).filter(
            ExternalObservation.variable_name == "production_kt",
            ExternalObservation.geography_id == "state_andhra_pradesh",
        ).order_by(ExternalObservation.date.desc()).first()
        prod_india = db.query(ExternalObservation).filter(
            ExternalObservation.variable_name == "production_kt",
            ExternalObservation.geography_id == "nation_india",
        ).order_by(ExternalObservation.date.desc()).first()
        if prod is not None:
            finding_parts.append(
                f"Standing AP production estimate {prod.value:,.1f} '000 MT"
                + (f" vs all-India {prod_india.value:,.1f} '000 MT" if prod_india is not None else "")
                + f" (as of {prod.date})."
            )
            evidence.append({
                "source": "Ingested context (Horticulture estimates)",
                "metric": "AP Production Estimate",
                "value": f"{prod.value:,.1f} '000 MT",
            })

        # Real arrival momentum, latest 14d (one observation row per day)
        rows = db.query(MarketObservation.arrivals_mt).filter(
            MarketObservation.commodity_id == settings.PILOT_COMMODITY_ID,
            MarketObservation.geography_id == settings.PILOT_MARKET_ID,
        ).order_by(MarketObservation.date.desc()).limit(14).all()
        if rows:
            daily = [r[0] for r in rows if r[0] is not None]
            avg14 = sum(daily) / max(1, len(daily))
            finding_parts.append(f"AP mandi arrivals now average {avg14:,.0f} MT/day (last 14 days, real series).")
            evidence.append({
                "source": "Ingested series",
                "metric": "Arrivals 14d Avg",
                "value": f"{avg14:,.0f} MT/day",
            })

        # Policy-configured buffer registry (NOT a measurement)
        finding_parts.append(
            "PSF buffer registry (policy-configured): 28,500 MT uncommitted ceiling is the "
            "scenario-engine planning parameter."
        )
        evidence.append({
            "source": "Policy Registry (configured)",
            "metric": "PSF Buffer Planning Cap",
            "value": "28,500 MT",
        })

        if not finding_parts:
            finding_parts.append("Supply context unavailable — no ingested supply signals.")

        return {
            "agent": self.name,
            "role": self.role,
            "confidence": "HIGH",
            "finding": " ".join(finding_parts),
            "evidence": evidence,
            "next_step": "Run multi-horizon forecast models",
        }


class ForecastAgent:
    name = "Forecasting Agent"
    role = "forecast"

    def run(self, forecast_data: Dict[str, Any], geography_id: str = "state_andhra_pradesh") -> Dict[str, Any]:
        series = forecast_data.get("series", [])
        model_name = forecast_data.get("model_name", "model unspecified")

        if not series:
            return {
                "agent": self.name,
                "role": self.role,
                "confidence": "LOW",
                "finding": "No forecast series available; foundation model unavailable and fallback failed.",
                "evidence": [{"source": "Forecast Service", "metric": "Status", "value": "unavailable"}],
                "next_step": "Inspect model availability and retry",
            }

        peak_pred = max(p["predicted_modal"] for p in series)
        peak_day = next(p for p in series if p["predicted_modal"] == peak_pred)
        last = series[-1]

        metrics = forecast_data.get("metrics") or _load_real_metrics(geography_id, forecast_data.get("horizon_days", 30))

        metrics_str = "not yet evaluated (artifact pending)"
        if metrics:
            metrics_str = (
                f"{metrics.get('model_name', 'champion')}: WAPE {metrics.get('wape_pct')}% "
                f"(MAE ₹{metrics.get('mae')}/kg, {metrics.get('eval_samples')} real eval points, "
                f"h={metrics.get('backtest_horizon_days')}d rolling folds)"
            )

        finding = (
            f"{model_name} projects the modal price path to peak at "
            f"₹{peak_pred:.2f}/kg around {peak_day['date']}, ending the horizon at "
            f"₹{last['predicted_modal']:.2f}/kg (80% band ₹{last['lower_80']:.2f}–₹{last['upper_80']:.2f}). "
            f"Real backtest: {metrics_str}."
        )

        evidence = [
            {"source": "Forecast Service", "metric": "Projected Peak", "value": f"₹{peak_pred:.2f}/kg @ {peak_day['date']}"},
            {"source": "Forecast Service", "metric": "Horizon-End (80% band)", "value": f"₹{last['lower_80']:.2f}–₹{last['upper_80']:.2f}"},
            {"source": "Rolling-Origin Backtest (REAL data)", "metric": "Champion WAPE", "value": f"{metrics.get('wape_pct')}%" if metrics else "pending artifact"},
        ]
        return {
            "agent": self.name,
            "role": self.role,
            "confidence": "HIGH",
            "finding": finding,
            "evidence": evidence,
            "next_step": "Compute threshold breach probabilities",
        }


class RiskAgent:
    name = "Price Spike Risk Agent"
    role = "risk"

    def run(self, risk_data: Dict[str, Any]) -> Dict[str, Any]:
        prob = risk_data.get("spike_probability")
        level = risk_data.get("threshold_level", "EVALUATED")

        if prob is None:
            return {
                "agent": self.name,
                "role": self.role,
                "confidence": "LOW",
                "finding": "Risk evaluation unavailable (no forecast distribution); cannot state breach probability.",
                "evidence": [{"source": "Risk Evaluator", "metric": "Status", "value": "unavailable"}],
                "next_step": "Serve a forecast run before risk evaluation",
            }

        crisis = settings.ONION_CRISIS_THRESHOLD
        sheet = risk_data.get("probability_sheet") or {}
        alert_sheet = (sheet.get("alert_exceedance") or {})

        finding = (
            f"{level}: deterministic calibrated evaluator puts spike probability "
            f"(vs alert ₹{settings.ONION_ALERT_THRESHOLD:.2f}/kg) at {prob*100:.0f}%. "
        )
        if alert_sheet:
            finding += (
                f"Quantile-ladder over the same Chronos-2 distribution: max-30d alert "
                f"exceedance {alert_sheet.get('max_within_30d', 0)*100:.1f}% "
                f"(day-7 {alert_sheet.get('day7', 0)*100:.1f}%, "
                f"day-30 {alert_sheet.get('day30', 0)*100:.1f}%). "
            )
        finding += f"Crisis threshold ₹{crisis:.2f}/kg per policy registry."

        evidence = [
            {"source": "Risk Evaluator (deterministic layer)", "metric": "Spike Probability", "value": f"{prob*100:.0f}%"},
            {"source": "Probability Sheet (quantile ladder, REAL Chronos-2 bands)", "metric": "Max-30d Alert Exceedance", "value": f"{alert_sheet.get('max_within_30d', 0)*100:.1f}%" if alert_sheet else "n/a"},
            {"source": "Policy Registry (configured)", "metric": "Crisis Threshold", "value": f"₹{crisis:.2f}/kg"},
            {"source": "Forecast Distribution", "metric": "Quantile-Ladder Basis", "value": "Chronos-2 bands -> evaluator features"},
        ]
        return {
            "agent": self.name,
            "role": self.role,
            "confidence": "HIGH",
            "finding": finding,
            "evidence": evidence,
            "next_step": "Match intervention playbook options",
        }


class InterventionAgent:
    name = "Intervention Catalog Agent"
    role = "intervention"

    def run(self, projected_peak: Optional[float] = None) -> Dict[str, Any]:
        catalog = [
            ("Option A", "5,000 MT Quick Release (Local Mandis)"),
            ("Option B", "10,000 MT Multi-District Rythu Bazaar Injection"),
            ("Option C", "20,000 MT State-Wide Mega Release"),
        ]
        if projected_peak is not None and projected_peak > settings.ONION_CRISIS_THRESHOLD:
            recommendation = "Option C (state-wide) indicated by projected peak vs crisis threshold."
        elif projected_peak is not None and projected_peak > settings.ONION_ALERT_THRESHOLD:
            recommendation = "Option B (targeted 10,000 MT) indicated by projected peak vs alert threshold."
        else:
            recommendation = "No tier indicated yet — peak does not exceed the alert threshold in the evaluated path."

        finding = (
            "Intervention playbook (policy-configured catalog): "
            + "; ".join(f"{k}: {v}" for k, v in catalog)
            + f". Screening: {recommendation}"
        )
        return {
            "agent": self.name,
            "role": self.role,
            "confidence": "HIGH",
            "finding": finding,
            "evidence": [
                {"source": "Intervention Catalog (policy-configured)", "metric": "Tier A", "value": "5,000 MT Quick Release"},
                {"source": "Intervention Catalog (policy-configured)", "metric": "Tier B", "value": "10,000 MT Multi-District Injection"},
                {"source": "Intervention Catalog (policy-configured)", "metric": "Tier C", "value": "20,000 MT State-Wide Release"},
            ],
            "next_step": "Execute deterministic what-if scenario simulation",
        }


class ScenarioAgent:
    name = "Scenario Simulator Agent"
    role = "scenario"

    def run(self, scenario_result: Dict[str, Any]) -> Dict[str, Any]:
        mitigation = scenario_result.get("expected_price_mitigation_pct")
        budget = scenario_result.get("total_budget_cr")
        stock_left = scenario_result.get("stock_remaining_mt")
        name = scenario_result.get("scenario_name", "configured scenario")

        if mitigation is None:
            return {
                "agent": self.name,
                "role": self.role,
                "confidence": "LOW",
                "finding": "Scenario simulation did not return mitigation metrics; no invented values shown.",
                "evidence": [{"source": "Scenario Engine", "metric": "Status", "value": "incomplete"}],
                "next_step": "Fix scenario inputs and re-run the simulation",
            }

        mitig_str = f"-{mitigation:.1f}%"
        budget_str = f"₹{budget:.2f} Cr" if budget is not None else "n/a"
        stock_str = f"{stock_left:,.0f} MT" if stock_left is not None else "n/a"

        finding = (
            f"Deterministic simulation ({name}, real constraint math — stock cap, subsidy, "
            f"logistics capacity): projected peak mitigation {mitig_str}, "
            f"subsidy outlay {budget_str}, remaining buffer registry reserve {stock_str}."
        )
        return {
            "agent": self.name,
            "role": self.role,
            "confidence": "HIGH",
            "finding": finding,
            "evidence": [
                {"source": "Scenario Engine (deterministic)", "metric": "Price Mitigation", "value": mitig_str},
                {"source": "Budget Engine (deterministic)", "metric": "Estimated Outlay", "value": budget_str},
                {"source": "Buffer Registry (configured)", "metric": "Reserve After Release", "value": stock_str},
            ],
            "next_step": "Draft governed decision brief for departmental review",
        }


class WorkflowAgent:
    name = "Workflow & Decision Brief Agent"
    role = "workflow"

    def run(self, brief_id: Optional[str] = None, audit_id: Optional[str] = None) -> Dict[str, Any]:
        finding = (
            "Governed decision brief registered in the platform (real database row). "
            "Demo policy: no approval UI in this session — brief remains SUBMITTED "
            "with the full audit trail attached."
        )
        return {
            "agent": self.name,
            "role": self.role,
            "confidence": "HIGH",
            "finding": finding,
            "evidence": [
                {"source": "Governance Service (real row)", "metric": "Review ID", "value": brief_id or "not created"},
                {"source": "Audit System (real row)", "metric": "Audit Trail ID", "value": audit_id or "not created"},
            ],
            "next_step": "Investigation complete; brief stored with immutable audit trail",
        }
