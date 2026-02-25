"""Port: caching."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypeVar

T = TypeVar("T")


class ICache(ABC):
    """Port for cache. Adapters: MemoryCache (dev), RedisCache (prod)."""

    @abstractmethod
    def get(self, key: str) -> Any | None: ...

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...
