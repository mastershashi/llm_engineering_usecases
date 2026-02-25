"""Auth adapters: mock (dev), JWT (prod)."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from shared.domain.exceptions import UnauthorizedError
from shared.domain.value_objects import TenantId, UserId
from shared.ports.auth_port import AuthResult, IAuthProvider


class MockAuthProvider(IAuthProvider):
    """Dev: accept any token or header; return fixed tenant/user from config."""

    def __init__(self, default_tenant_id: str, default_user_id: str):
        self._tenant = TenantId(UUID(default_tenant_id))
        self._user = UserId(UUID(default_user_id))

    def authenticate(self, token: str | None, headers: dict[str, str] | None = None) -> AuthResult:
        return AuthResult(tenant_id=self._tenant, user_id=self._user, claims={"mock": True})

    def optional_auth(self, token: str | None, headers: dict[str, str] | None = None) -> AuthResult | None:
        return self.authenticate(token, headers)


class JwtAuthProvider(IAuthProvider):
    """Prod: validate JWT and extract tenant_id, user_id from claims."""

    def __init__(self, secret: str, algorithm: str = "HS256"):
        self._secret = secret
        self._algorithm = algorithm

    def authenticate(self, token: str | None, headers: dict[str, str] | None = None) -> AuthResult:
        if not token and headers:
            token = headers.get("Authorization", "").replace("Bearer ", "").strip() or None
        if not token:
            raise UnauthorizedError("Missing token")
        try:
            import jwt
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
            tid = payload.get("tenant_id") or payload.get("tid")
            uid = payload.get("user_id") or payload.get("sub") or payload.get("uid")
            if not tid or not uid:
                raise UnauthorizedError("Invalid claims")
            return AuthResult(
                tenant_id=TenantId(UUID(tid) if isinstance(tid, str) else tid),
                user_id=UserId(UUID(uid) if isinstance(uid, str) else uid),
                claims=payload,
            )
        except Exception as e:
            raise UnauthorizedError(f"Invalid token: {e}") from e

    def optional_auth(self, token: str | None, headers: dict[str, str] | None = None) -> AuthResult | None:
        try:
            return self.authenticate(token, headers)
        except UnauthorizedError:
            return None


def create_auth_provider(backend: str, **kwargs: Any) -> IAuthProvider:
    if backend == "mock":
        return MockAuthProvider(
            kwargs.get("mock_default_tenant", "00000000-0000-0000-0000-000000000001"),
            kwargs.get("mock_default_user", "00000000-0000-0000-0000-000000000002"),
        )
    if backend == "jwt":
        return JwtAuthProvider(secret=kwargs.get("jwt_secret", ""), algorithm=kwargs.get("jwt_algorithm", "HS256"))
    raise ValueError(f"Unknown auth backend: {backend}")
