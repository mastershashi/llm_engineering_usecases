"""Port: authentication and authorization."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from shared.domain.value_objects import TenantId, UserId


class AuthResult:
    """Result of authentication."""
    __slots__ = ("tenant_id", "user_id", "claims")

    def __init__(self, tenant_id: TenantId, user_id: UserId, claims: dict[str, Any] | None = None):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.claims = claims or {}


class IAuthProvider(ABC):
    """Port for auth. Adapters: MockAuth (dev), JwtAuth (prod)."""

    @abstractmethod
    def authenticate(self, token: str | None, headers: dict[str, str] | None = None) -> AuthResult:
        """Validate token/headers and return tenant + user. Raises UnauthorizedError on failure."""
        ...

    @abstractmethod
    def optional_auth(self, token: str | None, headers: dict[str, str] | None = None) -> AuthResult | None:
        """Same as authenticate but returns None instead of raising when no/invalid token."""
        ...
