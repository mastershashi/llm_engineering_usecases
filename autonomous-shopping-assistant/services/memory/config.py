"""Memory service config."""
from shared.config.settings import get_settings

_settings = get_settings(service_name="memory")


def get_database_url() -> str:
    return _settings.database.url


def get_logging_format() -> str:
    return _settings.logging.format


def get_logging_level() -> str:
    return _settings.logging.level
