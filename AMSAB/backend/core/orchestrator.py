"""Stateful Orchestrator — drives the DAG execution lifecycle.

Responsibilities:
- Pick ready nodes and dispatch them to the Executor
- Handle HITL gates for high-risk nodes (with Decision Summary)
- Write checkpoints after every node (ChromaDB breadcrumbs)
- Trigger Architect patches on failure
- Broadcast live events over WebSocket
- Kill Switch support (immediate container termination)
- Idempotency warnings for rewound side-effect nodes
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

from .. import database as db
from ..config import settings
from ..models.state import WsEvent, WsEventType
from ..models.task_graph import NodeStatus, PlanStatus, TaskGraph, TaskNode
from .architect import architect
from .executor import executor
from .memory import memory_vault

# Tools that leave real-world side effects and need idempotency warnings
_SIDE_EFFECT_TOOLS = frozenset({
    "gmail_send", "gmail_draft", "filesystem_delete", "filesystem_write",
    "payment", "slack_post", "calendar_create",
})

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Keeps track of active WebSocket connections per plan."""

    def __init__(self) -> None:
        self._connections: dict[str, list[Any]] = {}  # plan_id -> [WebSocket, ...]

    def subscribe(self, plan_id: str, ws: Any) -> None:
        self._connections.setdefault(plan_id, []).append(ws)

    def unsubscribe(self, plan_id: str, ws: Any) -> None:
        self._connections.get(plan_id, []).remove(ws)  # type: ignore[arg-type]

    async def broadcast(self, event: WsEvent) -> None:
        for ws in list(self._connections.get(event.plan_id, [])):
            try:
                await ws.send_text(event.model_dump_json())
            except Exception:
                pass


ws_manager = ConnectionManager()

# Kill switch: plans whose execution should be immediately terminated
_killed_plans: set[str] = set()
# Guard against duplicate execute_plan calls for the same plan
_running_plans: set[str] = set()


