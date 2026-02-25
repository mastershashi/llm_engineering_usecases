"""Goal submission and plan management routes."""
from __future__ import annotations

import asyncio
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from ...core.architect import architect
from ...core.memory import memory_vault
from ...core.orchestrator import orchestrator
from ... import database as db
from ...models.state import NodeApprovalRequest, PlanResponse, RewindRequest
from ...models.task_graph import GoalRequest, PlanStatus

router = APIRouter(prefix="/api", tags=["plans"])


def _plan_response(plan_id: str) -> PlanResponse:
    plan = db.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return PlanResponse(
        plan_id=plan.plan_id,
        goal=plan.goal,
        status=plan.status,
        dag=plan.dag,
        branch_of=plan.branch_of,
        created_at=plan.created_at.isoformat(),
        updated_at=plan.updated_at.isoformat(),
    )


@router.post("/goals", response_model=PlanResponse, status_code=201)
async def submit_goal(request: GoalRequest) -> PlanResponse:
    """Submit a natural language goal. Returns a DAG plan for review."""
    plan_id = str(uuid.uuid4())
    dag = await architect.plan(request)
    db.create_plan(plan_id, request.goal, dag)
    return _plan_response(plan_id)


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans() -> list[PlanResponse]:
    plans = db.list_plans()
    return [
        PlanResponse(
            plan_id=p.plan_id,
            goal=p.goal,
            status=p.status,
            dag=p.dag,
            branch_of=p.branch_of,
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat(),
        )
        for p in plans
    ]


@router.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: str) -> PlanResponse:
    return _plan_response(plan_id)


@router.post("/plans/{plan_id}/approve", response_model=PlanResponse)
async def approve_plan(plan_id: str, background_tasks: BackgroundTasks) -> PlanResponse:
    """User reviewed the DAG and clicked 'Approve All'. Starts execution."""
    plan = db.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.status not in (PlanStatus.draft,):
        raise HTTPException(status_code=400, detail=f"Plan is already {plan.status}")
    db.update_plan_status(plan_id, PlanStatus.approved)
    background_tasks.add_task(orchestrator.execute_plan, plan_id)
    return _plan_response(plan_id)


@router.post("/plans/{plan_id}/nodes/{node_id}/approve", response_model=PlanResponse)
async def approve_node(
    plan_id: str, node_id: int, body: NodeApprovalRequest
) -> PlanResponse:
    """Human-in-the-loop: approve or reject a high-risk node."""
    if body.approved:
        await orchestrator.approve_node(plan_id, node_id, body.edited_args)
    else:
        await orchestrator.skip_node(plan_id, node_id)
    return _plan_response(plan_id)


@router.post("/plans/{plan_id}/nodes/{node_id}/rewind")
async def rewind_node(
    plan_id: str, node_id: int, body: RewindRequest, background_tasks: BackgroundTasks
) -> dict:
    """Time-travel: fork the plan from a specific node with new args.

    Returns the new branch plan plus any idempotency warnings for side-effect nodes.
    """
    branch_id, warnings = await orchestrator.rewind_node(
        plan_id, body.node_id, body.new_args, body.new_tool
    )
    background_tasks.add_task(orchestrator.execute_plan, branch_id)
    plan = _plan_response(branch_id)
    return {"plan": plan.model_dump(), "idempotency_warnings": warnings}


@router.post("/plans/{plan_id}/kill")
async def kill_plan(plan_id: str) -> dict:
    """Kill switch: immediately halt execution and destroy all containers."""
    await orchestrator.kill(plan_id)
    return {"status": "killed", "plan_id": plan_id}


@router.get("/plans/{plan_id}/logs")
async def get_logs(plan_id: str) -> list[dict]:
    return db.get_logs(plan_id)


# ── Memory Vault routes ────────────────────────────────────────────────────── #

@router.get("/plans/{plan_id}/memory/session")
async def get_session_memory(plan_id: str) -> dict:
    """Return short-term breadcrumb trail for a session."""
    return {
        "plan_id": plan_id,
        "breadcrumbs": memory_vault.get_session_breadcrumbs(plan_id),
        "stats": memory_vault.stats(),
    }


@router.delete("/plans/{plan_id}/memory/session")
async def wipe_session_memory(plan_id: str) -> dict:
    """Privacy Mode: clear all short-term memory for this session."""
    wiped = memory_vault.wipe_session(plan_id)
    return {"plan_id": plan_id, "wiped": wiped}


class LongTermRememberBody(BaseModel):
    key: str
    value: str
    category: str = "general"


@router.post("/memory/long-term")
async def remember(body: LongTermRememberBody) -> dict:
    """Store a long-term fact in the vector memory."""
    memory_vault.remember(body.key, body.value, body.category)
    return {"status": "stored", "key": body.key}


@router.get("/memory/long-term")
async def recall(q: str, n: int = 5) -> dict:
    """Semantic search across long-term memory."""
    results = memory_vault.recall(q, n_results=n)
    return {"query": q, "results": results}


@router.delete("/memory/all")
async def wipe_all_memory() -> dict:
    """Nuclear option — wipe ALL short and long-term memory."""
    memory_vault.wipe_all_memory()
    return {"status": "all_memory_wiped"}


@router.get("/memory/stats")
async def memory_stats() -> dict:
    return memory_vault.stats()
