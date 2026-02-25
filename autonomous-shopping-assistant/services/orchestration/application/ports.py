"""Orchestration ports."""
from __future__ import annotations

from abc import ABC, abstractmethod

from shared.domain.value_objects import TenantId, UserId, SessionId, TurnId
from services.orchestration.domain.entities import Session, Turn


class ISessionRepository(ABC):
    @abstractmethod
    def get(self, tenant_id: TenantId, session_id: SessionId) -> Session | None: ...

    @abstractmethod
    def create(self, tenant_id: TenantId, user_id: UserId, channel: str) -> Session: ...

    @abstractmethod
    def save(self, session: Session) -> None: ...


class ITurnRepository(ABC):
    @abstractmethod
    def create(self, session_id: SessionId, request_payload: dict, response_payload: dict) -> Turn: ...


class IAgentClient(ABC):
    """Port for calling Agent Service."""

    @abstractmethod
    def process(
        self,
        tenant_id: TenantId,
        user_id: UserId,
        messages: list[dict],
        context: dict,
    ) -> dict: ...


class IMemoryClient(ABC):
    """Port for calling Memory Service."""

    @abstractmethod
    def get_memory(self, tenant_id: TenantId, user_id: UserId) -> dict: ...

    @abstractmethod
    def get_history(self, tenant_id: TenantId, session_id: SessionId, last_n: int) -> list[dict]: ...

    @abstractmethod
    def append_turn(self, tenant_id: TenantId, session_id: SessionId, role: str, content: str) -> None: ...
