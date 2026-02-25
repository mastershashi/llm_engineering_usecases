"""Commerce service entrypoint. Run: ENV=dev uvicorn services.commerce.main:app --reload."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config.base import get_environment
from shared.adapters.logging_adapter import create_logger
from services.commerce.config import get_database_url, get_logging_level, get_logging_format
from services.commerce.infrastructure.http.routes import router
from services.commerce.infrastructure.persistence.unit_of_work import CommerceUnitOfWork
from services.commerce.infrastructure.persistence.models import ProductModel
from decimal import Decimal


def seed_products_if_needed():
    """Seed a few products for dev."""
    from services.commerce.config import get_database_url
    uow = CommerceUnitOfWork(get_database_url())
    with uow.session() as s:
        if s.query(ProductModel).count() > 0:
            return
        tid = "00000000-0000-0000-0000-000000000001"
        for i, (title, cat, price) in enumerate([
            ("Running Shoes Pro", "footwear", 89.99),
            ("Trail Running Shoes", "footwear", 79.99),
            ("Lightweight Running Shoes", "footwear", 59.99),
            ("Wireless Earbuds", "electronics", 49.99),
            ("Yoga Mat", "sports", 29.99),
        ], start=1):
            s.add(ProductModel(
                product_id=f"prod-{i}",
                tenant_id=tid,
                title=title,
                description=f"Great {title} for everyday use.",
                category=cat,
                price=Decimal(str(price)),
                attributes="{}",
            ))


@asynccontextmanager
async def lifespan(app: FastAPI):
    if get_environment().value == "dev":
        seed_products_if_needed()
    yield
    # shutdown


def create_app() -> FastAPI:
    env = get_environment()
    log_format = get_logging_format()
    log_level = get_logging_level()
    logger = create_logger("commerce", format_type=log_format, level=log_level)
    app = FastAPI(
        title="Commerce Service",
        description="Catalog, cart, orders",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()


@app.get("/health")
def health():
    return {"status": "ok", "service": "commerce"}
