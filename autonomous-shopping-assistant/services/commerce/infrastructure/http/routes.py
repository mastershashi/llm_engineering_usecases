"""Commerce HTTP API (FastAPI)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from shared.domain.value_objects import TenantId, UserId, ProductId, OrderId
from shared.domain.exceptions import NotFoundError

from services.commerce.application.use_cases import (
    ProductSearchUseCase,
    GetProductUseCase,
    GetCartUseCase,
    AddToCartUseCase,
    RemoveFromCartUseCase,
    CreateOrderUseCase,
    GetOrderUseCase,
    ConfirmPaymentUseCase,
    AddExternalOfferToCartUseCase,
)
from services.commerce.infrastructure.persistence.unit_of_work import CommerceUnitOfWork
from services.commerce.infrastructure.persistence.repositories import (
    ProductRepository,
    CartRepository,
    OrderRepository,
)


# --- Request/Response DTOs ---
class AddToCartBody(BaseModel):
    productId: str
    quantity: int = 1


class AddExternalToCartBody(BaseModel):
    sourceId: str
    title: str
    price: float
    quantity: int = 1


# --- Dependency: UoW and use cases ---
def get_uow() -> CommerceUnitOfWork:
    from services.commerce.config import get_database_url
    return CommerceUnitOfWork(get_database_url())


# --- Router ---
router = APIRouter(prefix="/v1/tenants/{tenant_id}", tags=["commerce"])


def _tenant(tenant_id: str) -> TenantId:
    return TenantId(UUID(tenant_id))


def _user(user_id: str) -> UserId:
    return UserId(UUID(user_id))


@router.get("/products/search")
def product_search(
    tenant_id: str,
    q: str | None = Query(None),
    category: str | None = Query(None),
    maxPrice: float | None = Query(None),
    limit: int = Query(20, le=100),
    uow: CommerceUnitOfWork = Depends(get_uow),
):
    tid = _tenant(tenant_id)
    with uow.session() as s:
        use_case = ProductSearchUseCase(uow.product_repo(s))
        return use_case.execute(tenant_id=tid, query=q, category=category, max_price=maxPrice, limit=limit)


@router.get("/products/{product_id}")
def get_product(
    tenant_id: str,
    product_id: str,
    uow: CommerceUnitOfWork = Depends(get_uow),
):
    try:
        with uow.session() as s:
            use_case = GetProductUseCase(uow.product_repo(s))
            return use_case.execute(_tenant(tenant_id), ProductId(product_id))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/users/{user_id}/cart")
def get_cart(
    tenant_id: str,
    user_id: str,
    uow: CommerceUnitOfWork = Depends(get_uow),
):
    with uow.session() as s:
        use_case = GetCartUseCase(uow.cart_repo(s))
        return use_case.execute(_tenant(tenant_id), _user(user_id))


@router.post("/users/{user_id}/cart/items/external")
def add_external_to_cart(
    tenant_id: str,
    user_id: str,
    body: AddExternalToCartBody,
    uow: CommerceUnitOfWork = Depends(get_uow),
):
    with uow.session() as s:
        use_case = AddExternalOfferToCartUseCase(uow.cart_repo(s))
        return use_case.execute(
            _tenant(tenant_id),
            _user(user_id),
            body.sourceId,
            body.title,
            body.price,
            quantity=body.quantity,
        )


@router.post("/users/{user_id}/cart/items")
def add_to_cart(
    tenant_id: str,
    user_id: str,
    body: AddToCartBody,
    uow: CommerceUnitOfWork = Depends(get_uow),
):
    try:
        with uow.session() as s:
            use_case = AddToCartUseCase(uow.cart_repo(s), uow.product_repo(s))
            return use_case.execute(
                _tenant(tenant_id),
                _user(user_id),
                ProductId(body.productId),
                quantity=body.quantity,
            )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/users/{user_id}/cart/items/{product_id}")
def remove_from_cart(
    tenant_id: str,
    user_id: str,
    product_id: str,
    uow: CommerceUnitOfWork = Depends(get_uow),
):
    with uow.session() as s:
        use_case = RemoveFromCartUseCase(uow.cart_repo(s))
        return use_case.execute(_tenant(tenant_id), _user(user_id), ProductId(product_id))


@router.post("/users/{user_id}/orders")
def create_order(
    tenant_id: str,
    user_id: str,
    uow: CommerceUnitOfWork = Depends(get_uow),
):
    try:
        with uow.session() as s:
            use_case = CreateOrderUseCase(uow.cart_repo(s), uow.order_repo(s))
            return use_case.execute(_tenant(tenant_id), _user(user_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orders/{order_id}")
def get_order(
    tenant_id: str,
    order_id: str,
    uow: CommerceUnitOfWork = Depends(get_uow),
):
    try:
        with uow.session() as s:
            use_case = GetOrderUseCase(uow.order_repo(s))
            return use_case.execute(_tenant(tenant_id), OrderId(order_id))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/users/{user_id}/orders/{order_id}/confirm-payment")
def confirm_payment(
    tenant_id: str,
    user_id: str,
    order_id: str,
    uow: CommerceUnitOfWork = Depends(get_uow),
):
    """Mock payment: mark order as paid. For real payment, use Stripe client_secret from create_order."""
    try:
        with uow.session() as s:
            use_case = ConfirmPaymentUseCase(uow.order_repo(s))
            return use_case.execute(_tenant(tenant_id), _user(user_id), OrderId(order_id))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
