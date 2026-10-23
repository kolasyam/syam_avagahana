import React, { useState, useEffect } from "react";
import {
  FileText, CheckCircle2, XCircle, ArrowRight, Printer,
  ShieldCheck, AlertTriangle, UserCheck, MessageSquare, CornerDownRight, Clock
} from "lucide-react";
import { DecisionReview } from "../types";
import { fetchDecisionBriefs, transitionDecisionBrief } from "../api/client";

interface DecisionBriefsViewProps {
  role?: string;
}

export const DecisionBriefsView: React.FC<DecisionBriefsViewProps> = ({ role = "Principal Secretary, Civil Supplies" }) => {
  const [briefs, setBriefs] = useState<DecisionReview[]>([]);
  const [selectedBrief, setSelectedBrief] = useState<DecisionReview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [commentText, setCommentText] = useState<string>("");
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const loadBriefs = async () => {
    setLoading(true);
    try {
      const data = await fetchDecisionBriefs();
      setBriefs(data);
      if (data.length > 0) {
        setSelectedBrief(data[0]);
      }
    } catch (e) {
      console.error("Failed to load decision briefs", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBriefs();
  }, []);

  const handleTransition = async (action: string) => {
    if (!selectedBrief) return;
    setActionError(null);
    setActionSuccess(null);

    const comment = commentText.trim() || `Action '${action}' executed by ${role}.`;

    try {
      const updated = await transitionDecisionBrief(
        selectedBrief.id,
        action,
        role,
        comment
      );
      setSelectedBrief(updated);
      setBriefs(briefs.map(b => b.id === updated.id ? updated : b));
      setCommentText("");
      setActionSuccess(`Successfully transitioned memorandum to '${updated.state}'.`);
    } catch (err: any) {
      setActionError(err.message || "Failed to transition decision brief.");
    }
  };

  const getStatusBadge = (state: string) => {
    switch (state) {
      case "APPROVED":
        return <span className="badge-glass badge-mint">RATIFIED & DISPATCHED</span>;
      case "IN_REVIEW":
        return <span className="badge-glass badge-lilac">EXECUTIVE REVIEW</span>;
      case "SUBMITTED":
        return <span className="badge-glass badge-cream">PENDING RATIFICATION</span>;
      case "REJECTED":
        return <span className="badge-glass badge-coral">AMENDMENT REQUIRED</span>;
      default:
        return <span className="badge-glass" style={{ background: "rgba(0,0,0,0.06)", color: "var(--color-ink)" }}>DRAFT</span>;
    }
  };

  const workflowSteps = ["DRAFT", "SUBMITTED", "IN_REVIEW", "APPROVED"];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Editorial Header */}
      <div>
        <div className="eyebrow-tag" style={{ color: "var(--color-primary)", marginBottom: "6px" }}>
          OFFICIAL EXECUTIVE MEMORANDA & RATIFICATION WORKFLOW
        </div>
        <h1 className="display-title" style={{ fontSize: "32px" }}>
          Decision Briefs & Sign-Offs
        </h1>
        <p style={{ fontFamily: "var(--font-serif)", fontStyle: "italic", fontSize: "17px", color: "var(--color-ink-muted)", marginTop: "4px" }}>
          Authoritative policy synthesis with multi-tier digital sign-off gates and immutable departmental audit records.
        </p>
      </div>

      {/* Main 2-Column Layout: Briefs List on Left, Document on Right */}
      <div style={{ display: "grid", gridTemplateColumns: "340px 1fr", gap: "24px", alignItems: "start" }}>
        {/* Left Column: Brief Selection */}
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div className="eyebrow-tag">OFFICIAL MEMORANDA ({briefs.length}):</div>

          {briefs.map((b) => {
            const isSelected = selectedBrief?.id === b.id;
            return (
              <div
                key={b.id}
                onClick={() => {
                  setSelectedBrief(b);
                  setActionError(null);
                  setActionSuccess(null);
                }}
                className={isSelected ? "liquid-glass-elevated" : "liquid-glass"}
                style={{
                  cursor: "pointer",
                  border: isSelected ? "1.5px solid var(--color-primary)" : "1px solid rgba(255, 255, 255, 0.7)",
                  backgroundColor: isSelected ? "rgba(255, 255, 255, 0.9)" : "rgba(255, 255, 255, 0.65)",
                  padding: "16px 18px",
                  transition: "all 0.2s cubic-bezier(0.16, 1, 0.3, 1)"
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                  <span className="eyebrow-tag" style={{ fontSize: "10px" }}>{b.id}</span>
                  {getStatusBadge(b.state)}
                </div>
                <h4 style={{ fontFamily: "var(--font-serif)", fontSize: "15.5px", fontWeight: 600, color: "var(--color-ink)", marginBottom: "4px" }}>
                  {b.title}
                </h4>
                <div style={{ fontSize: "12px", color: "var(--color-ink-muted)" }}>
                  Authority: {b.current_reviewer_role} • v{b.version}
                </div>
              </div>
            );
          })}
        </div>

        {/* Right Column: Selected Brief Document View */}
        {selectedBrief ? (
          <div className="liquid-glass-elevated" style={{ padding: "34px", display: "flex", flexDirection: "column", gap: "24px" }}>
            {/* Document Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
              <div>
                <div className="eyebrow-tag" style={{ color: "var(--color-primary)", marginBottom: "6px" }}>
                  GOVERNMENT OF ANDHRA PRADESH • DEPARTMENT OF FOOD & CIVIL SUPPLIES
                </div>
                <h2 style={{ fontFamily: "var(--font-serif)", fontSize: "26px", fontWeight: 400, color: "var(--color-ink)", letterSpacing: "-0.01em" }}>
                  {selectedBrief.title}
                </h2>
                <div style={{ fontSize: "13px", color: "var(--color-ink-muted)", marginTop: "4px" }}>
                  Memorandum Ref: <strong style={{ fontFamily: "var(--font-mono)" }}>{selectedBrief.id}</strong> • Linked Scenario: <strong style={{ fontFamily: "var(--font-mono)" }}>{selectedBrief.scenario_id}</strong>
                </div>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                {getStatusBadge(selectedBrief.state)}
                <button
                  className="btn-liquid btn-glass"
                  onClick={() => window.print()}
                  style={{ fontSize: "12px", padding: "6px 14px" }}
                >
                  <Printer size={13} />
                  Print Official Order
                </button>
              </div>
            </div>

            {/* Workflow Progress Stepper (iOS 26 Liquid Glass) */}
            <div style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "16px 22px",
              background: "rgba(255, 255, 255, 0.6)",
              border: "1px solid rgba(0, 0, 0, 0.06)",
              borderRadius: "var(--radius-pill)"
            }}>
              {workflowSteps.map((step, idx) => {
                const isPassed = workflowSteps.indexOf(selectedBrief.state) >= idx || selectedBrief.state === "APPROVED";
                const isCurrent = selectedBrief.state === step;

                return (
                  <div key={step} style={{ display: "flex", alignItems: "center", gap: "8px", flex: 1 }}>
                    <div style={{
                      width: "28px",
                      height: "28px",
                      borderRadius: "50%",
                      backgroundColor: isPassed ? "var(--color-primary)" : "rgba(0, 0, 0, 0.08)",
                      color: isPassed ? "#ffffff" : "var(--color-ink-muted)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontWeight: 700,
                      fontSize: "12px",
                      fontFamily: "var(--font-mono)",
                      boxShadow: isPassed ? "0 2px 6px rgba(0, 102, 204, 0.3)" : "none"
                    }}>
                      {isPassed ? "✓" : idx + 1}
                    </div>
                    <div>
                      <div style={{ fontSize: "11px", fontFamily: "var(--font-mono)", fontWeight: 600, color: isCurrent ? "var(--color-primary)" : "var(--color-ink-muted)" }}>
                        {step}
                      </div>
                    </div>
                    {idx < workflowSteps.length - 1 && (
                      <div style={{ flex: 1, height: "2px", backgroundColor: isPassed ? "var(--color-primary)" : "rgba(0, 0, 0, 0.08)", margin: "0 8px" }} />
                    )}
                  </div>
                );
              })}
            </div>

            {/* Executive Memorandum Body */}
            <div style={{
              padding: "24px 28px",
              background: "rgba(255, 255, 255, 0.8)",
              borderRadius: "var(--radius-lg)",
              border: "1px solid rgba(0, 0, 0, 0.06)",
              boxShadow: "var(--shadow-liquid-subtle)"
            }}>
              <div className="eyebrow-tag" style={{ marginBottom: "10px" }}>EXECUTIVE MEMORANDUM & INTERVENTION DIRECTIVE:</div>
              <p style={{ fontFamily: "var(--font-serif)", fontSize: "17px", lineHeight: 1.65, color: "var(--color-ink)" }}>
                {selectedBrief.summary}
              </p>
            </div>

            {/* Notification Feedback */}
            {actionSuccess && (
              <div style={{
                padding: "12px 18px",
                backgroundColor: "rgba(200, 230, 205, 0.5)",
                border: "1px solid rgba(18, 64, 25, 0.2)",
                color: "var(--glass-mint-ink)",
                borderRadius: "var(--radius-md)",
                fontSize: "13.5px",
                fontWeight: 600
              }}>
                ✓ {actionSuccess}
              </div>
            )}
            {actionError && (
              <div style={{
                padding: "12px 18px",
                backgroundColor: "rgba(243, 201, 182, 0.5)",
                border: "1px solid rgba(198, 69, 69, 0.2)",
                color: "var(--glass-coral-ink)",
                borderRadius: "var(--radius-md)",
                fontSize: "13.5px",
                fontWeight: 600
              }}>
                ✕ {actionError}
              </div>
            )}

            {/* Governed Action Console */}
            <div style={{
              padding: "20px 24px",
              border: "1px solid rgba(0, 0, 0, 0.08)",
              borderRadius: "var(--radius-lg)",
              background: "rgba(255, 255, 255, 0.6)",
              display: "flex",
              flexDirection: "column",
              gap: "14px"
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span className="eyebrow-tag">EXECUTIVE RATIFICATION CONSOLE • {role}</span>
                <span style={{ fontSize: "12px", color: "var(--color-ink-muted)", fontFamily: "var(--font-mono)" }}>
                  Status: <strong>{selectedBrief.state}</strong>
                </span>
              </div>

              <textarea
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                placeholder="Enter departmental directives, special distribution allocations, or sign-off notes..."
                rows={2}
                style={{
                  width: "100%",
                  padding: "10px 14px",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid rgba(0, 0, 0, 0.12)",
                  background: "rgba(255, 255, 255, 0.85)",
                  fontFamily: "var(--font-sans)",
                  fontSize: "14px",
                  outline: "none"
                }}
              />

              {/* Action Buttons based on state */}
              <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", justifyContent: "flex-end" }}>
                {selectedBrief.state === "DRAFT" && (
                  <button
                    className="btn-liquid btn-primary"
                    onClick={() => handleTransition("SUBMIT")}
                  >
                    Submit for Official Review
                  </button>
                )}

                {selectedBrief.state === "SUBMITTED" && (
                  <>
                    <button
                      className="btn-liquid btn-glass"
                      onClick={() => handleTransition("REJECT")}
                      style={{ color: "var(--status-critical)" }}
                    >
                      Return with Amendments
                    </button>
                    <button
                      className="btn-liquid btn-primary"
                      onClick={() => handleTransition("START_REVIEW")}
                    >
                      Begin Executive Review
                    </button>
                  </>
                )}

                {selectedBrief.state === "IN_REVIEW" && (
                  <>
                    <button
                      className="btn-liquid btn-glass"
                      onClick={() => handleTransition("RETURN")}
                    >
                      Return to Draft
                    </button>
                    <button
                      className="btn-liquid btn-glass"
                      onClick={() => handleTransition("REJECT")}
                      style={{ color: "var(--status-critical)" }}
                    >
                      Reject
                    </button>
                    <button
                      className="btn-liquid btn-terracotta"
                      onClick={() => handleTransition("APPROVE")}
                    >
                      <CheckCircle2 size={15} />
                      Grant Official Ratification
                    </button>
                  </>
                )}

                {selectedBrief.state === "APPROVED" && (
                  <div style={{ fontSize: "13.5px", color: "var(--status-normal)", fontWeight: 600, display: "flex", alignItems: "center", gap: "6px" }}>
                    <CheckCircle2 size={16} />
                    <span>This memorandum has been ratified by the Principal Secretary. Buffer liquidation orders active.</span>
                  </div>
                )}
              </div>
            </div>

            {/* Departmental Comments & Audit Log */}
            <div>
              <div className="eyebrow-tag" style={{ marginBottom: "12px" }}>
                IMMUTABLE AUDIT LOG & RATIFICATION NOTES ({selectedBrief.comments?.length || 0}):
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {(selectedBrief.comments || []).map((c, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: "12px 16px",
                      backgroundColor: "rgba(255, 255, 255, 0.7)",
                      borderRadius: "var(--radius-md)",
                      border: "1px solid rgba(0, 0, 0, 0.05)"
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                      <span style={{ fontWeight: 600, fontSize: "13px", color: "var(--color-ink)" }}>
                        {c.author}
                      </span>
                      <span style={{ fontSize: "11px", color: "var(--color-ink-muted)", fontFamily: "var(--font-mono)" }}>
                        {c.timestamp}
                      </span>
                    </div>
                    <div style={{ fontSize: "13px", color: "var(--color-ink-secondary)" }}>
                      {c.text}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="liquid-glass" style={{ padding: "40px", textAlign: "center", color: "var(--color-ink-muted)" }}>
            Select a decision brief to inspect and review.
          </div>
        )}
      </div>
    </div>
  );
};
