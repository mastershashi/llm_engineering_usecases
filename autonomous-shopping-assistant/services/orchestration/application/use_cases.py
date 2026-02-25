"""Orchestration use cases: session, agent, pass last best deal for add-to-cart."""
from __future__ import annotations

from uuid import uuid4
from shared.domain.value_objects import TenantId, UserId, SessionId, TurnId
from services.orchestration.domain.entities import Session, Turn
from services.orchestration.application.ports import (
    ISessionRepository,
    ITurnRepository,
    IAgentClient,
    IMemoryClient,
)

# Session-scoped last best deal and last order (for "Add best to cart" and "Pay")
_last_best_deal_by_session: dict[str, dict] = {}
_last_order_id_by_session: dict[str, str] = {}


class SendMessageUseCase:
    def __init__(
        self,
        session_repo: ISessionRepository,
        turn_repo: ITurnRepository,
        agent_client: IAgentClient,
        memory_client: IMemoryClient,
    ):
        self._session_repo = session_repo
        self._turn_repo = turn_repo
        self._agent_client = agent_client
        self._memory_client = memory_client

    def execute(
        self,
        tenant_id: TenantId,
        user_id: UserId,
        session_id: SessionId | None,
        channel: str,
        message: dict,
    ) -> dict:
        if session_id:
            session = self._session_repo.get(tenant_id, session_id)
        else:
            session = None
        if not session:
            session = self._session_repo.create(tenant_id, user_id, channel)
        # Get memory and history for context
        memory = self._memory_client.get_memory(tenant_id, user_id)
        history = self._memory_client.get_history(tenant_id, session.session_id, last_n=10)
        messages = [{"role": h["role"], "content": h["content"]} for h in history]
        user_content = message.get("text") or message.get("payload", {}).get("text", "")
        messages.append({"role": "user", "content": user_content})
        sid_str = str(session.session_id)
        context = {
            "userPreferences": memory.get("preferences", {}),
            "memorySummary": memory.get("summary", ""),
            "lastBestDeal": _last_best_deal_by_session.get(sid_str, {}),
            "lastOrderId": _last_order_id_by_session.get(sid_str),
        }
        # Call agent
        agent_response = self._agent_client.process(tenant_id, user_id, messages, context)
        reply = agent_response.get("reply", {})
        state = agent_response.get("state", "completed")
        structured = reply.get("structured") or {}
        if structured.get("bestDeal"):
            _last_best_deal_by_session[sid_str] = structured["bestDeal"]
        for tr in (structured.get("toolResults") or []):
            if tr.get("tool") == "create_order" and isinstance(tr.get("result"), dict):
                oid = tr["result"].get("orderId")
                if oid:
                    _last_order_id_by_session[sid_str] = oid
                    # Stub expects lastBestDeal.orderId for confirm_payment
                    _last_best_deal_by_session[sid_str] = {**_last_best_deal_by_session.get(sid_str, {}), "orderId": oid}
        # Persist turn
        self._memory_client.append_turn(tenant_id, session.session_id, "user", user_content)
        self._memory_client.append_turn(tenant_id, session.session_id, "assistant", reply.get("text", ""))
        turn = self._turn_repo.create(
            session.session_id,
            {"message": message},
            {"reply": reply, "state": state},
        )
        structured = reply.get("structured") or {}
        cards = structured.get("cards", [])
        suggested = ["Add the best one to cart", "View my cart"]
        if structured.get("bestDeal"):
            suggested = ["Add the best one to cart", "View my cart", "Checkout"]
        return {
            "sessionId": str(session.session_id),
            "turnId": str(turn.turn_id),
            "reply": {
                "type": "text",
                "text": reply.get("text", ""),
                "cards": cards,
                "bestDeal": structured.get("bestDeal"),
                "reasoning": structured.get("reasoning", ""),
                "suggestedActions": suggested,
            },
            "state": state,
        }
