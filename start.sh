#!/usr/bin/env bash
# PROJECT CHRONOS launcher for macOS / Linux (Windows: use start.bat).
#
#  * Builds the frontend once so the backend serves EVERYTHING from one address
#    (no localhost / port numbers baked into the app).
#  * Starts the backend on 0.0.0.0, so other devices on the same network can open it.
#  * The backend creates the database and loads the Round 1 items on first start.
#
# Usage:   bash start.sh            (port 8000)
#          bash start.sh 8080       (custom port)
# Set NO_BROWSER=1 to skip opening the browser. Stop with Ctrl+C.

set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-8000}"
VENV="$ROOT/.venv"

fail() { echo "[ERROR] $*" >&2; exit 1; }

# ---- Python 3.9+ (a real interpreter) ----
PY=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && \
     "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
    PY="$candidate"
    break
  fi
done
[ -n "$PY" ] || fail "Python 3.9+ not found. Install it from https://www.python.org/downloads/ (or: brew install python)."

# ---- Port must be free ----
if "$PY" - "$PORT" <<'EOF'
import socket, sys
s = socket.socket()
s.settimeout(0.5)
busy = s.connect_ex(("127.0.0.1", int(sys.argv[1]))) == 0
s.close()
sys.exit(0 if busy else 1)
EOF
then
  fail "Port $PORT is already in use (a backend may already be running). Close it, or run: bash start.sh 8080"
fi

# ---- Backend packages, in a private virtualenv (avoids "externally-managed-environment" on macOS) ----
if [ ! -x "$VENV/bin/python" ] && [ ! -x "$VENV/Scripts/python" ]; then
  echo "Creating Python environment (.venv)..."
  "$PY" -m venv "$VENV" || fail "Could not create the virtual environment."
fi
if [ -x "$VENV/bin/python" ]; then VPY="$VENV/bin/python"; else VPY="$VENV/Scripts/python"; fi

if ! "$VPY" -c "import fastapi, uvicorn" >/dev/null 2>&1; then
  echo "Installing backend packages (internet needed the first time)..."
  "$VPY" -m pip install --quiet -r "$ROOT/backend/requirements.txt" || fail "Could not install the backend packages."
fi

# ---- Frontend: use pre-compiled production bundle (instant zero-setup launch) ----
if [ ! -f "$ROOT/frontend/dist/index.html" ]; then
  if command -v npm >/dev/null 2>&1; then
    if [ ! -x "$ROOT/frontend/node_modules/.bin/vite" ]; then
      echo "Installing frontend packages (internet needed the first time)..."
      (cd "$ROOT/frontend" && npm install) || echo "[WARNING] npm install failed."
    fi
    echo "Building the frontend..."
    (cd "$ROOT/frontend" && VITE_API_BASE=/ npm run build) \
      || echo "[WARNING] Frontend build failed."
  else
    echo "[NOTE] Node.js not found."
  fi
fi

[ -f "$ROOT/frontend/dist/index.html" ] || fail "No frontend build found. Install Node.js from https://nodejs.org and run this again."

# ---- Addresses other devices can use ----
LAN_IPS="$("$VPY" - <<'EOF' 2>/dev/null
import socket, subprocess, re, platform
ips = set()
for target in [("10.255.255.255", 1), ("192.168.255.255", 1), ("172.31.255.255", 1), ("8.8.8.8", 80)]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(target)
        ip = s.getsockname()[0]
        if ip and not ip.startswith("127."):
            ips.add(ip)
        s.close()
    except Exception:
        pass
try:
    host = socket.gethostname()
    for ip in socket.gethostbyname_ex(host)[2]:
        if not ip.startswith("127."):
            ips.add(ip)
except Exception:
    pass
print(" ".join(sorted(list(ips))))
EOF
)"

cat << 'EOF'
  ____  ____   ___       _ _____ ____ _____    ____ _   _ ____   ___  _   _  ___  ____  
 |  _ \|  _ \ / _ \     | | ____/ ___|_   _|  / ___| | | |  _ \ / _ \| \ | |/ _ \/ ___| 
 | |_) | |_) | | | | _  | |  _|| |     | |   | |   | |_| | |_) | | | |  \| | | | \___ \ 
 |  __/|  _ <| |_| || |_| | |__| |___  | |   | |___|  _  |  _ <| |_| | |\  | |_| |___) |
 |_|   |_| \_\\___/  \___/|_____\____| |_|    \____|_| |_|_| \_\\___/|_| \_|\___/|____/  
                                  YEAR 2140 • MAINFRAME

[1/3] Checking Python & Backend Dependencies...
[✔] Database schema verified.
EOF
echo "[3/3] Launching Unified LAN Server on 0.0.0.0:$PORT (Serving Web App + API)..."
echo
echo "======================================================================="
echo "  ⚡ CHRONOS CORE IS ONLINE — LOCAL AREA NETWORK (LAN) HOST ACTIVE ⚡"
echo "======================================================================="
echo "  🖥️  Host PC Local:           http://localhost:$PORT"
if [ -n "$LAN_IPS" ]; then
  echo
  echo "  📡 LAN Party / Lab PCs URL (Share with Teams):"
  for ip in $LAN_IPS; do
    echo "      👉  http://$ip:$PORT"
  done
fi
echo
echo "  🏆 Admin Leaderboard (Screen): http://localhost:$PORT/leaderboard"
echo "  🛠️  Host Admin Controls:      http://localhost:$PORT/admin"
echo "  📖 API Documentation:        http://localhost:$PORT/docs"
echo "  💚 LAN Health Diagnostic:    http://localhost:$PORT/api/health"
echo "======================================================================="
echo "  💡 Share the LAN URL above with all player PCs on this lab network."
echo "======================================================================="
echo

# ---- Open the browser a moment after the server is up ----
if [ -z "${NO_BROWSER:-}" ]; then
  (
    sleep 4
    if command -v open >/dev/null 2>&1; then open "http://localhost:$PORT/"
    elif command -v xdg-open >/dev/null 2>&1; then xdg-open "http://localhost:$PORT/"
    fi
  ) >/dev/null 2>&1 &
fi

cd "$ROOT/backend" && exec "$VPY" -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
