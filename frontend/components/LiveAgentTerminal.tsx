"use client";

import React, { useEffect, useState, useRef } from "react";
import { Terminal } from "lucide-react";

export interface TraceEvent {
  id: string;
  timestamp: string;
  agent: string;
  type: "boot" | "reasoning" | "tool_execution" | "tool_result";
  tool_name?: string;
  content: string;
}

interface LiveAgentTerminalProps {
  events: TraceEvent[];
  onActiveAgentChange: (agent: string | null) => void;
}

export function LiveAgentTerminal({ events, onActiveAgentChange }: LiveAgentTerminalProps) {
  const [displayedEvents, setDisplayedEvents] = useState<TraceEvent[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);
  const sequenceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Simulating the sequential typing effect whenever events change or reset
  useEffect(() => {
    // Reset state if events is cleared (e.g., user clicked trigger again)
    if (events.length === 0) {
      setDisplayedEvents([]);
      setIsTyping(false);
      onActiveAgentChange(null);
      if (sequenceTimeoutRef.current) clearTimeout(sequenceTimeoutRef.current);
      if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
      return;
    }
    
    // We only want to animate NEW events.
    // If the backend appended more events to the list, we continue where we left off.
    let currentIndex = displayedEvents.length;
    
    const showNextEvent = () => {
      if (currentIndex >= events.length) {
        setIsTyping(false);
        // We do NOT clear active agent here so it stays highlighted on FINISH
        return;
      }
      
      const currentEvent = events[currentIndex];
      setDisplayedEvents((prev) => {
        // Prevent duplicate appending in React strict mode
        if (prev.some(e => e.id === currentEvent.id)) return prev;
        return [...prev, currentEvent];
      });
      setIsTyping(true);
      
      // Update visual graph active agent
      onActiveAgentChange(currentEvent.agent);
      
      // If it's a tool execution, simulate a longer "loading" state
      let delay = 300; 
      
      if (currentEvent.type === "tool_execution") {
        delay = 1500;
        let step = 0;
        setLoadingStep(0);
        if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
        progressIntervalRef.current = setInterval(() => {
          step += 1;
          setLoadingStep(step);
          if (step >= 5) clearInterval(progressIntervalRef.current!);
        }, 300);
      } else if (currentEvent.type === "reasoning") {
        delay = Math.max(800, Math.min(2000, currentEvent.content.length * 10)); 
      }
      
      currentIndex++;
      sequenceTimeoutRef.current = setTimeout(showNextEvent, delay);
    };
    
    // If we are already typing, don't interrupt. The next timeout will catch the new events.
    if (!isTyping && currentIndex < events.length) {
      sequenceTimeoutRef.current = setTimeout(showNextEvent, 500);
    }
    
    return () => {
      if (sequenceTimeoutRef.current) clearTimeout(sequenceTimeoutRef.current);
      if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
    };
  }, [events, displayedEvents.length, isTyping, onActiveAgentChange]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [displayedEvents, loadingStep]);

  const getAgentColor = (agent: string) => {
    switch (agent) {
      case "SYSTEM": return "text-emerald-400";
      case "SUPERVISOR": return "text-blue-400";
      case "DB_SYSTEM": return "text-yellow-400";
      case "REPORTER": return "text-purple-400";
      default: return "text-cyan-400"; // Specific worker agents
    }
  };

  const renderContent = (event: TraceEvent) => {
    if (event.type === "tool_execution") {
      const isCurrentlyLoading = isTyping && displayedEvents[displayedEvents.length - 1]?.id === event.id;
      const progressStr = isCurrentlyLoading 
        ? `[${'#'.repeat(loadingStep)}${'-'.repeat(5-loadingStep)}] ${loadingStep * 20}%` 
        : `[#####] 100%`;
        
      return (
        <span>
          <span className="text-gray-400">Executing: </span>
          <span className="text-white font-mono">{event.tool_name}({event.content})</span>
          <span className="ml-2 text-yellow-300">{progressStr}</span>
        </span>
      );
    }
    
    if (event.type === "tool_result") {
      return (
        <span className="text-gray-300 block ml-4 pl-2 border-l border-gray-700">
          {event.content}
        </span>
      );
    }

    return <span className="text-gray-100">{event.content}</span>;
  };

  return (
    <div className="flex flex-col bg-slate-950 rounded-xl border border-slate-800 shadow-2xl overflow-hidden h-[500px]">
      {/* Mac-style Terminal Header */}
      <div className="flex items-center px-4 py-3 bg-slate-900 border-b border-slate-800">
        <div className="flex space-x-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
        </div>
        <div className="mx-auto flex items-center text-slate-400 text-xs font-mono">
          <Terminal className="w-3 h-3 mr-2" />
          agent_orchestrator.py — Live Feed
        </div>
      </div>
      
      {/* Terminal Body */}
      <div 
        ref={scrollRef}
        className="p-4 flex-1 overflow-y-auto font-mono text-sm space-y-2"
        style={{ scrollBehavior: 'smooth' }}
      >
        {events.length === 0 && (
          <div className="text-gray-500 animate-pulse">Waiting for system trigger... Click "Simulate Alert" to begin.</div>
        )}
        
        {displayedEvents.map((ev, i) => (
          <div key={ev.id} className="leading-relaxed animate-in fade-in slide-in-from-bottom-2 duration-300">
            <span className="text-gray-600 mr-2 text-xs">
              [{new Date(ev.timestamp).toLocaleTimeString([], { hour12: false, second: '2-digit' })}]
            </span>
            <span className={`mr-2 font-bold ${getAgentColor(ev.agent)}`}>
              {ev.agent}:
            </span>
            {renderContent(ev)}
          </div>
        ))}
        
        {isTyping && (
          <div className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-1"></div>
        )}
      </div>
    </div>
  );
}
