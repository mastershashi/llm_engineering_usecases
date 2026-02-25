"""Rate limiter: in-memory (dev), optional Redis (prod)."""
from __future__ import annotations

import time
from collections import defaultdict

from shared.ports.cache_port import ICache


class InMemoryRateLimiter:
    """Simple sliding window: max 60 req/min per key (dev)."""
    def __init__(self, max_per_minute: int = 60):
        self._max = max_per_minute
        self._counts: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        window = now - 60
        self._counts[key] = [t for t in self._counts[key] if t > window]
        if len(self._counts[key]) >= self._max:
            return False
        self._counts[key].append(now)
        return True
