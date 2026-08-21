"use client";

import React, { useState, useEffect } from "react";
import { PageHeader } from "@/components/shared/page-header";
import { AIVisualGraph } from "@/components/AIVisualGraph";
import { LiveAgentTerminal } from "@/components/LiveAgentTerminal";
import { ScenarioSelector } from "@/components/ScenarioSelector";
import { Play, RotateCcw, Loader2 } from "lucide-react";

export interface Scenario {
  id: string;
  label: string;
  description: string;
  severity: "critical" | "warning" | "info";
  icon: string;
  tags: string[];
}

export default function LiveActivityPage() {
  const [activeAgent, setActiveAgent] = useState<string | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null);

  // Fetch scenarios from backend
  useEffect(() => {
    fetch("http://localhost:8000/api/v1/ai/scenarios")
      .then((r) => r.json())
      .then((data) => {
        const list: Scenario[] = data.scenarios || [];
        setScenarios(list);
        if (list.length > 0) setSelectedScenario(list[0]);
      })
      .catch(console.error);
  }, []);

  const handleTrigger = async () => {
    if (!selectedScenario) return;
    setRunId(null);
    setActiveAgent(null);
    setIsRunning(true);

    try {
      const response = await fetch("http://localhost:8000/api/v1/ai/trigger", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario_id: selectedScenario.id, site_id: "1" }),
      });

      if (response.ok) {
        const data = await response.json();
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
      {/* Header */}
      <div className="flex justify-between items-center flex-wrap gap-4">
        <PageHeader
          title="Live AI Activity"
          description="Real-time multi-agent investigation via WebSocket stream."
        />
        <button
          onClick={handleTrigger}
          disabled={isRunning || !selectedScenario}
          className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 disabled:bg-emerald-800 disabled:cursor-not-allowed text-white px-5 py-2.5 font-bold rounded-sm border-2 border-slate-800 shadow-brutal-sm transition-all active:translate-y-1 active:shadow-none whitespace-nowrap"
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
            : "Run Simulation"}
        </button>
      </div>

      {/* Scenario Selector */}
      <ScenarioSelector
        scenarios={scenarios}
        selected={selectedScenario}
        onSelect={setSelectedScenario}
        disabled={isRunning}
      />

      {/* Terminal */}
      <div className="flex flex-col w-full">
        <h2 className="text-xl font-bold mb-3 font-display">Agent Terminal Feed</h2>
        <LiveAgentTerminal
          runId={runId}
          onActiveAgentChange={setActiveAgent}
          onRunComplete={handleRunComplete}
        />
      </div>

      {/* Decision Tree */}
      <div className="flex flex-col w-full">
        <h2 className="text-xl font-bold mb-3 font-display">System Architecture</h2>
        <div className="w-full bg-slate-950 rounded-xl border-2 border-slate-800 shadow-brutal-md p-4">
          <AIVisualGraph activeAgent={activeAgent} />
        </div>
      </div>
    </div>
  );
}
