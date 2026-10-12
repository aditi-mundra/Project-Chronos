#!/usr/bin/env bash
# PROJECT CHRONOS — Single-Command Launcher (macOS / Linux)
# Single root-level launcher for LAN hosting and lab deployment.

set -e
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

VENV="$ROOT_DIR/.venv"

# 1. Prefer existing virtual environment if present
if [ -x "$VENV/bin/python" ]; then
  VPY="$VENV/bin/python"
elif [ -x "$VENV/bin/python3" ]; then
  VPY="$VENV/bin/python3"
elif [ -x "$VENV/Scripts/python" ]; then
  VPY="$VENV/Scripts/python"
else
  # 2. Locate system Python 3.9+ to bootstrap
  PY=""
  for candidate in python3 python /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
    if command -v "$candidate" >/dev/null 2>&1 && \
       "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
      PY="$candidate"
      break
    fi
  done

  if [ -z "$PY" ]; then
    echo "[ERROR] Python 3.9+ not found. Please install Python 3.9+." >&2
    exit 1
  fi

  echo "[i] Initializing Python virtual environment (.venv)..."
  "$PY" -m venv "$VENV" || echo "[WARNING] Could not create .venv, falling back to system Python."
  
  if [ -x "$VENV/bin/python" ]; then
    VPY="$VENV/bin/python"
  else
    VPY="$PY"
  fi
fi

# 3. Launch unified server via main.py
exec "$VPY" "$ROOT_DIR/main.py" "$@"
