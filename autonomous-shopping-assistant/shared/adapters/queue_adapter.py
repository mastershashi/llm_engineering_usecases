"""Queue adapters: in-memory (dev), Redis (prod)."""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Callable, Awaitable

from shared.ports.queue_port import IMessageQueue


class MemoryQueue(IMessageQueue):
    """Dev: in-memory queues; subscribe runs handler in same process."""

    def __init__(self):
        self._queues: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._handlers: dict[str, list[Callable]] = defaultdict(list)
        self._lock = asyncio.Lock()

    def publish(self, queue_name: str, message: dict[str, Any]) -> None:
        self._queues[queue_name].append(message)
        for h in self._handlers[queue_name]:
            try:
                result = h(message)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception:
                pass

    def subscribe(
        self,
        queue_name: str,
        handler: Callable[[dict[str, Any]], Awaitable[None] | None],
    ) -> None:
        self._handlers[queue_name].append(handler)


class RedisQueue(IMessageQueue):
    """Prod: Redis list as queue (LPUSH/BRPOP)."""

    def __init__(self, url: str):
        import redis
        self._client = redis.from_url(url, decode_responses=True)
        self._handlers: dict[str, Callable] = {}

    def publish(self, queue_name: str, message: dict[str, Any]) -> None:
        import json
        self._client.lpush(queue_name, json.dumps(message))

    def subscribe(
        self,
        queue_name: str,
        handler: Callable[[dict[str, Any]], Awaitable[None] | None],
    ) -> None:
        self._handlers[queue_name] = handler

    def blocking_consume(self, queue_name: str, timeout: int = 5) -> None:
        """Block and process messages (run in worker process)."""
        import json
        while True:
            _, raw = self._client.brpop(queue_name, timeout=timeout)
            if not raw:
                continue
            try:
                msg = json.loads(raw)
                h = self._handlers.get(queue_name)
                if h:
                    result = h(msg)
                    if asyncio.iscoroutine(result):
                        asyncio.run(result)
            except Exception:
                pass


def create_queue(backend: str, url: str | None = None) -> IMessageQueue:
    if backend == "memory":
        return MemoryQueue()
    if backend == "redis" and url:
        return RedisQueue(url)
    return MemoryQueue()
