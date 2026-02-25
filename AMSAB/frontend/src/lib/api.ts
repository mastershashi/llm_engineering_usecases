const BASE = "/api";

export interface TaskNode {
  id: number;
  task: string;
  tool: string;
  args: Record<string, unknown>;
  dependencies: number[];
  risk_level: "low" | "high";
  status: NodeStatus;
  result?: string;
  error?: string;
  token_usage: number;
  started_at?: string;
  completed_at?: string;
}

export interface TaskGraph {
  goal: string;
  nodes: TaskNode[];
  expected_outcome: string;
}

export type PlanStatus = "draft" | "approved" | "running" | "paused" | "completed" | "failed";
export type NodeStatus =
  | "pending"
  | "running"
  | "awaiting_approval"
  | "approved"
  | "completed"
  | "failed"
  | "skipped";

export interface Plan {
  plan_id: string;
  goal: string;
  status: PlanStatus;
  dag: TaskGraph;
  branch_of?: string;
  created_at: string;
  updated_at: string;
}

export interface GoalRequest {
  goal: string;
  permissions?: {
    read: boolean;
    write: boolean;
    network: boolean;
    admin: boolean;
  };
  allowed_tools?: string[];
}

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController();
  // 3-minute timeout — Ollama planning can take 30-60 s on first run
  const timer = setTimeout(() => controller.abort(), 180_000);
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    signal: controller.signal,
    ...options,
  }).finally(() => clearTimeout(timer));
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API error ${res.status}: ${err}`);
  }
  return res.json();
}

export const api = {
  submitGoal: (body: GoalRequest) =>
    req<Plan>("/goals", { method: "POST", body: JSON.stringify(body) }),

  listPlans: () => req<Plan[]>("/plans"),

  getPlan: (planId: string) => req<Plan>(`/plans/${planId}`),

  approvePlan: (planId: string) =>
    req<Plan>(`/plans/${planId}/approve`, { method: "POST" }),

  approveNode: (planId: string, nodeId: number, editedArgs?: Record<string, unknown>) =>
    req<Plan>(`/plans/${planId}/nodes/${nodeId}/approve`, {
      method: "POST",
      body: JSON.stringify({ approved: true, edited_args: editedArgs }),
    }),

  skipNode: (planId: string, nodeId: number) =>
    req<Plan>(`/plans/${planId}/nodes/${nodeId}/approve`, {
      method: "POST",
      body: JSON.stringify({ approved: false }),
    }),

  rewindNode: (planId: string, nodeId: number, newArgs?: Record<string, unknown>) =>
    req<{ plan: Plan; idempotency_warnings: string[] }>(
      `/plans/${planId}/nodes/${nodeId}/rewind`,
      { method: "POST", body: JSON.stringify({ node_id: nodeId, new_args: newArgs }) }
    ),

  killPlan: (planId: string) =>
    req<{ status: string; plan_id: string }>(`/plans/${planId}/kill`, { method: "POST" }),

  getLogs: (planId: string) =>
    req<Array<{ message: string; level: string; node_id?: number; created_at: string }>>(
      `/plans/${planId}/logs`
    ),

  memoryStats: () => req<{ short_term: number; long_term: number }>("/memory/stats"),

  recallLongTerm: (q: string, n = 5) =>
    req<{ query: string; results: unknown[] }>(`/memory/long-term?q=${encodeURIComponent(q)}&n=${n}`),

  rememberFact: (key: string, value: string, category = "general") =>
    req<{ status: string; key: string }>("/memory/long-term", {
      method: "POST",
      body: JSON.stringify({ key, value, category }),
    }),

  wipeSessionMemory: (planId: string) =>
    req<{ plan_id: string; wiped: number }>(`/plans/${planId}/memory/session`, { method: "DELETE" }),

  wipeAllMemory: () => req<{ status: string }>("/memory/all", { method: "DELETE" }),
};
