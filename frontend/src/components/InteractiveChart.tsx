import React, { useState } from "react";
import { Table, Eye, EyeOff } from "lucide-react";

interface DataPoint {
  date: string;
  modal_price?: number;
  arrivals_mt?: number;
  ma_7?: number;
  ma_14?: number;
  predicted_modal?: number;
  lower_80?: number;
  upper_80?: number;
  lower_95?: number;
  upper_95?: number;
  simulated_price?: number;
}

interface InteractiveChartProps {
  title: string;
  subtitle?: string;
  data: DataPoint[];
  alertThreshold?: number;
  crisisThreshold?: number;
  showArrivals?: boolean;
  showConfidenceInterval?: boolean;
  height?: number;
}

export const InteractiveChart: React.FC<InteractiveChartProps> = ({
  title,
  subtitle,
  data,
  alertThreshold = 35.0,
  crisisThreshold = 50.0,
  showArrivals = true,
  showConfidenceInterval = true,
  height = 360
}) => {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const [showTable, setShowTable] = useState<boolean>(false);

  if (!data || data.length === 0) {
    return (
      <div className="card-clean" style={{ padding: "40px", textAlign: "center", color: "var(--color-ink-muted)" }}>
        No chart telemetry records available for the selected parameters.
      </div>
    );
  }

  // Dimensions
  const paddingLeft = 55;
  const paddingRight = 45;
  const paddingTop = 25;
  const paddingBottom = 40;
  const width = 850;

  // Scales
  const allPrices: number[] = [];
  data.forEach(d => {
    if (d.modal_price) allPrices.push(d.modal_price);
    if (d.predicted_modal) allPrices.push(d.predicted_modal);
    if (d.upper_95) allPrices.push(d.upper_95);
    if (d.lower_95) allPrices.push(d.lower_95);
    if (d.simulated_price) allPrices.push(d.simulated_price);
  });
  allPrices.push(alertThreshold, crisisThreshold);

  const minPrice = Math.max(0, Math.floor(Math.min(...allPrices) * 0.85));
  const maxPrice = Math.ceil(Math.max(...allPrices) * 1.12);
  const maxArrivals = Math.max(...data.map(d => d.arrivals_mt || 0), 400);

  const chartW = width - paddingLeft - paddingRight;
  const chartH = height - paddingTop - paddingBottom;

  const getX = (idx: number) => paddingLeft + (idx / Math.max(1, data.length - 1)) * chartW;
  const getY = (val: number) => paddingTop + chartH - ((val - minPrice) / (maxPrice - minPrice)) * chartH;
  const getArrivalH = (val: number) => (val / maxArrivals) * (chartH * 0.35);

  // Generate paths
  const obsPoints = data.map((d, i) => d.modal_price !== undefined ? `${getX(i)},${getY(d.modal_price)}` : null).filter(Boolean);
  const obsPath = obsPoints.length > 1 ? `M ${obsPoints.join(" L ")}` : "";

  const fcPoints = data.map((d, i) => d.predicted_modal !== undefined ? `${getX(i)},${getY(d.predicted_modal)}` : null).filter(Boolean);
  const fcPath = fcPoints.length > 1 ? `M ${fcPoints.join(" L ")}` : "";

  const simPoints = data.map((d, i) => d.simulated_price !== undefined ? `${getX(i)},${getY(d.simulated_price)}` : null).filter(Boolean);
  const simPath = simPoints.length > 1 ? `M ${simPoints.join(" L ")}` : "";

  // 95% Confidence Interval Area
  const ciIndices = data.map((d, i) => d.upper_95 !== undefined && d.lower_95 !== undefined ? i : null).filter(x => x !== null) as number[];
  let ciPath = "";
  if (ciIndices.length > 1 && showConfidenceInterval) {
    const topPoints = ciIndices.map(i => `${getX(i)},${getY(data[i].upper_95!)}`);
    const bottomPoints = [...ciIndices].reverse().map(i => `${getX(i)},${getY(data[i].lower_95!)}`);
    ciPath = `M ${topPoints.join(" L ")} L ${bottomPoints.join(" L ")} Z`;
  }

  const activePoint = hoveredIdx !== null ? data[hoveredIdx] : data[data.length - 1];

  return (
    <div className="liquid-glass" style={{ position: "relative", overflow: "hidden", padding: "24px" }}>
      {/* Header bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
        <div>
          <h3 style={{ fontFamily: "var(--font-serif)", fontSize: "21px", fontWeight: 400, letterSpacing: "-0.01em", color: "var(--color-ink)" }}>{title}</h3>
          {subtitle && <p style={{ fontFamily: "var(--font-sans)", fontSize: "13.5px", color: "var(--color-ink-muted)", marginTop: "3px" }}>{subtitle}</p>}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <button
            className="btn-liquid btn-glass"
            style={{ fontSize: "12px", padding: "6px 14px" }}
            onClick={() => setShowTable(!showTable)}
          >
            <Table size={13} />
            {showTable ? "Chart Visualizer" : "Raw Telemetry"}
          </button>
        </div>
      </div>

      {showTable ? (
        <div style={{ maxHeight: "340px", overflowY: "auto", border: "1px solid var(--color-hairline)", borderRadius: "var(--radius-md)" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px", textAlign: "left" }}>
            <thead>
              <tr style={{ background: "var(--color-surface-soft)", borderBottom: "1px solid var(--color-hairline)" }}>
                <th style={{ padding: "10px 14px" }}>Date</th>
                <th style={{ padding: "10px 14px" }}>Modal Price (₹/kg)</th>
                <th style={{ padding: "10px 14px" }}>Predicted Modal</th>
                <th style={{ padding: "10px 14px" }}>95% Confidence Interval</th>
                <th style={{ padding: "10px 14px" }}>Arrivals (MT)</th>
              </tr>
            </thead>
            <tbody>
              {data.map((d, i) => (
                <tr key={i} style={{ borderBottom: "1px solid var(--color-hairline-soft)" }}>
                  <td style={{ padding: "8px 14px", fontFamily: "var(--font-mono)" }}>{d.date}</td>
                  <td style={{ padding: "8px 14px", fontWeight: 600 }}>{d.modal_price ? `₹${d.modal_price.toFixed(2)}` : "—"}</td>
                  <td style={{ padding: "8px 14px", color: "var(--color-terracotta)", fontWeight: 600 }}>
                    {d.predicted_modal ? `₹${d.predicted_modal.toFixed(2)}` : "—"}
                  </td>
                  <td style={{ padding: "8px 14px", color: "var(--color-ink-muted)", fontFamily: "var(--font-mono)" }}>
                    {d.lower_95 && d.upper_95 ? `₹${d.lower_95.toFixed(1)} – ₹${d.upper_95.toFixed(1)}` : "—"}
                  </td>
                  <td style={{ padding: "8px 14px" }}>{d.arrivals_mt ? `${d.arrivals_mt.toFixed(0)} MT` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div style={{ position: "relative", width: "100%", overflowX: "auto" }}>
          <svg
            viewBox={`0 0 ${width} ${height}`}
            style={{ width: "100%", height: "auto", display: "block" }}
            onMouseLeave={() => setHoveredIdx(null)}
          >
            <defs>
              <linearGradient id="ciGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#cc785c" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#cc785c" stopOpacity="0.04" />
              </linearGradient>
            </defs>

            {/* Horizontal Grid lines */}
            {[0, 0.25, 0.5, 0.75, 1.0].map((t, idx) => {
              const val = minPrice + t * (maxPrice - minPrice);
              const y = getY(val);
              return (
                <g key={idx}>
                  <line x1={paddingLeft} y1={y} x2={width - paddingRight} y2={y} stroke="var(--color-hairline-soft)" strokeDasharray="3 3" />
                  <text x={paddingLeft - 8} y={y + 4} textAnchor="end" fontSize="10.5" fill="var(--color-ink-muted)" fontFamily="var(--font-mono)">
                    ₹{val.toFixed(0)}
                  </text>
                </g>
              );
            })}

            {/* Arrivals Volume Bars on Bottom Secondary Scale */}
            {showArrivals && data.map((d, i) => {
              if (!d.arrivals_mt) return null;
              const barH = getArrivalH(d.arrivals_mt);
              const x = getX(i) - 2;
              const y = paddingTop + chartH - barH;
              return (
                <rect
                  key={`bar-${i}`}
                  x={x}
                  y={y}
                  width="4"
                  height={barH}
                  fill="#c8e6cd"
                  opacity={hoveredIdx === i ? 0.95 : 0.5}
                  rx="1"
                />
              );
            })}

            {/* Alert Threshold line (₹35) */}
            {alertThreshold >= minPrice && alertThreshold <= maxPrice && (
              <g>
                <line
                  x1={paddingLeft}
                  y1={getY(alertThreshold)}
                  x2={width - paddingRight}
                  y2={getY(alertThreshold)}
                  stroke="var(--status-watch)"
                  strokeWidth="1.2"
                  strokeDasharray="4 4"
                />
                <text x={width - paddingRight + 4} y={getY(alertThreshold) + 3} fontSize="9" fill="var(--status-watch)" fontWeight="600" fontFamily="var(--font-mono)">
                  ALERT ₹{alertThreshold}
                </text>
              </g>
            )}

            {/* Crisis Threshold line (₹50) */}
            {crisisThreshold >= minPrice && crisisThreshold <= maxPrice && (
              <g>
                <line
                  x1={paddingLeft}
                  y1={getY(crisisThreshold)}
                  x2={width - paddingRight}
                  y2={getY(crisisThreshold)}
                  stroke="var(--status-critical)"
                  strokeWidth="1.5"
                  strokeDasharray="4 4"
                />
                <text x={width - paddingRight + 4} y={getY(crisisThreshold) + 3} fontSize="9" fill="var(--status-critical)" fontWeight="600" fontFamily="var(--font-mono)">
                  CRISIS ₹{crisisThreshold}
                </text>
              </g>
            )}

            {/* Confidence Interval Ribbon */}
            {ciPath && (
              <path d={ciPath} fill="url(#ciGradient)" />
            )}

            {/* Historical Observed Line */}
            {obsPath && (
              <path
                d={obsPath}
                fill="none"
                stroke="var(--color-primary)"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            )}

            {/* Forecast Line */}
            {fcPath && (
              <path
                d={fcPath}
                fill="none"
                stroke="var(--color-terracotta)"
                strokeWidth="2.5"
                strokeDasharray="5 3"
                strokeLinecap="round"
              />
            )}

            {/* Simulated Mitigation Line */}
            {simPath && (
              <path
                d={simPath}
                fill="none"
                stroke="var(--status-normal)"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            )}

            {/* Hover Vertical Guide Line & Tooltip Anchor */}
            {hoveredIdx !== null && (
              <g>
                <line
                  x1={getX(hoveredIdx)}
                  y1={paddingTop}
                  x2={getX(hoveredIdx)}
                  y2={paddingTop + chartH}
                  stroke="var(--color-ink)"
                  strokeWidth="1"
                  strokeDasharray="2 2"
                />
                <circle
                  cx={getX(hoveredIdx)}
                  cy={getY(activePoint.modal_price || activePoint.predicted_modal || 0)}
                  r="5"
                  fill="#ffffff"
                  stroke="var(--color-primary)"
                  strokeWidth="2.5"
                />
              </g>
            )}

            {/* Invisible mouse hit boxes */}
            {data.map((_, i) => (
              <rect
                key={`hit-${i}`}
                x={getX(i) - (chartW / data.length) / 2}
                y={paddingTop}
                width={chartW / data.length}
                height={chartH}
                fill="transparent"
                style={{ cursor: "crosshair" }}
                onMouseEnter={() => setHoveredIdx(i)}
              />
            ))}

            {/* Date X-Axis Labels */}
            {data.filter((_, idx) => {
              const step = data.length > 50 ? Math.ceil(data.length / 8) : (data.length > 25 ? Math.ceil(data.length / 6) : Math.ceil(data.length / 5));
              return idx % step === 0 || idx === data.length - 1;
            }).map((d, i) => (
              <text
                key={`lbl-${i}`}
                x={getX(data.indexOf(d))}
                y={paddingTop + chartH + 20}
                textAnchor="middle"
                fontSize="10"
                fill="var(--color-ink-muted)"
                fontFamily="var(--font-mono)"
                fontWeight="500"
              >
                {d.date.slice(5)}
              </text>
            ))}
          </svg>

          {/* Interactive Legend & Active Hover Tooltip Card */}
          <div style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginTop: "14px",
            padding: "12px 18px",
            background: "rgba(255, 255, 255, 0.72)",
            backdropFilter: "blur(20px) saturate(180%)",
            WebkitBackdropFilter: "blur(20px) saturate(180%)",
            border: "1px solid rgba(255, 255, 255, 0.8)",
            borderRadius: "var(--radius-pill)",
            boxShadow: "var(--shadow-liquid-subtle)",
            fontSize: "12.5px"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "16px", flexWrap: "wrap", fontFamily: "var(--font-sans)" }}>
              <span style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
                <span style={{ width: "12px", height: "3px", backgroundColor: "var(--color-primary)", borderRadius: "2px" }} />
                Observed Modal Price
              </span>
              <span style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
                <span style={{ width: "12px", height: "3px", backgroundColor: "var(--color-terracotta)", borderRadius: "2px" }} />
                Predictive Horizon (AR-Lag)
              </span>
              {simPath && (
                <span style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
                  <span style={{ width: "12px", height: "3px", backgroundColor: "var(--status-normal)", borderRadius: "2px" }} />
                  Simulated Buffer Mitigation
                </span>
              )}
              {showArrivals && (
                <span style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
                  <span style={{ width: "8px", height: "8px", backgroundColor: "#c8e6cd", borderRadius: "1px" }} />
                  Daily Arrivals (MT)
                </span>
              )}
            </div>

            {activePoint && (
              <div style={{ fontFamily: "var(--font-mono)", fontWeight: 600, color: "var(--color-ink)", fontSize: "13px" }}>
                {activePoint.date}: {" "}
                {activePoint.modal_price ? (
                  <span style={{ color: "var(--color-primary)" }}>₹{activePoint.modal_price.toFixed(2)}/kg</span>
                ) : (
                  <span style={{ color: "var(--color-terracotta)" }}>
                    ₹{activePoint.predicted_modal?.toFixed(2)}/kg
                    {activePoint.upper_95 && ` (95% CI: ₹${activePoint.lower_95?.toFixed(1)}–₹${activePoint.upper_95?.toFixed(1)})`}
                  </span>
                )}
                {activePoint.arrivals_mt && ` • ${activePoint.arrivals_mt.toFixed(0)} MT`}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