class Orchestrator:
    """Drives plan execution with checkpoint-resume, HITL, memory vault, and kill switch."""

    async def execute_plan(self, plan_id: str) -> None:
        """Main execution loop for a plan. Called as a background task."""
        if plan_id in _running_plans:
            logger.warning("execute_plan already running for plan %s — ignoring duplicate", plan_id)
            return
        _running_plans.add(plan_id)
        logger.info("execute_plan started for plan %s", plan_id)
        plan = db.get_plan(plan_id)
        if not plan:
            logger.error("Plan %s not found in DB", plan_id)
            return

        dag = plan.dag
        context: dict[str, Any] = {}   # node_id -> output accumulated across runs
        db.update_plan_status(plan_id, PlanStatus.running)

        await ws_manager.broadcast(WsEvent(
            event=WsEventType.PLAN_APPROVED,
            plan_id=plan_id,
            data={"status": PlanStatus.running},
        ))

        dispatched_node_ids: set[int] = set()  # prevent re-queuing within this run
        try:
            while True:
                # Kill switch check
                if plan_id in _killed_plans:
                    _killed_plans.discard(plan_id)
                    db.update_plan_status(plan_id, PlanStatus.failed, dag)
                    db.add_log(plan_id, "🔴 Kill switch activated — execution terminated.")
                    await ws_manager.broadcast(WsEvent(
                        event=WsEventType.PLAN_FAILED,
                        plan_id=plan_id,
                        data={"reason": "kill_switch"},
                    ))
                    return

                ready = dag.ready_nodes()
                logger.info("Plan %s: ready_nodes=%s", plan_id, [n.id for n in ready])

                if not ready and dag.is_complete():
                    db.update_plan_status(plan_id, PlanStatus.completed, dag)
                    await ws_manager.broadcast(WsEvent(
                        event=WsEventType.PLAN_COMPLETED,
                        plan_id=plan_id,
                        data={"token_total": dag.total_tokens()},
                    ))
                    return

                if not ready:
                    # No ready nodes — check if we're actually done (all nodes terminal)
                    if dag.is_complete():
                        if dag.is_failed():
                            db.update_plan_status(plan_id, PlanStatus.failed, dag)
                            await ws_manager.broadcast(WsEvent(
                                event=WsEventType.PLAN_FAILED, plan_id=plan_id, data={}
                            ))
                        else:
                            db.update_plan_status(plan_id, PlanStatus.completed, dag)
                            await ws_manager.broadcast(WsEvent(
                                event=WsEventType.PLAN_COMPLETED,
                                plan_id=plan_id,
                                data={"token_total": dag.total_tokens()},
                            ))
                        return
                    # Waiting for HITL approval — pause
                    await asyncio.sleep(1)
                    plan = db.get_plan(plan_id)
                    if plan:
                        dag = plan.dag
                    continue

                # Filter out any nodes already dispatched in this run (double-safety)
                ready = [n for n in ready if n.id not in dispatched_node_ids]
                if not ready:
                    await asyncio.sleep(0.5)
                    continue
                dispatched_node_ids.update(n.id for n in ready)

                # Run all ready nodes concurrently
                tasks = [self._run_node(plan_id, dag, node, context) for node in ready]
                await asyncio.gather(*tasks)

                # Persist updated dag
                db.update_plan_status(plan_id, PlanStatus.running, dag)

        except Exception as exc:
            logger.error("execute_plan crashed for plan %s: %s", plan_id, exc, exc_info=True)
            db.update_plan_status(plan_id, PlanStatus.failed)
            db.add_log(plan_id, f"💥 Internal error: {exc}", level="error")
        finally:
            _running_plans.discard(plan_id)

    async def _run_node(
        self,
        plan_id: str,
        dag: TaskGraph,
        node: TaskNode,
        context: dict[str, Any],
    ) -> None:
        try:
            await self._run_node_inner(plan_id, dag, node, context)
        except Exception as exc:
            logger.error("_run_node crashed for node %d plan %s: %s", node.id, plan_id, exc, exc_info=True)
            node.status = NodeStatus.failed
            node.error = str(exc)
            db.upsert_node(plan_id, node.id, status=NodeStatus.failed, error=str(exc))
            db.add_log(plan_id, f"❌ Node {node.id} crashed: {exc}", node_id=node.id, level="error")

    async def _run_node_inner(
        self,
        plan_id: str,
        dag: TaskGraph,
        node: TaskNode,
        context: dict[str, Any],
    ) -> None:
        # High-risk nodes require human approval first — show Decision Summary
        if node.risk_level.value == "high":
            node.status = NodeStatus.awaiting_approval
            db.upsert_node(plan_id, node.id, status=NodeStatus.awaiting_approval)

            # Build HITL Decision Summary (Action / Intent / Logic)
            plan = db.get_plan(plan_id)
            decision_summary = {
                "action": f"Execute '{node.tool}' with args: {node.args}",
                "intent": f"To fulfill sub-task: '{node.task}'",
                "logic": (
                    f"Part of plan goal: '{plan.goal if plan else 'unknown'}'. "
                    f"Depends on nodes: {node.dependencies}. "
                    f"Resolved context keys: {[k for k in context if k.startswith('node_')]}."
                ),
            }

            await ws_manager.broadcast(WsEvent(
                event=WsEventType.NODE_AWAITING,
                plan_id=plan_id,
                data={
                    "node_id": node.id,
                    "tool": node.tool,
                    "args": node.args,
                    "decision_summary": decision_summary,
                },
            ))
            # Wait until status changes (approval or skip)
            while node.status == NodeStatus.awaiting_approval:
                await asyncio.sleep(0.5)
                plan = db.get_plan(plan_id)
                if plan:
                    updated = plan.dag.get_node(node.id)
                    if updated:
                        node.status = updated.status
                        node.args = updated.args
            if node.status == NodeStatus.skipped:
                return

        node.status = NodeStatus.running
        node.started_at = datetime.utcnow().isoformat()
        db.upsert_node(plan_id, node.id, status=NodeStatus.running, started_at=node.started_at)
        db.add_log(plan_id, f"▶ Node {node.id} started: {node.task}", node_id=node.id)

        await ws_manager.broadcast(WsEvent(
            event=WsEventType.NODE_STARTED,
            plan_id=plan_id,
            data={"node_id": node.id, "task": node.task, "tool": node.tool},
        ))

        async def _log(line: str) -> None:
            db.add_log(plan_id, line, node_id=node.id)
            await ws_manager.broadcast(WsEvent(
                event=WsEventType.LOG_LINE,
                plan_id=plan_id,
                data={"node_id": node.id, "line": line},
            ))

        result = await executor.run_node(plan_id, node, context, log_callback=_log)

        if result.success:
            node.status = NodeStatus.completed
            node.result = result.output
            node.completed_at = datetime.utcnow().isoformat()
            context[f"node_{node.id}_output"] = result.output

            db.upsert_node(
                plan_id, node.id,
                status=NodeStatus.completed,
                result=result.output,
                snapshot={"output": result.output, "context_keys": list(context.keys())},
                token_usage=result.token_usage,
            )
            db.add_log(plan_id, f"✅ Node {node.id} completed.", node_id=node.id)
            logger.info("Node %d completed successfully for plan %s", node.id, plan_id)

            # Record breadcrumb in short-term memory (non-fatal; run in thread to avoid blocking event loop)
            try:
                await asyncio.to_thread(
                    memory_vault.add_step,
                    plan_id=plan_id,
                    node_id=node.id,
                    task=node.task,
                    output=result.output,
                    tool=node.tool,
                )
            except Exception as mem_exc:
                logger.warning("memory_vault.add_step failed (non-fatal): %s", mem_exc)

            try:
                mem_stats = await asyncio.to_thread(memory_vault.stats)
            except Exception:
                mem_stats = {"short_term": 0, "long_term": 0}

            await ws_manager.broadcast(WsEvent(
                event=WsEventType.NODE_COMPLETED,
                plan_id=plan_id,
                data={
                    "node_id": node.id,
                    "output_preview": result.output[:200],
                    "memory_stats": mem_stats,
                },
            ))
        else:
            node.status = NodeStatus.failed
            node.error = result.output[-500:]  # last 500 chars of error output
            # Inject error into context so downstream nodes can still reference $node_N_output
            context[f"node_{node.id}_output"] = f"[FAILED] {node.error}"

            db.upsert_node(
                plan_id, node.id,
                status=NodeStatus.failed,
                error=node.error,
            )
            db.add_log(
                plan_id, f"❌ Node {node.id} failed: {node.error}", node_id=node.id, level="error"
            )
            await ws_manager.broadcast(WsEvent(
                event=WsEventType.NODE_FAILED,
                plan_id=plan_id,
                data={"node_id": node.id, "error": node.error},
            ))

            # Ask Architect to self-correct (skipped in Ollama-only mode)
            if settings.openai_api_key and settings.openai_api_key not in ("sk-dummy", "sk-...", ""):
                try:
                    patch = await architect.patch(node.id, node.error or "Unknown error", dag)
                    self._apply_patch(dag, patch)
                    db.add_log(plan_id, f"Architect patched node {node.id}", node_id=node.id)
                except Exception as exc:
                    logger.warning("Architect patch failed: %s", exc)
            else:
                logger.info("Skipping self-correction patch (no OpenAI key — Ollama-only mode)")

    @staticmethod
    def _apply_patch(dag: TaskGraph, patch: Any) -> None:
        for p in patch.patch_nodes:
            node = dag.get_node(p.node_id)
            if not node:
                continue
            if p.action == "retry":
                node.status = NodeStatus.pending
                if p.new_args:
                    node.args.update(p.new_args)
                if p.new_tool:
                    node.tool = p.new_tool
            elif p.action == "bypass":
                node.status = NodeStatus.skipped
            elif p.action == "replace":
                node.status = NodeStatus.pending
                if p.new_tool:
                    node.tool = p.new_tool
                if p.new_args:
                    node.args = p.new_args
        for new_node in patch.new_nodes:
            dag.nodes.append(new_node)

    async def approve_node(self, plan_id: str, node_id: int, edited_args: dict | None) -> None:
        """Called when user clicks Approve in HITL gate."""
        plan = db.get_plan(plan_id)
        if not plan:
            return
        node = plan.dag.get_node(node_id)
        if not node:
            return
        if edited_args:
            node.args = edited_args
        node.status = NodeStatus.approved
        db.update_plan_status(plan_id, PlanStatus.running, plan.dag)

    async def skip_node(self, plan_id: str, node_id: int) -> None:
        plan = db.get_plan(plan_id)
        if not plan:
            return
        node = plan.dag.get_node(node_id)
        if node:
            node.status = NodeStatus.skipped
        db.update_plan_status(plan_id, PlanStatus.running, plan.dag)

    async def kill(self, plan_id: str) -> None:
        """Kill switch — immediately halt all execution for a plan."""
        _killed_plans.add(plan_id)
        # Ask the executor to kill any running Docker containers for this plan
        await executor.kill_plan_containers(plan_id)
        logger.warning("Kill switch activated for plan %s", plan_id)

    async def rewind_node(
        self,
        plan_id: str,
        node_id: int,
        new_args: dict | None,
        new_tool: str | None,
    ) -> tuple[str, list[str]]:
        """Fork the plan at a specific node — time-travel debugging.

        Returns (branch_id, idempotency_warnings) where warnings list any side-
        effect tools that have already been executed and will re-run in the branch.
        """
        original = db.get_plan(plan_id)
        if not original:
            raise ValueError(f"Plan {plan_id} not found")

        # Collect idempotency warnings for side-effect nodes being rewound
        target_ids = self._downstream(original.dag, node_id) | {node_id}
        warnings: list[str] = []
        for n in original.dag.nodes:
            if (
                n.id in target_ids
                and n.status == NodeStatus.completed
                and n.tool in _SIDE_EFFECT_TOOLS
            ):
                warnings.append(
                    f"Node {n.id} ('{n.tool}') has already been performed in the "
                    f"real world — re-running may cause duplicates."
                )

        # Create a branch
        branch_id = str(uuid.uuid4())
        branch_dag = original.dag.model_copy(deep=True)

        # Reset the target node and all downstream nodes
        for n in branch_dag.nodes:
            if n.id in target_ids:
                n.status = NodeStatus.pending
                n.result = None
                n.error = None
        target_node = branch_dag.get_node(node_id)
        if target_node:
            if new_args:
                target_node.args = new_args
            if new_tool:
                target_node.tool = new_tool

        db.create_plan(branch_id, original.goal, branch_dag, branch_of=plan_id)
        return branch_id, warnings

    @staticmethod
    def _downstream(dag: TaskGraph, node_id: int) -> set[int]:
        """Return all node IDs that transitively depend on node_id."""
        result: set[int] = set()
        changed = True
        affected = {node_id}
        while changed:
            changed = False
            for n in dag.nodes:
                if any(d in affected for d in n.dependencies) and n.id not in result:
                    result.add(n.id)
                    affected.add(n.id)
                    changed = True
        return result


orchestrator = Orchestrator()
