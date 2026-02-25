"""Memory domain entities."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from shared.domain.value_objects import TenantId, UserId, SessionId


@dataclass
class UserMemory:
    user_id: UserId
    tenant_id: TenantId
    facts: dict[str, str]  # key -> value
    preferences: dict[str, str]

    def to_summary(self, max_len: int = 500) -> str:
        parts = []
        if self.preferences:
            parts.append("Preferences: " + ", ".join(f"{k}={v}" for k, v in list(self.preferences.items())[:10]))
        if self.facts:
            parts.append("Facts: " + ", ".join(f"{k}={v}" for k, v in list(self.facts.items())[:10]))
        s = " ".join(parts)
        return s[:max_len] + "..." if len(s) > max_len else s


@dataclass
class SessionTurn:
    role: str  # user | assistant
    content: str
    turn_id: str | None = None


@dataclass
class SessionHistory:
    session_id: SessionId
    tenant_id: TenantId
    user_id: UserId
    turns: list[SessionTurn]

    def last_n(self, n: int) -> list[SessionTurn]:
        return self.turns[-n:] if self.turns else []
