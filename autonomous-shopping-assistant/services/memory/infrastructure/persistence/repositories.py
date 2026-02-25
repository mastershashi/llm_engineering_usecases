"""Memory repositories."""
from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy.orm import Session

from shared.domain.value_objects import TenantId, UserId, SessionId
from services.memory.domain.entities import UserMemory, SessionTurn
from services.memory.application.ports import IUserMemoryRepository, ISessionHistoryRepository
from services.memory.infrastructure.persistence.models import Base, UserMemoryModel, SessionTurnModel


def _t(t) -> str:
    return str(t) if isinstance(t, UUID) else t


class UserMemoryRepository(IUserMemoryRepository):
    def __init__(self, session: Session):
        self._session = session

    def get(self, tenant_id: TenantId, user_id: UserId) -> UserMemory | None:
        r = self._session.query(UserMemoryModel).filter(
            UserMemoryModel.tenant_id == _t(tenant_id),
            UserMemoryModel.user_id == _t(user_id),
        ).first()
        if not r:
            return None
        return UserMemory(
            user_id=UserId(UUID(r.user_id)),
            tenant_id=TenantId(UUID(r.tenant_id)),
            facts=json.loads(r.facts) if r.facts else {},
            preferences=json.loads(r.preferences) if r.preferences else {},
        )

    def upsert(self, memory: UserMemory) -> None:
        r = self.get(memory.tenant_id, memory.user_id)
        if r:
            m = self._session.query(UserMemoryModel).filter(
                UserMemoryModel.tenant_id == _t(memory.tenant_id),
                UserMemoryModel.user_id == _t(memory.user_id),
            ).first()
            if m:
                m.facts = json.dumps(memory.facts)
                m.preferences = json.dumps(memory.preferences)
            return
        self._session.add(UserMemoryModel(
            user_id=_t(memory.user_id),
            tenant_id=_t(memory.tenant_id),
            facts=json.dumps(memory.facts),
            preferences=json.dumps(memory.preferences),
        ))

    def update_facts(self, tenant_id: TenantId, user_id: UserId, facts: dict) -> None:
        mem = self.get(tenant_id, user_id)
        if not mem:
            mem = UserMemory(user_id=user_id, tenant_id=tenant_id, facts=facts, preferences={})
        else:
            mem.facts = {**mem.facts, **facts}
        self.upsert(mem)

    def update_preferences(self, tenant_id: TenantId, user_id: UserId, preferences: dict) -> None:
        mem = self.get(tenant_id, user_id)
        if not mem:
            mem = UserMemory(user_id=user_id, tenant_id=tenant_id, facts={}, preferences=preferences)
        else:
            mem.preferences = {**mem.preferences, **preferences}
        self.upsert(mem)


class SessionHistoryRepository(ISessionHistoryRepository):
    def __init__(self, session: Session):
        self._session = session

    def get(self, tenant_id: TenantId, session_id: SessionId) -> None:
        return None  # We only use get_last_n

    def append(self, tenant_id: TenantId, session_id: SessionId, turn: SessionTurn) -> None:
        self._session.add(SessionTurnModel(
            tenant_id=_t(tenant_id),
            session_id=_t(session_id),
            role=turn.role,
            content=turn.content,
        ))

    def get_last_n(self, tenant_id: TenantId, session_id: SessionId, n: int) -> list[SessionTurn]:
        rows = (
            self._session.query(SessionTurnModel)
            .filter(
                SessionTurnModel.tenant_id == _t(tenant_id),
                SessionTurnModel.session_id == _t(session_id),
            )
            .order_by(SessionTurnModel.id.desc())
            .limit(n)
            .all()
        )
        return [SessionTurn(role=r.role, content=r.content) for r in reversed(rows)]
