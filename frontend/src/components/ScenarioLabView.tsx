import React, { useState, useEffect } from "react";
import { Sliders, AlertTriangle, CheckCircle2, TrendingDown, DollarSign, Truck, Train, FileText, ArrowRight } from "lucide-react";
import { ScenarioRun } from "../types";
import { simulateScenario } from "../api/client";
import { InteractiveChart } from "./InteractiveChart";

interface ScenarioLabViewProps {
  commodityId: string;
  geographyId: string;
  onNavigateTab: (tab: string) => void;
}

export const ScenarioLabView: React.FC<ScenarioLabViewProps> = ({
  commodityId,
  geographyId,
  onNavigateTab
}) => {
  // Input parameters
  const [releaseQuantity, setReleaseQuantity] = useState<number>(10000);
  const [timingDays, setTimingDays] = useState<number>(3);
  const [subsidyCost, setSubsidyCost] = useState<number>(8.50);
  const [logisticsMode, setLogisticsMode] = useState<string>("TRUCK_CONVOY");
  const [targetDistricts, setTargetDistricts] = useState<string[]>([
    "Kurnool", "Kadapa", "Vijayawada", "Tirupati"
  ]);

  const [activeScenario, setActiveScenario] = useState<ScenarioRun | null>(null);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSimulate = async () => {
    setIsSimulating(true);
    setErrorMsg(null);
    try {
      const res = await simulateScenario({
        name: `Targeted ${releaseQuantity.toLocaleString()} MT Buffer Liquidation (${logisticsMode === "TRUCK_CONVOY" ? "Truck" : "Rail"})`,
        commodity_id: commodityId,
        geography_id: geographyId,
        release_quantity_mt: releaseQuantity,
        target_districts: targetDistricts,
        timing_days: timingDays,
        logistics_mode: logisticsMode,
        cost_per_kg_subsidy: subsidyCost
      });

      if (res.is_constraint_violated) {
        setErrorMsg(res.violation_reason || "Capacity constraint violated.");
      }
      setActiveScenario(res);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to simulate scenario.");
    } finally {
      setIsSimulating(false);
    }
  };

  useEffect(() => {
    handleSimulate();
  }, []);

  // Real-time client constraint verification
  const TOTAL_BUFFER = 28500;
  const exceedsStock = releaseQuantity > TOTAL_BUFFER;
  const maxFlow = logisticsMode === "RAILWAY_FREIGHT" ? 6000 : 3500;
  const dailyFlow = releaseQuantity / Math.max(timingDays, 1);
  const exceedsLogistics = dailyFlow > maxFlow;
  const liveBudgetCr = (releaseQuantity * 1000 * subsidyCost) / 10000000;

  const toggleDistrict = (d: string) => {
    if (targetDistricts.includes(d)) {
      if (targetDistricts.length > 1) {
        setTargetDistricts(targetDistricts.filter(x => x !== d));
      }
    } else {
      setTargetDistricts([...targetDistricts, d]);
    }
  };

  // Chart data formatting
  const chartData = (activeScenario?.simulated_price_path || []).map((pt) => ({
    date: pt.date,
    predicted_modal: pt.baseline_price || 40.88,
    simulated_price: pt.simulated_price
  }));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Editorial Header */}
      <div>
        <div className="eyebrow-tag" style={{ color: "var(--color-primary)", marginBottom: "6px" }}>
          POLICY SIMULATOR & CAPACITY CONSTRAINT CHECKER
        </div>
        <h1 className="display-title" style={{ fontSize: "32px" }}>
          Scenario Lab
        </h1>
        <p style={{ fontFamily: "var(--font-serif)", fontStyle: "italic", fontSize: "17px", color: "var(--color-ink-muted)", marginTop: "4px" }}>
          Simulate counter-factual market interventions: test buffer stock releases, subsidy outlays, and freight bottlenecks.
        </p>
      </div>

      {/* Main Grid: Parameter Controls on Left, Results on Right */}
      <div style={{ display: "grid", gridTemplateColumns: "1.1fr 1.9fr", gap: "24px", alignItems: "start" }}>
        {/* Controls Column (iOS 26 Liquid Glass) */}
        <div className="liquid-glass" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ fontFamily: "var(--font-serif)", fontSize: "20px", fontWeight: 400, color: "var(--color-ink)" }}>
              Policy Levers
            </h3>
            <span className="eyebrow-tag" style={{ fontSize: "10.5px" }}>SIMULATION ENGINE</span>
          </div>

          {/* Release Quantity Slider */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
              <label style={{ fontSize: "13.5px", fontWeight: 600, color: "var(--color-ink)" }}>
                Buffer Release Volume (MT)
              </label>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "14px", fontWeight: 700, color: "var(--color-primary)" }}>
                {releaseQuantity.toLocaleString()} MT
              </span>
            </div>
            <input
              type="range"
              min="1000"
              max="35000"
              step="1000"
              value={releaseQuantity}
              onChange={(e) => setReleaseQuantity(Number(e.target.value))}
              style={{ width: "100%", accentColor: "var(--color-primary)", cursor: "pointer" }}
            />
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--color-ink-muted)", marginTop: "3px", fontFamily: "var(--font-mono)" }}>
              <span>1,000 MT</span>
              <span style={{ color: exceedsStock ? "var(--status-critical)" : "inherit", fontWeight: 600 }}>
                Total AP Reserve: 28,500 MT
              </span>
              <span>35,000 MT</span>
            </div>
          </div>

          {/* Timing Days Slider */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
              <label style={{ fontSize: "13.5px", fontWeight: 600, color: "var(--color-ink)" }}>
                Injection Window (Days)
              </label>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "14px", fontWeight: 700, color: "var(--color-ink)" }}>
                {timingDays} Days
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="14"
              value={timingDays}
              onChange={(e) => setTimingDays(Number(e.target.value))}
              style={{ width: "100%", accentColor: "var(--color-ink)", cursor: "pointer" }}
            />
            <div style={{ fontSize: "12px", color: exceedsLogistics ? "var(--status-critical)" : "var(--color-ink-muted)", marginTop: "3px", fontFamily: "var(--font-mono)" }}>
              Daily Flow: {dailyFlow.toFixed(0)} MT/day (Mode Limit: {maxFlow} MT/day)
            </div>
          </div>

          {/* Subsidy Outlay Input */}
          <div>
            <label style={{ fontSize: "13.5px", fontWeight: 600, color: "var(--color-ink)", display: "block", marginBottom: "6px" }}>
              Subsidy Outlay (₹/kg)
            </label>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "15px", color: "var(--color-ink-muted)", fontFamily: "var(--font-mono)" }}>₹</span>
              <input
                type="number"
                min="1.0"
                max="25.0"
                step="0.5"
                value={subsidyCost}
                onChange={(e) => setSubsidyCost(Number(e.target.value))}
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid rgba(0, 0, 0, 0.12)",
                  background: "rgba(255, 255, 255, 0.8)",
                  fontFamily: "var(--font-mono)",
                  fontSize: "14px",
                  fontWeight: 600
                }}
              />
            </div>
            <div style={{ fontSize: "12px", color: "var(--color-ink-muted)", marginTop: "4px" }}>
              Budget Outlay: <strong style={{ fontFamily: "var(--font-mono)", color: "var(--color-ink)" }}>₹{liveBudgetCr.toFixed(2)} Crores</strong>
            </div>
          </div>

          {/* Logistics Mode Selection */}
          <div>
            <label style={{ fontSize: "13.5px", fontWeight: 600, color: "var(--color-ink)", display: "block", marginBottom: "8px" }}>
              Logistics Mode
            </label>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
              <button
                type="button"
                className={`btn-liquid ${logisticsMode === "TRUCK_CONVOY" ? "btn-primary" : "btn-glass"}`}
                style={{ fontSize: "12px", padding: "8px" }}
                onClick={() => setLogisticsMode("TRUCK_CONVOY")}
              >
                <Truck size={14} />
                Truck (≤ 3.5k MT/d)
              </button>
              <button
                type="button"
                className={`btn-liquid ${logisticsMode === "RAILWAY_FREIGHT" ? "btn-primary" : "btn-glass"}`}
                style={{ fontSize: "12px", padding: "8px" }}
                onClick={() => setLogisticsMode("RAILWAY_FREIGHT")}
              >
                <Train size={14} />
                Rail (≤ 6.0k MT/d)
              </button>
            </div>
          </div>

          {/* Target Consumption Districts */}
          <div>
            <label style={{ fontSize: "13.5px", fontWeight: 600, color: "var(--color-ink)", display: "block", marginBottom: "8px" }}>
              Target Consumption Hubs
            </label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
              {["Kurnool", "Kadapa", "Vijayawada", "Tirupati", "Visakhapatnam"].map((dist) => (
                <button
                  key={dist}
                  type="button"
                  onClick={() => toggleDistrict(dist)}
                  className="btn-liquid"
                  style={{
                    padding: "4px 10px",
                    fontSize: "12px",
                    fontWeight: 500,
                    border: targetDistricts.includes(dist) ? "1px solid var(--color-primary)" : "1px solid rgba(0, 0, 0, 0.1)",
                    backgroundColor: targetDistricts.includes(dist) ? "rgba(0, 102, 204, 0.08)" : "transparent",
                    color: targetDistricts.includes(dist) ? "var(--color-primary)" : "var(--color-ink-muted)"
                  }}
                >
                  {dist}
                </button>
              ))}
            </div>
          </div>

          {/* Constraints Validation Badges */}
          <div style={{
            padding: "14px",
            background: "rgba(255, 255, 255, 0.6)",
            border: "1px solid rgba(0, 0, 0, 0.06)",
            borderRadius: "var(--radius-md)",
            display: "flex",
            flexDirection: "column",
            gap: "8px"
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "12px" }}>
              <span style={{ color: "var(--color-ink-secondary)" }}>Stock Reserve Feasibility:</span>
              <span className={`badge-glass ${exceedsStock ? "badge-coral" : "badge-mint"}`} style={{ fontSize: "10px" }}>
                {exceedsStock ? "VIOLATED" : "FEASIBLE"}
              </span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "12px" }}>
              <span style={{ color: "var(--color-ink-secondary)" }}>Logistics Bottleneck Check:</span>
              <span className={`badge-glass ${exceedsLogistics ? "badge-coral" : "badge-mint"}`} style={{ fontSize: "10px" }}>
                {exceedsLogistics ? "BOTTLENECK" : "FEASIBLE"}
              </span>
            </div>
          </div>

          {/* Simulate Action Button */}
          <button
            className="btn-liquid btn-primary"
            disabled={isSimulating}
            onClick={handleSimulate}
            style={{ width: "100%", padding: "12px", fontSize: "14px" }}
          >
            {isSimulating ? "Simulating Market Physics..." : "Simulate What-If Trajectory"}
          </button>
        </div>

        {/* Results Column */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {errorMsg && (
            <div style={{
              padding: "14px 18px",
              backgroundColor: "rgba(243, 201, 182, 0.4)",
              border: "1px solid rgba(198, 69, 69, 0.3)",
              color: "var(--glass-coral-ink)",
              borderRadius: "var(--radius-lg)",
              display: "flex",
              alignItems: "center",
              gap: "10px",
              fontSize: "14px",
              fontWeight: 500
            }}>
              <AlertTriangle size={18} />
              <span>{errorMsg}</span>
            </div>
          )}

          {activeScenario && !activeScenario.is_constraint_violated && (
            <>
              {/* Simulation Outcome Cards */}
              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                gap: "14px"
              }}>
                <div className="liquid-glass" style={{ padding: "18px 20px" }}>
                  <div className="eyebrow-tag">EXPECTED MITIGATION</div>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: "26px", fontWeight: 700, color: "var(--status-normal)", marginTop: "4px" }}>
                    -{activeScenario.expected_price_mitigation_pct.toFixed(1)}%
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--color-ink-muted)", marginTop: "2px" }}>
                    Stabilizes spot modal around ₹32.00/kg
                  </div>
                </div>

                <div className="liquid-glass" style={{ padding: "18px 20px" }}>
                  <div className="eyebrow-tag">TOTAL SUBSIDY BUDGET</div>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: "26px", fontWeight: 700, color: "var(--color-ink)", marginTop: "4px" }}>
                    ₹{activeScenario.total_budget_cr.toFixed(2)} Cr
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--color-ink-muted)", marginTop: "2px" }}>
                    ₹{subsidyCost.toFixed(2)}/kg consumer discount
                  </div>
                </div>

                <div className="liquid-glass" style={{ padding: "18px 20px" }}>
                  <div className="eyebrow-tag">STOCK REMAINING</div>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: "26px", fontWeight: 700, color: "var(--color-ink)", marginTop: "4px" }}>
                    {activeScenario.stock_remaining_mt.toLocaleString()} MT
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--color-ink-muted)", marginTop: "2px" }}>
                    {((activeScenario.stock_remaining_mt / TOTAL_BUFFER) * 100).toFixed(0)}% reserve retained
                  </div>
                </div>
              </div>

              {/* Chart Comparison */}
              <InteractiveChart
                title="Baseline Modal vs Simulated Buffer Intervention"
                subtitle={`Mitigation Trajectory across ${timingDays} Injection Days and 14-Day Settlement`}
                data={chartData}
                alertThreshold={35.0}
                crisisThreshold={50.0}
                showArrivals={false}
                showConfidenceInterval={false}
                height={340}
              />

              {/* Interconnected CTA to submit to Decision Briefs */}
              <div className="liquid-glass-elevated" style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "14px",
                padding: "20px 24px"
              }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: "15px", color: "var(--color-ink)" }}>
                    Ready to route this scenario for executive ratification?
                  </div>
                  <div style={{ fontSize: "13px", color: "var(--color-ink-muted)", marginTop: "2px" }}>
                    Generates an authoritative Memorandum with audit trail ready for Principal Secretary sign-off.
                  </div>
                </div>

                <button
                  className="btn-liquid btn-terracotta"
                  onClick={() => onNavigateTab("briefs")}
                  style={{ padding: "10px 20px" }}
                >
                  <span>Draft Executive Memorandum</span>
                  <ArrowRight size={15} />
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
