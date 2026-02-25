"""Central settings: dev vs prod for DB, cache, logging, auth, queue."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.config.base import get_environment, get_env, is_dev, is_prod, Environment


@dataclass
class DatabaseSettings:
    url: str
    echo: bool = False
    pool_size: int = 5
    pool_pre_ping: bool = True

    @classmethod
    def for_environment(cls, env: Environment) -> "DatabaseSettings":
        if env == Environment.PROD:
            return cls(
                url=get_env("DATABASE_URL", "postgresql://user:pass@localhost:5432/shopping"),
                echo=False,
                pool_size=20,
                pool_pre_ping=True,
            )
        # Dev: SQLite by default for local run without Postgres
        return cls(
            url=get_env("DATABASE_URL", "sqlite:///./dev.db"),
            echo=get_env("SQL_ECHO", "false").lower() == "true",
            pool_size=5,
            pool_pre_ping=False,
        )


@dataclass
class CacheSettings:
    backend: str  # "memory" | "redis"
    url: str | None = None
    ttl_seconds: int = 300
    key_prefix: str = "shopping"

    @classmethod
    def for_environment(cls, env: Environment) -> "CacheSettings":
        if env == Environment.PROD:
            return cls(
                backend="redis",
                url=get_env("REDIS_URL", "redis://localhost:6379/0"),
                ttl_seconds=600,
                key_prefix="shopping:prod",
            )
        return cls(
            backend="memory",
            url=None,
            ttl_seconds=60,
            key_prefix="shopping:dev",
        )


@dataclass
class LoggingSettings:
    level: str
    format: str  # "console" | "json"
    include_trace: bool = True

    @classmethod
    def for_environment(cls, env: Environment) -> "LoggingSettings":
        if env == Environment.PROD:
            return cls(
                level=get_env("LOG_LEVEL", "INFO"),
                format="json",
                include_trace=True,
            )
        return cls(
            level=get_env("LOG_LEVEL", "DEBUG"),
            format="console",
            include_trace=True,
        )


@dataclass
class AuthSettings:
    backend: str  # "mock" | "jwt"
    jwt_secret: str | None = None
    jwt_algorithm: str = "HS256"
    mock_default_tenant: str | None = None
    mock_default_user: str | None = None

    @classmethod
    def for_environment(cls, env: Environment) -> "AuthSettings":
        if env == Environment.PROD:
            return cls(
                backend="jwt",
                jwt_secret=get_env("JWT_SECRET", "change-me-in-prod"),
                jwt_algorithm="HS256",
            )
        return cls(
            backend="mock",
            mock_default_tenant=get_env("MOCK_TENANT_ID", "00000000-0000-0000-0000-000000000001"),
            mock_default_user=get_env("MOCK_USER_ID", "00000000-0000-0000-0000-000000000002"),
        )


@dataclass
class QueueSettings:
    backend: str  # "memory" | "redis" | "rabbitmq"
    url: str | None = None
    default_queue: str = "default"

    @classmethod
    def for_environment(cls, env: Environment) -> "QueueSettings":
        if env == Environment.PROD:
            return cls(
                backend=get_env("QUEUE_BACKEND", "redis"),
                url=get_env("REDIS_URL", "redis://localhost:6379/1"),
                default_queue="shopping:jobs",
            )
        return cls(
            backend="memory",
            url=None,
            default_queue="shopping:dev",
        )


@dataclass
class AppSettings:
    env: Environment
    service_name: str = "shopping"
    database: DatabaseSettings = field(default_factory=lambda: DatabaseSettings.for_environment(get_environment()))
    cache: CacheSettings = field(default_factory=lambda: CacheSettings.for_environment(get_environment()))
    logging: LoggingSettings = field(default_factory=lambda: LoggingSettings.for_environment(get_environment()))
    auth: AuthSettings = field(default_factory=lambda: AuthSettings.for_environment(get_environment()))
    queue: QueueSettings = field(default_factory=lambda: QueueSettings.for_environment(get_environment()))

    @classmethod
    def load(cls, service_name: str = "shopping") -> "AppSettings":
        env = get_environment()
        return cls(
            env=env,
            service_name=service_name,
            database=DatabaseSettings.for_environment(env),
            cache=CacheSettings.for_environment(env),
            logging=LoggingSettings.for_environment(env),
            auth=AuthSettings.for_environment(env),
            queue=QueueSettings.for_environment(env),
        )


def get_settings(service_name: str = "shopping") -> AppSettings:
    return AppSettings.load(service_name=service_name)
