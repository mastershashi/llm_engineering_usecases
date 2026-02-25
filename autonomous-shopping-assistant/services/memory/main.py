"""Memory service entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config.base import get_environment
from shared.adapters.logging_adapter import create_logger
from services.memory.config import get_logging_level, get_logging_format
from services.memory.infrastructure.http.routes import router


def create_app() -> FastAPI:
    log_format = get_logging_format()
    log_level = get_logging_level()
    create_logger("memory", format_type=log_format, level=log_level)
    app = FastAPI(title="Memory Service", version="0.1.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    app.include_router(router)
    return app


app = create_app()


@app.get("/health")
def health():
    return {"status": "ok", "service": "memory"}
