"""HTTP client to Orchestration."""
from __future__ import annotations

import httpx
from shared.ports.auth_port import AuthResult


class HttpUpstreamClient:
    def __init__(self, orchestration_url: str):
        self._base = orchestration_url.rstrip("/")

    def post_sessions(self, tenant_id: str, body: dict, auth: AuthResult) -> dict:
        r = httpx.post(
            f"{self._base}/v1/tenants/{tenant_id}/sessions",
            json=body,
            timeout=30.0,
        )
        r.raise_for_status()
        return r.json()
