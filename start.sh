#!/usr/bin/env bash
# AMRPredict — Antibiotic Resistance System
# macOS / Linux launcher (the counterpart to start.bat on Windows)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/.venv"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${PORT:-5055}"

echo
echo " ============================================"
echo "  AMRPredict — Antibiotic Resistance System"
echo " ============================================"
echo

# --- Python ---------------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] python3 not found. Install Python 3.9+ (brew install python)."
    exit 1
fi

# --- Virtualenv -----------------------------------------------------------
if [ ! -x "$VENV/bin/python" ]; then
    echo "[1/5] Creating virtual environment..."
    python3 -m venv "$VENV"
else
    echo "[1/5] Using existing virtual environment."
fi
PY="$VENV/bin/python"

# --- libomp (required by LightGBM on macOS) -------------------------------
# LightGBM's lib_lightgbm.dylib links against @rpath/libomp.dylib. Without it
# the import fails and the whole forecasting model is unavailable.
if [[ "$(uname -s)" == "Darwin" ]]; then
    if ! "$PY" -c "import lightgbm" >/dev/null 2>&1; then
        if command -v brew >/dev/null 2>&1 && [ ! -d "$(brew --prefix)/opt/libomp" ]; then
            echo "[2/5] Installing libomp (LightGBM dependency)..."
            brew install libomp
        fi
    fi
fi
echo "[2/5] Checked native dependencies."

# --- Python dependencies --------------------------------------------------
echo "[3/5] Installing backend + frontend dependencies..."
"$PY" -m pip install --upgrade pip -q
"$PY" -m pip install -r "$ROOT/backend/requirements.txt" -q
"$PY" -m pip install -r "$ROOT/frontend/requirements.txt" -q

if ! "$PY" -c "import lightgbm" >/dev/null 2>&1; then
    echo "[WARN] LightGBM could not be imported — forecasting will fall back."
    echo "       Try: brew install libomp"
fi

# --- Port helpers ---------------------------------------------------------
# macOS note: port 5000 is taken by AirPlay Receiver (Control Center), so the
# frontend defaults to 5055 here rather than the 5000 used on Windows.
port_busy() { lsof -iTCP:"$1" -sTCP:LISTEN -P -n >/dev/null 2>&1; }

find_free_port() {
    local p="$1"
    while port_busy "$p"; do
        p=$((p + 1))
    done
    echo "$p"
}

if port_busy "$BACKEND_PORT"; then
    echo "[ERROR] Port $BACKEND_PORT is already in use (the backend URL is hard-coded to it)."
    echo "        Free it with: lsof -ti:$BACKEND_PORT | xargs kill"
    exit 1
fi

NEW_FRONTEND_PORT="$(find_free_port "$FRONTEND_PORT")"
if [ "$NEW_FRONTEND_PORT" != "$FRONTEND_PORT" ]; then
    echo "[INFO] Port $FRONTEND_PORT busy; using $NEW_FRONTEND_PORT instead."
    FRONTEND_PORT="$NEW_FRONTEND_PORT"
fi

# --- Shutdown handling ----------------------------------------------------
# Job control puts each background job in its own process group, so a single
# `kill -- -PGID` takes down the whole tree. Django's auto-reloader forks a
# child server, which would otherwise survive and keep holding the port.
set -m

BACKEND_PID=""
FRONTEND_PID=""

stop_group() {
    local pid="$1"
    [ -n "$pid" ] || return 0
    kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
}

cleanup() {
    trap - EXIT INT TERM
    echo
    echo "Stopping servers..."
    stop_group "$FRONTEND_PID"
    stop_group "$BACKEND_PID"
    sleep 1
    # Anything still holding a port gets a KILL.
    for port in "$BACKEND_PORT" "$FRONTEND_PORT"; do
        local stragglers
        stragglers="$(lsof -ti:"$port" -sTCP:LISTEN 2>/dev/null || true)"
        [ -n "$stragglers" ] && echo "$stragglers" | xargs kill -9 2>/dev/null || true
    done
    echo "Servers stopped."
}
trap cleanup EXIT INT TERM

# --- Backend --------------------------------------------------------------
echo "[4/5] Starting Django backend on http://127.0.0.1:$BACKEND_PORT ..."
# DEBUG=True is local development: no SECRET_KEY or ALLOWED_HOSTS needed.
# Export ADMIN_TOKEN before running this to use Train/Reload.
(cd "$ROOT/backend" && DEBUG=True exec "$PY" manage.py runserver "$BACKEND_PORT") &
BACKEND_PID=$!

for _ in $(seq 1 30); do
    curl -sf -o /dev/null "http://127.0.0.1:$BACKEND_PORT/api/health/" && break
    sleep 1
done

if ! curl -sf -o /dev/null "http://127.0.0.1:$BACKEND_PORT/api/health/"; then
    echo "[ERROR] Backend failed to start."
    exit 1
fi

# --- Frontend -------------------------------------------------------------
echo "[5/5] Starting Flask frontend on http://127.0.0.1:$FRONTEND_PORT ..."
(cd "$ROOT/frontend" \
    && PORT="$FRONTEND_PORT" \
       BACKEND_URL="http://127.0.0.1:$BACKEND_PORT/api" \
       exec "$PY" app.py) &
FRONTEND_PID=$!

for _ in $(seq 1 30); do
    curl -sf -o /dev/null "http://127.0.0.1:$FRONTEND_PORT/" && break
    sleep 1
done

echo
echo " ============================================"
echo "  Both servers started!"
echo " ============================================"
echo
echo "   Frontend (UI):  http://127.0.0.1:$FRONTEND_PORT"
echo "   Backend  (API): http://127.0.0.1:$BACKEND_PORT/api"
echo
echo "   Press Ctrl+C to stop both servers."
echo

if [[ "$(uname -s)" == "Darwin" ]]; then
    open "http://127.0.0.1:$FRONTEND_PORT" 2>/dev/null || true
fi

wait
