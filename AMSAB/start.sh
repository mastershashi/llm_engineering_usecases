#!/bin/sh
# ═══════════════════════════════════════════════════════════════════════════════
#  AMSAB — Start All Services
#  Usage:  ./start.sh
#  Stop:   Ctrl+C
# ═══════════════════════════════════════════════════════════════════════════════

PROJ_DIR="$(cd "$(dirname "$0")" && pwd)"
NODE_BIN="$PROJ_DIR/.node/bin"
VENV_BIN="$PROJ_DIR/.venv/bin"

# ── Banner ────────────────────────────────────────────────────────────────────
printf "\n"
printf "  ██████╗   AMSAB\n"
printf "  ██╔══██╗  Autonomous Multi-Step Agent Builder\n"
printf "  ███████║\n"
printf "  ██╔══██║\n"
printf "  ██║  ██║  Starting all services...\n"
printf "  ╚═╝  ╚═╝\n\n"

# ── Helpers ───────────────────────────────────────────────────────────────────
ok()   { printf "  [OK]  $1\n"; }
warn() { printf "  [!!]  $1\n"; }
die()  { printf "  [ERR] $1\n"; exit 1; }
say()  { printf "\n  ---  $1\n"; }

# ── Pre-flight checks ─────────────────────────────────────────────────────────
say "Pre-flight checks"

# 1. .env / OpenAI key
if [ ! -f "$PROJ_DIR/.env" ]; then
    if [ -f "$PROJ_DIR/env.example" ]; then
        cp "$PROJ_DIR/env.example" "$PROJ_DIR/.env"
    else
        printf "OPENAI_API_KEY=\nARCHITECT_MODEL=gpt-4o\nWORKER_MODEL=gpt-4o-mini\n" > "$PROJ_DIR/.env"
    fi
    die ".env not found — created a blank one at $PROJ_DIR/.env\n       Set OPENAI_API_KEY=sk-... then re-run."
fi
if ! grep -q "OPENAI_API_KEY=sk-" "$PROJ_DIR/.env" 2>/dev/null; then
    die "OPENAI_API_KEY not set.\n       Edit: $PROJ_DIR/.env\n       For Ollama-only mode set: OPENAI_API_KEY=sk-dummy"
fi

# Check planning mode
if grep -q "USE_OLLAMA_FOR_PLANNING=true" "$PROJ_DIR/.env" 2>/dev/null; then
    ok "Planning mode: Ollama (local LLM) — OpenAI only used for self-correction patches"
    # Verify Ollama is reachable
    OLLAMA_URL=$(grep "OLLAMA_BASE_URL=" "$PROJ_DIR/.env" | cut -d= -f2 | tr -d ' ')
    OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
    if ! curl -sf --max-time 2 "$OLLAMA_URL" >/dev/null 2>&1; then
        warn "Ollama not reachable at $OLLAMA_URL — start it with: ollama serve"
    else
        OLLAMA_MODEL=$(grep "OLLAMA_MODEL=" "$PROJ_DIR/.env" | cut -d= -f2 | tr -d ' ')
        OLLAMA_MODEL="${OLLAMA_MODEL:-llama3}"
        ok "Ollama is running at $OLLAMA_URL (model: $OLLAMA_MODEL)"
    fi
else
    ok "Planning mode: OpenAI (cloud LLM)"
fi

# 2. Python venv
if [ ! -x "$VENV_BIN/python3" ]; then
    warn "Python venv missing — creating..."
    python3 -m venv "$PROJ_DIR/.venv"
    ok "venv created"
fi
ok "Python venv ready"

# 3. Python packages
if ! "$VENV_BIN/python3" -c "import fastapi, chromadb, openai, uvicorn" 2>/dev/null; then
    warn "Some Python packages missing — installing..."
    "$VENV_BIN/pip" install -r "$PROJ_DIR/requirements.txt" -q \
        --trusted-host pypi.org --trusted-host files.pythonhosted.org
    ok "Python packages installed"
else
    ok "Python packages ready"
fi

# 4. Node.js
if [ -x "$NODE_BIN/node" ]; then
    export PATH="$NODE_BIN:$PATH"
    ok "Node.js (bundled) ready: $(node --version)"
elif command -v node >/dev/null 2>&1; then
    ok "Node.js (system) ready: $(node --version)"
else
    die "Node.js not found. Install from https://nodejs.org or restore .node/ bundle."
fi

# 5. npm packages
if [ ! -d "$PROJ_DIR/frontend/node_modules/.bin/next" ] && \
   [ ! -f "$PROJ_DIR/frontend/node_modules/.bin/next" ]; then
    warn "node_modules missing — running npm install (first-time, ~30 s)..."
    npm --prefix "$PROJ_DIR/frontend" install --silent
    ok "npm packages installed"
else
    ok "npm packages ready"
fi

# 6. Docker (optional)
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    ok "Docker is running"
    if docker image inspect amsab-worker:latest >/dev/null 2>&1; then
        ok "Docker worker image ready (amsab-worker:latest)"
    else
        warn "Worker image not built — node execution will fail!"
        warn "Fix: docker build -t amsab-worker:latest -f docker/worker/Dockerfile ."
    fi
else
    warn "Docker not running — task execution will fail (UI + planning still work)"
fi

# ── Cleanup handler ───────────────────────────────────────────────────────────
BACKEND_PID=""
FRONTEND_PID=""
TAIL_PID=""

