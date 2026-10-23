import React, { useState } from "react";
import {
  Send, Sparkles, CheckCircle2, Loader2, ArrowRight,
  TrendingUp, CloudRain, Truck, Activity, ShieldAlert,
  Sliders, FileText, CheckCircle, Database, ChevronDown, ChevronUp, ExternalLink
} from "lucide-react";
import { streamInvestigation } from "../api/client";
import { AgentStreamEvent } from "../types";

interface WorkspaceViewProps {
  commodityId: string;
  geographyId: string;
  onNavigateTab: (tab: string) => void;
  onNavigateForecast: (horizonDays: number) => void;
}

export const WorkspaceView: React.FC<WorkspaceViewProps> = ({
  commodityId,
  geographyId,
  onNavigateTab,
  onNavigateForecast
}) => {
  const [query, setQuery] = useState(
    "Analyze the modal onion price surge across Kurnool mandis and formulate an emergency buffer liquidation strategy."
  );
  const [horizon, setHorizon] = useState<number>(14);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [events, setEvents] = useState<AgentStreamEvent[]>([]);
  const [finalSynthesis, setFinalSynthesis] = useState<any | null>(null);
  const [expandedAgents, setExpandedAgents] = useState<Record<string, boolean>>({});

  const quickPrompts = [
    { label: "14-Day Surge Analysis", text: "Analyze the modal onion price surge across Kurnool mandis and formulate an emergency buffer liquidation strategy.", h: 14 },
    { label: "60-Day Kharif Harvest Forecast", text: "Evaluate 60-day price trends considering late Kharif crop arrivals and Maharashtra inflow patterns.", h: 60 },
    { label: "90-Day Seasonal Clearing", text: "Project 90-day wholesale price trajectory, Rabi planting outlook, and buffer re-accumulation.", h: 90 },
  ];

  const handleStartInvestigation = (customQuery?: string, customHorizon?: number) => {
    const q = customQuery || query;
    const h = customHorizon || horizon;
    if (!q.trim() || isStreaming) return;

    setIsStreaming(true);
    setEvents([]);
    setFinalSynthesis(null);
    setExpandedAgents({});

    streamInvestigation(
      q,
      commodityId,
      geographyId,
      h,
      (event) => {
        setEvents((prev) => {
          const idx = prev.findIndex(
            (e) => e.agent === event.agent && e.stage === event.stage
          );
          if (idx >= 0) {
            const copy = [...prev];
            copy[idx] = event;
            return copy;
          }
          return [...prev, event];
        });

        if (event.status === "completed") {
          setExpandedAgents((prev) => ({ ...prev, [event.agent]: true }));
        }

        if (event.stage === "05_LEARN" && event.status === "completed") {
          setFinalSynthesis(event.payload);
        }
      },
      () => {
        setIsStreaming(false);
      },
      (err) => {
        console.error("Stream error", err);
        setIsStreaming(false);
      }
    );
  };

  const toggleExpand = (agentName: string) => {
    setExpandedAgents((prev) => ({
      ...prev,
      [agentName]: !prev[agentName]
    }));
  };

  const getAgentIcon = (agent: string) => {
    if (agent.includes("Market")) return TrendingUp;
    if (agent.includes("Weather")) return CloudRain;
    if (agent.includes("Supply")) return Truck;
    if (agent.includes("Forecast")) return Activity;
    if (agent.includes("Risk")) return ShieldAlert;
    if (agent.includes("Intervention")) return Sliders;
    if (agent.includes("Scenario")) return CheckCircle2;
    if (agent.includes("Workflow")) return FileText;
    return Sparkles;
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
      {/* Editorial Header (Google Sans + Times New Roman Italic) */}
      <section style={{ maxWidth: "880px" }}>
        <div className="eyebrow-tag" style={{ color: "var(--color-primary)", marginBottom: "8px" }}>
          Autonomous Stabilization Hub • Andhra Pradesh
        </div>
        <h1 className="display-title" style={{ marginBottom: "8px" }}>
          Market Intelligence & Decision Console
        </h1>
        <p style={{
          fontFamily: "var(--font-serif)",
          fontStyle: "italic",
          fontSize: "20px",
          color: "var(--color-ink-secondary)",
          lineHeight: 1.4
        }}>
          Multi-agent causal reasoning orchestrating AGMARKNET feeds, Doppler rainfall indices,
          AR-Lag tabular forecasting up to 90 days, and deterministic Price Stabilisation Fund releases.
        </p>
      </section>

      {/* Production Liquid Glass Query Card */}
      <div className="liquid-glass-elevated" style={{ padding: "20px 24px" }}>
        {/* Suggestion Chips */}
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "14px" }}>
          {quickPrompts.map((p, idx) => (
            <button
              key={idx}
              className="btn-liquid btn-glass"
              onClick={() => {
                setQuery(p.text);
                setHorizon(p.h);
                handleStartInvestigation(p.text, p.h);
              }}
              style={{
                padding: "6px 14px",
                fontSize: "12.5px",
                fontWeight: 500,
                color: "var(--color-ink)"
              }}
            >
              <Sparkles size={12} color="var(--color-primary)" />
              {p.label}
            </button>
          ))}
        </div>

        {/* Text Input & Controls */}
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            rows={2}
            placeholder="Enter market anomaly, arrival deficit, or intervention directive..."
            style={{
              width: "100%",
              fontFamily: "var(--font-sans)",
              fontSize: "15.5px",
              lineHeight: 1.5,
              color: "var(--color-ink)",
              border: "none",
              outline: "none",
              resize: "none",
              background: "transparent"
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleStartInvestigation();
              }
            }}
          />

          <div style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            paddingTop: "12px",
            borderTop: "1px solid rgba(0, 0, 0, 0.05)",
            flexWrap: "wrap",
            gap: "12px"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span className="eyebrow-tag" style={{ fontSize: "10.5px" }}>PROJECTION HORIZON:</span>
              {[7, 14, 30, 60, 90].map((h) => (
                <button
                  key={h}
                  onClick={() => setHorizon(h)}
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "12px",
                    fontWeight: 600,
                    padding: "4px 10px",
                    borderRadius: "var(--radius-pill)",
                    border: "1px solid",
                    borderColor: horizon === h ? "var(--color-primary)" : "rgba(0,0,0,0.08)",
                    backgroundColor: horizon === h ? "rgba(0, 102, 204, 0.1)" : "rgba(255,255,255,0.6)",
                    color: horizon === h ? "var(--color-primary)" : "var(--color-ink-muted)",
                    cursor: "pointer",
                    transition: "all 0.15s ease"
                  }}
                >
                  {h}D
                </button>
              ))}
            </div>

            <button
              className="btn-liquid btn-primary"
              disabled={isStreaming || !query.trim()}
              onClick={() => handleStartInvestigation()}
              style={{
                opacity: isStreaming || !query.trim() ? 0.6 : 1,
                cursor: isStreaming || !query.trim() ? "not-allowed" : "pointer"
              }}
            >
              {isStreaming ? (
                <>
                  <Loader2 size={15} className="animate-spin" />
                  Agents Orchestrating...
                </>
              ) : (
                <>
                  <Send size={14} />
                  Initiate Multi-Agent Analysis
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Real-time Streaming Agent Chain */}
      {events.length > 0 && (
        <section style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 className="section-title" style={{ fontSize: "20px", display: "flex", alignItems: "center", gap: "10px" }}>
              Agent Reasoning & Evidence Trace
              {isStreaming && (
                <span className="badge-glass badge-mint" style={{ fontSize: "10px" }}>
                  <Loader2 size={10} className="animate-spin" /> LIVE INGESTION
                </span>
              )}
            </h2>
            <div className="eyebrow-tag">
              {events.filter((e) => e.status === "completed").length} OF {events.length} AGENTS COMPLETED
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {events.map((evt, idx) => {
              const Icon = getAgentIcon(evt.agent);
              const isRunning = evt.status === "running";
              const isCompleted = evt.status === "completed";
              const isExpanded = !!expandedAgents[evt.agent];

              return (
                <div key={idx} className="liquid-glass" style={{ overflow: "hidden" }}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "14px 18px",
                      cursor: "pointer",
                      background: isExpanded ? "rgba(255, 255, 255, 0.4)" : "transparent"
                    }}
                    onClick={() => toggleExpand(evt.agent)}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                      <div style={{
                        width: "32px",
                        height: "32px",
                        borderRadius: "8px",
                        backgroundColor: isCompleted ? "rgba(30, 166, 74, 0.12)" : "rgba(0, 102, 204, 0.1)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: isCompleted ? "var(--status-normal)" : "var(--color-primary)"
                      }}>
                        <Icon size={16} />
                      </div>

                      <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <span style={{ fontWeight: 600, fontSize: "14.5px", color: "var(--color-ink)" }}>
                            {evt.agent}
                          </span>
                          <span className="eyebrow-tag" style={{ fontSize: "9.5px" }}>
                            {evt.stage}
                          </span>
                        </div>
                        {isRunning && (
                          <div style={{ fontSize: "12.5px", color: "var(--color-ink-muted)", marginTop: "2px" }}>
                            {evt.payload?.message || "Running telemetry checks..."}
                          </div>
                        )}
                      </div>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      {isRunning && <Loader2 size={15} className="animate-spin" color="var(--color-primary)" />}
                      {isCompleted && <CheckCircle size={16} color="var(--status-normal)" />}
                      {isExpanded ? <ChevronUp size={15} color="var(--color-ink-muted)" /> : <ChevronDown size={15} color="var(--color-ink-muted)" />}
                    </div>
                  </div>

                  {isExpanded && isCompleted && evt.payload && (
                    <div style={{ padding: "16px 18px", borderTop: "1px solid rgba(0, 0, 0, 0.05)" }}>
                      <p style={{ fontSize: "14.5px", color: "var(--color-ink)", lineHeight: 1.5, marginBottom: "12px" }}>
                        {evt.payload.finding || evt.payload.message}
                      </p>

                      {evt.payload.evidence && evt.payload.evidence.length > 0 && (
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                          {evt.payload.evidence.map((ev: any, eIdx: number) => (
                            <div
                              key={eIdx}
                              style={{
                                padding: "6px 10px",
                                background: "rgba(255, 255, 255, 0.7)",
                                border: "1px solid rgba(0,0,0,0.06)",
                                borderRadius: "var(--radius-sm)",
                                fontSize: "12px"
                              }}
                            >
                              <span style={{ color: "var(--color-ink-muted)", fontSize: "11px", marginRight: "4px" }}>
                                {ev.source}:
                              </span>
                              <strong style={{ color: "var(--color-ink)" }}>{ev.metric}</strong> = <span style={{ color: "var(--color-primary)", fontWeight: 600 }}>{ev.value}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Production Executive Synthesis Card */}
      {finalSynthesis && (
        <section className="liquid-glass-elevated" style={{ padding: "28px 32px", display: "flex", flexDirection: "column", gap: "20px" }}>
          <div>
            <div className="eyebrow-tag" style={{ color: "var(--color-terracotta)", marginBottom: "4px" }}>
              STATE STABILISATION DIRECTIVE • EXECUTIVE RATIFICATION READY
            </div>
            <h2 className="section-title" style={{ fontSize: "26px", marginBottom: "8px" }}>
              Targeted 10,000 MT PSF Buffer Stock Release
            </h2>
            <p style={{ fontSize: "15.5px", color: "var(--color-ink-secondary)", lineHeight: 1.55 }}>
              {finalSynthesis.summary}
            </p>
          </div>

          {/* Metric Quad */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "14px"
          }}>
            <div className="liquid-glass" style={{ padding: "16px" }}>
              <div className="eyebrow-tag">CURRENT SPOT MODAL</div>
              <div className="metric-number" style={{ fontSize: "24px", fontWeight: 700, color: "var(--color-ink)", marginTop: "4px" }}>
                ₹{finalSynthesis.market_analytics?.latest_modal_price?.toFixed(2) || "40.88"}/kg
              </div>
              <div style={{ fontSize: "12px", color: "var(--status-critical)", marginTop: "2px" }}>
                +18.5% Inflow Deficit Shock
              </div>
            </div>

            <div className="liquid-glass" style={{ padding: "16px" }}>
              <div className="eyebrow-tag">PEAK UNMITIGATED</div>
              <div className="metric-number" style={{ fontSize: "24px", fontWeight: 700, color: "var(--color-ink)", marginTop: "4px" }}>
                ₹{finalSynthesis.forecast_peak?.toFixed(2) || "48.50"}/kg
              </div>
              <div style={{ fontSize: "12px", color: "var(--color-ink-muted)", marginTop: "2px" }}>
                Uncertainty Cone ±₹3.80
              </div>
            </div>

            <div className="liquid-glass" style={{ padding: "16px" }}>
              <div className="eyebrow-tag">THRESHOLD BREACH RISK</div>
              <div className="metric-number" style={{ fontSize: "24px", fontWeight: 700, color: "var(--status-critical)", marginTop: "4px" }}>
                {(finalSynthesis.spike_probability * 100).toFixed(0)}%
              </div>
              <div style={{ fontSize: "12px", color: "var(--status-critical)", marginTop: "2px" }}>
                Probability of ₹50 Cap Breach
              </div>
            </div>

            <div className="liquid-glass" style={{ padding: "16px" }}>
              <div className="eyebrow-tag">PROJECTED MITIGATION</div>
              <div className="metric-number" style={{ fontSize: "24px", fontWeight: 700, color: "var(--status-normal)", marginTop: "4px" }}>
                -{finalSynthesis.recommended_scenario?.expected_price_mitigation_pct || 26.4}%
              </div>
              <div style={{ fontSize: "12px", color: "var(--status-normal)", marginTop: "2px" }}>
                Stabilizes wholesale @ ₹32.00/kg
              </div>
            </div>
          </div>

          {/* Fluid Interconnected Navigation Links */}
          <div style={{
            display: "flex",
            justifyContent: "flex-end",
            alignItems: "center",
            gap: "10px",
            flexWrap: "wrap",
            paddingTop: "16px",
            borderTop: "1px solid rgba(0,0,0,0.06)"
          }}>
            <button
              className="btn-liquid btn-glass"
              onClick={() => onNavigateForecast(horizon)}
            >
              Inspect {horizon}-Day & 60/90-Day Cones →
            </button>
            <button
              className="btn-liquid btn-glass"
              onClick={() => onNavigateTab("scenario")}
            >
              Adjust Buffer Volume & Subsidy →
            </button>
            <button
              className="btn-liquid btn-terracotta"
              onClick={() => onNavigateTab("briefs")}
            >
              Sign & Dispatch Decision Brief
              <ArrowRight size={14} />
            </button>
          </div>
        </section>
      )}
    </div>
  );
};
