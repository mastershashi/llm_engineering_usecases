"""Cache adapters: in-memory (dev), Redis (prod)."""
from __future__ import annotations

import time
from typing import Any

from shared.ports.cache_port import ICache


class MemoryCache(ICache):
    """Dev: in-memory cache with TTL."""
    _store: dict[str, tuple[Any, float]]

    def __init__(self, default_ttl: int = 300):
        self._store = {}
        self._default_ttl = default_ttl

    def _expire(self) -> None:
        now = time.monotonic()
        for k in list(self._store):
            if self._store[k][1] <= now:
                del self._store[k]

    def get(self, key: str) -> Any | None:
        self._expire()
        if key not in self._store:
            return None
        return self._store[key][0]

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds or self._default_ttl
        self._store[key] = (value, time.monotonic() + ttl)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def exists(self, key: str) -> bool:
        self._expire()
        return key in self._store


class RedisCache(ICache):
    """Prod: Redis backend."""

    def __init__(self, url: str, key_prefix: str = "", default_ttl: int = 300):
        import redis
        self._client = redis.from_url(url, decode_responses=True)
        self._prefix = key_prefix.rstrip(":") + ":" if key_prefix else ""
        self._default_ttl = default_ttl

    def _key(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def get(self, key: str) -> Any | None:
        import json
        raw = self._client.get(self._key(key))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return raw

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        import json
        ttl = ttl_seconds or self._default_ttl
        serialized = json.dumps(value) if not isinstance(value, (str, int, float)) else value
        self._client.setex(self._key(key), ttl, str(serialized))

    def delete(self, key: str) -> None:
        self._client.delete(self._key(key))

    def exists(self, key: str) -> bool:
        return bool(self._client.exists(self._key(key)))


def create_cache(backend: str, url: str | None = None, key_prefix: str = "", ttl_seconds: int = 300) -> ICache:
    if backend == "memory":
        return MemoryCache(default_ttl=ttl_seconds)
    if backend == "redis" and url:
        return RedisCache(url, key_prefix=key_prefix, default_ttl=ttl_seconds)
    return MemoryCache(default_ttl=ttl_seconds)
