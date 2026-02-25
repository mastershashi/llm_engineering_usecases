"""WebSocket route for live plan updates."""
from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ...core.orchestrator import ws_manager
from ... import database as db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/plans/{plan_id}")
async def plan_websocket(websocket: WebSocket, plan_id: str) -> None:
    """
    Connect to receive real-time events for a plan:
    - node_started, node_completed, node_failed
    - node_awaiting_approval (HITL gate)
    - log_line (live sandbox stdout)
    - token_update, plan_completed, plan_failed
    """
    await websocket.accept()
    ws_manager.subscribe(plan_id, websocket)

    # Send current logs so late-joiners catch up
    logs = db.get_logs(plan_id, limit=50)
    for log in logs:
        try:
            await websocket.send_json({"event": "log_line", "plan_id": plan_id, "data": log})
        except Exception:
            break

    try:
        while True:
            # Keep connection alive; client can send pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        logger.debug("WebSocket disconnected for plan %s", plan_id)
    finally:
        ws_manager.unsubscribe(plan_id, websocket)
