import {
  Geography, Commodity, MarketObservation, MarketAnalytics,
  ForecastRun, RiskAssessment, ScenarioRun, DecisionReview,
  ConnectorHealth, AuditEvent, AgentStreamEvent
} from "../types";

const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api/v1";

export async function fetchGeographies(): Promise<Geography[]> {
  const res = await fetch(`${BASE_URL}/reference/geographies`);
  if (!res.ok) throw new Error("Failed to load geographies");
  return res.json();
}

export async function fetchCommodities(): Promise<Commodity[]> {
  const res = await fetch(`${BASE_URL}/reference/commodities`);
  if (!res.ok) throw new Error("Failed to load commodities");
  return res.json();
}

export async function fetchObservations(
  commodityId: string,
  geographyId: string,
  days: number = 60
): Promise<MarketObservation[]> {
  const res = await fetch(`${BASE_URL}/observations?commodity_id=${commodityId}&geography_id=${geographyId}&days=${days}`);
  if (!res.ok) throw new Error("Failed to load observations");
  return res.json();
}

export async function fetchAnalytics(
  commodityId: string,
  geographyId: string,
  days: number = 90
): Promise<MarketAnalytics> {
  const res = await fetch(`${BASE_URL}/observations/analytics?commodity_id=${commodityId}&geography_id=${geographyId}&days=${days}`);
  if (!res.ok) throw new Error("Failed to load analytics");
  return res.json();
}

export async function fetchLatestForecast(
  commodityId: string,
  geographyId: string,
  horizonDays: number = 14
): Promise<ForecastRun> {
  const res = await fetch(`${BASE_URL}/forecast/latest?commodity_id=${commodityId}&geography_id=${geographyId}&horizon_days=${horizonDays}`);
  if (!res.ok) throw new Error("Failed to load forecast");
  return res.json();
}

export async function runForecast(
  commodityId: string,
  geographyId: string,
  horizonDays: number = 14,
  useChronos: boolean = false
): Promise<ForecastRun> {
  const res = await fetch(
    `${BASE_URL}/forecast/run?commodity_id=${commodityId}&geography_id=${geographyId}&horizon_days=${horizonDays}&use_chronos_candidate=${useChronos}`,
    { method: "POST" }
  );
  if (!res.ok) throw new Error("Failed to run forecast");
  return res.json();
}

export async function fetchBacktest(
  commodityId: string,
  geographyId: string,
  horizonDays: number = 14
): Promise<any> {
  const res = await fetch(`${BASE_URL}/forecast/backtest?commodity_id=${commodityId}&geography_id=${geographyId}&horizon_days=${horizonDays}`);
  if (!res.ok) throw new Error("Failed to load backtest report");
  return res.json();
}

export async function fetchLatestRisk(
  commodityId: string,
  geographyId: string
): Promise<RiskAssessment> {
  const res = await fetch(`${BASE_URL}/risk/latest?commodity_id=${commodityId}&geography_id=${geographyId}`);
  if (!res.ok) throw new Error("Failed to load risk assessment");
  return res.json();
}

export async function fetchScenarios(): Promise<ScenarioRun[]> {
  const res = await fetch(`${BASE_URL}/scenarios`);
  if (!res.ok) throw new Error("Failed to load scenarios");
  return res.json();
}

export async function simulateScenario(payload: {
  name: string;
  commodity_id: string;
  geography_id: string;
  release_quantity_mt: number;
  target_districts: string[];
  timing_days: number;
  logistics_mode: string;
  cost_per_kg_subsidy: number;
}): Promise<ScenarioRun> {
  const res = await fetch(`${BASE_URL}/scenarios/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to simulate scenario");
  }
  return res.json();
}

export async function fetchDecisionBriefs(): Promise<DecisionReview[]> {
  const res = await fetch(`${BASE_URL}/recommendations`);
  if (!res.ok) throw new Error("Failed to load decision briefs");
  return res.json();
}

export async function transitionDecisionBrief(
  reviewId: string,
  action: string,
  role: string,
  comment: string
): Promise<DecisionReview> {
  const res = await fetch(`${BASE_URL}/recommendations/${reviewId}/transition`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, reviewer_role: role, comment })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Transition failed");
  }
  return res.json();
}

export async function fetchSources(): Promise<ConnectorHealth[]> {
  const res = await fetch(`${BASE_URL}/sources`);
  if (!res.ok) throw new Error("Failed to load data sources");
  return res.json();
}

export async function uploadAndProfileDataset(file: File): Promise<any> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/sources/profile-upload`, {
    method: "POST",
    body: formData
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "File profiling failed");
  }
  return res.json();
}

export async function fetchAuditEvents(): Promise<AuditEvent[]> {
  const res = await fetch(`${BASE_URL}/audit/events?limit=50`);
  if (!res.ok) throw new Error("Failed to load audit events");
  return res.json();
}

export async function streamInvestigation(
  query: string,
  commodityId: string,
  geographyId: string,
  horizonDays: number,
  onEvent: (event: AgentStreamEvent) => void,
  onComplete: () => void,
  onError: (err: any) => void
) {
  try {
    const res = await fetch(`${BASE_URL}/investigate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        commodity_id: commodityId,
        geography_id: geographyId,
        horizon_days: horizonDays
      })
    });

    if (!res.ok || !res.body) {
      throw new Error("Investigation stream failed to connect");
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith("data: ")) {
          try {
            const data: AgentStreamEvent = JSON.parse(trimmed.slice(6));
            onEvent(data);
          } catch (e) {
            console.error("Failed to parse SSE payload", e);
          }
        }
      }
    }
    onComplete();
  } catch (err) {
    onError(err);
  }
}

/* ------------------------------- Agentic Chat ------------------------------ */

export interface ChatSseFrame {
  event: string;
  data: any;
}

export async function fetchChatHealth(): Promise<any> {
  const res = await fetch(`${BASE_URL}/chat/health`);
  if (!res.ok) return { status: "OFFLINE" };
  return res.json();
}

export async function streamChat(
  message: string,
  history: Array<{ role: string; content: string }>,
  onFrame: (frame: ChatSseFrame) => void,
  onComplete: () => void,
  onError: (err: any) => void
) {
  try {
    const res = await fetch(`${BASE_URL}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history })
    });

    if (!res.ok || !res.body) {
      throw new Error("Chat stream failed to connect");
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const frames = buffer.split("\n\n");
      buffer = frames.pop() || "";

      for (const frame of frames) {
        const lines = frame.split("\n");
        let eventType = "message";
        let dataRaw = "";
        for (const ln of lines) {
          if (ln.startsWith("event: ")) eventType = ln.slice(7).trim();
          else if (ln.startsWith("data: ")) dataRaw += ln.slice(6);
        }
        if (dataRaw) onFrame({ event: eventType, data: dataRaw });
      }
    }
    onComplete();
  } catch (err) {
    onError(err);
  }
}

export function parseChatFrame(raw: any): { event: string; data: any } {
  try {
    return { event: raw.event, data: JSON.parse(raw.data) };
  } catch {
    return { event: raw.event, data: raw.data };
  }
}
