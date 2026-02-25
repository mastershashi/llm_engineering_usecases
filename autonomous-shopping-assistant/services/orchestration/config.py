"""Orchestration config."""
import os

def get_agent_url() -> str:
    return os.getenv("AGENT_URL", "http://localhost:8003")

def get_memory_url() -> str:
    return os.getenv("MEMORY_URL", "http://localhost:8002")
