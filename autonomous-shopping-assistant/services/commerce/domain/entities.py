"""Commerce domain entities."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from shared.domain.value_objects import TenantId, UserId, ProductId, CartId, OrderId


@dataclass
class Product:
    product_id: ProductId
    tenant_id: TenantId
    title: str
    description: str
    category: str
    price: Decimal
    attributes: dict
    external_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "productId": str(self.product_id),
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "price": float(self.price),
            "attributes": self.attributes,
        }


@dataclass
class CartItem:
    product_id: ProductId
    quantity: int
    unit_price: Decimal
    title: str

    def to_dict(self) -> dict:
        return {
            "productId": str(self.product_id),
            "quantity": self.quantity,
            "unitPrice": float(self.unit_price),
            "title": self.title,
        }


@dataclass
class Cart:
    cart_id: CartId
    tenant_id: TenantId
    user_id: UserId
    items: list[CartItem]

    def to_dict(self) -> dict:
        return {
            "cartId": str(self.cart_id),
            "items": [i.to_dict() for i in self.items],
            "totalItems": sum(i.quantity for i in self.items),
        }


@dataclass
class Order:
    order_id: OrderId
    tenant_id: TenantId
    user_id: UserId
    cart_id: CartId
    status: str  # created | confirmed | paid | shipped
    total_amount: Decimal
    items: list[CartItem]

    def to_dict(self) -> dict:
        return {
            "orderId": str(self.order_id),
            "status": self.status,
            "totalAmount": float(self.total_amount),
            "items": [i.to_dict() for i in self.items],
        }
