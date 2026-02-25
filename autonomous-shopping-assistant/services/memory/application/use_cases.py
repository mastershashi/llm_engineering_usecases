"""Memory use cases."""
from __future__ import annotations

from shared.domain.value_objects import TenantId, UserId, SessionId

from services.memory.domain.entities import UserMemory, SessionTurn
from services.memory.application.ports import IUserMemoryRepository, ISessionHistoryRepository


class GetUserMemoryUseCase:
    def __init__(self, repo: IUserMemoryRepository):
        self._repo = repo

    def execute(self, tenant_id: TenantId, user_id: UserId) -> dict:
        memory = self._repo.get(tenant_id, user_id)
        if not memory:
            return {"facts": {}, "preferences": {}, "summary": ""}
        return {
            "facts": memory.facts,
            "preferences": memory.preferences,
            "summary": memory.to_summary(),
        }


class UpdateUserMemoryUseCase:
    def __init__(self, repo: IUserMemoryRepository):
        self._repo = repo

    def execute(
        self,
        tenant_id: TenantId,
        user_id: UserId,
        facts: dict[str, str] | None = None,
        preferences: dict[str, str] | None = None,
    ) -> dict:
        self._repo.update_facts(tenant_id, user_id, facts or {})
        self._repo.update_preferences(tenant_id, user_id, preferences or {})
        memory = self._repo.get(tenant_id, user_id)
        return {"facts": memory.facts, "preferences": memory.preferences, "summary": memory.to_summary()}


class GetSessionHistoryUseCase:
    def __init__(self, repo: ISessionHistoryRepository):
        self._repo = repo

    def execute(self, tenant_id: TenantId, session_id: SessionId, last_n: int = 10) -> list[dict]:
        turns = self._repo.get_last_n(tenant_id, session_id, last_n)
        return [{"role": t.role, "content": t.content} for t in turns]


class AppendSessionTurnUseCase:
    def __init__(self, repo: ISessionHistoryRepository):
        self._repo = repo

    def execute(
        self,
        tenant_id: TenantId,
        session_id: SessionId,
        role: str,
        content: str,
    ) -> None:
        self._repo.append(tenant_id, session_id, SessionTurn(role=role, content=content))
