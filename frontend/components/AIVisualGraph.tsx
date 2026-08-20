"use client";

import React from "react";
import { 
  Bot, Server, BrainCircuit, Activity, Wrench, 
  Package, FolderKanban, Wallet, ShoppingCart, FileText,
  ArrowRight
} from "lucide-react";

interface NodeProps {
  label: string;
  icon: React.ElementType;
  isActive: boolean;
  colorClass: string;
}

const GraphNode = ({ label, icon: Icon, isActive, colorClass }: NodeProps) => (
  <div className={`flex flex-col items-center justify-center p-4 rounded-xl border-2 transition-all duration-500 ease-in-out ${
    isActive 
      ? `scale-110 shadow-lg shadow-${colorClass.split('-')[1]}/50 border-${colorClass.split('-')[1]}-500 bg-slate-800` 
      : 'border-slate-800 bg-slate-900 opacity-60'
  }`}>
    <div className={`p-3 rounded-full mb-2 ${isActive ? 'bg-slate-700 animate-pulse' : 'bg-slate-800'}`}>
      <Icon className={`w-8 h-8 ${isActive ? colorClass : 'text-slate-500'}`} />
    </div>
    <span className={`text-sm font-bold ${isActive ? 'text-white' : 'text-slate-400'}`}>{label}</span>
  </div>
);

export function AIVisualGraph({ activeAgent }: { activeAgent: string | null }) {
  
  // Helper to determine active state
  const isSys = activeAgent === 'SYSTEM';
  const isSup = activeAgent === 'SUPERVISOR';
  const isEquip = activeAgent === 'EQUIPMENT_AGENT';
  const isStock = activeAgent === 'STOCK_AGENT';
  const isProj = activeAgent === 'PROJECT_AGENT';
  const isBudg = activeAgent === 'BUDGET_AGENT';
  const isProc = activeAgent === 'PROCUREMENT_AGENT';
  const isRep = activeAgent === 'REPORTER';
  const isDb = activeAgent === 'DB_SYSTEM';

  return (
    <div className="w-full bg-slate-950 rounded-xl border border-slate-800 p-8 flex flex-col items-center justify-center min-h-[500px]">
      
      {/* Top level: Ingestion */}
      <div className="flex w-full justify-center mb-12">
        <GraphNode label="Anomaly Detector" icon={Activity} isActive={isSys} colorClass="text-emerald-400" />
      </div>
      
      {/* Middle level: Supervisor */}
      <div className="flex w-full justify-center mb-12 relative">
        <GraphNode label="Supervisor Agent" icon={BrainCircuit} isActive={isSup} colorClass="text-blue-400" />
      </div>

      {/* Domain Agents Level */}
      <div className="flex w-full justify-center gap-6 mb-12 flex-wrap">
        <GraphNode label="Equipment" icon={Wrench} isActive={isEquip} colorClass="text-cyan-400" />
        <GraphNode label="Stock" icon={Package} isActive={isStock} colorClass="text-cyan-400" />
        <GraphNode label="Project" icon={FolderKanban} isActive={isProj} colorClass="text-cyan-400" />
        <GraphNode label="Budget" icon={Wallet} isActive={isBudg} colorClass="text-cyan-400" />
        <GraphNode label="Procurement" icon={ShoppingCart} isActive={isProc} colorClass="text-cyan-400" />
      </div>

      {/* Bottom Level: Reporter & Database */}
      <div className="flex w-full justify-between items-center px-12 mt-4">
        <GraphNode label="Master Reporter" icon={FileText} isActive={isRep} colorClass="text-purple-400" />
        <GraphNode label="Database / Tools" icon={Server} isActive={isDb} colorClass="text-yellow-400" />
      </div>

    </div>
  );
}
