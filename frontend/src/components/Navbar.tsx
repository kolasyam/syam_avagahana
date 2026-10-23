import React from "react";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab
}) => {
  const tabs = [
    { id: "workspace", label: "Executive Workspace" },
    { id: "market", label: "Market Intelligence" },
    { id: "forecast", label: "Forecast & Risk" },
    { id: "scenario", label: "Scenario Lab" },
    { id: "briefs", label: "Decision Briefs" },
    { id: "sources", label: "Data Fabric" },
    { id: "upload", label: "Data Intake" },
    { id: "inspector", label: "Audit Trail" }
  ];

  return (
    <nav className="liquid-nav">
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "16px"
      }}>
        {/* Brand identity (Apple clean layout + Times New Roman italic accent) */}
        <div
          style={{ display: "flex", alignItems: "center", gap: "12px", cursor: "pointer" }}
          onClick={() => setActiveTab("workspace")}
        >
          <div style={{
            width: "36px",
            height: "36px",
            borderRadius: "10px",
            backgroundColor: "var(--color-ink)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#ffffff",
            fontFamily: "var(--font-sans)",
            fontWeight: 700,
            fontSize: "16px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.18)"
          }}>
            AP
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{
                fontFamily: "var(--font-sans)",
                fontSize: "15px",
                fontWeight: 600,
                color: "var(--color-ink)",
                letterSpacing: "-0.2px"
              }}>
                Price Intelligence Platform
              </span>
              <span style={{
                fontFamily: "var(--font-serif)",
                fontStyle: "italic",
                fontSize: "13px",
                color: "var(--color-primary)"
              }}>
                Govt. of Andhra Pradesh
              </span>
            </div>
          </div>
        </div>

        {/* Center: Apple iOS 26 Liquid Glass Segmented Pill Bar */}
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "4px",
          background: "rgba(0, 0, 0, 0.04)",
          padding: "4px",
          borderRadius: "var(--radius-pill)",
          overflowX: "auto"
        }}>
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  fontFamily: "var(--font-sans)",
                  fontSize: "13.5px",
                  fontWeight: isActive ? 600 : 500,
                  padding: "6px 14px",
                  borderRadius: "var(--radius-pill)",
                  border: "none",
                  cursor: "pointer",
                  transition: "all 0.2s cubic-bezier(0.16, 1, 0.3, 1)",
                  backgroundColor: isActive ? "#ffffff" : "transparent",
                  color: isActive ? "var(--color-ink)" : "var(--color-ink-muted)",
                  boxShadow: isActive ? "0 2px 8px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)" : "none",
                  whiteSpace: "nowrap"
                }}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Right: Integrated System Status Badge */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div className="badge-glass badge-mint">
            <span style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              backgroundColor: "var(--status-normal)",
              display: "inline-block"
            }} />
            <span>ONLINE • 147 MANDIS</span>
          </div>
        </div>
      </div>
    </nav>
  );
};
