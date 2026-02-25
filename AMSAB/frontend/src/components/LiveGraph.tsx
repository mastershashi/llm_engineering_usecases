"use client";
import React, { useCallback, useEffect, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeTypes,
  type NodeMouseHandler,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { type TaskNode, type NodeStatus } from "@/lib/api";

const STATUS_COLOR: Record<NodeStatus, string> = {
  pending: "#30363d",
  running: "#58a6ff",
  awaiting_approval: "#d29922",
  approved: "#58a6ff",
  completed: "#3fb950",
  failed: "#f85149",
  skipped: "#8b949e",
};

// Ghosted (branch-comparison) opacity for failed/skipped original paths
const STATUS_OPACITY: Record<NodeStatus, number> = {
  pending: 1,
  running: 1,
  awaiting_approval: 1,
  approved: 1,
  completed: 1,
  failed: 0.35,   // ghosted — failed original path
  skipped: 0.35,
};

interface NodeData extends TaskNode {
  onSelect: (n: TaskNode) => void;
  onDoubleClick: (n: TaskNode) => void;
}

function TaskNodeCard({ data }: { data: NodeData }) {
  const color = STATUS_COLOR[data.status] ?? "#30363d";
  const opacity = STATUS_OPACITY[data.status] ?? 1;
  const isRunning = data.status === "running";
  const isAwaiting = data.status === "awaiting_approval";
  const isFailed = data.status === "failed";

  return (
    <div
      onClick={() => data.onSelect(data)}
      onDoubleClick={(e) => { e.stopPropagation(); data.onDoubleClick(data); }}
      className="cursor-pointer rounded-lg border-2 p-3 min-w-[180px] max-w-[240px] transition-all"
      title="Click to inspect · Double-click to edit"
      style={{
        background: "#161b22",
        borderColor: color,
        opacity,
        boxShadow: isRunning
          ? `0 0 14px ${color}99`
          : isAwaiting
          ? `0 0 10px ${color}77`
          : isFailed
          ? `0 0 8px ${color}44`
          : "none",
        // Ghosted failed nodes get a dashed border
        borderStyle: isFailed || data.status === "skipped" ? "dashed" : "solid",
      }}
    >
      <div className="flex items-center justify-between mb-1 gap-2">
        <span className="text-xs font-mono text-muted">#{data.id}</span>
        <span
          className="text-xs px-1.5 py-0.5 rounded font-mono"
          style={{ background: `${color}22`, color }}
        >
          {data.status}
        </span>
      </div>
      <div className="text-sm font-medium text-white leading-tight mb-1 line-clamp-2">
        {data.task}
      </div>
      <div className="flex items-center gap-1 mt-1">
        <span className="text-xs text-muted font-mono">{data.tool}</span>
        {data.risk_level === "high" && (
          <span className="text-xs px-1 rounded" style={{ background: "#f8514922", color: "#f85149" }}>
            ⚠ HIGH
          </span>
        )}
      </div>
      {isRunning && (
        <div className="mt-2 h-0.5 rounded bg-border overflow-hidden">
          <div className="h-full bg-accent animate-pulse rounded" style={{ width: "60%" }} />
        </div>
      )}
      {/* Ghosted label for failed/skipped nodes in comparison */}
      {(isFailed || data.status === "skipped") && (
        <div className="mt-1 text-xs text-center" style={{ color: "#f85149" }}>
          — original path —
        </div>
      )}
    </div>
  );
}

const nodeTypes: NodeTypes = { taskNode: TaskNodeCard as any };

interface EditNodeModalProps {
  node: TaskNode;
  onSave: (nodeId: number, newTask: string) => void;
  onClose: () => void;
}

function EditNodeModal({ node, onSave, onClose }: EditNodeModalProps) {
  const [taskText, setTaskText] = useState(node.task);
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: "#00000088" }}>
      <div
        className="rounded-xl p-5 w-[420px] shadow-2xl border border-border"
        style={{ background: "#161b22" }}
      >
        <h3 className="text-sm font-semibold text-white mb-1">Edit Node #{node.id} Prompt</h3>
        <p className="text-xs text-muted mb-3">
          Change this sub-task description. The new prompt will be sent to the Worker agent.
        </p>
        <textarea
          className="w-full rounded-lg px-3 py-2 text-sm resize-none mb-3"
          rows={4}
          style={{ background: "#0d1117", border: "1px solid #30363d", color: "#e6edf3", outline: "none" }}
          value={taskText}
          onChange={(e) => setTaskText(e.target.value)}
          autoFocus
        />
        <div className="flex gap-2 justify-end">
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg text-xs"
            style={{ background: "#30363d", color: "#8b949e" }}
          >
            Cancel
          </button>
          <button
            onClick={() => { onSave(node.id, taskText); onClose(); }}
            className="px-3 py-1.5 rounded-lg text-xs font-medium"
            style={{ background: "#58a6ff", color: "#0d1117" }}
          >
            Save & Replan
          </button>
        </div>
      </div>
    </div>
  );
}

interface Props {
  nodes: TaskNode[];
  onNodeSelect: (node: TaskNode) => void;
  onNodeEdit?: (nodeId: number, newTask: string) => void;
}

export default function LiveGraph({ nodes, onNodeSelect, onNodeEdit }: Props) {
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState<Node>([]);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [editingNode, setEditingNode] = useState<TaskNode | null>(null);

  const handleDoubleClick = useCallback((node: TaskNode) => {
    setEditingNode(node);
  }, []);

  useEffect(() => {
    const COLS = 3;
    const H_GAP = 280;
    const V_GAP = 160;

    const flowNodes: Node[] = nodes.map((n, i) => ({
      id: String(n.id),
      type: "taskNode",
      position: { x: (i % COLS) * H_GAP, y: Math.floor(i / COLS) * V_GAP },
      data: { ...n, onSelect: onNodeSelect, onDoubleClick: handleDoubleClick },
    }));

    const flowEdges: Edge[] = nodes.flatMap((n) =>
      n.dependencies.map((dep) => {
        const sourceNode = nodes.find((x) => x.id === dep);
        const isFailed = n.status === "failed" || n.status === "skipped";
        const isRunning = n.status === "running";
        return {
          id: `${dep}-${n.id}`,
          source: String(dep),
          target: String(n.id),
          animated: isRunning,
          style: {
            stroke: isFailed
              ? "#f8514955"   // ghosted red dashed for failed paths
              : isRunning
              ? "#58a6ff"
              : sourceNode?.status === "completed"
              ? "#3fb95066"
              : "#30363d",
            strokeWidth: isFailed ? 1 : 2,
            strokeDasharray: isFailed ? "6 4" : undefined,
            opacity: isFailed ? 0.4 : 1,
          },
        };
      })
    );

    setRfNodes(flowNodes);
    setRfEdges(flowEdges);
  }, [nodes, onNodeSelect, handleDoubleClick, setRfNodes, setRfEdges]);

  return (
    <div style={{ width: "100%", height: "100%", position: "relative" }}>
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#30363d" gap={24} />
        <Controls style={{ background: "#161b22", border: "1px solid #30363d" }} />
        <MiniMap
          nodeColor={(n) => STATUS_COLOR[(n.data as TaskNode).status] ?? "#30363d"}
          style={{ background: "#0d1117", border: "1px solid #30363d" }}
        />
      </ReactFlow>

      {/* Double-click edit modal */}
      {editingNode && (
        <EditNodeModal
          node={editingNode}
          onSave={(id, task) => onNodeEdit?.(id, task)}
          onClose={() => setEditingNode(null)}
        />
      )}
    </div>
  );
}
