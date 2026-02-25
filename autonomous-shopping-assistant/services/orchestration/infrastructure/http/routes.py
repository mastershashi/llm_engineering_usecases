"""Orchestration HTTP API."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from shared.domain.value_objects import TenantId, UserId, SessionId
from shared.ports.auth_port import IAuthProvider, AuthResult
from services.orchestration.application.use_cases import SendMessageUseCase
from services.orchestration.application.ports import IAgentClient, IMemoryClient
from services.orchestration.infrastructure.persistence.repositories import InMemorySessionRepository, InMemoryTurnRepository
from services.orchestration.infrastructure.clients.http_agent_client import HttpAgentClient
from services.orchestration.infrastructure.clients.http_memory_client import HttpMemoryClient
from services.orchestration.config import get_agent_url, get_memory_url


class MessagePayload(BaseModel):
    text: str | None = None


class SendMessageBody(BaseModel):
    sessionId: str | None = None
    channel: str = "web"
    message: dict  # { type, payload: { text } }


def get_auth() -> IAuthProvider:
    from shared.config.settings import get_settings
    from shared.adapters.auth_adapter import create_auth_provider
    s = get_settings(service_name="orchestration")
    auth_vars = {k: v for k, v in vars(s.auth).items() if k != "backend"}
    return create_auth_provider(s.auth.backend, **auth_vars)


def get_agent_client() -> IAgentClient:
    return HttpAgentClient(get_agent_url())


def get_memory_client() -> IMemoryClient:
    return HttpMemoryClient(get_memory_url())


_session_repo = InMemorySessionRepository()
_turn_repo = InMemoryTurnRepository()


def get_send_message_use_case(
    agent_client: IAgentClient = Depends(get_agent_client),
    memory_client: IMemoryClient = Depends(get_memory_client),
) -> SendMessageUseCase:
    return SendMessageUseCase(
        session_repo=_session_repo,
        turn_repo=_turn_repo,
        agent_client=agent_client,
        memory_client=memory_client,
    )


router = APIRouter(prefix="/v1/tenants/{tenant_id}", tags=["orchestration"])


@router.post("/sessions")
def send_message(
    tenant_id: str,
    body: SendMessageBody,
    use_case: SendMessageUseCase = Depends(get_send_message_use_case),
):
    auth = get_auth()
    try:
        result = auth.authenticate(None, {})
    except Exception:
        result = auth.optional_auth(None)
    if not result:
        result = AuthResult(TenantId(UUID(tenant_id)), UserId(UUID("00000000-0000-0000-0000-000000000002")))
    tid, uid = result.tenant_id, result.user_id
    session_id = SessionId(UUID(body.sessionId)) if body.sessionId else None
    msg = body.message or {}
    if not (isinstance(msg, dict) and msg.get("payload") and "text" in msg.get("payload", {})):
        msg = {"type": "text", "payload": {"text": str(msg.get("text", msg))}}
    out = use_case.execute(tenant_id=tid, user_id=uid, session_id=session_id, channel=body.channel, message=msg)
    return out
