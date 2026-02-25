"""Mock payment provider: no real charge, just marks order paid."""
from __future__ import annotations

from shared.domain.value_objects import TenantId, UserId, OrderId
from services.commerce.application.payment_ports import IPaymentProvider


class MockPaymentProvider(IPaymentProvider):
    def create_payment_intent(
        self,
        tenant_id: TenantId,
        user_id: UserId,
        order_id: OrderId,
        amount_cents: int,
        currency: str = "usd",
    ) -> dict:
        return {
            "client_secret": f"mock_pi_{order_id}",
            "payment_intent_id": f"mock_{order_id}",
            "mock": True,
        }

    def confirm_payment(self, order_id: OrderId, payment_intent_id: str | None = None) -> dict:
        return {"status": "succeeded", "orderId": str(order_id), "mock": True}
