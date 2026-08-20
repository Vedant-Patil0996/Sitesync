"use client";

import React, { useEffect, useState } from "react";
import { 
  Bot, Server, BrainCircuit, Activity, Wrench, 
  Package, FolderKanban, Wallet, ShoppingCart, FileText
} from "lucide-react";

interface NodeProps {
  label: string;
  icon: React.ElementType;
  isActive: boolean;
  colorClass: string;
  top: string;
  left: string;
}

const GraphNode = ({ label, icon: Icon, isActive, colorClass, top, left }: NodeProps) => {
  // Unicode spinner frames for active state
  const spinnerFrames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
  const [frame, setFrame] = useState(0);

  useEffect(() => {
    if (!isActive) return;
    const interval = setInterval(() => {
      setFrame(f => (f + 1) % spinnerFrames.length);
    }, 80);
    return () => clearInterval(interval);
  }, [isActive]);

  // Map colorClass to actual tailwind border/shadow classes to avoid dynamic construction issues
  const highlightClasses = {
    'text-emerald-400': 'border-emerald-500 shadow-[0_0_20px_rgba(0,0,0,0.5)] shadow-emerald-500/40 z-20',
    'text-blue-400': 'border-blue-500 shadow-[0_0_20px_rgba(0,0,0,0.5)] shadow-blue-500/40 z-20',
    'text-cyan-400': 'border-cyan-500 shadow-[0_0_20px_rgba(0,0,0,0.5)] shadow-cyan-500/40 z-20',
    'text-purple-400': 'border-purple-500 shadow-[0_0_20px_rgba(0,0,0,0.5)] shadow-purple-500/40 z-20',
    'text-yellow-400': 'border-yellow-500 shadow-[0_0_20px_rgba(0,0,0,0.5)] shadow-yellow-500/40 z-20'
  }[colorClass] || 'border-slate-500 shadow-slate-500/40 z-20';

  return (
    <div 
      className={`absolute flex flex-col items-center justify-center p-3 w-[140px] rounded-xl border-2 transition-all duration-300 ease-in-out transform -translate-x-1/2 -translate-y-1/2 z-10 bg-slate-900 ${
        isActive 
          ? `scale-110 ${highlightClasses}` 
          : 'border-slate-800 opacity-70 hover:opacity-100'
      }`}
      style={{ top, left }}
    >
      <div className={`relative p-2 rounded-full mb-1 ${isActive ? 'bg-slate-800 animate-pulse' : 'bg-slate-800/50'}`}>
        <Icon className={`w-6 h-6 ${isActive ? colorClass : 'text-slate-500'}`} />
        {isActive && (
          <div className={`absolute -top-2 -right-2 text-xs font-mono font-bold ${colorClass}`}>
            {spinnerFrames[frame]}
          </div>
        )}
      </div>
      <span className={`text-[11px] font-bold text-center leading-tight ${isActive ? 'text-white' : 'text-slate-400'}`}>
        {label}
      </span>
    </div>
  );
};

// Component for a connecting edge
const Edge = ({ x1, y1, x2, y2, isActive, color }: { x1: string, y1: string, x2: string, y2: string, isActive: boolean, color: string }) => (
  <g>
    {/* Base line */}
    <line 
      x1={x1} y1={y1} x2={x2} y2={y2} 
      stroke="#1e293b" 
      strokeWidth="3" 
    />
    {/* Active animated line */}
    {isActive && (
      <line 
        x1={x1} y1={y1} x2={x2} y2={y2} 
        stroke={color} 
        strokeWidth="3" 
        className="animate-pulse"
        strokeDasharray="8 8"
      >
        <animate attributeName="stroke-dashoffset" values="16;0" dur="0.5s" repeatCount="indefinite" />
      </line>
    )}
  </g>
);

