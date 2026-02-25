"""Agent service config: dev vs prod (LLM, commerce/memory URLs)."""
import os

from shared.config.settings import get_settings
from shared.config.base import get_environment

_settings = get_settings(service_name="agent")
_env = get_environment()


def get_commerce_url() -> str:
    return os.getenv("COMMERCE_URL", "http://localhost:8001")


def get_memory_url() -> str:
    return os.getenv("MEMORY_URL", "http://localhost:8002")


def get_llm_backend() -> str:
    return os.getenv("LLM_BACKEND", "stub" if _env.value == "dev" else "openai")
