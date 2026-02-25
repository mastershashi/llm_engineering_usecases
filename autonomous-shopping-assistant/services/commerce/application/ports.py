"""Commerce ports: repository and external interfaces."""
from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from uuid import UUID

from shared.domain.value_objects import TenantId, UserId, ProductId, CartId, OrderId

from ..domain.entities import Product, Cart, Order


class IProductRepository(ABC):
    @abstractmethod
    def search(
        self,
        tenant_id: TenantId,
        query: str | None = None,
        category: str | None = None,
        max_price: float | None = None,
        limit: int = 20,
    ) -> list[Product]: ...

    @abstractmethod
    def get_by_id(self, tenant_id: TenantId, product_id: ProductId) -> Product | None: ...

    @abstractmethod
    def add(self, product: Product) -> None: ...


class ICartRepository(ABC):
    @abstractmethod
    def get_or_create(self, tenant_id: TenantId, user_id: UserId) -> Cart: ...

    @abstractmethod
    def add_item(
        self,
        tenant_id: TenantId,
        user_id: UserId,
        product_id: ProductId,
        quantity: int,
        unit_price: Decimal,
        title: str,
    ) -> Cart: ...

    @abstractmethod
    def remove_item(
        self,
        tenant_id: TenantId,
        user_id: UserId,
        product_id: ProductId,
    ) -> Cart: ...

    @abstractmethod
    def save(self, cart: Cart) -> None: ...


class IOrderRepository(ABC):
    @abstractmethod
    def create(self, tenant_id: TenantId, user_id: UserId, cart: Cart) -> Order: ...

    @abstractmethod
    def get(self, tenant_id: TenantId, order_id: OrderId) -> Order | None: ...

    @abstractmethod
    def update_status(self, tenant_id: TenantId, order_id: OrderId, status: str) -> None: ...
