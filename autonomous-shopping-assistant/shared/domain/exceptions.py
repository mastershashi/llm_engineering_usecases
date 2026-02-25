"""Shared domain exceptions."""
from __future__ import annotations


class DomainError(Exception):
    """Base for domain errors."""
    pass


class NotFoundError(DomainError):
    """Resource not found."""
    pass


class UnauthorizedError(DomainError):
    """Authentication/authorization failed."""
    pass


class ValidationError(DomainError):
    """Invalid input or state."""
    pass


class RateLimitError(DomainError):
    """Rate limit exceeded."""
    pass
