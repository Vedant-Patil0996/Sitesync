"use client";

import React, { useEffect, useRef, useState } from "react";
import { Terminal, FileText } from "lucide-react";

export interface AgentEvent {
  id: string;
  run_id: string;
  timestamp: string;
  type: string;
  agent: string;
  content: string;
  tool_name?: string;
  data?: Record<string, unknown>;
}

interface Props {
  runId: string | null;
  onActiveAgentChange: (agent: string | null) => void;
  onRunComplete: () => void;
}

const AGENT_COLOR: Record<string, string> = {
  SYSTEM:            "text-gray-400",
  ANOMALY_DETECTOR:  "text-emerald-400",
  SUPERVISOR:        "text-blue-400",
  STOCK_AGENT:       "text-cyan-400",
  BUDGET_AGENT:      "text-cyan-400",
  EQUIPMENT_AGENT:   "text-cyan-400",
  PROJECT_AGENT:     "text-cyan-400",
  PROCUREMENT_AGENT: "text-cyan-400",
  DB_SYSTEM:         "text-yellow-400",
  REPORTER:          "text-purple-400",
};

const TYPE_ICON: Record<string, string> = {
  RUN_STARTED:     "🚀",
  RUN_COMPLETED:   "✅",
  RUN_FAILED:      "❌",
  AGENT_STARTED:   "▶",
  AGENT_COMPLETED: "✓",
  TOOL_STARTED:    "⚙",
  TOOL_COMPLETED:  "↩",
  FINAL_REPORT:    "📋",
  MESSAGE:         "›",
};

// Events we render inline in the terminal (skip FINAL_REPORT — shown separately)
const SKIP_IN_TERMINAL = new Set(["PING", "FINAL_REPORT"]);

export function LiveAgentTerminal({ runId, onActiveAgentChange, onRunComplete }: Props) {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [finalReport, setFinalReport] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Connect WebSocket whenever runId changes
  useEffect(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (!runId) {
      setEvents([]);
      setFinalReport(null);
      setConnected(false);
      onActiveAgentChange(null);
      return;
    }

    setEvents([]);
    setFinalReport(null);
    setConnected(false);

    const ws = new WebSocket(`ws://localhost:8000/api/v1/ai/stream/${runId}`);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);

    ws.onmessage = (msg) => {
      try {
        const event: AgentEvent = JSON.parse(msg.data);

        if (event.type === "PING") return;

        // Capture final report separately
        if (event.type === "FINAL_REPORT") {
          setFinalReport(event.content);
          return;
        }

        setEvents((prev) => [...prev, event]);

        if (["AGENT_STARTED", "AGENT_COMPLETED", "TOOL_STARTED", "TOOL_COMPLETED"].includes(event.type)) {
          onActiveAgentChange(event.agent);
        }

        if (event.type === "RUN_COMPLETED" || event.type === "RUN_FAILED") {
          setConnected(false);
          ws.close();
          onRunComplete();
        }
      } catch {
        setEvents((prev) => [
          ...prev,
          {
            id: `raw_${Date.now()}`,
            run_id: runId,
            timestamp: new Date().toISOString(),
            type: "MESSAGE",
            agent: "SYSTEM",
            content: msg.data,
          },
        ]);
      }
    };

    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    return () => {
      ws.close();
    };
  }, [runId]);

  // Auto-scroll terminal
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  const renderLine = (ev: AgentEvent, idx: number) => {
    const color = AGENT_COLOR[ev.agent] ?? "text-gray-300";
    const icon = TYPE_ICON[ev.type] ?? "›";
    const time = new Date(ev.timestamp).toLocaleTimeString([], { hour12: false });

    return (
      <div
        key={ev.id ?? idx}
        className="leading-relaxed animate-in fade-in duration-100"
      >
        <span className="text-gray-600 text-xs mr-2">[{time}]</span>
        <span className={`font-bold mr-1 ${color}`}>{ev.agent}:</span>
        <span className="text-gray-500 mr-2">{icon}</span>
        {ev.tool_name && (
          <span className="text-yellow-300 font-mono mr-2">{ev.tool_name}</span>
        )}
        <span className="text-gray-200 break-words">{ev.content}</span>
      </div>
    );
  };

  return (
    <div className="flex flex-col gap-4">
      {/* Terminal */}
      <div className="flex flex-col bg-slate-950 rounded-xl border border-slate-800 shadow-2xl overflow-hidden h-[360px]">
        {/* Mac-style header */}
        <div className="flex items-center px-4 py-3 bg-slate-900 border-b border-slate-800 shrink-0">
          <div className="flex space-x-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <div className="w-3 h-3 rounded-full bg-yellow-500" />
            <div className={`w-3 h-3 rounded-full ${connected ? "bg-green-500 animate-pulse" : "bg-gray-600"}`} />
          </div>
          <div className="mx-auto flex items-center text-slate-400 text-xs font-mono gap-2">
            <Terminal className="w-3 h-3" />
            agent_orchestrator.py — Live Feed
            {connected && <span className="text-emerald-400 text-[10px]">● LIVE</span>}
            {!connected && finalReport && <span className="text-purple-400 text-[10px]">● COMPLETE</span>}
          </div>
        </div>

        {/* Body */}
        <div
          ref={scrollRef}
          className="p-4 flex-1 overflow-y-auto font-mono text-sm space-y-1"
          style={{ scrollBehavior: "smooth" }}
        >
          {!runId && (
            <div className="text-gray-500 animate-pulse">
              Waiting for system trigger… Click "Simulate Alert" to begin.
            </div>
          )}
          {runId && events.length === 0 && (
            <div className="text-gray-500 animate-pulse">Connecting to agent stream…</div>
          )}
          {events.map(renderLine)}
          {connected && (
            <div className="inline-block w-2 h-4 bg-emerald-400 animate-pulse ml-1 align-middle" />
          )}
        </div>
      </div>

      {/* Final Report Panel — shown after run completes */}
      {finalReport && (
        <div className="bg-slate-900 border-2 border-purple-800 rounded-xl overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="flex items-center gap-2 px-4 py-3 bg-slate-800 border-b border-purple-800">
            <FileText className="w-4 h-4 text-purple-400" />
            <span className="text-purple-300 font-bold text-sm">Master Reporter — Final Investigation Report</span>
          </div>
          <div className="p-6 text-gray-200 text-sm leading-relaxed whitespace-pre-wrap max-h-[500px] overflow-y-auto">
            {finalReport}
          </div>
        </div>
      )}
    </div>
  );
}
