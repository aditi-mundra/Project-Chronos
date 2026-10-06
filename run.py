#!/usr/bin/env python3
"""
Project Chronos — Unified Single-Server Launcher & Deployment Engine
Hosts both the React Web UI and FastAPI REST API on a single port (0.0.0.0:8000).

Usage:
  python3 run.py            # Unified single-server mode (Default, port 8000)
  python3 run.py --build    # Rebuild frontend and launch single-server
  python3 run.py --dev      # Dual-server dev mode (Vite on 5173 + FastAPI on 8000)
"""

import os
import sys
import shutil
import subprocess
import signal
import time
import glob
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"
DIST_DIR = FRONTEND_DIR / "dist"

# Ensure root is in sys.path
sys.path.insert(0, str(ROOT_DIR))

def resolve_npm_path() -> str:
    """
    Attempts to locate 'npm' across standard macOS/Linux directories,
    Homebrew, NVM, FNM, Volta, and Conda environments.
    """
    # 1. Standard PATH check
    npm_bin = shutil.which("npm")
    if npm_bin:
        return npm_bin

    # 2. Check standard system and package manager paths
    search_paths = [
        "/opt/homebrew/bin",
        "/opt/homebrew/sbin",
        "/usr/local/bin",
        "/usr/bin",
        "/bin",
        "/opt/anaconda3/bin",
        str(Path.home() / ".nvm/versions/node"),
        str(Path.home() / ".fnm/current/bin"),
        str(Path.home() / ".volta/bin"),
        str(Path.home() / ".asdf/shims"),
    ]

    for p in search_paths:
        if os.path.isdir(p):
            candidate = os.path.join(p, "npm")
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                os.environ["PATH"] = f"{p}:{os.environ.get('PATH', '')}"
                return candidate
            
            # Handle NVM wildcard path ~/.nvm/versions/node/v*/bin/npm
            if "node" in p:
                nvm_matches = glob.glob(f"{p}/*/bin/npm")
                if nvm_matches:
                    found = nvm_matches[-1]
                    bin_dir = os.path.dirname(found)
                    os.environ["PATH"] = f"{bin_dir}:{os.environ.get('PATH', '')}"
                    return found

    return ""

def build_frontend_if_needed(force_build=False):
    """Ensures frontend/dist is built and ready to be served by FastAPI."""
    index_html = DIST_DIR / "index.html"
    if not force_build and index_html.exists():
        return True

    npm_bin = resolve_npm_path()
    if not npm_bin:
        if index_html.exists():
            return True
        print("\033[93m[!] npm not found to build frontend. Will serve existing build or API.\033[0m")
        return False

    print("\033[96m[i] Building frontend production bundle for single-server hosting...\033[0m")
    if not (FRONTEND_DIR / "node_modules" / ".bin" / "vite").exists():
        print(f"\033[93m[i] Installing node modules using {npm_bin}...\033[0m")
        subprocess.run([npm_bin, "install"], cwd=str(FRONTEND_DIR), check=True)

    subprocess.run([npm_bin, "run", "build"], cwd=str(FRONTEND_DIR), check=True)
    print("\033[92m[✔] Frontend successfully compiled into frontend/dist.\033[0m")
    return True

def main():
    print("\033[95m")
    print(r"""
  ____  ____   ___       _ _____ ____ _____    ____ _   _ ____   ___  _   _  ___  ____  
 |  _ \|  _ \ / _ \     | | ____/ ___|_   _|  / ___| | | |  _ \ / _ \| \ | |/ _ \/ ___| 
 | |_) | |_) | | | | _  | |  _|| |     | |   | |   | |_| | |_) | | | |  \| | | | \___ \ 
 |  __/|  _ <| |_| || |_| | |__| |___  | |   | |___|  _  |  _ <| |_| | |\  | |_| |___) |
 |_|   |_| \_\\___/  \___/|_____\____| |_|    \____|_| |_|_| \_\\___/|_| \_|\___/|____/  
                                  YEAR 2140 • MAINFRAME
    """)
    print("\033[0m")

    # 1. Initialize SQLite Database Schema
    try:
        from backend.app.database.schema import create_tables
        create_tables()
        print("\033[92m[✔] Central SQLite schema verified and ready.\033[0m")
    except Exception as e:
        print(f"\033[93m[!] Database initialization note: {e}\033[0m")

    # Check flags
    dev_mode = "--dev" in sys.argv
    force_build = "--build" in sys.argv

    if not dev_mode:
        # Build frontend for single-server hosting
        build_frontend_if_needed(force_build=force_build)

    processes = []

    def cleanup(signum=None, frame=None):
        print("\n\033[93m[!] Stopping Project Chronos server...\033[0m")
        for p in processes:
            try:
                p.terminate()
            except Exception:
                pass
        print("\033[92m[✔] Server stopped cleanly.\033[0m")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT_DIR)

    if dev_mode:
        print("\033[96m[DEV MODE] Starting dual-server development setup...\033[0m")
        backend_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
            cwd=str(ROOT_DIR),
            env=env
        )
        processes.append(backend_proc)

        npm_bin = resolve_npm_path()
        if npm_bin:
            frontend_proc = subprocess.Popen(
                [npm_bin, "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"],
                cwd=str(FRONTEND_DIR),
                env=os.environ.copy()
            )
            processes.append(frontend_proc)
    else:
        # Unified Single Server (FastAPI serving both Static Web UI + REST API)
        print("\033[96m[1/1] Launching Unified Single Server on 0.0.0.0:8000...\033[0m")
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
            cwd=str(ROOT_DIR),
            env=env
        )
        processes.append(server_proc)

    time.sleep(1.5)
    print("\n\033[92m================================================================\033[0m")
    print("\033[92m  CHRONOS CORE IS ONLINE & READY (UNIFIED SINGLE SERVER)\033[0m")
    print("\033[92m================================================================\033[0m")
    print("  🌐 \033[93mWeb App & Game:\033[0m     \033[96mhttp://localhost:8000\033[0m")
    print("  📡 \033[93mAPI Docs:\033[0m           \033[96mhttp://localhost:8000/docs\033[0m")
    print("  🏆 \033[93mAdmin Leaderboard:\033[0m  \033[96mhttp://localhost:8000/api/admin/leaderboard\033[0m")
    print("\033[92m================================================================\033[0m")
    print("Press \033[91mCtrl+C\033[0m to stop server.\n")

    for p in processes:
        p.wait()

if __name__ == "__main__":
    main()
