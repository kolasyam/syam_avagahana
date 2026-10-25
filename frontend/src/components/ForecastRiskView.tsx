import React, { useState, useEffect } from "react";
import { Cpu, ArrowRight, TrendingUp, Calendar, AlertTriangle, Sparkles, CheckCircle2 } from "lucide-react";
import { ForecastRun, RiskAssessment } from "../types";
import { fetchLatestForecast, runForecast, fetchLatestRisk, fetchBacktest } from "../api/client";
import { InteractiveChart } from "./InteractiveChart";
import { RiskGauge } from "./RiskGauge";

interface ForecastRiskViewProps {
  commodityId: string;
  geographyId: string;
  initialHorizon?: number;
  onNavigateScenario?: () => void;
}

export const ForecastRiskView: React.FC<ForecastRiskViewProps> = ({
  commodityId,
  geographyId,
  initialHorizon = 14,
  onNavigateScenario
}) => {
  const [horizon, setHorizon] = useState<number>(initialHorizon);
  const [useChronos, setUseChronos] = useState<boolean>(false);
  const [forecast, setForecast] = useState<ForecastRun | null>(null);
  const [risk, setRisk] = useState<RiskAssessment | null>(null);
  const [backtest, setBacktest] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Sync if initialHorizon changes from parent
  useEffect(() => {
    if (initialHorizon) {
      setHorizon(initialHorizon);
    }
  }, [initialHorizon]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [fc, rk, bt] = await Promise.all([
        fetchLatestForecast(commodityId, geographyId, horizon).catch(e => {
          console.error("Forecast fetch failed", e);
          return null;
        }),
        fetchLatestRisk(commodityId, geographyId).catch(e => {
          console.error("Risk fetch failed", e);
          return null;
        }),
        fetchBacktest(commodityId, geographyId, horizon).catch(e => {
          console.error("Backtest fetch failed", e);
          return null;
        })
      ]);
      if (fc) setForecast(fc);
      if (rk) setRisk(rk);
      if (bt) setBacktest(bt);
    } catch (e) {
      console.error("Failed to load forecast data", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [commodityId, geographyId, horizon]);

  const handleRunForecast = async (chronos: boolean) => {
    setLoading(true);
    try {
      const newFc = await runForecast(commodityId, geographyId, horizon, chronos);
      setForecast(newFc);
    } catch (e) {
      console.error("Forecast run failed", e);
    } finally {
      setLoading(false);
    }
  };

  // Prepare chart points
  const chartData = (forecast?.forecast_series || []).map((pt) => ({
    date: pt.date,
    predicted_modal: pt.predicted_modal,
    lower_80: pt.lower_80,
    upper_80: pt.upper_80,
    lower_95: pt.lower_95,
    upper_95: pt.upper_95
  }));

  const metrics: any = forecast?.metrics;
  // Real artifact fields: mae / wape_pct / coverage_80 / eval_samples (rolling backtest)
  const maeVal = typeof metrics?.mae === "number" ? metrics.mae : null;
  const wapeVal = typeof metrics?.wape_pct === "number" ? metrics.wape_pct
    : typeof metrics?.wape === "number" ? metrics.wape : null;
  const covVal = typeof metrics?.coverage_80 === "number" ? metrics.coverage_80
    : typeof metrics?.interval_coverage === "number" ? metrics.interval_coverage : null;
  const evalPoints = typeof metrics?.eval_samples === "number" ? metrics.eval_samples : null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Editorial Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div className="eyebrow-tag" style={{ color: "var(--color-primary)", marginBottom: "6px" }}>
            PREDICTIVE MODELING & THRESHOLD SURVEILLANCE
          </div>
          <h1 className="display-title" style={{ fontSize: "32px" }}>
            Forecast & Risk Intelligence
          </h1>
          <p style={{ fontFamily: "var(--font-serif)", fontStyle: "italic", fontSize: "17px", color: "var(--color-ink-muted)", marginTop: "4px" }}>
            Foundation-model forecasting (real Chronos-2) with deterministic fallback, backed by a rolling-origin backtest on four years of real market data.
          </p>
        </div>

        {/* Controls: Multi-Horizon Pills & Model Switcher */}
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          backgroundColor: "rgba(255, 255, 255, 0.75)",
          backdropFilter: "blur(20px) saturate(200%)",
          WebkitBackdropFilter: "blur(20px) saturate(200%)",
          padding: "6px 14px",
          borderRadius: "var(--radius-pill)",
          border: "1px solid rgba(255, 255, 255, 0.85)",
          boxShadow: "var(--shadow-liquid-subtle)",
          flexWrap: "wrap"
        }}>
          {/* Horizon Selection Buttons */}
          <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            <span className="eyebrow-tag" style={{ fontSize: "10px", marginRight: "4px" }}>HORIZON:</span>
            {[
              { val: 7, label: "7D Tactical" },
              { val: 14, label: "14D Buffer" },
              { val: 30, label: "30D Monthly" },
              { val: 60, label: "60D Harvest Influx" },
              { val: 90, label: "90D Clearing" }
            ].map((h) => (
              <button
                key={h.val}
                onClick={() => setHorizon(h.val)}
                className="btn-liquid"
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "11px",
                  fontWeight: 600,
                  padding: "4px 10px",
                  backgroundColor: horizon === h.val ? "var(--color-primary)" : "transparent",
                  color: horizon === h.val ? "#ffffff" : "var(--color-ink-muted)",
                  border: horizon === h.val ? "none" : "1px solid transparent",
                  boxShadow: horizon === h.val ? "0 2px 8px rgba(0, 102, 204, 0.28)" : "none"
                }}
              >
                {h.label}
              </button>
            ))}
          </div>

          <span style={{ color: "rgba(0, 0, 0, 0.12)" }}>|</span>

          {/* Model Switcher */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <button
              className={`btn-liquid ${!useChronos ? "btn-primary" : "btn-glass"}`}
              style={{ fontSize: "11px", padding: "5px 12px" }}
              onClick={() => {
                setUseChronos(false);
                handleRunForecast(false);
              }}
            >
              AR-Lag Covariate
            </button>
            <button
              className={`btn-liquid ${useChronos ? "btn-terracotta" : "btn-glass"}`}
              style={{ fontSize: "11px", padding: "5px 12px" }}
              onClick={() => {
                setUseChronos(true);
                handleRunForecast(true);
              }}
            >
              <Cpu size={12} />
              Chronos Candidate
            </button>
          </div>
        </div>
      </div>

      {/* Model Spec & Accuracy Bar */}
      {metrics && (
        <div className="liquid-glass" style={{
          padding: "20px 24px",
          background: "linear-gradient(135deg, rgba(200, 230, 205, 0.28) 0%, rgba(255, 255, 255, 0.7) 100%)",
          border: "1px solid rgba(200, 230, 205, 0.6)"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
            <div>
              <div className="eyebrow-tag" style={{ color: "var(--glass-mint-ink)" }}>ACTIVE MODEL ENGINE • {forecast?.status}</div>
              <div style={{ fontFamily: "var(--font-sans)", fontSize: "18px", fontWeight: 700, marginTop: "2px", color: "var(--color-ink)" }}>
                {forecast?.model_name} ({forecast?.model_version})
              </div>
              <div style={{ fontSize: "13px", color: "var(--color-ink-muted)", marginTop: "2px" }}>
                Cutoff Date: <span style={{ fontFamily: "var(--font-mono)" }}>{forecast?.data_cutoff_date}</span> • Horizon: <strong style={{ fontFamily: "var(--font-mono)", color: "var(--color-primary)" }}>{horizon} Days</strong>
              </div>
            </div>

            <div style={{ display: "flex", gap: "24px", flexWrap: "wrap" }}>
              <div>
                <div className="eyebrow-tag" style={{ color: "var(--color-ink-muted)", fontSize: "10px" }}>MAE (₹/KG, ROLLING BACKTEST)</div>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: "20px", fontWeight: 700, color: "var(--color-ink)" }}>{maeVal != null ? `₹${maeVal.toFixed(2)}` : "—"}</div>
              </div>
              <div>
                <div className="eyebrow-tag" style={{ color: "var(--color-ink-muted)", fontSize: "10px" }}>BACKTEST EVAL POINTS</div>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: "20px", fontWeight: 700, color: "var(--color-ink)" }}>{evalPoints != null ? evalPoints : "—"}</div>
              </div>
              <div>
                <div className="eyebrow-tag" style={{ color: "var(--color-ink-muted)", fontSize: "10px" }}>WAPE</div>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: "20px", fontWeight: 700, color: "var(--status-normal)" }}>{wapeVal != null ? `${wapeVal.toFixed(1)}%` : "—"}</div>
              </div>
              <div>
                <div className="eyebrow-tag" style={{ color: "var(--color-ink-muted)", fontSize: "10px" }}>80% COVERAGE (BACKTEST)</div>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: "20px", fontWeight: 700, color: "var(--color-primary)" }}>{covVal != null ? `${covVal.toFixed(1)}%` : "—"}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 60-Day & 90-Day Seasonal Harvest Outlook & Actionable Policy Advisory Card */}
      {forecast?.advisory && (
        <div className="liquid-glass-elevated" style={{
          padding: "24px 28px",
          background: horizon >= 60
            ? "linear-gradient(135deg, rgba(244, 236, 214, 0.45) 0%, rgba(255, 255, 255, 0.85) 100%)"
            : "linear-gradient(135deg, rgba(243, 201, 182, 0.3) 0%, rgba(255, 255, 255, 0.85) 100%)",
          border: horizon >= 60 ? "1px solid rgba(212, 160, 23, 0.35)" : "1px solid rgba(204, 120, 92, 0.35)"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
            <div style={{ flex: 1, minWidth: "320px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                <span className={`badge-glass ${horizon >= 60 ? "badge-cream" : "badge-coral"}`}>
                  {horizon === 60 ? "60-DAY MEDIUM-TERM HARVEST OUTLOOK" : (horizon === 90 ? "90-DAY LONG-TERM MARKET STABILISATION" : `${horizon}-DAY OPERATIONAL DIRECTIVE`)}
                </span>
                <span className="eyebrow-tag" style={{ fontSize: "10.5px" }}>STATE PRICE STABILISATION FUND (PSF)</span>
              </div>

              <h3 style={{ fontFamily: "var(--font-serif)", fontStyle: "italic", fontSize: "22px", fontWeight: 400, color: "var(--color-ink)", marginBottom: "8px" }}>
                {horizon >= 60 ? "Seasonal Crop Physics & Market Influx Horizon" : "Immediate Supply Deficit Containment"}
              </h3>

              <p style={{ fontFamily: "var(--font-sans)", fontSize: "15px", lineHeight: 1.6, color: "var(--color-ink-secondary)" }}>
                {forecast.advisory}
              </p>
            </div>

            {onNavigateScenario && (
              <button
                className="btn-liquid btn-primary"
                onClick={onNavigateScenario}
                style={{ padding: "10px 20px", fontSize: "13.5px", alignSelf: "center" }}
              >
                <span>Simulate Policy Scenario for {horizon}D</span>
                <ArrowRight size={15} />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Primary Chart & Risk Gauge Row */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "24px" }}>
        <InteractiveChart
          title={`${horizon}-Day Predictive Price Trajectory`}
          subtitle={`AR-Lag Tabular Engine with IMD Rainfall & Arrival Deficit Covariates • 80% & 95% Confidence Intervals`}
          data={chartData}
          alertThreshold={35.0}
          crisisThreshold={50.0}
          showArrivals={false}
          showConfidenceInterval={true}
          height={380}
        />

        <RiskGauge risk={risk} />
      </div>

      {/* Model Comparison & Rolling Backtest Matrix — REAL artifact numbers only */}
      {backtest && backtest.models && (
        <div className="liquid-glass" style={{ padding: "24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "8px" }}>
            <div>
              <div className="eyebrow-tag">ROLLING-ORIGIN VALIDATION • REAL DATA</div>
              <h3 style={{ fontFamily: "var(--font-serif)", fontSize: "20px", fontWeight: 400, color: "var(--color-ink)" }}>
                Backtest Benchmark ({backtest.horizon_tested ?? backtest.horizon_requested ?? horizon}-Day Horizons, {backtest.n_folds ?? "?"} Folds)
              </h3>
            </div>
            <span className="badge-glass badge-mint" style={{ fontSize: "10px" }}>
              BACKTEST ARTIFACT {backtest.generated_at ? new Date(backtest.generated_at).toLocaleDateString() : ""}
            </span>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px", textAlign: "left" }}>
              <thead>
                <tr style={{ background: "rgba(0, 0, 0, 0.03)", borderBottom: "1px solid rgba(0, 0, 0, 0.08)" }}>
                  <th style={{ padding: "10px 14px" }}>Model</th>
                  <th style={{ padding: "10px 14px" }}>MAE (₹/kg)</th>
                  <th style={{ padding: "10px 14px" }}>RMSE (₹/kg)</th>
                  <th style={{ padding: "10px 14px" }}>WAPE (%)</th>
                  <th style={{ padding: "10px 14px" }}>80% Coverage</th>
                  <th style={{ padding: "10px 14px" }}>95% Coverage</th>
                  <th style={{ padding: "10px 14px" }}>Role</th>
                </tr>
              </thead>
              <tbody>
                {backtest.models.map((m: any, idx: number) => (
                  <tr
                    key={idx}
                    style={{
                      borderBottom: "1px solid rgba(0, 0, 0, 0.05)",
                      backgroundColor: m.is_champion ? "rgba(0, 102, 204, 0.05)" : "transparent",
                    }}
                  >
                    <td style={{ padding: "10px 14px", fontWeight: m.is_champion ? 600 : 500, color: m.is_champion ? "var(--color-primary)" : "var(--color-ink)" }}>
                      {m.model_name}
                    </td>
                    <td style={{ padding: "10px 14px", fontFamily: "var(--font-mono)" }}>{m.mae?.toFixed(2)}</td>
                    <td style={{ padding: "10px 14px", fontFamily: "var(--font-mono)" }}>{m.rmse?.toFixed(2)}</td>
                    <td style={{ padding: "10px 14px", fontFamily: "var(--font-mono)", fontWeight: 600, color: "var(--status-normal)" }}>
                      {m.wape_pct?.toFixed(1)}%
                    </td>
                    <td style={{ padding: "10px 14px", fontFamily: "var(--font-mono)" }}>
                      {m.interval_80_coverage_pct != null ? `${m.interval_80_coverage_pct.toFixed(1)}%` : "—"}
                    </td>
                    <td style={{ padding: "10px 14px", fontFamily: "var(--font-mono)" }}>
                      {m.interval_95_coverage_pct != null ? `${m.interval_95_coverage_pct.toFixed(1)}%` : "—"}
                    </td>
                    <td style={{ padding: "10px 14px" }}>
                      {m.is_champion ? (
                        <span className="badge-glass badge-mint" style={{ fontSize: "10px" }}>CHAMPION</span>
                      ) : m.is_baseline ? (
                        <span className="badge-glass badge-cream" style={{ fontSize: "10px" }}>NAIVE BASELINE</span>
                      ) : (
                        <span className="badge-glass badge-lilac" style={{ fontSize: "10px" }}>TABULAR</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {backtest.chronos_skill_vs_naive_pct != null && (
            <div style={{ marginTop: "12px", fontSize: "12.5px", color: "var(--color-ink-secondary)" }}>
              Champion skill vs naive baseline: <strong>{backtest.chronos_skill_vs_naive_pct > 0 ? "+" : ""}{backtest.chronos_skill_vs_naive_pct}% MAE improvement</strong> · errors in ₹/kg (quintal/100)
            </div>
          )}
          {backtest.selection_rule && (
            <div style={{ marginTop: "8px", fontSize: "11.5px", color: "var(--color-ink-muted)", fontStyle: "italic" }}>
              Selection rule: {backtest.selection_rule}
            </div>
          )}
          {Array.isArray(backtest.honest_notes) && backtest.honest_notes.length > 0 && (
            <div style={{ marginTop: "8px", display: "flex", flexDirection: "column", gap: "4px" }}>
              {backtest.honest_notes.map((n: string, i: number) => (
                <div key={i} style={{ fontSize: "12px", color: "var(--color-terracotta)" }}>⚠ {n}</div>
              ))}
            </div>
          )}
          {backtest.note && (
            <div style={{ marginTop: "6px", fontSize: "12px", color: "var(--color-ink-muted)" }}>{backtest.note}</div>
          )}
        </div>
      )}
    </div>
  );
};
