#!/usr/bin/env bash
# AMRPredict — Antibiotic Resistance System
# macOS / Linux launcher (the counterpart to start.bat on Windows)
#
#   ./start.sh                          backend + React app (web/), everything except Train/Reload
#   ./start.sh --flask                  backend + the older Flask app (frontend/) instead
#   ./start.sh --update                 also reinstall/upgrade dependencies (needs internet)
#   ADMIN_TOKEN=some-password ./start.sh   also Train/Reload: type the same
#                                          password on the Train page
#
# Runs the backend in local development mode (DEBUG=True), so no SECRET_KEY
# or ALLOWED_HOSTS is needed; those are for the Railway deployment only.

set -euo pipefail

# Every path below is relative to the project folder, so work from there.
cd "$(dirname "${BASH_SOURCE[0]}")"
VENV=".venv"
UPDATE=0
UI=react
for arg in "$@"; do
    case "$arg" in
        --update) UPDATE=1 ;;
        --flask)  UI=flask ;;
        --react)  UI=react ;;
        *) echo "[ERROR] Unknown option: $arg (use --update, --flask)"; exit 1 ;;
    esac
done

# The React app needs Node.js 18+; without it, fall back to the Flask app
if [ "$UI" = react ] && ! command -v npm >/dev/null 2>&1; then
    echo "[WARN] Node.js (npm) not found, so starting the Flask app instead."
    echo "       Install Node.js 18+ (brew install node) for the React app with the Resistance Explorer."
    UI=flask
fi

BACKEND_PORT="${BACKEND_PORT:-8000}"   # recommended; the frontend expects the API here
if [ "$UI" = react ]; then
    FRONTEND_PORT="${PORT:-5173}"      # Vite's port
else
    FRONTEND_PORT="${PORT:-5001}"      # app.py's own default (5000 is AirPlay on macOS)
fi

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
            brew install libomp || echo "[WARN] Could not install libomp (no internet?)."
        fi
    fi
fi
echo "[2/5] Checked native dependencies."

# --- Python dependencies --------------------------------------------------
# Checked offline first: `pip install --no-index` succeeds only when every
# requirement is already installed at a matching version, and never touches
# the network. So a start with no internet does not hang on pip. Only when
# something is missing does it go online, with a short timeout; if that
# fails the servers start anyway with a warning.
#   ./start.sh --update   force a full online install and upgrade pip
REQS=(-r backend/requirements.txt -r frontend/requirements.txt)
PIP=("$PY" -m pip --disable-pip-version-check)
if [ "$UPDATE" = 1 ]; then
    echo "[3/5] Updating dependencies (--update)..."
    "${PIP[@]}" install --upgrade pip -q || echo "[WARN] Could not upgrade pip."
    "${PIP[@]}" install "${REQS[@]}" -q || echo "[WARN] Some dependencies failed to install."
elif "${PIP[@]}" install --no-index "${REQS[@]}" -q >/dev/null 2>&1; then
    echo "[3/5] Dependencies already installed; skipping (no internet needed)."
else
    echo "[3/5] Installing missing dependencies..."
    if ! "${PIP[@]}" install --timeout 15 --retries 1 "${REQS[@]}" -q; then
        echo "[WARN] Could not install every dependency (no internet?)."
        echo "       Starting anyway; run ./start.sh --update once you are online."
    fi
fi

# React app packages: installed once (and again with --update)
if [ "$UI" = react ] && { [ "$UPDATE" = 1 ] || [ ! -d web/node_modules ]; }; then
    echo "[3/5] Installing the React app's packages (npm ci)..."
    if ! (cd web && npm ci --no-audit --no-fund); then
        echo "[WARN] npm ci failed (no internet?); starting the Flask app instead."
        UI=flask
        FRONTEND_PORT="${PORT:-5001}"
    fi
fi

if ! "$PY" -c "import lightgbm" >/dev/null 2>&1; then
    echo "[WARN] LightGBM could not be imported — forecasting will fall back."
    echo "       Try: brew install libomp"
fi

# --- Port helpers ---------------------------------------------------------
# Recommended ports on every system: 8000 for the backend, 5001 for the
# frontend (app.py's default). 5000 is avoided: AirPlay Receiver owns it on macOS.
port_busy() { lsof -iTCP:"$1" -sTCP:LISTEN -P -n >/dev/null 2>&1; }

