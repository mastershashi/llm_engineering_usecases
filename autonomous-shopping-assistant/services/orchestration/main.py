"""Orchestration service entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.orchestration.infrastructure.http.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="Orchestration Service", version="0.1.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    app.include_router(router)
    return app


app = create_app()


@app.get("/health")
def health():
    return {"status": "ok", "service": "orchestration"}
