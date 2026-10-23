import React from "react";
import { AlertTriangle, TrendingUp, CheckCircle, Info } from "lucide-react";
import { RiskAssessment } from "../types";

interface RiskGaugeProps {
  risk: RiskAssessment | null;
}

export const RiskGauge: React.FC<RiskGaugeProps> = ({ risk }) => {
  if (!risk) return null;

  const prob = risk.spike_probability;
  const pct = Math.round(prob * 100);

  // Status color
  let color = "var(--status-normal)";
  let badgeClass = "badge-mint";
  if (risk.threshold_level === "CRITICAL" || prob >= 0.75) {
    color = "var(--status-critical)";
    badgeClass = "badge-coral";
  } else if (risk.threshold_level === "HIGH_ALERT" || prob >= 0.50) {
    color = "var(--status-watch)";
    badgeClass = "badge-cream";
  }

  return (
    <div className="liquid-glass" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "18px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div className="eyebrow-tag" style={{ color: "var(--color-ink-muted)" }}>RISK ASSESSMENT ENGINE</div>
          <h3 style={{ fontFamily: "var(--font-serif)", fontSize: "20px", fontWeight: 400, color: "var(--color-ink)", marginTop: "2px" }}>
            Price Spike & Breach Risk
          </h3>
        </div>
        <span className={`badge-glass ${badgeClass}`}>
          {risk.threshold_level}
        </span>
      </div>

      {/* Probability Gauge Indicator */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: "18px",
        padding: "16px",
        background: "rgba(255, 255, 255, 0.65)",
        border: "1px solid rgba(0, 0, 0, 0.05)",
        borderRadius: "var(--radius-lg)"
      }}>
        <div style={{ position: "relative", width: "80px", height: "80px", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <svg viewBox="0 0 36 36" style={{ width: "100%", height: "100%", transform: "rotate(-90deg)" }}>
            <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="rgba(0, 0, 0, 0.08)" strokeWidth="3.2" />
            <circle
              cx="18"
              cy="18"
              r="15.915"
              fill="transparent"
              stroke={color}
              strokeWidth="3.4"
              strokeDasharray={`${pct}, 100`}
              strokeLinecap="round"
              style={{ transition: "stroke-dasharray 0.6s ease" }}
            />
          </svg>
          <div style={{
            position: "absolute",
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center"
          }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "20px", fontWeight: 700, color: "var(--color-ink)", lineHeight: 1 }}>
              {pct}%
            </span>
            <span style={{ fontSize: "8.5px", fontFamily: "var(--font-mono)", color: "var(--color-ink-muted)", marginTop: "2px" }}>
              BREACH PROB
            </span>
          </div>
        </div>

        <div style={{ flex: 1 }}>
          <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--color-ink)", marginBottom: "3px" }}>
            Crisis Threshold Risk (₹50.00 Cap)
          </div>
          <p style={{ fontSize: "13px", color: "var(--color-ink-secondary)", lineHeight: 1.45 }}>
            {risk.narrative}
          </p>
        </div>
      </div>

      {/* Primary Drivers Breakdown */}
      {risk.primary_drivers && risk.primary_drivers.length > 0 && (
        <div>
          <div className="eyebrow-tag" style={{ marginBottom: "8px" }}>
            PRIMARY CAUSAL DRIVERS:
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {risk.primary_drivers.map((d, i) => (
              <div key={i} style={{
                padding: "10px 14px",
                background: "rgba(255, 255, 255, 0.7)",
                border: "1px solid rgba(0, 0, 0, 0.05)",
                borderRadius: "var(--radius-md)"
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2px" }}>
                  <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-ink)" }}>
                    {d.driver}
                  </span>
                  <span className="badge-glass badge-cream" style={{ fontSize: "10px" }}>
                    {d.impact_pct}% WEIGHT
                  </span>
                </div>
                <div style={{ fontSize: "12px", color: "var(--color-ink-muted)" }}>
                  {d.detail}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
