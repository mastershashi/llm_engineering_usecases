"""HTTP client for Memory Service."""
from __future__ import annotations

import httpx
from shared.domain.value_objects import TenantId, UserId, SessionId
from services.orchestration.application.ports import IMemoryClient


class HttpMemoryClient(IMemoryClient):
    def __init__(self, base_url: str):
        self._base = base_url.rstrip("/")

    def get_memory(self, tenant_id: TenantId, user_id: UserId) -> dict:
        try:
            r = httpx.get(f"{self._base}/v1/tenants/{tenant_id}/users/{user_id}/memory", timeout=5.0)
            r.raise_for_status()
            return r.json()
        except Exception:
            return {"facts": {}, "preferences": {}, "summary": ""}

    def get_history(self, tenant_id: TenantId, session_id: SessionId, last_n: int) -> list[dict]:
        try:
            r = httpx.get(
                f"{self._base}/v1/tenants/{tenant_id}/sessions/{session_id}/history",
                params={"last_n": last_n},
                timeout=5.0,
            )
            r.raise_for_status()
            return r.json()
        except Exception:
            return []

    def append_turn(self, tenant_id: TenantId, session_id: SessionId, role: str, content: str) -> None:
        try:
            httpx.post(
                f"{self._base}/v1/tenants/{tenant_id}/sessions/{session_id}/turns",
                json={"role": role, "content": content},
                timeout=5.0,
            )
        except Exception:
            pass
