import React, { useState, useEffect } from "react";
import { Database, CheckCircle2, Clock, AlertTriangle, ShieldCheck, RefreshCw } from "lucide-react";
import { ConnectorHealth } from "../types";
import { fetchSources } from "../api/client";

export const DataFabricView: React.FC = () => {
  const [sources, setSources] = useState<ConnectorHealth[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const loadSources = async () => {
    setLoading(true);
    try {
      const data = await fetchSources();
      setSources(data);
    } catch (e) {
      console.error("Failed to load sources", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSources();
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div className="eyebrow-tag" style={{ color: "var(--color-primary)", marginBottom: "6px" }}>
            FEDERATED DATA FABRIC & CONNECTOR REGISTRY
          </div>
          <h1 className="display-title" style={{ fontSize: "32px" }}>
            Authoritative Data Lineage
          </h1>
          <p style={{ fontFamily: "var(--font-serif)", fontStyle: "italic", fontSize: "17px", color: "var(--color-ink-muted)", marginTop: "4px" }}>
            Data connectors integrating APMC mandis, central buffer stock ledgers, IMD weather radar, and freight transit waybills.
          </p>
        </div>

        <button className="btn-liquid btn-glass" onClick={loadSources} disabled={loading} style={{ fontSize: "13px", padding: "8px 16px" }}>
          <RefreshCw size={13} className={loading ? "spin-animate" : ""} />
          Ping Source Adapters
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "20px" }}>
        {sources.map((src) => (
          <div key={src.connector_id} className="liquid-glass" style={{ padding: "22px", display: "flex", flexDirection: "column", gap: "14px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <span className="eyebrow-tag" style={{ fontSize: "10px" }}>{src.family}</span>
                <h4 style={{ fontFamily: "var(--font-serif)", fontSize: "18px", fontWeight: 400, color: "var(--color-ink)", marginTop: "2px" }}>
                  {src.name}
                </h4>
              </div>
              <span className="badge-glass badge-mint" style={{ fontSize: "10px" }}>
                {src.status}
              </span>
            </div>

            <div style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "10px",
              background: "rgba(255, 255, 255, 0.65)",
              border: "1px solid rgba(0, 0, 0, 0.05)",
              padding: "14px",
              borderRadius: "var(--radius-md)",
              fontSize: "13px"
            }}>
              <div>
                <span style={{ color: "var(--color-ink-muted)", fontSize: "11px", display: "block" }}>Freshness</span>
                <span style={{ fontWeight: 600, fontFamily: "var(--font-mono)" }}>{src.freshness_hours}h ago</span>
              </div>
              <div>
                <span style={{ color: "var(--color-ink-muted)", fontSize: "11px", display: "block" }}>Quality Score</span>
                <span style={{ fontWeight: 600, fontFamily: "var(--font-mono)", color: "var(--status-normal)" }}>
                  {(src.quality_score * 100).toFixed(0)}%
                </span>
              </div>
              <div>
                <span style={{ color: "var(--color-ink-muted)", fontSize: "11px", display: "block" }}>Live Ingested</span>
                <span style={{ fontWeight: 600, fontFamily: "var(--font-mono)" }}>{src.records_count.toLocaleString()}</span>
              </div>
              <div>
                <span style={{ color: "var(--color-ink-muted)", fontSize: "11px", display: "block" }}>Pipeline Sync</span>
                <span style={{ fontWeight: 600, color: "var(--status-normal)" }}>Synchronized</span>
              </div>
            </div>

            <div style={{ fontSize: "12px", color: "var(--color-ink-muted)" }}>
              Gateway: <strong style={{ color: "var(--color-ink)" }}>{src.mode_label}</strong>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
