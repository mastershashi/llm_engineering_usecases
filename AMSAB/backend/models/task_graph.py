"""Pydantic models for the AMSAB task graph (DAG)."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    low = "low"
    high = "high"


class NodeStatus(str, Enum):
    pending = "pending"
    running = "running"
    awaiting_approval = "awaiting_approval"
    approved = "approved"
    completed = "completed"
    failed = "failed"
    skipped = "skipped"


class PlanStatus(str, Enum):
    draft = "draft"              # DAG generated, not yet approved by user
    approved = "approved"        # User approved, ready to execute
    running = "running"
    paused = "paused"            # HITL gate triggered
    completed = "completed"
    failed = "failed"


AVAILABLE_TOOLS = [
    "web_search",       # search the web; args: {query}
    "scraper",          # fetch full page content; args: {url}
    "python_interpreter",  # run Python code; args: {code} — code must use print()
    "filesystem_read",  # read a file; args: {path}
    "filesystem_write", # write a file; args: {filename, content}
    "filesystem_delete",
    "gmail_draft",      # draft an email; args: {to, subject, body}
    "gmail_send",
    "shell_exec",       # run a shell command; args: {command}
    "mcp_generic",      # call MCP server (only if server URL known); args: {server, method, params}
]


class TaskNode(BaseModel):
    id: int
    task: str = Field(..., description="Human-readable description of what this node does")
    tool: str = Field(..., description="Tool to use from the available registry")
    args: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[int] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.low

    # Runtime fields (populated during execution)
    status: NodeStatus = NodeStatus.pending
    result: str | None = None
    error: str | None = None
    token_usage: int = 0
    started_at: str | None = None
    completed_at: str | None = None


class TaskGraph(BaseModel):
    goal: str
    nodes: list[TaskNode]
    expected_outcome: str

    def get_node(self, node_id: int) -> TaskNode | None:
        return next((n for n in self.nodes if n.id == node_id), None)

    def ready_nodes(self) -> list[TaskNode]:
        """Return nodes whose dependencies are all resolved (completed, failed, or skipped).

        Treating failed/skipped as resolved lets downstream nodes still run — they'll
        receive an error-message context value for the failed dependency instead of
        being permanently blocked.
        """
        resolved_ids = {
            n.id for n in self.nodes
            if n.status in (NodeStatus.completed, NodeStatus.failed, NodeStatus.skipped)
        }
        return [
            n for n in self.nodes
            if n.status == NodeStatus.pending
            and all(dep in resolved_ids for dep in n.dependencies)
        ]

    def is_complete(self) -> bool:
        """All nodes are in a terminal state (no more work to do)."""
        terminal = (NodeStatus.completed, NodeStatus.skipped, NodeStatus.failed)
        return all(n.status in terminal for n in self.nodes)

    def is_failed(self) -> bool:
        """True only when every node ended in failure/skipped with no completions at all."""
        return (
            any(n.status == NodeStatus.failed for n in self.nodes)
            and not any(n.status == NodeStatus.completed for n in self.nodes)
        )

    def total_tokens(self) -> int:
        return sum(n.token_usage for n in self.nodes)


class GoalRequest(BaseModel):
    goal: str = Field(..., min_length=5, description="Natural language goal for the agent")
    allowed_tools: list[str] | None = None
    permissions: dict[str, bool] = Field(
        default_factory=lambda: {
            "read": True,
            "write": False,
            "network": False,
            "admin": False,
        }
    )


class PatchNode(BaseModel):
    """Used by the Architect to patch a failed node."""
    node_id: int
    action: str  # "retry" | "bypass" | "replace"
    new_args: dict[str, Any] | None = None
    new_tool: str | None = None
    bypass_reason: str | None = None


class GraphPatch(BaseModel):
    patch_nodes: list[PatchNode]
    new_nodes: list[TaskNode] = Field(default_factory=list)
