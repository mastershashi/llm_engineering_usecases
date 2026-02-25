"""Orchestration domain."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from shared.domain.value_objects import TenantId, UserId, SessionId, TurnId


@dataclass
class Session:
    session_id: SessionId
    tenant_id: TenantId
    user_id: UserId
    channel: str
    state: str  # active | ended


@dataclass
class Turn:
    turn_id: TurnId
    session_id: SessionId
    request_payload: dict
    response_payload: dict
