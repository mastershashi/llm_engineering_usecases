"use client";
import React, { useState } from "react";
import { X, Clock, Cpu, Target, Lightbulb, GitBranch } from "lucide-react";
import type { TaskNode } from "@/lib/api";

interface DecisionSummary {
  action: string;
  intent: string;
  logic: string;
}

interface Props {
  node: TaskNode | null;
  decisionSummary?: DecisionSummary;
  onClose: () => void;
  onApprove: (nodeId: number, editedArgs?: Record<string, unknown>) => void;
  onSkip: (nodeId: number) => void;
  onRewind: (nodeId: number) => void;
}

function SummaryRow({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex gap-3">
      <div className="shrink-0 mt-0.5 text-muted">{icon}</div>
      <div>
        <div className="text-xs font-semibold text-muted uppercase tracking-wider mb-0.5">{label}</div>
        <div className="text-sm text-white leading-snug">{value}</div>
      </div>
    </div>
  );
}

export default function NodeInspector({
  node, decisionSummary, onClose, onApprove, onSkip, onRewind,
}: Props) {
  const [view, setView] = useState<"dev" | "business">("dev");
  const [editedArgs, setEditedArgs] = useState("");
  const [argsError, setArgsError] = useState("");

  if (!node) return null;

  const isAwaitingApproval = node.status === "awaiting_approval";
  const isCompleted = node.status === "completed";
  const isFailed = node.status === "failed";
  const isGhosted = isFailed || node.status === "skipped";

  const handleApprove = () => {
    try {
      const args = editedArgs ? JSON.parse(editedArgs) : undefined;
      onApprove(node.id, args);
      setArgsError("");
    } catch {
      setArgsError("Invalid JSON — please fix before approving.");
    }
  };

  return (
    <div
      className="fixed right-0 top-0 h-full w-[420px] z-50 flex flex-col overflow-hidden"
      style={{
        background: "#161b22",
        borderLeft: "1px solid #30363d",
        opacity: isGhosted ? 0.85 : 1,
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
        <div>
          <div className="text-xs text-muted font-mono">Node #{node.id}</div>
          <div className="font-semibold text-white">{node.tool}</div>
          {isGhosted && (
            <div className="text-xs mt-0.5" style={{ color: "#f85149" }}>
              — Original (ghosted) path —
            </div>
          )}
        </div>
        <button onClick={onClose} className="text-muted hover:text-white">
          <X size={18} />
        </button>
      </div>

      {/* View toggle */}
      <div className="flex border-b border-border shrink-0">
        {(["dev", "business"] as const).map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            className="flex-1 py-2 text-sm capitalize transition-colors"
            style={{
              color: view === v ? "#58a6ff" : "#8b949e",
              borderBottom: view === v ? "2px solid #58a6ff" : "2px solid transparent",
            }}
          >
            {v === "dev" ? "Developer" : "Business"} View
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div>
          <div className="text-xs text-muted mb-1">Task</div>
          <div className="text-sm text-white">{node.task}</div>
        </div>

        {view === "dev" ? (
          <>
            <div>
              <div className="text-xs text-muted mb-1">Input Args</div>
              <pre className="text-xs rounded p-2 overflow-x-auto" style={{ background: "#0d1117" }}>
                {JSON.stringify(node.args, null, 2)}
              </pre>
            </div>
            {(isCompleted || isFailed) && (
              <div>
                <div className="text-xs text-muted mb-1">{isFailed ? "Error" : "Output"}</div>
                <pre
                  className="text-xs rounded p-2 overflow-x-auto max-h-48"
                  style={{ background: "#0d1117", color: isFailed ? "#f85149" : "#3fb950" }}
                >
                  {node.result || node.error || "—"}
                </pre>
              </div>
            )}
            <div className="flex gap-4 text-xs text-muted">
              <span className="flex items-center gap-1">
                <Cpu size={12} /> {node.token_usage} tokens
              </span>
              {node.started_at && (
                <span className="flex items-center gap-1">
                  <Clock size={12} /> {new Date(node.started_at).toLocaleTimeString()}
                </span>
              )}
            </div>
          </>
        ) : (
          <div className="text-sm text-white leading-relaxed">
            {isCompleted
              ? `Completed. The "${node.tool}" tool was used to: ${node.task}`
              : isFailed
              ? `Failed. Error: ${node.error?.slice(0, 200)}`
              : `Will use "${node.tool}" to: ${node.task}`}
          </div>
        )}

        {/* ── HITL Decision Summary Card ─────────────────────────────── */}
        {isAwaitingApproval && (
          <div
            className="rounded-lg p-4 border space-y-4"
            style={{ background: "#d2992211", borderColor: "#d29922" }}
          >
            <div className="text-sm font-bold" style={{ color: "#d29922" }}>
              ⚠ Human Approval Required
            </div>

            {/* Decision Summary — Action / Intent / Logic */}
            {decisionSummary ? (
              <div className="space-y-3">
                <SummaryRow
                  icon={<Target size={14} />}
                  label="The Action"
                  value={decisionSummary.action}
                />
                <SummaryRow
                  icon={<Lightbulb size={14} />}
                  label="The Intent"
                  value={decisionSummary.intent}
                />
                <SummaryRow
                  icon={<GitBranch size={14} />}
                  label="The Logic"
                  value={decisionSummary.logic}
                />
              </div>
            ) : (
              <p className="text-xs text-muted">
                This is a <strong className="text-white">high-risk</strong> operation. Review
                and optionally edit the arguments below before approving.
              </p>
            )}

            {/* Correction Mode — editable args */}
            <div>
              <div className="text-xs text-muted mb-1">
                Correction Mode — edit args before approving (JSON):
              </div>
              <textarea
                className="w-full text-xs font-mono rounded p-2 resize-none"
                rows={4}
                style={{ background: "#0d1117", border: "1px solid #30363d", color: "#e6edf3" }}
                placeholder={JSON.stringify(node.args, null, 2)}
                value={editedArgs}
                onChange={(e) => setEditedArgs(e.target.value)}
              />
              {argsError && <div className="text-xs mt-1" style={{ color: "#f85149" }}>{argsError}</div>}
            </div>

            {/* Approve / Veto / Skip */}
            <div className="flex gap-2">
              <button
                onClick={handleApprove}
                className="flex-1 py-2 rounded text-sm font-medium"
                style={{ background: "#3fb950", color: "#0d1117" }}
              >
                ✅ Approve
              </button>
              <button
                onClick={() => {
                  const confirmed = confirm(
                    "Veto: the agent will abandon this branch and try a different path. Continue?"
                  );
                  if (confirmed) onSkip(node.id);
                }}
                className="flex-1 py-2 rounded text-sm font-medium"
                style={{ background: "#f8514922", color: "#f85149", border: "1px solid #f85149" }}
              >
                ❌ Veto
              </button>
            </div>
          </div>
        )}

        {/* Time-travel */}
        {(isCompleted || isFailed) && (
          <button
            onClick={() => onRewind(node.id)}
            className="w-full py-2 rounded text-sm font-medium border"
            style={{ borderColor: "#58a6ff", color: "#58a6ff", background: "transparent" }}
          >
            ⏪ Rewind & Fork from here
          </button>
        )}
      </div>
    </div>
  );
}
