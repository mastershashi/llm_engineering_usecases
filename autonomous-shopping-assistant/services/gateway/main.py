"""Gateway entrypoint: auth, rate limit, proxy to orchestration, serve chat UI."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from shared.ports.auth_port import IAuthProvider, AuthResult
from shared.config.settings import get_settings
from shared.adapters.auth_adapter import create_auth_provider
from services.gateway.infrastructure.rate_limit import InMemoryRateLimiter
from services.gateway.infrastructure.upstream import HttpUpstreamClient
from services.gateway.config import get_orchestration_url


class SendMessageBody(BaseModel):
    sessionId: str | None = None
    channel: str = "web"
    message: dict


def get_auth() -> IAuthProvider:
    s = get_settings(service_name="gateway")
    auth_vars = {k: v for k, v in vars(s.auth).items() if k != "backend"}
    return create_auth_provider(s.auth.backend, **auth_vars)


_rate_limiter = InMemoryRateLimiter(max_per_minute=120)
_upstream = None

def get_upstream() -> HttpUpstreamClient:
    global _upstream
    if _upstream is None:
        _upstream = HttpUpstreamClient(get_orchestration_url())
    return _upstream


app = FastAPI(title="Gateway", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.post("/v1/tenants/{tenant_id}/sessions")
def proxy_sessions(
    tenant_id: str,
    body: SendMessageBody,
    request: Request,
    auth: IAuthProvider = Depends(get_auth),
    upstream: HttpUpstreamClient = Depends(get_upstream),
):
    # Rate limit by tenant (or tenant+user when we have auth)
    if not _rate_limiter.allow(tenant_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    try:
        result = auth.authenticate(None, dict(request.headers))
    except Exception:
        result = auth.optional_auth(None)
    if not result:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return upstream.post_sessions(tenant_id, body.model_dump(), result)


@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway"}


# Chat UI: serve from clients/web when running from project root
_ui_path = Path(__file__).resolve().parents[2] / "clients" / "web" / "index.html"


@app.get("/")
def serve_chat_ui():
    """Serve the Personal Shopping Assistant chat UI."""
    if _ui_path.exists():
        return FileResponse(_ui_path, media_type="text/html")
    return {"message": "Gateway API. Chat UI not found. POST /v1/tenants/{tenant_id}/sessions to send messages."}
