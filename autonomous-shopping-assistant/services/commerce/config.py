"""Commerce service config: dev vs prod (DB, logging, etc.)."""
from __future__ import annotations

from shared.config.settings import get_settings

_settings = get_settings(service_name="commerce")


def get_database_url() -> str:
    return _settings.database.url


def get_logging_level() -> str:
    return _settings.logging.level


def get_logging_format() -> str:
    return _settings.logging.format
