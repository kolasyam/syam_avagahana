import React, { useEffect, useRef, useState } from "react";
import {
  Send, Loader2, Database, Globe, ShieldCheck, ShieldAlert, Bot,
  BrainCircuit, Radar, BarChart3, MessageSquareText, ChevronDown, ChevronUp, User
} from "lucide-react";
import { fetchChatHealth, streamChat, parseChatFrame, ChatSseFrame } from "../api/client";

/* ------------------------------ types ------------------------------ */

interface ChatMessageItem {
  role: "user" | "assistant";
  content: string;
  agents?: string[];
  tools?: string[];
  sources?: Array<{ type: string; trust?: string; url?: string; title?: string; source?: string; label?: string; ingested?: boolean }>;
  meta?: { model?: string; llm_status?: string; duration_seconds?: number; agents?: string[] };
}

interface AgentChipState {
  name: string;
  status: "idle" | "running" | "completed";
  detail?: string;
}

const AGENT_ICONS: Record<string, any> = {
  "Router": BrainCircuit,
  "Market Agent": Radar,
  "Forecast Agent": BarChart3,
  "Analysis Agent": ShieldCheck,
  "Response Agent": MessageSquareText,
};

const QUICK_PROMPTS = [
  "What is the average onion price over the last 2 months?",
  "What is today's onion price?",
  "Give me the 30-day forecast and breach risk.",
  "What if rainfall next month is 150 mm — add it as a factor.",
  "Why should I trust the forecast?",
];

/* --------------------------- component ---------------------------- */

