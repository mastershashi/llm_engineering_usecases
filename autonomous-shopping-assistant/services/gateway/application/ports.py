"""Gateway ports."""
from __future__ import annotations

from abc import ABC, abstractmethod

from shared.ports.auth_port import AuthResult


class IRateLimiter(ABC):
    @abstractmethod
    def allow(self, key: str) -> bool: ...


class IUpstreamClient(ABC):
    """Port for calling Orchestration."""
    @abstractmethod
    def post_sessions(self, tenant_id: str, body: dict, auth: AuthResult) -> dict: ...
