"""Database row models and response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from .task_graph import NodeStatus, PlanStatus, TaskGraph, TaskNode


class PlanRow(BaseModel):
    plan_id: str
    goal: str
    dag: TaskGraph
    status: PlanStatus
    branch_of: str | None = None   # parent plan_id if this is a "What-If" branch
    created_at: datetime
    updated_at: datetime


class NodeRow(BaseModel):
    plan_id: str
    node_id: int
    status: NodeStatus
    result: str | None = None
    error: str | None = None
    snapshot: dict[str, Any] | None = None  # full state blob at checkpoint
    token_usage: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


# ── WebSocket event schemas ──────────────────────────────────────────────────

class WsEventType(str):
    PLAN_CREATED = "plan_created"
    PLAN_APPROVED = "plan_approved"
    NODE_STARTED = "node_started"
    NODE_COMPLETED = "node_completed"
    NODE_FAILED = "node_failed"
    NODE_AWAITING = "node_awaiting_approval"
    PLAN_COMPLETED = "plan_completed"
    PLAN_FAILED = "plan_failed"
    LOG_LINE = "log_line"
    TOKEN_UPDATE = "token_update"


class WsEvent(BaseModel):
    event: str
    plan_id: str
    data: dict[str, Any] = {}
    timestamp: str = ""

    def __init__(self, **data: Any):
        if not data.get("timestamp"):
            data["timestamp"] = datetime.utcnow().isoformat()
        super().__init__(**data)


# ── REST response schemas ────────────────────────────────────────────────────

class PlanResponse(BaseModel):
    plan_id: str
    goal: str
    status: PlanStatus
    dag: TaskGraph
    branch_of: str | None
    created_at: str
    updated_at: str


class NodeApprovalRequest(BaseModel):
    approved: bool
    edited_args: dict[str, Any] | None = None  # user-edited tool arguments


class RewindRequest(BaseModel):
    node_id: int
    new_args: dict[str, Any] | None = None
    new_tool: str | None = None
