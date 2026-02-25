"""HTTP client for Agent Service."""
from __future__ import annotations

import httpx
from shared.domain.value_objects import TenantId, UserId
from services.orchestration.application.ports import IAgentClient


class HttpAgentClient(IAgentClient):
    def __init__(self, base_url: str):
        self._base = base_url.rstrip("/")

    def process(
        self,
        tenant_id: TenantId,
        user_id: UserId,
        messages: list[dict],
        context: dict,
    ) -> dict:
        r = httpx.post(
            f"{self._base}/v1/process",
            json={
                "tenantId": str(tenant_id),
                "userId": str(user_id),
                "messages": messages,
                "context": context,
                "toolsAvailable": ["search_internet", "add_external_to_cart", "get_cart", "product_search", "add_to_cart"],
            },
            timeout=30.0,
        )
        r.raise_for_status()
        return r.json()
