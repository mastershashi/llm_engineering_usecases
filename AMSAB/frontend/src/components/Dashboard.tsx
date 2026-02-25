"use client";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Send, Play, RefreshCw, Shield, ShieldOff, Square,
  Brain, Database, Trash2, Search, ChevronRight, AlertTriangle,
} from "lucide-react";
import { api, type Plan, type TaskNode } from "@/lib/api";
import { PlanSocket } from "@/lib/websocket";
import dynamic from "next/dynamic";
import NodeInspector from "./NodeInspector";
import SandboxTerminal from "./SandboxTerminal";
import ContextHeatmap from "./ContextHeatmap";
import ThreadNavigator from "./ThreadNavigator";

const LiveGraph = dynamic(() => import("./LiveGraph"), { ssr: false });

interface LogEntry { message: string; level: string; node_id?: number; created_at: string; }
interface Permissions { read: boolean; write: boolean; network: boolean; admin: boolean; }
interface Breadcrumb { document: string; node_id: number; tool: string; ts: string; }
interface MemoryStats { short_term: number; long_term: number; }
interface LongTermResult { document: string; distance: number; key?: string; category?: string; }

const DEFAULT_PERMS: Permissions = { read: true, write: false, network: false, admin: false };

// Trust meter: counts high-risk nodes and new tools to compute hallucination risk (0-100)
function computeTrustScore(plan: Plan | null): number {
  if (!plan) return 100;
  const nodes = plan.dag.nodes;
  if (!nodes.length) return 100;
  const highRisk = nodes.filter((n) => n.risk_level === "high").length;
  const failedOrWaiting = nodes.filter(
    (n) => n.status === "failed" || n.status === "awaiting_approval"
  ).length;
  const score = Math.max(0, 100 - highRisk * 15 - failedOrWaiting * 20);
  return score;
}

function TrustMeter({ score }: { score: number }) {
  const color = score > 70 ? "#3fb950" : score > 40 ? "#d29922" : "#f85149";
  const label = score > 70 ? "Low Risk" : score > 40 ? "Moderate Risk" : "High Risk";
  return (
    <div className="px-4 py-3 border-b border-border" style={{ background: "#161b22" }}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-muted font-medium">Trust Meter / Hallucination Risk</span>
        <span className="text-xs font-bold" style={{ color }}>{label}</span>
      </div>
      <div className="w-full h-2 rounded-full overflow-hidden" style={{ background: "#30363d" }}>
        <div
          className="h-2 rounded-full transition-all duration-500"
          style={{ width: `${score}%`, background: color }}
        />
      </div>
      <p className="text-xs text-muted mt-1">
        Score {score}/100 — based on high-risk nodes and failures
      </p>
    </div>
  );
}

