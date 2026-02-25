"""Gateway config."""
import os

def get_orchestration_url() -> str:
    return os.getenv("ORCHESTRATION_URL", "http://localhost:8000")