find_free_port() {
    local p="$1"
    while port_busy "$p"; do
        p=$((p + 1))
    done
    echo "$p"
}

# Our backend answers /api/health/ with its "models" block; another program
# on the port (another project's server) does not
is_our_backend() { curl -sf --max-time 3 "http://127.0.0.1:$1/api/health/" 2>/dev/null | grep -q '"models"'; }

# Port taken: by this project's backend (an earlier ./start.sh still running)
# it is reused; by another program, the backend moves to the next free port
# and the frontend is pointed at it
REUSE_BACKEND=0
if port_busy "$BACKEND_PORT"; then
    if is_our_backend "$BACKEND_PORT"; then
        echo "[INFO] The backend is already running on port $BACKEND_PORT; using it."
        REUSE_BACKEND=1
    else
        NEW_BACKEND_PORT="$(find_free_port $((BACKEND_PORT + 1)))"
        echo "[INFO] Port $BACKEND_PORT is used by another program; the backend uses $NEW_BACKEND_PORT."
        BACKEND_PORT="$NEW_BACKEND_PORT"
    fi
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
    local ports="$FRONTEND_PORT"
    [ "$REUSE_BACKEND" = 1 ] || ports="$ports $BACKEND_PORT"
    for port in $ports; do
        local stragglers
        stragglers="$(lsof -ti:"$port" -sTCP:LISTEN 2>/dev/null || true)"
        [ -n "$stragglers" ] && echo "$stragglers" | xargs kill -9 2>/dev/null || true
    done
    echo "Servers stopped."
}
trap cleanup EXIT INT TERM

# --- Backend --------------------------------------------------------------
[ "$REUSE_BACKEND" = 1 ] || echo "[4/5] Starting Django backend on http://127.0.0.1:$BACKEND_PORT ..."
# DEBUG=True is local development: no SECRET_KEY or ALLOWED_HOSTS needed.
# Export ADMIN_TOKEN before running this to use Train/Reload.
if [ "$REUSE_BACKEND" = 0 ]; then
    (cd backend && DEBUG=True exec "../$PY" manage.py runserver "$BACKEND_PORT") &
    BACKEND_PID=$!
fi

# Loading the models takes a few seconds; wait up to 60
for _ in $(seq 1 60); do
    is_our_backend "$BACKEND_PORT" && break
    sleep 1
done

if ! is_our_backend "$BACKEND_PORT"; then
    echo "[ERROR] Backend failed to start. Its error is printed above."
    exit 1
fi

# --- Frontend -------------------------------------------------------------
if [ "$UI" = react ]; then
    # Vite serves web/ and passes /api through to the backend (API_PROXY)
    echo "[5/5] Starting React frontend on http://127.0.0.1:$FRONTEND_PORT ..."
    (cd web \
        && API_PROXY="http://127.0.0.1:$BACKEND_PORT" \
           exec npx vite --host 127.0.0.1 --port "$FRONTEND_PORT" --strictPort) &
else
    echo "[5/5] Starting Flask frontend on http://127.0.0.1:$FRONTEND_PORT ..."
    (cd frontend \
        && PORT="$FRONTEND_PORT" \
           BACKEND_URL="http://127.0.0.1:$BACKEND_PORT/api" \
           exec "../$PY" app.py) &
fi
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
echo "   Frontend (UI):  http://127.0.0.1:$FRONTEND_PORT  ($UI app)"
echo "   Backend  (API): http://127.0.0.1:$BACKEND_PORT/api"
echo
if [ -n "${ADMIN_TOKEN:-}" ]; then
    echo "   Train/Reload:   on; use your ADMIN_TOKEN as the password on the Train page."
else
    echo "   Train/Reload:   off. To use them, restart with:"
    echo "                   ADMIN_TOKEN=some-password ./start.sh"
fi
echo
echo "   Press Ctrl+C to stop both servers."
echo

if [[ "$(uname -s)" == "Darwin" ]]; then
    open "http://127.0.0.1:$FRONTEND_PORT" 2>/dev/null || true
fi

wait
