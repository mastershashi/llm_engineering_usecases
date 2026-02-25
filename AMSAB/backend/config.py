"""Central configuration for AMSAB backend."""
from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM providers
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Architect model – use a cheap/fast model for planning
    architect_model: str = "gpt-4o-mini"
    # Execution model – used for complex reasoning inside tasks
    worker_model: str = "gpt-4o"

    # Local Llama via Ollama (optional fast planner)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    use_ollama_for_planning: bool = False

    # Paths
    base_dir: Path = Path(__file__).parent.parent
    sqlite_path: str = str(Path(__file__).parent.parent / "state.db")
    chroma_path: str = str(Path(__file__).parent.parent / "chroma_db")
    # Workspace is inside the project dir (accessible to Docker/Colima bind-mounts).
    # uvicorn --reload-dir backend ensures this folder is never watched for reloads.
    workspace_dir: str = str(Path(__file__).parent.parent / "workspace")

    # Docker
    docker_image: str = "amsab-worker:latest"
    docker_network: str = "none"           # air-gapped by default
    docker_workspace_mount: str = "/workspace"
    docker_timeout_seconds: int = 120

    # CORS / server
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    host: str = "0.0.0.0"
    port: int = 8088

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
