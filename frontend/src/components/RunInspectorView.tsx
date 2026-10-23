import React, { useState, useEffect } from "react";
import { Clock, ShieldCheck, CheckCircle2, AlertCircle, RefreshCw } from "lucide-react";
import { AuditEvent } from "../types";
import { fetchAuditEvents } from "../api/client";

export const RunInspectorView: React.FC = () => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const loadEvents = async () => {
    setLoading(true);
    try {
      const data = await fetchAuditEvents();
      setEvents(data);
    } catch (e) {
      console.error("Failed to load audit events", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div className="eyebrow-tag" style={{ color: "var(--color-primary)", marginBottom: "6px" }}>
            DECISION PROVENANCE & IMMUTABLE TRACEABILITY
          </div>
          <h1 className="display-title" style={{ fontSize: "32px" }}>
            Run Inspector & Audit Trail
          </h1>
          <p style={{ fontFamily: "var(--font-serif)", fontStyle: "italic", fontSize: "17px", color: "var(--color-ink-muted)", marginTop: "4px" }}>
            Immutable append-only ledger tracking every agentic investigation, model run, scenario simulation, and ministerial ratification.
          </p>
        </div>

        <button className="btn-liquid btn-glass" onClick={loadEvents} disabled={loading} style={{ fontSize: "13px", padding: "8px 16px" }}>
          <RefreshCw size={13} className={loading ? "spin-animate" : ""} />
          Refresh Audit Ledger
        </button>
      </div>

      {/* Production Governance Notice */}
      <div className="liquid-glass" style={{
        display: "flex",
        alignItems: "flex-start",
        gap: "14px",
        padding: "18px 24px",
        background: "linear-gradient(135deg, rgba(200, 230, 205, 0.35) 0%, rgba(255, 255, 255, 0.8) 100%)",
        border: "1px solid rgba(200, 230, 205, 0.6)"
      }}>
        <ShieldCheck size={22} color="var(--glass-mint-ink)" style={{ flexShrink: 0, marginTop: "2px" }} />
        <div style={{ fontSize: "14px", lineHeight: 1.5, color: "var(--glass-mint-ink)" }}>
          <strong>Production Statutory Governance Guardrail: </strong>
          All autonomous agents operate in predictive analytics and scenario modeling capacity. Consequential real-world interventions
          (physical buffer liquidation, procurement tenders, and administrative price caps) require digital ratification by the Principal Secretary or Departmental Director.
        </div>
      </div>

      {/* Audit Events Table */}
      <div className="liquid-glass" style={{ padding: "24px" }}>
        <h3 style={{ fontFamily: "var(--font-serif)", fontSize: "20px", fontWeight: 400, color: "var(--color-ink)", marginBottom: "16px" }}>
          Immutable Decision Events ({events.length})
        </h3>

        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px", textAlign: "left" }}>
            <thead>
              <tr style={{ background: "rgba(0, 0, 0, 0.03)", borderBottom: "1px solid rgba(0, 0, 0, 0.08)" }}>
                <th style={{ padding: "10px 14px" }}>Timestamp (UTC)</th>
                <th style={{ padding: "10px 14px" }}>Action</th>
                <th style={{ padding: "10px 14px" }}>Actor / Role</th>
                <th style={{ padding: "10px 14px" }}>Target</th>
                <th style={{ padding: "10px 14px" }}>Outcome</th>
                <th style={{ padding: "10px 14px" }}>Correlation ID</th>
              </tr>
            </thead>
            <tbody>
              {events.map((e) => (
                <tr key={e.id} style={{ borderBottom: "1px solid rgba(0, 0, 0, 0.05)" }}>
                  <td style={{ padding: "10px 14px", fontFamily: "var(--font-mono)", color: "var(--color-ink-muted)" }}>
                    {e.timestamp.replace("T", " ").slice(0, 19)}
                  </td>
                  <td style={{ padding: "10px 14px", fontWeight: 600 }}>
                    <span className="eyebrow-tag" style={{ color: "var(--color-primary)" }}>
                      {e.action}
                    </span>
                  </td>
                  <td style={{ padding: "10px 14px" }}>
                    {e.actor_role} ({e.actor_id})
                  </td>
                  <td style={{ padding: "10px 14px", fontFamily: "var(--font-mono)" }}>
                    {e.target_type}: {e.target_id}
                  </td>
                  <td style={{ padding: "10px 14px" }}>
                    <span className="badge-glass badge-mint" style={{ fontSize: "10px" }}>
                      {e.outcome}
                    </span>
                  </td>
                  <td style={{ padding: "10px 14px", fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--color-ink-muted)" }}>
                    {e.correlation_id || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
