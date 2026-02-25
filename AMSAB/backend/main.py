"""AMSAB FastAPI application entry point."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .api.routes.goals import router as goals_router
from .api.routes.ws import router as ws_router
from .api.routes.mcp import router as mcp_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="AMSAB — Autonomous Multi-Step Agent Builder",
    description=(
        "A Local-First, Sandbox-Native agent framework using Hierarchical Planning "
        "and a Visual State Machine to provide deterministic reliability and "
        "human-in-the-loop safety."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(goals_router)
app.include_router(ws_router)
app.include_router(mcp_router)


@app.on_event("startup")
async def startup() -> None:
    init_db()
    logging.getLogger(__name__).info("AMSAB backend started. DB: %s", settings.sqlite_path)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}
