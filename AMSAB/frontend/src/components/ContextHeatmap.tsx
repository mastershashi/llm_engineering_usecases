"use client";
import React from "react";
import { Cpu } from "lucide-react";

interface Props {
  usedTokens: number;
  maxTokens?: number;
}

export default function ContextHeatmap({ usedTokens, maxTokens = 128_000 }: Props) {
  const pct = Math.min((usedTokens / maxTokens) * 100, 100);
  const color = pct < 50 ? "#3fb950" : pct < 80 ? "#d29922" : "#f85149";
  const label = pct < 50 ? "Healthy" : pct < 80 ? "Warning" : "Critical";

  return (
    <div
      className="flex items-center gap-3 px-3 py-2 rounded-lg border text-sm"
      style={{ background: "#161b22", borderColor: "#30363d" }}
    >
      <Cpu size={14} style={{ color }} />
      <div className="flex-1">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-muted">Context Window</span>
          <span style={{ color }}>{label}</span>
        </div>
        <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "#30363d" }}>
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{ width: `${pct}%`, background: color }}
          />
        </div>
        <div className="text-xs text-muted mt-0.5">
          {usedTokens.toLocaleString()} / {maxTokens.toLocaleString()} tokens
        </div>
      </div>
    </div>
  );
}