function MemoryVaultPanel({
  planId,
  onClose,
}: {
  planId: string;
  onClose: () => void;
}) {
  const [breadcrumbs, setBreadcrumbs] = useState<Breadcrumb[]>([]);
  const [stats, setStats] = useState<MemoryStats>({ short_term: 0, long_term: 0 });
  const [ltQuery, setLtQuery] = useState("");
  const [ltResults, setLtResults] = useState<LongTermResult[]>([]);
  const [wiping, setWiping] = useState(false);

  const load = useCallback(async () => {
    const r = await fetch(`/api/plans/${planId}/memory/session`);
    const d = await r.json();
    setBreadcrumbs(d.breadcrumbs ?? []);
    setStats(d.stats ?? { short_term: 0, long_term: 0 });
  }, [planId]);

  useEffect(() => { load(); }, [load]);

  const handleSearch = async () => {
    if (!ltQuery.trim()) return;
    const r = await fetch(`/api/memory/long-term?q=${encodeURIComponent(ltQuery)}&n=5`);
    const d = await r.json();
    setLtResults(d.results ?? []);
  };

  const handleWipeSession = async () => {
    setWiping(true);
    await fetch(`/api/plans/${planId}/memory/session`, { method: "DELETE" });
    await load();
    setWiping(false);
  };

  const handleWipeAll = async () => {
    if (!confirm("Wipe ALL memory (short-term + long-term)? This cannot be undone.")) return;
    await fetch("/api/memory/all", { method: "DELETE" });
    await load();
    setBreadcrumbs([]);
    setLtResults([]);
  };

  return (
    <div
      className="absolute inset-y-0 right-0 w-80 z-50 flex flex-col border-l border-border shadow-2xl overflow-hidden"
      style={{ background: "#161b22" }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
        <div className="flex items-center gap-2">
          <Brain size={16} className="text-blue-400" />
          <span className="text-sm font-semibold text-white">Memory Vault</span>
        </div>
        <button onClick={onClose} className="text-muted hover:text-white">✕</button>
      </div>

      {/* Stats */}
      <div className="flex gap-3 px-4 py-2 border-b border-border shrink-0">
        <div className="text-xs text-muted">
          <span className="text-white font-bold">{stats.short_term}</span> short-term
        </div>
        <div className="text-xs text-muted">
          <span className="text-white font-bold">{stats.long_term}</span> long-term
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {/* Short-term breadcrumbs */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-muted uppercase tracking-wider">
              Short-Term (Session Breadcrumbs)
            </span>
            <button
              onClick={handleWipeSession}
              disabled={wiping}
              className="text-xs flex items-center gap-1"
              style={{ color: "#f85149" }}
            >
              <Trash2 size={10} />
              {wiping ? "Wiping…" : "Wipe Session"}
            </button>
          </div>
          {breadcrumbs.length === 0 ? (
            <p className="text-xs text-muted italic">No breadcrumbs yet.</p>
          ) : (
            <div className="space-y-1.5">
              {breadcrumbs.map((b) => (
                <div
                  key={b.node_id}
                  className="rounded p-2 text-xs"
                  style={{ background: "#0d1117", border: "1px solid #30363d" }}
                >
                  <div className="flex items-center gap-1 text-blue-400 font-mono mb-1">
                    <ChevronRight size={10} />
                    Node {b.node_id} · {b.tool}
                  </div>
                  <p className="text-muted line-clamp-2">{b.document}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Long-term memory search */}
        <div>
          <span className="text-xs font-semibold text-muted uppercase tracking-wider">
            Long-Term Memory
          </span>
          <div className="flex gap-1 mt-2">
            <input
              className="flex-1 rounded px-2 py-1 text-xs"
              style={{ background: "#0d1117", border: "1px solid #30363d", color: "#e6edf3" }}
              placeholder="Search knowledge…"
              value={ltQuery}
              onChange={(e) => setLtQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
            <button
              onClick={handleSearch}
              className="p-1.5 rounded"
              style={{ background: "#30363d", color: "#58a6ff" }}
            >
              <Search size={12} />
            </button>
          </div>
          {ltResults.length > 0 && (
            <div className="mt-2 space-y-1.5">
              {ltResults.map((r, i) => (
                <div
                  key={i}
                  className="rounded p-2 text-xs"
                  style={{ background: "#0d1117", border: "1px solid #30363d" }}
                >
                  <p className="text-white">{r.document}</p>
                  <p className="text-muted mt-0.5">relevance {(1 - r.distance).toFixed(2)}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Privacy mode */}
      <div className="px-4 py-3 border-t border-border shrink-0">
        <button
          onClick={handleWipeAll}
          className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-medium"
          style={{ background: "#f8514920", color: "#f85149", border: "1px solid #f85149" }}
        >
          <Trash2 size={12} />
          Privacy Mode — Wipe All Memory
        </button>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [goalInput, setGoalInput] = useState("");
  const [plans, setPlans] = useState<Plan[]>([]);
  const [activePlanId, setActivePlanId] = useState<string | null>(null);
  const [activePlan, setActivePlan] = useState<Plan | null>(null);
  const [selectedNode, setSelectedNode] = useState<TaskNode | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [permissions, setPermissions] = useState<Permissions>(DEFAULT_PERMS);
  const [showPerms, setShowPerms] = useState(false);
  const [showMemory, setShowMemory] = useState(false);
  const [rewindWarnings, setRewindWarnings] = useState<string[]>([]);
  const [decisionSummary, setDecisionSummary] = useState<{ action: string; intent: string; logic: string } | undefined>();
  const socketRef = useRef<PlanSocket | null>(null);

  const totalTokens = activePlan?.dag.nodes.reduce((s, n) => s + n.token_usage, 0) ?? 0;
  const trustScore = computeTrustScore(activePlan);

  const completedNodes = activePlan?.dag.nodes.filter((n) => n.status === "completed").length ?? 0;
  const totalNodes = activePlan?.dag.nodes.length ?? 0;

  useEffect(() => {
    api.listPlans().then(setPlans).catch(console.error);
  }, []);

  useEffect(() => {
    socketRef.current?.disconnect();
    if (!activePlanId) return;
    const sock = new PlanSocket(activePlanId).connect();
    socketRef.current = sock;

    sock.on("*", () => {
      api.getPlan(activePlanId).then((p) => {
        setActivePlan(p);
        setPlans((prev) => prev.map((x) => (x.plan_id === p.plan_id ? p : x)));
      });
    });
    sock.on("node_awaiting", (ev) => {
      // Capture the Decision Summary (Action/Intent/Logic) for the HITL gate
      if (ev.data.decision_summary) {
        setDecisionSummary(ev.data.decision_summary as { action: string; intent: string; logic: string });
      }
    });
    sock.on("log_line", (ev) => {
      setLogs((prev) => [
        ...prev,
        {
          message: String(ev.data.line ?? ev.data.message ?? ""),
          level: String(ev.data.level ?? "info"),
          node_id: ev.data.node_id as number | undefined,
          created_at: ev.timestamp,
        },
      ]);
    });
    return () => sock.disconnect();
  }, [activePlanId]);

  const selectPlan = useCallback(async (planId: string) => {
    setActivePlanId(planId);
    setSelectedNode(null);
    setLogs([]);
    setRewindWarnings([]);
    setDecisionSummary(undefined);
    const [plan, planLogs] = await Promise.all([api.getPlan(planId), api.getLogs(planId)]);
    setActivePlan(plan);
    setLogs(planLogs);
  }, []);

  const handleSubmitGoal = async () => {
    if (!goalInput.trim()) return;
    setLoading(true);
    try {
      const plan = await api.submitGoal({ goal: goalInput, permissions });
      setPlans((prev) => [plan, ...prev]);
      await selectPlan(plan.plan_id);
      setGoalInput("");
    } catch (e) { alert(String(e)); }
    finally { setLoading(false); }
  };

  const handleApprovePlan = async () => {
    if (!activePlanId) return;
    const plan = await api.approvePlan(activePlanId);
    setActivePlan(plan);
  };

  const handleApproveNode = async (nodeId: number, editedArgs?: Record<string, unknown>) => {
    if (!activePlanId) return;
    const plan = await api.approveNode(activePlanId, nodeId, editedArgs);
    setActivePlan(plan);
    setSelectedNode(null);
  };

  const handleSkipNode = async (nodeId: number) => {
    if (!activePlanId) return;
    const plan = await api.skipNode(activePlanId, nodeId);
    setActivePlan(plan);
    setSelectedNode(null);
  };

  const handleRewindNode = async (nodeId: number) => {
    if (!activePlanId) return;
    const result = await api.rewindNode(activePlanId, nodeId);
    const branch = result.plan ?? result;
    const warnings: string[] = result.idempotency_warnings ?? [];
    setRewindWarnings(warnings);
    setPlans((prev) => [branch, ...prev]);
    await selectPlan(branch.plan_id);
    setSelectedNode(null);
  };

  const handleKillSwitch = async () => {
    if (!activePlanId) return;
    if (!confirm("Kill switch: immediately terminate all running containers for this plan?")) return;
    await fetch(`/api/plans/${activePlanId}/kill`, { method: "POST" });
  };

  const togglePerm = (key: keyof Permissions) =>
    setPermissions((p) => ({ ...p, [key]: !p[key] }));

  const statusColor: Record<string, string> = {
    draft: "#8b949e", approved: "#58a6ff", running: "#58a6ff",
    paused: "#d29922", completed: "#3fb950", failed: "#f85149",
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden" style={{ background: "#0d1117" }}>
      {/* ── Top bar ─────────────────────────────────────────────────────── */}
      <header
        className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0"
        style={{ background: "#161b22" }}
      >
        <div className="flex items-center gap-3">
          <span className="text-white font-bold text-lg tracking-tight">AMSAB</span>
          <span className="text-xs text-muted">Autonomous Multi-Step Agent Builder</span>
        </div>
        <div className="flex items-center gap-3">
          {activePlan && (
            <span className="text-xs" style={{ color: statusColor[activePlan.status] ?? "#8b949e" }}>
              ● {activePlan.status.toUpperCase()}
            </span>
          )}
          {activePlan && <ContextHeatmap usedTokens={totalTokens} />}
          {/* Memory Vault button */}
          <button
            onClick={() => setShowMemory((v) => !v)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs"
            style={{ background: "#30363d", color: "#58a6ff" }}
            title="Memory Vault"
          >
            <Brain size={13} />
            Memory
          </button>
          {/* Kill Switch */}
          {activePlan && ["running", "approved"].includes(activePlan.status) && (
            <button
              onClick={handleKillSwitch}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold"
              style={{ background: "#f85149", color: "#fff" }}
              title="Kill Switch — immediately stop all execution"
            >
              <Square size={12} />
              KILL
            </button>
          )}
        </div>
      </header>

      {/* Thread navigator */}
      {plans.length > 0 && (
        <ThreadNavigator
          plans={plans}
          activePlanId={activePlanId ?? ""}
          onSelect={selectPlan}
        />
      )}

      {/* ── Goal input ──────────────────────────────────────────────────── */}
      <div className="px-4 py-3 border-b border-border shrink-0" style={{ background: "#161b22" }}>
        <div className="flex gap-2 items-start">
          <div className="flex-1">
            <textarea
              className="w-full rounded-lg px-3 py-2 text-sm resize-none"
              rows={2}
              style={{ background: "#0d1117", border: "1px solid #30363d", color: "#e6edf3", outline: "none" }}
              placeholder="Describe your goal… e.g. 'Research top 3 AI agents in 2026 and save a summary to research.txt'"
              value={goalInput}
              onChange={(e) => setGoalInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmitGoal();
              }}
            />
          </div>
          <div className="flex flex-col gap-1">
            <button
              onClick={handleSubmitGoal}
              disabled={loading || !goalInput.trim()}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium"
              style={{ background: loading ? "#30363d" : "#58a6ff", color: "#0d1117", opacity: loading ? 0.6 : 1 }}
            >
              {loading ? <RefreshCw size={14} className="animate-spin" /> : <Send size={14} />}
              Plan
            </button>
            <button
              onClick={() => setShowPerms((v) => !v)}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs"
              style={{ background: "#30363d", color: "#8b949e" }}
            >
              <Shield size={12} />
              Perms
            </button>
          </div>
        </div>

        {/* Capability Toggles */}
        {showPerms && (
          <div className="mt-2 flex flex-wrap gap-2">
            {(Object.keys(permissions) as Array<keyof Permissions>).map((k) => (
              <button
                key={k}
                onClick={() => togglePerm(k)}
                className="flex items-center gap-1 px-2.5 py-1 rounded text-xs font-mono"
                style={{
                  background: permissions[k] ? "#3fb95022" : "#30363d",
                  color: permissions[k] ? "#3fb950" : "#8b949e",
                  border: `1px solid ${permissions[k] ? "#3fb950" : "#30363d"}`,
                }}
              >
                {permissions[k] ? <Shield size={10} /> : <ShieldOff size={10} />}
                {k}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Trust Meter */}
      {activePlan && <TrustMeter score={trustScore} />}

      {/* ── Idempotency warnings ────────────────────────────────────────── */}
      {rewindWarnings.length > 0 && (
        <div
          className="mx-4 my-2 p-3 rounded-lg text-xs flex gap-2"
          style={{ background: "#f8514915", border: "1px solid #f85149", color: "#f85149" }}
        >
          <AlertTriangle size={14} className="shrink-0 mt-0.5" />
          <div>
            <p className="font-bold mb-1">Idempotency Warning</p>
            <ul className="list-disc ml-3 space-y-0.5">
              {rewindWarnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          </div>
        </div>
      )}

      {/* ── Main area ───────────────────────────────────────────────────── */}
      <div className="flex flex-1 min-h-0 relative">
        {/* ── Left pane: Goal Tracker ─────────────────────────────────── */}
        <div className="w-56 shrink-0 border-r border-border flex flex-col" style={{ background: "#161b22" }}>
          <div className="px-3 py-2 border-b border-border">
            <span className="text-xs font-semibold text-muted uppercase tracking-wider">Goal Tracker</span>
          </div>
          {activePlan ? (
            <div className="p-3 flex flex-col gap-3">
              <p className="text-xs text-white leading-relaxed line-clamp-3">{activePlan.goal}</p>
              {/* Progress bar */}
              <div>
                <div className="flex justify-between text-xs text-muted mb-1">
                  <span>Progress</span>
                  <span className="text-white font-mono">{completedNodes}/{totalNodes}</span>
                </div>
                <div className="w-full h-2 rounded-full overflow-hidden" style={{ background: "#30363d" }}>
                  <div
                    className="h-2 rounded-full transition-all duration-500"
                    style={{
                      width: totalNodes ? `${(completedNodes / totalNodes) * 100}%` : "0%",
                      background: "#3fb950",
                    }}
                  />
                </div>
              </div>
              {/* Node status list */}
              <div className="space-y-1">
                {activePlan.dag.nodes.map((n) => {
                  const c =
                    n.status === "completed" ? "#3fb950" :
                    n.status === "running" ? "#58a6ff" :
                    n.status === "failed" ? "#f85149" :
                    n.status === "awaiting_approval" ? "#d29922" : "#8b949e";
                  return (
                    <div key={n.id} className="flex items-center gap-2 text-xs">
                      <span className="w-2 h-2 rounded-full shrink-0" style={{ background: c }} />
                      <span className="truncate text-muted">{n.task}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center p-4 text-xs text-muted text-center">
              Submit a goal to see the tracker.
            </div>
          )}
        </div>

        {/* ── Center: DAG Canvas ──────────────────────────────────────── */}
        <div className="flex flex-col flex-1 min-w-0">
          {activePlan?.status === "draft" && (
            <div
              className="flex items-center justify-between px-4 py-2 border-b border-border shrink-0"
              style={{ background: "#161b22" }}
            >
              <div className="text-sm text-muted">
                Review the plan, then click <strong className="text-white">Approve All</strong> to start.
              </div>
              <button
                onClick={handleApprovePlan}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium"
                style={{ background: "#3fb950", color: "#0d1117" }}
              >
                <Play size={14} />
                Approve All & Run
              </button>
            </div>
          )}

          <div className="flex-1 min-h-0">
            {activePlan ? (
              <LiveGraph
                nodes={activePlan.dag.nodes}
                onNodeSelect={setSelectedNode}
                onNodeEdit={(nodeId, newTask) => {
                  // Double-click edit: rewind the node with updated task description
                  // We don't have a direct "edit task" API so we rewind with a note in args
                  if (activePlanId) {
                    api.rewindNode(activePlanId, nodeId, { _edited_task: newTask }).then((result) => {
                      const branch = result.plan;
                      setPlans((prev) => [branch, ...prev]);
                      selectPlan(branch.plan_id);
                    });
                  }
                }}
              />
            ) : (
              <div className="flex items-center justify-center h-full text-center">
                <div>
                  <div className="text-4xl mb-3">🤖</div>
                  <div className="text-lg font-semibold text-white">Welcome to AMSAB</div>
                  <div className="text-sm text-muted mt-1 max-w-sm">
                    Type a goal above and click <strong className="text-white">Plan</strong> to
                    generate a visual execution graph.
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="h-48 shrink-0">
            <SandboxTerminal logs={logs} />
          </div>
        </div>

        {/* ── Right: Node Inspector ───────────────────────────────────── */}
        {selectedNode && (
          <NodeInspector
            node={selectedNode}
            decisionSummary={decisionSummary}
            onClose={() => { setSelectedNode(null); setDecisionSummary(undefined); }}
            onApprove={handleApproveNode}
            onSkip={handleSkipNode}
            onRewind={handleRewindNode}
          />
        )}

        {/* ── Memory Vault overlay panel ──────────────────────────────── */}
        {showMemory && activePlanId && (
          <MemoryVaultPanel
            planId={activePlanId}
            onClose={() => setShowMemory(false)}
          />
        )}
      </div>
    </div>
  );
}
