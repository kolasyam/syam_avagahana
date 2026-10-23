import React, { useState, useEffect } from "react";
import { TrendingUp, AlertTriangle, ArrowUpRight, ArrowDownRight, RefreshCw, Calendar, MapPin, Activity, ArrowRight } from "lucide-react";
import { Geography, Commodity, MarketAnalytics, MarketObservation } from "../types";
import { fetchObservations, fetchAnalytics } from "../api/client";
import { InteractiveChart } from "./InteractiveChart";

interface MarketIntelligenceViewProps {
  geographies: Geography[];
  commodities: Commodity[];
  selectedCommodity: string;
  setSelectedCommodity: (c: string) => void;
  selectedGeography: string;
  setSelectedGeography: (g: string) => void;
  onNavigateForecast?: (horizonDays?: number) => void;
}

export const MarketIntelligenceView: React.FC<MarketIntelligenceViewProps> = ({
  geographies,
  commodities,
  selectedCommodity,
  setSelectedCommodity,
  selectedGeography,
  setSelectedGeography,
  onNavigateForecast
}) => {
  const [days, setDays] = useState<number>(60);
  const [analytics, setAnalytics] = useState<MarketAnalytics | null>(null);
  const [observations, setObservations] = useState<MarketObservation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [obs, anal] = await Promise.all([
        fetchObservations(selectedCommodity, selectedGeography, days),
        fetchAnalytics(selectedCommodity, selectedGeography, days)
      ]);
      setObservations(obs);
      setAnalytics(anal);
    } catch (e) {
      console.error("Failed to load market intelligence", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedCommodity, selectedGeography, days]);

  const currGeo = geographies.find(g => g.id === selectedGeography);
  const currComm = commodities.find(c => c.id === selectedCommodity);
  const summary = analytics?.summary;

  const chartData = (analytics?.series || []).map(s => ({
    date: s.date,
    modal_price: s.modal_price,
    arrivals_mt: s.arrivals_mt,
    ma_7: s.ma_7,
    ma_14: s.ma_14
  }));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Editorial Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div className="eyebrow-tag" style={{ color: "var(--color-primary)", marginBottom: "6px" }}>
            MANDI SURVEILLANCE & SPOT TELEMETRY
          </div>
          <h1 className="display-title" style={{ fontSize: "32px" }}>
            Market Intelligence
          </h1>
          <p style={{ fontFamily: "var(--font-serif)", fontStyle: "italic", fontSize: "17px", color: "var(--color-ink-muted)", marginTop: "4px" }}>
            High-frequency daily arrivals, modal price trajectories, and automated Z-score anomaly surveillance.
          </p>
        </div>

        {/* Filter Controls & Interconnected Action */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
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
            {/* Commodity Dropdown */}
            <select
              value={selectedCommodity}
              onChange={(e) => setSelectedCommodity(e.target.value)}
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "13px",
                fontWeight: 600,
                color: "var(--color-ink)",
                border: "none",
                background: "transparent",
                outline: "none",
                cursor: "pointer"
              }}
            >
              {commodities.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>

            <span style={{ color: "rgba(0, 0, 0, 0.12)" }}>|</span>

            {/* Mandi Dropdown */}
            <select
              value={selectedGeography}
              onChange={(e) => setSelectedGeography(e.target.value)}
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "13px",
                fontWeight: 600,
                color: "var(--color-ink)",
                border: "none",
                background: "transparent",
                outline: "none",
                cursor: "pointer"
              }}
            >
              {geographies.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name} ({g.district})
                </option>
              ))}
            </select>

            <span style={{ color: "rgba(0, 0, 0, 0.12)" }}>|</span>

            {/* Days buttons */}
            {[30, 60, 90, 180].map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className="btn-liquid"
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "11px",
                  fontWeight: 600,
                  padding: "3px 8px",
                  backgroundColor: days === d ? "var(--color-primary)" : "transparent",
                  color: days === d ? "#ffffff" : "var(--color-ink-muted)",
                  border: "none",
                  boxShadow: days === d ? "0 2px 6px rgba(0, 102, 204, 0.25)" : "none"
                }}
              >
                {d}D
              </button>
            ))}
          </div>

          {onNavigateForecast && (
            <button
              className="btn-liquid btn-primary"
              onClick={() => onNavigateForecast(14)}
              style={{ fontSize: "13px", padding: "8px 16px" }}
            >
              <span>Forecast Trajectory</span>
              <ArrowRight size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Hero Metric Cards (Apple-style 4-tile grid with iOS 26 Liquid Glass) */}
      {summary && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: "16px"
        }}>
          <div className="liquid-glass" style={{ padding: "20px 22px" }}>
            <div className="eyebrow-tag">CURRENT SPOT MODAL</div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "28px", fontWeight: 700, color: "var(--color-ink)", marginTop: "6px" }}>
              ₹{summary.latest_modal_price?.toFixed(2)}/kg
            </div>
            <div style={{
              display: "flex",
              alignItems: "center",
              gap: "4px",
              fontFamily: "var(--font-mono)",
              fontSize: "13px",
              fontWeight: 600,
              color: summary.wow_price_change_pct > 0 ? "var(--status-critical)" : "var(--status-normal)",
              marginTop: "4px"
            }}>
              {summary.wow_price_change_pct > 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
              {summary.wow_price_change_pct > 0 ? `+${summary.wow_price_change_pct.toFixed(1)}%` : `${summary.wow_price_change_pct.toFixed(1)}%`} WoW
              <span style={{ fontFamily: "var(--font-sans)", fontWeight: 400, color: "var(--color-ink-muted)", marginLeft: "4px" }}>
                Range: ₹{summary.latest_min_price?.toFixed(1)}–₹{summary.latest_max_price?.toFixed(1)}
              </span>
            </div>
          </div>

          <div className="liquid-glass" style={{ padding: "20px 22px" }}>
            <div className="eyebrow-tag">DAILY MANDI ARRIVALS</div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "28px", fontWeight: 700, color: "var(--color-ink)", marginTop: "6px" }}>
              {summary.latest_arrivals_mt?.toFixed(0)} MT
            </div>
            <div style={{
              display: "flex",
              alignItems: "center",
              gap: "4px",
              fontFamily: "var(--font-mono)",
              fontSize: "13px",
              fontWeight: 600,
              color: summary.wow_arrivals_change_pct < 0 ? "var(--status-critical)" : "var(--status-normal)",
              marginTop: "4px"
            }}>
              {summary.wow_arrivals_change_pct < 0 ? <ArrowDownRight size={14} /> : <ArrowUpRight size={14} />}
              {summary.wow_arrivals_change_pct.toFixed(1)}% WoW Deficit
              <span style={{ fontFamily: "var(--font-sans)", fontWeight: 400, color: "var(--color-ink-muted)", marginLeft: "4px" }}>
                5-Yr Normal: 380 MT
              </span>
            </div>
          </div>

          <div className="liquid-glass" style={{ padding: "20px 22px" }}>
            <div className="eyebrow-tag">30-DAY VOLATILITY (STD DEV)</div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "28px", fontWeight: 700, color: "var(--color-ink)", marginTop: "6px" }}>
              {summary.current_volatility?.toFixed(2)}
            </div>
            <div style={{ fontSize: "13px", color: "var(--color-ink-muted)", marginTop: "4px" }}>
              Elevated market dispersion index
            </div>
          </div>

          <div className="liquid-glass" style={{ padding: "20px 22px" }}>
            <div className="eyebrow-tag">PERIOD BOUNDS ({days} DAYS)</div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "28px", fontWeight: 700, color: "var(--color-ink)", marginTop: "6px" }}>
              ₹{summary.period_min?.toFixed(1)} – ₹{summary.period_max?.toFixed(1)}
            </div>
            <div style={{ fontSize: "13px", color: "var(--color-ink-muted)", marginTop: "4px" }}>
              Mean: <span style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>₹{summary.period_mean?.toFixed(2)}/kg</span>
            </div>
          </div>
        </div>
      )}

      {/* Main Interactive Chart */}
      <InteractiveChart
        title={`${currComm?.name || "Onion"} Spot Prices & Inflow Volume`}
        subtitle={`${currGeo?.name || "Kurnool Agricultural Market Yard"} • Observed Daily Feeds vs 7-Day & 14-Day Rolling Means`}
        data={chartData}
        alertThreshold={currComm?.alert_threshold || 35.0}
        crisisThreshold={currComm?.crisis_threshold || 50.0}
        showArrivals={true}
        showConfidenceInterval={false}
        height={380}
      />

      {/* Anomaly Detection Grid & Recent Ingestion Log */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))", gap: "20px" }}>
        {/* Active Anomalies Panel */}
        <div className="liquid-glass" style={{ padding: "24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <h3 style={{ fontFamily: "var(--font-serif)", fontSize: "20px", fontWeight: 400, color: "var(--color-ink)" }}>
              Statistical Anomalies Detected
            </h3>
            <span className="badge-glass badge-coral">
              {analytics?.anomalies?.length || 0} ACTIVE
            </span>
          </div>

          {analytics?.anomalies && analytics.anomalies.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {analytics.anomalies.map((anom, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: "12px 16px",
                    backgroundColor: "rgba(255, 255, 255, 0.65)",
                    borderRadius: "var(--radius-md)",
                    borderLeft: "4px solid var(--status-critical)",
                    border: "1px solid rgba(0, 0, 0, 0.05)"
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "12px", fontWeight: 600 }}>
                      {anom.date}
                    </span>
                    <span className="badge-glass badge-coral" style={{ fontSize: "10px" }}>
                      Z-SCORE: {anom.z_score.toFixed(2)}
                    </span>
                  </div>
                  <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--color-ink)" }}>
                    Modal ₹{anom.price.toFixed(2)}/kg ({anom.dod_change_pct > 0 ? `+${anom.dod_change_pct.toFixed(1)}%` : `${anom.dod_change_pct.toFixed(1)}%`} DoD)
                  </div>
                  <div style={{ fontSize: "12.5px", color: "var(--color-ink-muted)", marginTop: "2px" }}>
                    {anom.reason}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ padding: "24px", textAlign: "center", color: "var(--color-ink-muted)", fontSize: "14px" }}>
              No statistical price anomalies exceeding threshold in this period.
            </div>
          )}
        </div>

        {/* Recent Ingestion Log Table */}
        <div className="liquid-glass" style={{ padding: "24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <h3 style={{ fontFamily: "var(--font-serif)", fontSize: "20px", fontWeight: 400, color: "var(--color-ink)" }}>
              Recent Ingested Daily Feeds
            </h3>
            <span className="badge-glass badge-mint">
              AGMARKNET VERIFIED
            </span>
          </div>

          <div style={{ maxHeight: "310px", overflowY: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px", textAlign: "left" }}>
              <thead>
                <tr style={{ background: "rgba(0, 0, 0, 0.03)", borderBottom: "1px solid rgba(0, 0, 0, 0.08)" }}>
                  <th style={{ padding: "8px 12px" }}>Date</th>
                  <th style={{ padding: "8px 12px" }}>Modal</th>
                  <th style={{ padding: "8px 12px" }}>Min / Max</th>
                  <th style={{ padding: "8px 12px" }}>Arrivals</th>
                  <th style={{ padding: "8px 12px" }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {observations.slice(-8).reverse().map((o, idx) => (
                  <tr key={idx} style={{ borderBottom: "1px solid rgba(0, 0, 0, 0.05)" }}>
                    <td style={{ padding: "8px 12px", fontFamily: "var(--font-mono)" }}>{o.date}</td>
                    <td style={{ padding: "8px 12px", fontWeight: 600, color: "var(--color-ink)", fontFamily: "var(--font-mono)" }}>₹{o.modal_price.toFixed(2)}</td>
                    <td style={{ padding: "8px 12px", color: "var(--color-ink-muted)", fontFamily: "var(--font-mono)" }}>₹{o.min_price.toFixed(1)} – ₹{o.max_price.toFixed(1)}</td>
                    <td style={{ padding: "8px 12px", fontFamily: "var(--font-mono)" }}>{o.arrivals_mt.toFixed(0)} MT</td>
                    <td style={{ padding: "8px 12px" }}>
                      <span className="badge-glass badge-mint" style={{ fontSize: "9px" }}>
                        {o.quality_flags}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
