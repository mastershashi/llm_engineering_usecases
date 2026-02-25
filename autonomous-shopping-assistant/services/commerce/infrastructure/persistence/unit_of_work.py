"""Unit of work for Commerce: DB session (dev SQLite / prod Postgres)."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from shared.ports.unit_of_work_port import IUnitOfWork
from services.commerce.infrastructure.persistence.models import Base
from services.commerce.infrastructure.persistence.repositories import (
    ProductRepository,
    CartRepository,
    OrderRepository,
)


class CommerceUnitOfWork(IUnitOfWork):
    """Single UoW for Commerce: same DB URL for dev (SQLite) or prod (Postgres)."""

    def __init__(self, database_url: str):
        self._engine = create_engine(
            database_url,
            echo=False,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        )
        Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine, autocommit=False, autoflush=False)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def product_repo(self, session: Session) -> ProductRepository:
        return ProductRepository(session)

    def cart_repo(self, session: Session) -> CartRepository:
        return CartRepository(session)

    def order_repo(self, session: Session) -> OrderRepository:
        return OrderRepository(session)
