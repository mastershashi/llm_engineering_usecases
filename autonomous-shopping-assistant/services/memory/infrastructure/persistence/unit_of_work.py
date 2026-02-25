"""Memory UoW."""
from __future__ import annotations

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from shared.ports.unit_of_work_port import IUnitOfWork
from services.memory.infrastructure.persistence.models import Base
from services.memory.infrastructure.persistence.repositories import UserMemoryRepository, SessionHistoryRepository


class MemoryUnitOfWork(IUnitOfWork):
    def __init__(self, database_url: str):
        self._engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        )
        Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine, autocommit=False, autoflush=False)

    @contextmanager
    def session(self):
        s = self._session_factory()
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    def user_memory_repo(self, s: Session) -> UserMemoryRepository:
        return UserMemoryRepository(s)

    def session_history_repo(self, s: Session) -> SessionHistoryRepository:
        return SessionHistoryRepository(s)