export const ChatPanel: React.FC<{ geographyId: string }> = ({ geographyId }) => {
  const [llmStatus, setLlmStatus] = useState<any>(null);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [agents, setAgents] = useState<AgentChipState[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [openTrace, setOpenTrace] = useState<boolean>(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchChatHealth().then(setLlmStatus).catch(() => setLlmStatus({ status: "OFFLINE" }));
    // pre-warm the local model quietly (no blocking): keeps RAM-resident model hot
    fetch(`${import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api/v1"}/chat/warm`, { method: "POST" })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, agents]);

  const agentStatus = (name: string): AgentChipState =>
    agents.find((a) => a.name === name) || { name, status: "idle" };

  const send = (text?: string) => {
    const msg = (text || input).trim();
    if (!msg || streaming) return;

    setInput("");
    const history = messages.slice(-6).map((m) => ({ role: m.role, content: m.content }));
    const userItem: ChatMessageItem = { role: "user", content: msg };
    const assistantItem: ChatMessageItem = { role: "assistant", content: "", agents: [], tools: [], sources: [] };
    setMessages((prev) => [...prev, userItem, assistantItem]);
    setStreaming(true);
    setAgents([{ name: "Router", status: "running", detail: "local LLM (Ollama)" }]);

    streamChat(
      msg,
      history,
      (frame: ChatSseFrame) => {
        const { event, data } = parseChatFrame(frame);

        if (event === "agent") {
          setAgents((prev) => {
            const next = prev.filter((a) => a.name !== data.agent);
            next.push({ name: data.agent, status: data.status, detail: data.detail });
            return next;
          });
        } else if (event === "token") {
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last?.role === "assistant") {
              copy[copy.length - 1] = { ...last, content: last.content + (typeof data === "string" ? data : JSON.stringify(data)) };
            }
            return copy;
          });
        } else if (event === "tool") {
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last?.role === "assistant") {
              copy[copy.length - 1] = { ...last, tools: [...(last.tools || []), `${data.tool}: ${data.status === "completed" ? data.summary || "done" : "running"}`] };
            }
            return copy;
          });
        } else if (event === "sources") {
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last?.role === "assistant") {
              copy[copy.length - 1] = { ...last, sources: Array.isArray(data) ? data : [] };
            }
            return copy;
          });
        } else if (event === "audit") {
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last?.role === "assistant") {
              copy[copy.length - 1] = { ...last, meta: data };
            }
            return copy;
          });
          setAgents((prev) => prev.map((a) => ({ ...a, status: a.status === "running" ? "completed" : a.status })));
        } else if (event === "error" || event === "done") {
          // stream lifecycle
        }
      },
      () => {
        setStreaming(false);
        setAgents((prev) => prev.map((a) => ({ ...a, status: a.status === "running" ? "completed" : a.status })));
      },
      (err) => {
        console.error("chat stream error", err);
        setStreaming(false);
        setMessages((prev) => {
          const copy = [...prev];
          const last = copy[copy.length - 1];
          if (last?.role === "assistant" && !last.content) {
            copy[copy.length - 1] = { ...last, content: "[Connection error — backend unreachable]" };
          }
          return copy;
        });
      }
    );
  };

  const statusColor =
    llmStatus?.status === "READY" ? "var(--status-normal)"
    : llmStatus?.status === "OFFLINE" ? "var(--status-critical)"
    : "var(--color-amber, #d97706)";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
      {/* header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
        <div>
          <div className="eyebrow-tag" style={{ color: "var(--color-primary)", marginBottom: "6px" }}>
            Agentic Chat • Grounded Tool Loop
          </div>
          <h2 className="section-title" style={{ fontSize: "22px", marginBottom: "2px" }}>
            Ask the Onion Market Agent
          </h2>
          <p style={{ fontFamily: "var(--font-serif)", fontStyle: "italic", fontSize: "16px", color: "var(--color-ink-secondary)" }}>
            Every number below comes from a live tool call — the local model never invents prices.
          </p>
        </div>
        <div className="badge-glass" style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", padding: "6px 12px" }}>
          <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: statusColor, display: "inline-block" }} />
          LLM: {llmStatus ? `${llmStatus.status === "READY" ? llmStatus.model : llmStatus.status}` : "checking…"}
        </div>
      </div>

      {/* agent chips */}
      <div className="liquid-glass" style={{ padding: "10px 14px", display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
        {["Router", "Market Agent", "Forecast Agent", "Analysis Agent", "Response Agent"].map((name) => {
          const st = agentStatus(name);
          const Icon = AGENT_ICONS[name] || Bot;
          const color =
            st.status === "completed" ? "var(--status-normal)"
            : st.status === "running" ? "var(--color-primary)"
            : "var(--color-ink-muted)";
          return (
            <div key={name} style={{ display: "flex", alignItems: "center", gap: "6px", opacity: st.status === "idle" ? 0.45 : 1 }}>
              <Icon size={14} color={color} style={st.status === "running" ? { animation: "spin 1s linear infinite" } : undefined} />
              <span style={{ fontSize: "11.5px", fontWeight: 600, color }}>{name}</span>
            </div>
          );
        })}
        <div style={{ marginLeft: "auto" }}>
          <button
            className="btn-liquid btn-glass"
            onClick={() => setOpenTrace((o) => !o)}
            style={{ padding: "4px 10px", fontSize: "11px", display: "flex", alignItems: "center", gap: "4px" }}
          >
            Tool Trace {openTrace ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
        </div>
      </div>

      {/* transcript */}
      <div className="liquid-glass-elevated" style={{ padding: "18px", display: "flex", flexDirection: "column", gap: "14px" }}>
        <div ref={scrollRef} style={{ maxHeight: "46vh", overflowY: "auto", display: "flex", flexDirection: "column", gap: "14px", paddingRight: "4px" }}>
          {messages.length === 0 && (
            <div style={{ textAlign: "center", padding: "18px 8px", color: "var(--color-ink-muted)" }}>
              <Bot size={30} color="var(--color-primary)" style={{ marginBottom: "8px" }} />
              <div style={{ fontSize: "13.5px" }}>
                Ask about prices, averages, forecasts, breach risk, or add a factor conversationally.
              </div>
            </div>
          )}

          {messages.map((m, idx) => (
            <div key={idx} style={{ display: "flex", gap: "10px", alignItems: "flex-start", flexDirection: m.role === "user" ? "row-reverse" : "row" }}>
              <div style={{
                width: "30px", height: "30px", borderRadius: "8px", flexShrink: 0,
                display: "flex", alignItems: "center", justifyContent: "center",
                background: m.role === "user" ? "rgba(0,102,204,0.12)" : "rgba(255,255,255,0.65)",
                color: "var(--color-primary)"
              }}>
                {m.role === "user" ? <User size={15} /> : <Bot size={15} />}
              </div>
              <div style={{ maxWidth: "82%" }}>
                <div style={{
                  background: m.role === "user" ? "rgba(0,102,204,0.08)" : "rgba(255,255,255,0.6)",
                  border: "1px solid rgba(0,0,0,0.05)",
                  borderRadius: "12px", padding: "12px 14px", fontSize: "14.5px", lineHeight: 1.5,
                  color: "var(--color-ink)", whiteSpace: "pre-wrap"
                }}>
                  {m.content || (streaming ? <Loader2 size={14} className="animate-spin" /> : "")}
                </div>

                {openTrace && m.role === "assistant" && (m.tools?.length || m.meta) && (
                  <div style={{ marginTop: "6px", fontSize: "11px", color: "var(--color-ink-muted)", fontFamily: "var(--font-mono)" }}>
                    {m.tools?.map((t, ti) => (<div key={ti}>› {t}</div>))}
                    {m.meta && (
                      <div style={{ opacity: 0.75 }}>
                        {m.meta.llm_status === "LLM" ? m.meta.model : "rule-based fallback"} · {m.meta.duration_seconds}s
                        {m.meta.agents?.length ? ` · agents: ${m.meta.agents.join(" → ")}` : ""}
                      </div>
                    )}
                  </div>
                )}

                {m.role === "assistant" && m.sources && m.sources.length > 0 && (
                  <div style={{ marginTop: "8px", display: "flex", gap: "6px", flexWrap: "wrap" }}>
                    {m.sources.map((s, si) => {
                      const isWeb = s.type === "WEB";
                      const bad = s.trust === "APPROVED_TRUST_SOURCE";
                      return (
                        <div key={si} style={{
                          display: "flex", alignItems: "center", gap: "4px", fontSize: "10.5px",
                          padding: "4px 8px", borderRadius: "999px", background: "rgba(255,255,255,0.7)",
                          border: "1px solid rgba(0,0,0,0.06)",
                          color: isWeb ? (bad ? "var(--status-normal)" : "var(--color-amber, #d97706)") : "var(--color-primary)",
                        }}>
                          {isWeb ? (bad ? <ShieldCheck size={11} /> : <ShieldAlert size={11} />) : <Database size={11} />}
                          {isWeb
                            ? (s.url || "").replace(/^https?:\/\//, "").split("/")[0] + (s.ingested ? "" : " · citation only")
                            : (s.source || s.label || "ingested series")}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* quick prompts */}
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", borderTop: "1px solid rgba(0,0,0,0.05)", paddingTop: "12px" }}>
          {QUICK_PROMPTS.map((q, i) => (
            <button key={i} className="btn-liquid btn-glass" disabled={streaming}
              onClick={() => send(q)}
              style={{ padding: "5px 12px", fontSize: "12px", opacity: streaming ? 0.5 : 1 }}>
              {q}
            </button>
          ))}
        </div>

        {/* composer */}
        <div style={{ display: "flex", gap: "10px", alignItems: "flex-end" }}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
            }}
            rows={2}
            disabled={streaming}
            placeholder={`Ask about ${geographyId === "state_andhra_pradesh" ? "AP" : geographyId} onion prices, forecasts, or add a what-if factor…`}
            style={{
              flex: 1, border: "1px solid rgba(0,0,0,0.08)", borderRadius: "12px",
              padding: "10px 12px", fontSize: "14.5px", fontFamily: "var(--font-sans)",
              resize: "none", outline: "none", background: "rgba(255,255,255,0.6)", color: "var(--color-ink)"
            }}
          />
          <button
            className="btn-liquid btn-primary"
            disabled={streaming || !input.trim()}
            onClick={() => send()}
            style={{ padding: "12px 16px", opacity: streaming || !input.trim() ? 0.6 : 1 }}
          >
            {streaming ? <Loader2 size={15} className="animate-spin" /> : <Send size={14} />}
          </button>
        </div>
      </div>
    </div>
  );
};
