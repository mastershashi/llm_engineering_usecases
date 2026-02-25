"""In-memory session and turn repos (dev). Can add SQLite/Postgres adapter for prod."""
from __future__ import annotations

from uuid import uuid4, UUID

from shared.domain.value_objects import TenantId, UserId, SessionId, TurnId
from services.orchestration.domain.entities import Session, Turn
from services.orchestration.application.ports import ISessionRepository, ITurnRepository


class InMemorySessionRepository(ISessionRepository):
    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def _key(self, tid: TenantId, sid: SessionId) -> str:
        return f"{tid}:{sid}"

    def get(self, tenant_id: TenantId, session_id: SessionId) -> Session | None:
        return self._sessions.get(self._key(tenant_id, session_id))

    def create(self, tenant_id: TenantId, user_id: UserId, channel: str) -> Session:
        sid = SessionId(uuid4())
        s = Session(session_id=sid, tenant_id=tenant_id, user_id=user_id, channel=channel, state="active")
        self._sessions[f"{tenant_id}:{sid}"] = s
        return s

    def save(self, session: Session) -> None:
        self._sessions[f"{session.tenant_id}:{session.session_id}"] = session


class InMemoryTurnRepository(ITurnRepository):
    def __init__(self):
        self._turns: list[Turn] = []

    def create(self, session_id: SessionId, request_payload: dict, response_payload: dict) -> Turn:
        turn = Turn(
            turn_id=TurnId(uuid4()),
            session_id=session_id,
            request_payload=request_payload,
            response_payload=response_payload,
        )
        self._turns.append(turn)
        return turn
