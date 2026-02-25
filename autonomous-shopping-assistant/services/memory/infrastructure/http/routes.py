"""Memory HTTP API."""
from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from shared.domain.value_objects import TenantId, UserId, SessionId
from services.memory.application.use_cases import (
    GetUserMemoryUseCase,
    UpdateUserMemoryUseCase,
    GetSessionHistoryUseCase,
    AppendSessionTurnUseCase,
)
from services.memory.infrastructure.persistence.unit_of_work import MemoryUnitOfWork


def get_uow() -> MemoryUnitOfWork:
    from services.memory.config import get_database_url
    return MemoryUnitOfWork(get_database_url())


class UpdateMemoryBody(BaseModel):
    facts: dict[str, str] | None = None
    preferences: dict[str, str] | None = None


class AppendTurnBody(BaseModel):
    role: str
    content: str


router = APIRouter(prefix="/v1/tenants/{tenant_id}", tags=["memory"])


def _tenant(t: str) -> TenantId:
    return TenantId(UUID(t))


def _user(u: str) -> UserId:
    return UserId(UUID(u))


def _session(s: str) -> SessionId:
    return SessionId(UUID(s))


@router.get("/users/{user_id}/memory")
def get_memory(tenant_id: str, user_id: str, uow: MemoryUnitOfWork = Depends(get_uow)):
    with uow.session() as s:
        uc = GetUserMemoryUseCase(uow.user_memory_repo(s))
        return uc.execute(_tenant(tenant_id), _user(user_id))


@router.post("/users/{user_id}/memory")
def update_memory(tenant_id: str, user_id: str, body: UpdateMemoryBody, uow: MemoryUnitOfWork = Depends(get_uow)):
    with uow.session() as s:
        uc = UpdateUserMemoryUseCase(uow.user_memory_repo(s))
        return uc.execute(_tenant(tenant_id), _user(user_id), body.facts, body.preferences)


@router.get("/sessions/{session_id}/history")
def get_history(
    tenant_id: str,
    session_id: str,
    last_n: int = 10,
    uow: MemoryUnitOfWork = Depends(get_uow),
):
    with uow.session() as s:
        uc = GetSessionHistoryUseCase(uow.session_history_repo(s))
        return uc.execute(_tenant(tenant_id), _session(session_id), last_n)


@router.post("/sessions/{session_id}/turns")
def append_turn(
    tenant_id: str,
    session_id: str,
    body: AppendTurnBody,
    uow: MemoryUnitOfWork = Depends(get_uow),
):
    with uow.session() as s:
        uc = AppendSessionTurnUseCase(uow.session_history_repo(s))
        uc.execute(_tenant(tenant_id), _session(session_id), body.role, body.content)
    return {"ok": True}
