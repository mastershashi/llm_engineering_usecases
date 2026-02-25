"""Base configuration and environment detection."""
from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any


class Environment(str, Enum):
    DEV = "dev"
    PROD = "prod"


def _env() -> Environment:
    v = os.getenv("ENV", "dev").lower()
    return Environment.PROD if v == "prod" else Environment.DEV


def _load_env_file(env: Environment) -> None:
    """Load .env.{env} from repo root if present."""
    try:
        from dotenv import load_dotenv
        repo_root = Path(__file__).resolve().parents[2]
        path = repo_root / f".env.{env.value}"
        if path.exists():
            load_dotenv(path)
    except ImportError:
        pass


@lru_cache(maxsize=1)
def get_environment() -> Environment:
    _load_env_file(_env())
    return _env()


def is_dev() -> bool:
    return get_environment() == Environment.DEV


def is_prod() -> bool:
    return get_environment() == Environment.PROD


def get_env(key: str, default: Any = None) -> str | None:
    return os.getenv(key, default)
