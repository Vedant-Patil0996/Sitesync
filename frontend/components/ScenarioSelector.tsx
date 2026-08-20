"use client";

import React from "react";
import { AlertTriangle, AlertCircle, Info, Tag } from "lucide-react";
import type { Scenario } from "@/app/(app)/live-activity/page";

interface Props {
  scenarios: Scenario[];
  selected: Scenario | null;
  onSelect: (s: Scenario) => void;
  disabled?: boolean;
}

const SEVERITY_STYLES: Record<string, { border: string; bg: string; badge: string; icon: React.ReactNode }> = {
  critical: {
    border: "border-red-600",
    bg: "bg-red-950/30",
    badge: "bg-red-900/60 text-red-300",
    icon: <AlertTriangle className="w-3 h-3 text-red-400" />,
  },
  warning: {
    border: "border-yellow-600",
    bg: "bg-yellow-950/20",
    badge: "bg-yellow-900/50 text-yellow-300",
    icon: <AlertCircle className="w-3 h-3 text-yellow-400" />,
  },
  info: {
    border: "border-blue-700",
    bg: "bg-blue-950/20",
    badge: "bg-blue-900/50 text-blue-300",
    icon: <Info className="w-3 h-3 text-blue-400" />,
  },
};

const SELECTED_RING: Record<string, string> = {
  critical: "ring-2 ring-red-500 ring-offset-2 ring-offset-slate-950",
  warning:  "ring-2 ring-yellow-500 ring-offset-2 ring-offset-slate-950",
  info:     "ring-2 ring-blue-500 ring-offset-2 ring-offset-slate-950",
};

export function ScenarioSelector({ scenarios, selected, onSelect, disabled }: Props) {
  if (scenarios.length === 0) {
    return (
      <div className="text-slate-500 text-sm animate-pulse">Loading scenarios…</div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-bold mb-3 font-display">Select Simulation Scenario</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-3">
        {scenarios.map((s) => {
          const isSelected = selected?.id === s.id;
          const styles = SEVERITY_STYLES[s.severity] ?? SEVERITY_STYLES.info;

          return (
            <button
              key={s.id}
              onClick={() => !disabled && onSelect(s)}
              disabled={disabled}
              className={`
                group relative text-left rounded-xl border-2 p-4
                transition-all duration-200 cursor-pointer
                ${styles.border} ${styles.bg}
                ${isSelected ? SELECTED_RING[s.severity] : "opacity-70 hover:opacity-100 hover:scale-[1.02]"}
                ${disabled ? "cursor-not-allowed opacity-50" : ""}
              `}
            >
              {/* Selected indicator */}
              {isSelected && (
                <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              )}

              {/* Icon + title */}
              <div className="flex items-center gap-2 mb-2">
                <span className="text-2xl">{s.icon}</span>
                <span className="font-bold text-white text-sm leading-tight">{s.label}</span>
              </div>

              {/* Description */}
              <p className="text-slate-400 text-xs leading-relaxed mb-3">
                {s.description}
              </p>

              {/* Footer: severity badge + tags */}
              <div className="flex flex-wrap gap-1.5 items-center">
                <span className={`flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${styles.badge}`}>
                  {styles.icon}
                  {s.severity}
                </span>
                {s.tags.map((tag) => (
                  <span key={tag} className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">
                    <Tag className="w-2.5 h-2.5" />
                    {tag}
                  </span>
                ))}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
