"use client";
import React, { useEffect, useRef } from "react";
import { Terminal } from "lucide-react";

interface LogEntry {
  message: string;
  level: string;
  node_id?: number;
  created_at: string;
}

interface Props {
  logs: LogEntry[];
}

export default function SandboxTerminal({ logs }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const levelColor = (level: string) => {
    if (level === "error") return "#f85149";
    if (level === "warn") return "#d29922";
    return "#3fb950";
  };

  return (
    <div
      className="flex flex-col h-full"
      style={{ background: "#0d1117", borderTop: "1px solid #30363d" }}
    >
      <div
        className="flex items-center gap-2 px-3 py-2 border-b border-border text-xs text-muted"
        style={{ background: "#161b22" }}
      >
        <Terminal size={12} />
        <span className="font-mono">Sandbox Terminal</span>
      </div>
      <div className="flex-1 overflow-y-auto p-3 font-mono text-xs space-y-0.5">
        {logs.length === 0 && (
          <div className="text-muted">Waiting for execution logs…</div>
        )}
        {logs.map((log, i) => (
          <div key={i} className="flex gap-2 leading-5">
            <span className="shrink-0" style={{ color: "#8b949e" }}>
              {log.node_id != null ? `[N${log.node_id}]` : "[SYS]"}
            </span>
            <span style={{ color: levelColor(log.level) }}>{log.message}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
