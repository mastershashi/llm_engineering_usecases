"""Shared value objects and identifiers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import NewType
from uuid import UUID

TenantId = NewType("TenantId", UUID)
UserId = NewType("UserId", UUID)
SessionId = NewType("SessionId", UUID)
TurnId = NewType("TurnId", UUID)
ProductId = NewType("ProductId", str)
CartId = NewType("CartId", UUID)
OrderId = NewType("OrderId", UUID)


@dataclass(frozen=True)
class TenantContext:
    tenant_id: TenantId
    user_id: UserId


@dataclass(frozen=True)
class RequestContext:
    tenant_id: TenantId
    user_id: UserId
    session_id: SessionId | None
    request_id: str
    correlation_id: str
