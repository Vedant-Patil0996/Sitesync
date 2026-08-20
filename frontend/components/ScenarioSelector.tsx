"use client";

import React from "react";
import { Zap, Package, TrendingDown, Calendar, TrendingUp, Globe, ShieldAlert, CheckCircle2 } from "lucide-react";
import type { Scenario } from "@/app/(app)/live-activity/page";

interface Props {
  scenarios: Scenario[];
  selected: Scenario | null;
  onSelect: (s: Scenario) => void;
  disabled?: boolean;
}

// Map scenario id -> lucide icon
const SCENARIO_ICON: Record<string, React.ReactNode> = {
  equipment_critical_failure: <Zap className="w-5 h-5" />,
  stock_critically_low:       <Package className="w-5 h-5" />,
  budget_overrun:             <TrendingDown className="w-5 h-5" />,
  task_delay_cascade:         <Calendar className="w-5 h-5" />,
  vendor_price_spike:         <TrendingUp className="w-5 h-5" />,
  multi_site_cascade:         <Globe className="w-5 h-5" />,
  safety_violation:           <ShieldAlert className="w-5 h-5" />,
};

const SEVERITY_CONFIG: Record<string, {
  glow: string;
  border: string;
  activeBorder: string;
  badge: string;
  iconBg: string;
  iconColor: string;
  dot: string;
}> = {
  critical: {
    glow:        "hover:shadow-[0_0_24px_rgba(239,68,68,0.25)]",
    border:      "border-slate-700",
    activeBorder:"border-red-500 shadow-[0_0_24px_rgba(239,68,68,0.3)]",
    badge:       "bg-red-950 text-red-400 border border-red-800",
    iconBg:      "bg-red-950/60",
    iconColor:   "text-red-400",
    dot:         "bg-red-500",
  },
  warning: {
    glow:        "hover:shadow-[0_0_24px_rgba(234,179,8,0.2)]",
    border:      "border-slate-700",
    activeBorder:"border-yellow-500 shadow-[0_0_24px_rgba(234,179,8,0.25)]",
    badge:       "bg-yellow-950 text-yellow-400 border border-yellow-800",
    iconBg:      "bg-yellow-950/60",
    iconColor:   "text-yellow-400",
    dot:         "bg-yellow-400",
  },
  info: {
    glow:        "hover:shadow-[0_0_24px_rgba(59,130,246,0.2)]",
    border:      "border-slate-700",
    activeBorder:"border-blue-500 shadow-[0_0_24px_rgba(59,130,246,0.25)]",
    badge:       "bg-blue-950 text-blue-400 border border-blue-800",
    iconBg:      "bg-blue-950/60",
    iconColor:   "text-blue-400",
    dot:         "bg-blue-400",
  },
};

export function ScenarioSelector({ scenarios, selected, onSelect, disabled }: Props) {
  if (scenarios.length === 0) {
    return (
      <div className="flex items-center gap-2 text-slate-500 text-sm py-2">
        <span className="animate-spin inline-block w-3 h-3 border border-slate-600 border-t-slate-400 rounded-full" />
        Loading scenarios…
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xl font-bold font-display">Select Simulation Scenario</h2>
        <span className="text-xs text-slate-500 font-mono">{scenarios.length} scenarios available</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-3">
        {scenarios.map((s) => {
          const isSelected = selected?.id === s.id;
          const cfg = SEVERITY_CONFIG[s.severity] ?? SEVERITY_CONFIG.info;
          const icon = SCENARIO_ICON[s.id];

          return (
            <button
              key={s.id}
              onClick={() => !disabled && onSelect(s)}
              disabled={disabled}
              className={`
                group relative text-left rounded-xl border bg-slate-900
                transition-all duration-200
                ${disabled ? "cursor-not-allowed opacity-40" : "cursor-pointer"}
                ${isSelected ? cfg.activeBorder : `${cfg.border} ${!disabled ? cfg.glow : ""} hover:border-slate-500`}
              `}
            >
              {/* Selected pulse dot */}
              {isSelected && (
                <span className={`absolute top-3 right-3 w-2 h-2 rounded-full ${cfg.dot} animate-pulse`} />
              )}
              {isSelected && (
                <span className="absolute top-3 right-3 w-2 h-2 rounded-full bg-white/30 scale-150 animate-ping" />
              )}

              <div className="p-4">
                {/* Icon + title row */}
                <div className="flex items-start gap-3 mb-3">
                  <div className={`shrink-0 p-2 rounded-lg ${cfg.iconBg} ${cfg.iconColor}`}>
                    {icon ?? <span className="text-lg">{s.icon}</span>}
                  </div>
                  <div className="min-w-0">
                    <p className="font-bold text-white text-sm leading-snug">{s.label}</p>
                    <span className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full mt-1 uppercase tracking-wider ${cfg.badge}`}>
                      {s.severity}
                    </span>
                  </div>
                </div>

                {/* Description */}
                <p className="text-slate-400 text-xs leading-relaxed mb-3">
                  {s.description}
                </p>

                {/* Tags */}
                <div className="flex flex-wrap gap-1">
                  {s.tags.map((tag) => (
                    <span
                      key={tag}
                      className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700 font-mono"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              </div>

              {/* Selected footer bar */}
              {isSelected && (
                <div className={`flex items-center gap-1.5 px-4 py-2 border-t ${cfg.activeBorder.includes("red") ? "border-red-900/50 bg-red-950/20" : cfg.activeBorder.includes("yellow") ? "border-yellow-900/50 bg-yellow-950/20" : "border-blue-900/50 bg-blue-950/20"}`}>
                  <CheckCircle2 className={`w-3 h-3 ${cfg.iconColor}`} />
                  <span className={`text-[10px] font-bold uppercase tracking-wider ${cfg.iconColor}`}>Selected — ready to run</span>
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
