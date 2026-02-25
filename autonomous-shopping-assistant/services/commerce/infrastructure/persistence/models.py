"""SQLAlchemy models for Commerce (dev SQLite / prod Postgres)."""
from __future__ import annotations

from decimal import Decimal
from uuid import uuid4, UUID
import json

from sqlalchemy import create_engine, Column, String, Numeric, Text, ForeignKey, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship, Session
from sqlalchemy.sql import func

Base = declarative_base()


def _uuid4_str():
    return str(uuid4())


class ProductModel(Base):
    __tablename__ = "products"
    product_id = Column(String(36), primary_key=True, default=_uuid4_str)
    tenant_id = Column(String(36), nullable=False, index=True)
    external_id = Column(String(255), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    price = Column(Numeric(12, 2), nullable=False)
    attributes = Column(Text, default="{}")  # JSON string for SQLite; use JSONB in Postgres

    def get_attributes(self):
        try:
            return json.loads(self.attributes) if self.attributes else {}
        except Exception:
            return {}


class CartModel(Base):
    __tablename__ = "carts"
    cart_id = Column(String(36), primary_key=True, default=_uuid4_str)
    tenant_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CartItemModel(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cart_id = Column(String(36), ForeignKey("carts.cart_id"), nullable=False)
    product_id = Column(String(36), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False)
    title = Column(String(500), nullable=False)
    cart = relationship("CartModel", backref="item_models")


class OrderModel(Base):
    __tablename__ = "orders"
    order_id = Column(String(36), primary_key=True, default=_uuid4_str)
    tenant_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    cart_id = Column(String(36), nullable=False)
    status = Column(String(50), nullable=False, default="created")
    total_amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OrderItemModel(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(36), ForeignKey("orders.order_id"), nullable=False)
    product_id = Column(String(36), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    title = Column(String(500), nullable=False)
    order = relationship("OrderModel", backref="item_models")
