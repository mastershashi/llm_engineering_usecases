"""Port: message queue / job queue."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Awaitable


class IMessageQueue(ABC):
    """Port for queue. Adapters: MemoryQueue (dev), RedisQueue (prod)."""

    @abstractmethod
    def publish(self, queue_name: str, message: dict[str, Any]) -> None: ...

    @abstractmethod
    def subscribe(
        self,
        queue_name: str,
        handler: Callable[[dict[str, Any]], Awaitable[None] | None],
    ) -> None: ...


class IQueueConsumer(ABC):
    """Port for long-running consumer (prod)."""

    @abstractmethod
    def start(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...
