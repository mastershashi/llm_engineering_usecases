"""Logging adapters: console (dev), json (prod)."""
from __future__ import annotations

import json
import logging
import sys
from typing import Any

from shared.ports.logging_port import ILogger


class ConsoleLogger(ILogger):
    """Dev: human-readable console logs."""
    _LEVELS = {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARNING": logging.WARNING, "ERROR": logging.ERROR}

    def __init__(self, name: str, level: str = "DEBUG"):
        self._name = name
        self._log = logging.getLogger(name)
        self._log.setLevel(self._LEVELS.get(level, logging.DEBUG))
        if not self._log.handlers:
            h = logging.StreamHandler(sys.stdout)
            h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
            self._log.addHandler(h)
        self._context: dict[str, Any] = {}

    def _msg(self, message: str, **kwargs: Any) -> str:
        if kwargs or self._context:
            extra = {**self._context, **kwargs}
            return f"{message} | {extra}"
        return message

    def debug(self, message: str, **kwargs: Any) -> None:
        self._log.debug(self._msg(message, **kwargs))

    def info(self, message: str, **kwargs: Any) -> None:
        self._log.info(self._msg(message, **kwargs))

    def warning(self, message: str, **kwargs: Any) -> None:
        self._log.warning(self._msg(message, **kwargs))

    def error(self, message: str, **kwargs: Any) -> None:
        self._log.error(self._msg(message, **kwargs))

    def exception(self, message: str, **kwargs: Any) -> None:
        self._log.exception(self._msg(message, **kwargs))

    def with_context(self, **kwargs: Any) -> ILogger:
        child = ConsoleLogger(self._name)
        child._context = {**self._context, **kwargs}
        child._log = self._log
        return child


class JsonLogger(ILogger):
    """Prod: structured JSON logs for aggregation."""
    _LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}

    def __init__(self, name: str, level: str = "INFO"):
        self._name = name
        self._level = self._LEVELS.get(level, 20)
        self._context: dict[str, Any] = {}

    def _emit(self, level: str, message: str, **kwargs: Any) -> None:
        if self._LEVELS.get(level, 0) < self._level:
            return
        payload = {
            "level": level,
            "logger": self._name,
            "message": message,
            **self._context,
            **kwargs,
        }
        print(json.dumps(payload), file=sys.stdout, flush=True)

    def debug(self, message: str, **kwargs: Any) -> None:
        self._emit("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        self._emit("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._emit("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self._emit("ERROR", message, **kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        self._emit("ERROR", message, **kwargs)

    def with_context(self, **kwargs: Any) -> ILogger:
        child = JsonLogger(self._name)
        child._level = self._level
        child._context = {**self._context, **kwargs}
        return child


def create_logger(service_name: str, format_type: str = "console", level: str = "DEBUG") -> ILogger:
    if format_type == "json":
        return JsonLogger(service_name, level=level)
    return ConsoleLogger(service_name, level=level)
