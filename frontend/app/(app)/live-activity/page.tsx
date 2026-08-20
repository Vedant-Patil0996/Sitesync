"use client";

import React, { useState, useEffect } from "react";
import { PageHeader } from "@/components/shared/page-header";
import { AIVisualGraph } from "@/components/AIVisualGraph";
import { LiveAgentTerminal, TraceEvent } from "@/components/LiveAgentTerminal";
import { Play, RotateCcw } from "lucide-react";

export default function LiveActivityPage() {
  const [activeAgent, setActiveAgent] = useState<string | null>(null);
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [isSimulating, setIsSimulating] = useState(false);

  // Poll for agent_trace.json
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (isSimulating) {
      interval = setInterval(async () => {
        try {
          const res = await fetch("/agent_trace.json?" + new Date().getTime());
          if (res.ok) {
            const data = await res.json();
            setEvents(data);
          }
        } catch (err) {
          console.error("Failed to fetch agent trace", err);
        }
      }, 1000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isSimulating]);

  const handleTrigger = async () => {
    setIsSimulating(false);
    setEvents([]);
    setActiveAgent(null);
    
    try {
      // Small delay to allow state to reset visually
      setTimeout(async () => {
        const response = await fetch("http://localhost:8000/api/v1/ai/trigger", {
          method: "POST"
        });
        
        if (response.ok) {
          setIsSimulating(true);
        } else {
          console.error("Failed to trigger simulation");
        }
      }, 500);
    } catch (error) {
      console.error("Error triggering AI:", error);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <PageHeader
          title="Live AI Activity"
          description="Monitor the multi-agent system executing real-time anomaly investigations and workflows."
        />
        
        <button 
          onClick={handleTrigger}
          className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-white px-4 py-2 font-bold rounded-sm border-2 border-slate-800 shadow-brutal-sm transition-all active:translate-y-1 active:shadow-none"
        >
          {isSimulating ? <RotateCcw className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          {isSimulating ? "Restart Simulation" : "Simulate Alert (Equipment Failure)"}
        </button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Left Column: Visual Decision Graph */}
        <div className="flex flex-col h-full">
          <h2 className="text-xl font-bold mb-4 font-display">System Architecture</h2>
          <div className="flex-1 bg-slate-950 rounded-xl border-2 border-slate-800 shadow-brutal-md p-4">
            <AIVisualGraph activeAgent={activeAgent} />
          </div>
        </div>

        {/* Right Column: Live Terminal */}
        <div className="flex flex-col h-full">
          <h2 className="text-xl font-bold mb-4 font-display">Agent Terminal Feed</h2>
          <div className="flex-1 shadow-brutal-md rounded-xl">
            <LiveAgentTerminal 
              events={events} 
              onActiveAgentChange={setActiveAgent} 
            />
          </div>
        </div>
      </div>
    </div>
  );
}
