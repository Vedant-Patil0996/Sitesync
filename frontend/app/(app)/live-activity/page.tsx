"use client";

import React, { useState } from "react";
import { PageHeader } from "@/components/shared/page-header";
import { AIVisualGraph } from "@/components/AIVisualGraph";
import { LiveAgentTerminal } from "@/components/LiveAgentTerminal";
import { Play, RotateCcw, Loader2 } from "lucide-react";

export default function LiveActivityPage() {
  const [activeAgent, setActiveAgent] = useState<string | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const handleTrigger = async () => {
    // Reset
    setRunId(null);
    setActiveAgent(null);
    setIsRunning(true);

    try {
      const response = await fetch("http://localhost:8000/api/v1/ai/trigger", {
        method: "POST",
      });

      if (response.ok) {
        const data = await response.json();
        // Slight delay so the WS endpoint is ready before connecting
        setTimeout(() => setRunId(data.run_id), 200);
      } else {
        console.error("Failed to trigger AI simulation");
        setIsRunning(false);
      }
    } catch (error) {
      console.error("Error triggering AI:", error);
      setIsRunning(false);
    }
  };

  const handleRunComplete = () => {
    setIsRunning(false);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <PageHeader
          title="Live AI Activity"
          description="Real-time multi-agent investigation via WebSocket stream."
        />

        <button
          onClick={handleTrigger}
          disabled={isRunning}
          className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 disabled:bg-emerald-800 disabled:cursor-not-allowed text-white px-4 py-2 font-bold rounded-sm border-2 border-slate-800 shadow-brutal-sm transition-all active:translate-y-1 active:shadow-none"
        >
          {isRunning ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : runId ? (
            <RotateCcw className="w-4 h-4" />
          ) : (
            <Play className="w-4 h-4" />
          )}
          {isRunning
            ? "Agent Running…"
            : runId
            ? "Run Again"
            : "Simulate Alert (Equipment Failure)"}
        </button>
      </div>

      <div className="flex flex-col gap-6">
        {/* Top: Terminal (full width) */}
        <div className="flex flex-col w-full">
          <h2 className="text-xl font-bold mb-3 font-display">Agent Terminal Feed</h2>
          <LiveAgentTerminal
            runId={runId}
            onActiveAgentChange={setActiveAgent}
            onRunComplete={handleRunComplete}
          />
        </div>

        {/* Bottom: Decision Tree */}
        <div className="flex flex-col w-full">
          <h2 className="text-xl font-bold mb-3 font-display">System Architecture</h2>
          <div className="w-full bg-slate-950 rounded-xl border-2 border-slate-800 shadow-brutal-md p-4">
            <AIVisualGraph activeAgent={activeAgent} />
          </div>
        </div>
      </div>
    </div>
  );
}