kill_tree() {
    # Kill a PID and all its descendants
    local pid="$1"
    local sig="${2:-TERM}"
    [ -z "$pid" ] && return
    # Kill children first (pkill -P sends signal to all direct children)
    pkill -"$sig" -P "$pid" 2>/dev/null || true
    kill -"$sig" "$pid" 2>/dev/null || true
}

cleanup() {
    # Prevent re-entry if user hammers Ctrl+C
    trap - INT TERM
    printf "\n\n  Shutting down AMSAB...\n"

    kill_tree "$TAIL_PID"
    kill_tree "$FRONTEND_PID"
    kill_tree "$BACKEND_PID"

    # Give processes up to 2 s to exit gracefully, then force-kill
    sleep 0.5
    kill_tree "$FRONTEND_PID" KILL
    kill_tree "$BACKEND_PID"  KILL

    printf "  All services stopped.\n\n"
    exit 0
}
trap cleanup INT TERM

# ── Start Backend ─────────────────────────────────────────────────────────────
say "Starting backend (port 8088)"
# Kill any leftover process still holding our ports from a previous run
OLD_BACKEND=$(lsof -ti :8088 2>/dev/null)
[ -n "$OLD_BACKEND" ] && { warn "Port 8088 in use (PID $OLD_BACKEND) — killing..."; kill -9 $OLD_BACKEND 2>/dev/null; sleep 0.5; }
OLD_FRONTEND=$(lsof -ti :3000 2>/dev/null)
[ -n "$OLD_FRONTEND" ] && { warn "Port 3000 in use (PID $OLD_FRONTEND) — killing..."; kill -9 $OLD_FRONTEND 2>/dev/null; sleep 0.5; }
cd "$PROJ_DIR"

"$VENV_BIN/uvicorn" backend.main:app \
    --reload \
    --reload-dir "$PROJ_DIR/backend" \
    --reload-exclude "workspace/*" \
    --reload-exclude "chroma_db/*" \
    --reload-exclude "*.db" \
    --host 0.0.0.0 \
    --port 8088 \
    --log-level warning \
    > "$PROJ_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

# Poll /health with a timeout
printf "  Waiting for backend"
TRIES=0
while ! curl -sf --max-time 1 http://localhost:8088/health >/dev/null 2>&1; do
    TRIES=$((TRIES + 1))
    if [ "$TRIES" -gt 30 ]; then
        printf "\n"
        warn "Backend didn't respond in 15 s. Last log lines:"
        tail -20 "$PROJ_DIR/backend.log"
        die "Backend failed to start."
    fi
    # If the process died, bail early
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        printf "\n"
        warn "Backend process exited unexpectedly. Last log lines:"
        tail -20 "$PROJ_DIR/backend.log"
        die "Backend crashed on startup."
    fi
    printf "."
    sleep 0.5
done
printf "\n"
ok "Backend is up  -> http://localhost:8088"
ok "API docs       -> http://localhost:8088/docs"

# ── Start Frontend ────────────────────────────────────────────────────────────
say "Starting frontend (port 3000)"

npm --prefix "$PROJ_DIR/frontend" run dev \
    > "$PROJ_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

# Poll for "Ready" in the log file (avoids curl issues with Next.js redirects)
printf "  Waiting for frontend"
TRIES=0
while ! grep -q "Ready" "$PROJ_DIR/frontend.log" 2>/dev/null; do
    TRIES=$((TRIES + 1))
    if [ "$TRIES" -gt 60 ]; then
        printf "\n"
        warn "Frontend didn't start in 30 s. Last log lines:"
        tail -20 "$PROJ_DIR/frontend.log"
        die "Frontend failed to start."
    fi
    if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
        printf "\n"
        warn "Frontend process exited unexpectedly. Last log lines:"
        tail -20 "$PROJ_DIR/frontend.log"
        die "Frontend crashed on startup."
    fi
    printf "."
    sleep 0.5
done
printf "\n"

# Detect the actual port Next.js chose (it may skip 3000 if already in use)
FRONTEND_PORT=$(grep -oE 'localhost:[0-9]+' "$PROJ_DIR/frontend.log" | head -1 | cut -d: -f2)
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

ok "Frontend is up -> http://localhost:$FRONTEND_PORT"

# ── All up ────────────────────────────────────────────────────────────────────
printf "\n"
printf "  ╔══════════════════════════════════════════╗\n"
printf "  ║   AMSAB is running!                      ║\n"
printf "  ║                                          ║\n"
printf "  ║   UI      ->  http://localhost:%-5s      ║\n" "$FRONTEND_PORT"
printf "  ║   API     ->  http://localhost:8088       ║\n"
printf "  ║   API docs->  http://localhost:8088/docs  ║\n"
printf "  ║                                          ║\n"
printf "  ║   Logs:  ./backend.log  ./frontend.log   ║\n"
printf "  ║   Stop:  Ctrl+C                          ║\n"
printf "  ╚══════════════════════════════════════════╝\n\n"

# ── Tail both logs so activity is visible ─────────────────────────────────────
tail -F "$PROJ_DIR/backend.log" "$PROJ_DIR/frontend.log" &
TAIL_PID=$!

# Keep alive — exit if either service dies unexpectedly
while true; do
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        printf "\n  [ERR] Backend exited unexpectedly. Check backend.log\n"
        cleanup
    fi
    if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
        printf "\n  [ERR] Frontend exited unexpectedly. Check frontend.log\n"
        cleanup
    fi
    sleep 2
done
