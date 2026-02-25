"""Commerce repositories: SQLAlchemy implementations (dev SQLite / prod Postgres)."""
from __future__ import annotations

import json
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session
from shared.domain.value_objects import TenantId, UserId, ProductId, CartId, OrderId

from services.commerce.domain.entities import (
    Product,
    Cart,
    CartItem,
    Order,
)
from services.commerce.infrastructure.persistence.models import (
    Base,
    ProductModel,
    CartModel,
    CartItemModel,
    OrderModel,
    OrderItemModel,
)
from services.commerce.application.ports import (
    IProductRepository,
    ICartRepository,
    IOrderRepository,
)


def _tenant_str(t: TenantId) -> str:
    return str(t) if isinstance(t, UUID) else t


def _user_str(u: UserId) -> str:
    return str(u) if isinstance(u, UUID) else u


class ProductRepository(IProductRepository):
    def __init__(self, session: Session):
        self._session = session

    def search(
        self,
        tenant_id: TenantId,
        query: str | None = None,
        category: str | None = None,
        max_price: float | None = None,
        limit: int = 20,
    ) -> list[Product]:
        q = self._session.query(ProductModel).filter(ProductModel.tenant_id == _tenant_str(tenant_id))
        if category:
            q = q.filter(ProductModel.category == category)
        if max_price is not None:
            q = q.filter(ProductModel.price <= max_price)
        if query:
            q = q.filter(
                ProductModel.title.ilike(f"%{query}%") | ProductModel.description.ilike(f"%{query}%")
            )
        rows = q.limit(limit).all()
        return [
            Product(
                product_id=ProductId(r.product_id),
                tenant_id=TenantId(UUID(r.tenant_id)),
                title=r.title,
                description=r.description,
                category=r.category,
                price=Decimal(str(r.price)),
                attributes=r.get_attributes(),
                external_id=r.external_id,
            )
            for r in rows
        ]

    def get_by_id(self, tenant_id: TenantId, product_id: ProductId) -> Product | None:
        r = (
            self._session.query(ProductModel)
            .filter(
                ProductModel.tenant_id == _tenant_str(tenant_id),
                ProductModel.product_id == str(product_id),
            )
            .first()
        )
        if not r:
            return None
        return Product(
            product_id=ProductId(r.product_id),
            tenant_id=TenantId(UUID(r.tenant_id)),
            title=r.title,
            description=r.description,
            category=r.category,
            price=Decimal(str(r.price)),
            attributes=r.get_attributes(),
            external_id=r.external_id,
        )

    def add(self, product: Product) -> None:
        m = ProductModel(
            product_id=str(product.product_id),
            tenant_id=_tenant_str(product.tenant_id),
            title=product.title,
            description=product.description,
            category=product.category,
            price=product.price,
            attributes=json.dumps(product.attributes),
            external_id=product.external_id,
        )
        self._session.add(m)


class CartRepository(ICartRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_or_create(self, tenant_id: TenantId, user_id: UserId) -> Cart:
        r = (
            self._session.query(CartModel)
            .filter(
                CartModel.tenant_id == _tenant_str(tenant_id),
                CartModel.user_id == _user_str(user_id),
            )
            .first()
        )
        if r:
            items = [
                CartItem(
                    product_id=ProductId(i.product_id),
                    quantity=i.quantity,
                    unit_price=Decimal(str(i.unit_price)),
                    title=i.title,
                )
                for i in r.item_models
            ]
            return Cart(
                cart_id=CartId(UUID(r.cart_id)),
                tenant_id=TenantId(UUID(r.tenant_id)),
                user_id=UserId(UUID(r.user_id)),
                items=items,
            )
        r = CartModel(tenant_id=_tenant_str(tenant_id), user_id=_user_str(user_id))
        self._session.add(r)
        self._session.flush()
        return Cart(
            cart_id=CartId(UUID(r.cart_id)),
            tenant_id=TenantId(UUID(r.tenant_id)),
            user_id=UserId(UUID(r.user_id)),
            items=[],
        )

    def add_item(
        self,
        tenant_id: TenantId,
        user_id: UserId,
        product_id: ProductId,
        quantity: int,
        unit_price: Decimal,
        title: str,
    ) -> Cart:
        cart = self.get_or_create(tenant_id, user_id)
        existing = next((i for i in cart.items if str(i.product_id) == str(product_id)), None)
        if existing:
            for m in self._session.query(CartItemModel).filter(
                CartItemModel.cart_id == str(cart.cart_id),
                CartItemModel.product_id == str(product_id),
            ):
                m.quantity += quantity
            self._session.flush()
        else:
            self._session.add(
                CartItemModel(
                    cart_id=str(cart.cart_id),
                    product_id=str(product_id),
                    quantity=quantity,
                    unit_price=unit_price,
                    title=title,
                )
            )
            self._session.flush()
        return self.get_or_create(tenant_id, user_id)

    def remove_item(self, tenant_id: TenantId, user_id: UserId, product_id: ProductId) -> Cart:
        cart = self.get_or_create(tenant_id, user_id)
        self._session.query(CartItemModel).filter(
            CartItemModel.cart_id == str(cart.cart_id),
            CartItemModel.product_id == str(product_id),
        ).delete()
        self._session.flush()
        return self.get_or_create(tenant_id, user_id)

    def save(self, cart: Cart) -> None:
        self._session.flush()


class OrderRepository(IOrderRepository):
    def __init__(self, session: Session):
        self._session = session

    def create(self, tenant_id: TenantId, user_id: UserId, cart: Cart) -> Order:
        total = sum(i.unit_price * i.quantity for i in cart.items)
        order = OrderModel(
            tenant_id=_tenant_str(tenant_id),
            user_id=_user_str(user_id),
            cart_id=str(cart.cart_id),
            status="created",
            total_amount=total,
        )
        self._session.add(order)
        self._session.flush()
        for item in cart.items:
            self._session.add(
                OrderItemModel(
                    order_id=order.order_id,
                    product_id=str(item.product_id),
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    title=item.title,
                )
            )
        self._session.flush()
        return Order(
            order_id=OrderId(order.order_id),
            tenant_id=TenantId(UUID(order.tenant_id)),
            user_id=UserId(UUID(order.user_id)),
            cart_id=CartId(UUID(order.cart_id)),
            status=order.status,
            total_amount=Decimal(str(order.total_amount)),
            items=cart.items,
        )

    def get(self, tenant_id: TenantId, order_id: OrderId) -> Order | None:
        r = (
            self._session.query(OrderModel)
            .filter(
                OrderModel.tenant_id == _tenant_str(tenant_id),
                OrderModel.order_id == str(order_id),
            )
            .first()
        )
        if not r:
            return None
        items = [
            CartItem(
                product_id=ProductId(i.product_id),
                quantity=i.quantity,
                unit_price=Decimal(str(i.unit_price)),
                title=i.title,
            )
            for i in r.item_models
        ]
        return Order(
            order_id=OrderId(r.order_id),
            tenant_id=TenantId(UUID(r.tenant_id)),
            user_id=UserId(UUID(r.user_id)),
            cart_id=CartId(UUID(r.cart_id)),
            status=r.status,
            total_amount=Decimal(str(r.total_amount)),
            items=items,
        )

    def update_status(self, tenant_id: TenantId, order_id: OrderId, status: str) -> None:
        r = (
            self._session.query(OrderModel)
            .filter(
                OrderModel.tenant_id == _tenant_str(tenant_id),
                OrderModel.order_id == str(order_id),
            )
            .first()
        )
        if r:
            r.status = status
            self._session.flush()
