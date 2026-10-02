#!/usr/bin/env python3
"""
Project Chronos — Unified Python Launcher & Deployment Engine
Runs both the FastAPI backend (0.0.0.0:8000) and Vite frontend (0.0.0.0:5173).
Usage: 
  python3 run.py                # Launches Backend + Frontend
  python3 run.py --backend-only # Launches only FastAPI Backend
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
                # Add to PATH
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

def main():
    print("\033[95m")
    print(r"""
  ____  ____   ___       _ _____ ____ _____    ____ _   _ ____   ___  _   _  ___  ____  
 |  _ \|  _ \ / _ \     | | ____/ ___|_   _|  / ___| | | |  _ \ / _ \| \ | |/ _ \/ ___| 
 | |_) | |_) | | | | _  | |  _|| |     | |   | |   | |_| | |_) | | | |  \| | | | \___ \ 
 |  __/|  _ <| |_| || |_| | |__| |___  | |   | |___|  _  |  _ <| |_| | |\  | |_| |___) |
 |_|   |_| \_\\___/  \___/|_____\____| |_|    \____|_| |_|_| \_\\___/|_| \_|\___/|____/  
                                  YEAR 2140 // MAINFRAME
    """)
    print("\033[0m")

    # 1. Initialize SQLite Database Schema
    try:
        from backend.app.database.schema import create_tables
        create_tables()
        print("\033[92m[✔] Central SQLite schema verified and ready.\033[0m")
    except Exception as e:
        print(f"\033[93m[!] Database initialization note: {e}\033[0m")

    processes = []

    def cleanup(signum=None, frame=None):
        print("\n\033[93m[!] Stopping all Project Chronos servers...\033[0m")
        for p in processes:
            try:
                p.terminate()
            except Exception:
                pass
        print("\033[92m[✔] All services stopped cleanly.\033[0m")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # 2. Launch FastAPI Backend
    print("\033[96m[1/2] Launching FastAPI Backend on 0.0.0.0:8000 (LAN accessible)...\033[0m")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT_DIR)
    
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=str(ROOT_DIR),
        env=env
    )
    processes.append(backend_proc)

    # 3. Check for --backend-only flag
    if "--backend-only" in sys.argv or "--api-only" in sys.argv:
        print("\033[93m[i] Running in --backend-only mode.\033[0m")
    else:
        # Locate npm binary
        npm_bin = resolve_npm_path()

        if not npm_bin:
            print("\n\033[91m[!] Node.js & npm were not detected on this system.\033[0m")
            print("\033[93mTo run the React Frontend, please install Node.js using one of the following:\033[0m")
            print("  - Homebrew: \033[96mbrew install node\033[0m")
            print("  - Conda:    \033[96mconda install -c conda-forge nodejs\033[0m")
            print("  - Official: \033[96mhttps://nodejs.org\033[0m")
            print("\n\033[92m[i] The FastAPI Backend is currently running at http://127.0.0.1:8000/docs\033[0m")
            print("Press \033[91mCtrl+C\033[0m to exit.")
        else:
            # Check node_modules
            if not (FRONTEND_DIR / "node_modules").exists():
                print(f"\033[93m[i] Installing frontend dependencies using {npm_bin}...\033[0m")
                subprocess.run([npm_bin, "install"], cwd=str(FRONTEND_DIR), check=True)

            # Launch React Frontend
            print("\033[96m[2/2] Launching React Frontend on 0.0.0.0:5173 (LAN accessible)...\033[0m")
            frontend_proc = subprocess.Popen(
                [npm_bin, "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"],
                cwd=str(FRONTEND_DIR),
                env=os.environ.copy()
            )
            processes.append(frontend_proc)

    time.sleep(2)
    print("\n\033[92m================================================================\033[0m")
    print("\033[92m  CHRONOS CORE IS ONLINE & READY\033[0m")
    print("\033[92m================================================================\033[0m")
    print("  🌐 \033[93mLocal Client:\033[0m       \033[96mhttp://localhost:5173\033[0m")
    print("  📡 \033[93mAPI Docs:\033[0m           \033[96mhttp://127.0.0.1:8000/docs\033[0m")
    print("  🏆 \033[93mAdmin Leaderboard:\033[0m  \033[96mhttp://127.0.0.1:8000/api/admin/leaderboard\033[0m")
    print("\033[92m================================================================\033[0m")
    print("Press \033[91mCtrl+C\033[0m to stop all servers simultaneously.\n")

    for p in processes:
        p.wait()

if __name__ == "__main__":
    main()
