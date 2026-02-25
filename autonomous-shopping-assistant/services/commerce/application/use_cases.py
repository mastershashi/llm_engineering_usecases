"""Commerce use cases."""
from __future__ import annotations

from decimal import Decimal

from shared.domain.value_objects import TenantId, UserId, ProductId, CartId, OrderId
from shared.domain.exceptions import NotFoundError

from ..domain.entities import Product, Cart, Order
from .ports import IProductRepository, ICartRepository, IOrderRepository


class ProductSearchUseCase:
    def __init__(self, product_repo: IProductRepository):
        self._repo = product_repo

    def execute(
        self,
        tenant_id: TenantId,
        query: str | None = None,
        category: str | None = None,
        max_price: float | None = None,
        limit: int = 20,
    ) -> list[dict]:
        products = self._repo.search(
            tenant_id=tenant_id,
            query=query,
            category=category,
            max_price=max_price,
            limit=limit,
        )
        return [p.to_dict() for p in products]


class GetProductUseCase:
    def __init__(self, product_repo: IProductRepository):
        self._repo = product_repo

    def execute(self, tenant_id: TenantId, product_id: ProductId) -> dict:
        product = self._repo.get_by_id(tenant_id, product_id)
        if not product:
            raise NotFoundError(f"Product {product_id} not found")
        return product.to_dict()


class GetCartUseCase:
    def __init__(self, cart_repo: ICartRepository):
        self._repo = cart_repo

    def execute(self, tenant_id: TenantId, user_id: UserId) -> dict:
        cart = self._repo.get_or_create(tenant_id, user_id)
        return cart.to_dict()


class AddToCartUseCase:
    def __init__(self, cart_repo: ICartRepository, product_repo: IProductRepository):
        self._cart_repo = cart_repo
        self._product_repo = product_repo

    def execute(
        self,
        tenant_id: TenantId,
        user_id: UserId,
        product_id: ProductId,
        quantity: int = 1,
    ) -> dict:
        product = self._product_repo.get_by_id(tenant_id, product_id)
        if not product:
            raise NotFoundError(f"Product {product_id} not found")
        cart = self._cart_repo.add_item(
            tenant_id=tenant_id,
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=product.price,
            title=product.title,
        )
        return cart.to_dict()


class RemoveFromCartUseCase:
    def __init__(self, cart_repo: ICartRepository):
        self._repo = cart_repo

    def execute(self, tenant_id: TenantId, user_id: UserId, product_id: ProductId) -> dict:
        cart = self._repo.remove_item(tenant_id, user_id, product_id)
        return cart.to_dict()


class CreateOrderUseCase:
    def __init__(self, cart_repo: ICartRepository, order_repo: IOrderRepository):
        self._cart_repo = cart_repo
        self._order_repo = order_repo

    def execute(self, tenant_id: TenantId, user_id: UserId) -> dict:
        cart = self._cart_repo.get_or_create(tenant_id, user_id)
        if not cart.items:
            raise ValueError("Cart is empty")
        order = self._order_repo.create(tenant_id, user_id, cart)
        return order.to_dict()


class GetOrderUseCase:
    def __init__(self, order_repo: IOrderRepository):
        self._repo = order_repo

    def execute(self, tenant_id: TenantId, order_id: OrderId) -> dict:
        order = self._repo.get(tenant_id, order_id)
        if not order:
            raise NotFoundError(f"Order {order_id} not found")
        return order.to_dict()


class ConfirmPaymentUseCase:
    """Mark order as paid (mock or after real payment)."""

    def __init__(self, order_repo: IOrderRepository):
        self._repo = order_repo

    def execute(self, tenant_id: TenantId, user_id: UserId, order_id: OrderId) -> dict:
        order = self._repo.get(tenant_id, order_id)
        if not order:
            raise NotFoundError(f"Order {order_id} not found")
        self._repo.update_status(tenant_id, order_id, "paid")
        return {"orderId": str(order_id), "status": "paid"}


class AddExternalOfferToCartUseCase:
    """Add an external (internet) offer to cart by source_id, title, price (no product in our catalog)."""

    def __init__(self, cart_repo: ICartRepository):
        self._repo = cart_repo

    def execute(
        self,
        tenant_id: TenantId,
        user_id: UserId,
        source_id: str,
        title: str,
        price: float,
        quantity: int = 1,
    ) -> dict:
        from decimal import Decimal
        cart = self._repo.add_item(
            tenant_id=tenant_id,
            user_id=user_id,
            product_id=ProductId(source_id),
            quantity=quantity,
            unit_price=Decimal(str(price)),
            title=title,
        )
        return cart.to_dict()
