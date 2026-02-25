"""Payment port: mock or Stripe."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from shared.domain.value_objects import TenantId, UserId, OrderId


class IPaymentProvider(ABC):
    @abstractmethod
    def create_payment_intent(
        self,
        tenant_id: TenantId,
        user_id: UserId,
        order_id: OrderId,
        amount_cents: int,
        currency: str = "usd",
    ) -> dict[str, Any]:
        """Return { client_secret, payment_intent_id } for Stripe; or mock equivalent."""
        ...

    @abstractmethod
    def confirm_payment(self, order_id: OrderId, payment_intent_id: str | None = None) -> dict[str, Any]:
        """Mark order as paid. Mock: just update status. Real: verify with provider."""
        ...