export function AIVisualGraph({ activeAgent }: { activeAgent: string | null }) {
  const isSys = activeAgent === 'SYSTEM';
  const isSup = activeAgent === 'SUPERVISOR';
  const isEquip = activeAgent === 'EQUIPMENT_AGENT';
  const isStock = activeAgent === 'STOCK_AGENT';
  const isProj = activeAgent === 'PROJECT_AGENT';
  const isBudg = activeAgent === 'BUDGET_AGENT';
  const isProc = activeAgent === 'PROCUREMENT_AGENT';
  const isRep = activeAgent === 'REPORTER';
  const isDb = activeAgent === 'DB_SYSTEM';

  // Any worker agent active means we're in the middle of processing
  const anyWorkerActive = isEquip || isStock || isProj || isBudg || isProc;

  return (
    <div className="relative w-full h-[600px] bg-slate-950 overflow-hidden font-sans select-none">
      
      {/* SVG Edges Layer */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none">
        <defs>
          {/* Subtle grid background pattern */}
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#0f172a" strokeWidth="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
        
        {/* Connection from Anomaly Detector to Supervisor */}
        <Edge x1="50%" y1="12%" x2="50%" y2="30%" isActive={isSup || anyWorkerActive || isRep} color="#3b82f6" />
        
        {/* Connections from Supervisor to Workers */}
        <Edge x1="50%" y1="30%" x2="15%" y2="55%" isActive={isEquip} color="#22d3ee" />
        <Edge x1="50%" y1="30%" x2="32.5%" y2="55%" isActive={isStock} color="#22d3ee" />
        <Edge x1="50%" y1="30%" x2="50%" y2="55%" isActive={isProj} color="#22d3ee" />
        <Edge x1="50%" y1="30%" x2="67.5%" y2="55%" isActive={isBudg} color="#22d3ee" />
        <Edge x1="50%" y1="30%" x2="85%" y2="55%" isActive={isProc} color="#22d3ee" />

        {/* Connections from Workers to Reporter (Convergence) */}
        <Edge x1="15%" y1="55%" x2="40%" y2="85%" isActive={isRep && isEquip} color="#a855f7" />
        <Edge x1="32.5%" y1="55%" x2="40%" y2="85%" isActive={isRep} color="#a855f7" />
        <Edge x1="50%" y1="55%" x2="40%" y2="85%" isActive={isRep} color="#a855f7" />
        <Edge x1="67.5%" y1="55%" x2="40%" y2="85%" isActive={isRep} color="#a855f7" />
        <Edge x1="85%" y1="55%" x2="40%" y2="85%" isActive={isRep} color="#a855f7" />

        {/* Database Connection */}
        <Edge x1="80%" y1="85%" x2="50%" y2="55%" isActive={isDb} color="#facc15" />
      </svg>

      {/* Nodes Layer */}
      <GraphNode label="Anomaly Detector" icon={Activity} isActive={isSys} colorClass="text-emerald-400" top="12%" left="50%" />
      
      <GraphNode label="Supervisor Agent" icon={BrainCircuit} isActive={isSup} colorClass="text-blue-400" top="30%" left="50%" />
      
      {/* Workers Row */}
      <GraphNode label="Equipment" icon={Wrench} isActive={isEquip} colorClass="text-cyan-400" top="55%" left="15%" />
      <GraphNode label="Stock" icon={Package} isActive={isStock} colorClass="text-cyan-400" top="55%" left="32.5%" />
      <GraphNode label="Project" icon={FolderKanban} isActive={isProj} colorClass="text-cyan-400" top="55%" left="50%" />
      <GraphNode label="Budget" icon={Wallet} isActive={isBudg} colorClass="text-cyan-400" top="55%" left="67.5%" />
      <GraphNode label="Procurement" icon={ShoppingCart} isActive={isProc} colorClass="text-cyan-400" top="55%" left="85%" />

      {/* Bottom Nodes */}
      <GraphNode label="Master Reporter" icon={FileText} isActive={isRep} colorClass="text-purple-400" top="85%" left="40%" />
      <GraphNode label="Database & Tools" icon={Server} isActive={isDb} colorClass="text-yellow-400" top="85%" left="80%" />

    </div>
  );
}
