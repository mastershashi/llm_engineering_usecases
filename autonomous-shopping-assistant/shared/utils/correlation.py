"""Correlation and request ID for tracing."""
from __future__ import annotations

import uuid
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def set_request_context(request_id: str | None = None, correlation_id: str | None = None) -> None:
    request_id_var.set(request_id or str(uuid.uuid4()))
    correlation_id_var.set(correlation_id or request_id_var.get())


def get_request_id() -> str:
    return request_id_var.get() or ""


def get_correlation_id() -> str:
    return correlation_id_var.get() or get_request_id()
