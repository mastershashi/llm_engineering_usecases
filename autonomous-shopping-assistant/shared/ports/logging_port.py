"""Port: logging (abstract)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ILogger(ABC):
    """Port for logging. Adapters: ConsoleLogger (dev), JsonLogger (prod)."""

    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None: ...

    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None: ...

    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None: ...

    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None: ...

    @abstractmethod
    def exception(self, message: str, **kwargs: Any) -> None: ...

    def with_context(self, **kwargs: Any) -> "ILogger":
        """Return a logger with bound context (e.g. request_id). Default: return self."""
        return self
