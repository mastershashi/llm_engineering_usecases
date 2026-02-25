"""Memory ports."""
from __future__ import annotations

from abc import ABC, abstractmethod

from shared.domain.value_objects import TenantId, UserId, SessionId

from services.memory.domain.entities import UserMemory, SessionHistory, SessionTurn


class IUserMemoryRepository(ABC):
    @abstractmethod
    def get(self, tenant_id: TenantId, user_id: UserId) -> UserMemory | None: ...

    @abstractmethod
    def upsert(self, memory: UserMemory) -> None: ...

    @abstractmethod
    def update_facts(self, tenant_id: TenantId, user_id: UserId, facts: dict[str, str]) -> None: ...

    @abstractmethod
    def update_preferences(self, tenant_id: TenantId, user_id: UserId, preferences: dict[str, str]) -> None: ...


class ISessionHistoryRepository(ABC):
    @abstractmethod
    def get(self, tenant_id: TenantId, session_id: SessionId) -> SessionHistory | None: ...

    @abstractmethod
    def append(self, tenant_id: TenantId, session_id: SessionId, turn: SessionTurn) -> None: ...

    @abstractmethod
    def get_last_n(self, tenant_id: TenantId, session_id: SessionId, n: int) -> list[SessionTurn]: ...
