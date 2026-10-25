import React, { useState, useEffect } from "react";
import "./styles/tokens.css";
import { Navbar } from "./components/Navbar";
import { WorkspaceView } from "./components/WorkspaceView";
import { ChatPanel } from "./components/ChatPanel";
import { MarketIntelligenceView } from "./components/MarketIntelligenceView";
import { ForecastRiskView } from "./components/ForecastRiskView";
import { ScenarioLabView } from "./components/ScenarioLabView";
import { DecisionBriefsView } from "./components/DecisionBriefsView";
import { DataFabricView } from "./components/DataFabricView";
import { DataIntakeView } from "./components/DataIntakeView";
import { RunInspectorView } from "./components/RunInspectorView";
import { Geography, Commodity } from "./types";
import { fetchGeographies, fetchCommodities } from "./api/client";

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>("workspace");
  const [geographies, setGeographies] = useState<Geography[]>([]);
  const [commodities, setCommodities] = useState<Commodity[]>([]);
  const [selectedGeography, setSelectedGeography] = useState<string>("state_andhra_pradesh");
  const [selectedCommodity, setSelectedCommodity] = useState<string>("onion");
  const [sharedHorizon, setSharedHorizon] = useState<number>(14);

  useEffect(() => {
    async function init() {
      try {
        const [geos, comms] = await Promise.all([
          fetchGeographies(),
          fetchCommodities()
        ]);
        setGeographies(geos);
        setCommodities(comms);
      } catch (e) {
        console.error("Initial load failed", e);
      }
    }
    init();
  }, []);

  const navigateToForecast = (horizonDays: number = 14) => {
    setSharedHorizon(horizonDays);
    setActiveTab("forecast");
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Top iOS 26 Liquid Glass Navigation Bar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      {/* Main Content Area */}
      <main style={{ flex: 1, maxWidth: "1440px", width: "100%", margin: "0 auto", padding: "28px 20px" }}>
        {activeTab === "workspace" && (
          <WorkspaceView
            commodityId={selectedCommodity}
            geographyId={selectedGeography}
            onNavigateTab={setActiveTab}
            onNavigateForecast={navigateToForecast}
          />
        )}

        {activeTab === "agentic-chat" && (
          <div style={{ maxWidth: "960px", margin: "0 auto" }}>
            <ChatPanel geographyId={selectedGeography} />
          </div>
        )}

        {activeTab === "market" && (
          <MarketIntelligenceView
            geographies={geographies}
            commodities={commodities}
            selectedCommodity={selectedCommodity}
            setSelectedCommodity={setSelectedCommodity}
            selectedGeography={selectedGeography}
            setSelectedGeography={setSelectedGeography}
            onNavigateForecast={navigateToForecast}
          />
        )}

        {activeTab === "forecast" && (
          <ForecastRiskView
            commodityId={selectedCommodity}
            geographyId={selectedGeography}
            initialHorizon={sharedHorizon}
            onNavigateScenario={() => setActiveTab("scenario")}
          />
        )}

        {activeTab === "scenario" && (
          <ScenarioLabView
            commodityId={selectedCommodity}
            geographyId={selectedGeography}
            onNavigateTab={setActiveTab}
          />
        )}

        {activeTab === "briefs" && (
          <DecisionBriefsView />
        )}

        {activeTab === "sources" && <DataFabricView />}

        {activeTab === "upload" && <DataIntakeView />}

        {activeTab === "inspector" && <RunInspectorView />}
      </main>

      {/* Production Government Footer */}
      <footer style={{
        background: "rgba(255, 255, 255, 0.4)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        borderTop: "1px solid rgba(0, 0, 0, 0.06)",
        padding: "24px 20px",
        marginTop: "48px",
        fontSize: "13px",
        color: "var(--color-ink-muted)"
      }}>
        <div style={{
          maxWidth: "1440px",
          margin: "0 auto",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px"
        }}>
          <div>
            <span style={{ fontFamily: "var(--font-sans)", fontWeight: 600, color: "var(--color-ink)" }}>
              Department of Food & Civil Supplies
            </span>
            {" • "}
            <span style={{ fontFamily: "var(--font-serif)", fontStyle: "italic" }}>
              Government of Andhra Pradesh
            </span>
            <div style={{ fontSize: "12px", marginTop: "2px" }}>
              Authoritative Essential Commodities Price Intelligence & Autonomous Stabilisation Infrastructure
            </div>
          </div>
          <div style={{ textAlign: "right", fontFamily: "var(--font-mono)", fontSize: "11.5px" }}>
            AGMARKNET Curated Series • IMD Context • Tavily Web Fallback (citation-only) • Local LLM (Ollama)
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
