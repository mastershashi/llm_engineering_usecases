"use client";
import React from "react";
import { GitBranch, X } from "lucide-react";
import type { Plan } from "@/lib/api";

interface Props {
  plans: Plan[];
  activePlanId: string;
  onSelect: (planId: string) => void;
}

const STATUS_DOT: Record<string, string> = {
  draft: "#8b949e",
  approved: "#58a6ff",
  running: "#58a6ff",
  paused: "#d29922",
  completed: "#3fb950",
  failed: "#f85149",
};

export default function ThreadNavigator({ plans, activePlanId, onSelect }: Props) {
  return (
    <div
      className="flex items-center gap-1 px-2 overflow-x-auto"
      style={{ background: "#161b22", borderBottom: "1px solid #30363d", minHeight: "40px" }}
    >
      {plans.map((p) => {
        const isActive = p.plan_id === activePlanId;
        const dot = STATUS_DOT[p.status] ?? "#8b949e";
        return (
          <button
            key={p.plan_id}
            onClick={() => onSelect(p.plan_id)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs whitespace-nowrap transition-colors shrink-0"
            style={{
              background: isActive ? "#0d1117" : "transparent",
              color: isActive ? "#e6edf3" : "#8b949e",
              border: isActive ? "1px solid #30363d" : "1px solid transparent",
            }}
          >
            {p.branch_of && <GitBranch size={10} className="shrink-0" style={{ color: dot }} />}
            <span
              className="w-1.5 h-1.5 rounded-full shrink-0"
              style={{ background: dot }}
            />
            <span className="max-w-[160px] truncate">{p.goal}</span>
          </button>
        );
      })}
    </div>
  );
}
