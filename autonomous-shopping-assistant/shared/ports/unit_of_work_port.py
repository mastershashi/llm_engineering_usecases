"""Port: unit of work for persistence (DB layer)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Generator


class IUnitOfWork(ABC):
    """Port for transactional boundary. Adapters: SqliteUoW (dev), PostgresUoW (prod)."""

    @abstractmethod
    @contextmanager
    def session(self) -> Generator[Any, None, None]:
        """Yield a session; commit on success, rollback on exception."""
        ...
