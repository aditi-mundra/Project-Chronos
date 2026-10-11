#!/usr/bin/env python3
"""
Project Chronos — Unified LAN Party & Lab Deployment Engine
Hosts both the React Web UI and FastAPI REST API on a single port (0.0.0.0:8000).

Usage:
  python3 run.py            # Unified single-server mode (Default, port 8000)
  python3 run.py --port 8080# Run on custom port 8080
  python3 run.py --build    # Rebuild frontend and launch single-server
  python3 run.py --dev      # Dual-server dev mode (Vite on 5173 + FastAPI on 8000)
"""

import os
import sys
import shutil
import subprocess
import signal
import socket
import re
import platform
import time
import glob
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"
DIST_DIR = FRONTEND_DIR / "dist"

# Ensure root is in sys.path
sys.path.insert(0, str(ROOT_DIR))

def get_lan_ip_addresses() -> list:
    """
    Discovers all non-loopback IPv4 addresses on the host machine across
    Ethernet, Wi-Fi, and active network adapters.
    """
    ips = set()

    # Method 1: Connect UDP socket to routable targets (no packets actually sent)
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

    # Method 2: Hostname resolution
    try:
        host = socket.gethostname()
        for ip in socket.gethostbyname_ex(host)[2]:
            if not ip.startswith("127."):
                ips.add(ip)
    except Exception:
        pass

    # Method 3: System utility fallback (ipconfig, ifconfig, hostname)
    try:
        sys_name = platform.system().lower()
        if sys_name == "windows":
            out = subprocess.check_output("ipconfig", text=True, errors="ignore")
            for match in re.finditer(r"IPv4 Address[.\s]+:\s*([0-9.]+)", out):
                ips.add(match.group(1))
        elif sys_name in ["darwin", "linux"]:
            try:
                out = subprocess.check_output(["ifconfig"], text=True, errors="ignore")
                for match in re.finditer(r"inet\s+([0-9.]+)", out):
                    ip = match.group(1)
                    if not ip.startswith("127."):
                        ips.add(ip)
            except Exception:
                pass
    except Exception:
        pass

    return sorted(list(ips))

def is_port_in_use(port: int) -> bool:
    """Checks whether the given TCP port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0

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

    # Parse command line arguments
    dev_mode = "--dev" in sys.argv
    force_build = "--build" in sys.argv
    
    port = 8000
    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            try:
                port = int(sys.argv[i + 1])
            except ValueError:
                print(f"\033[91m[!] Invalid port: {sys.argv[i + 1]}. Defaulting to 8000.\033[0m")

    if is_port_in_use(port):
        print(f"\033[91m[ERROR] Port {port} is already in use by another application.\033[0m")
        print(f"        Please stop the conflicting process or choose another port: python3 run.py --port {port + 1}")
        sys.exit(1)

    print("[1/3] Checking Python & Backend Dependencies...")

    # 1. Initialize SQLite Database Schema
    try:
        from backend.app.database.schema import create_tables
        create_tables()
        print("\033[92m[✔] Database schema verified.\033[0m")
    except Exception as e:
        print(f"\033[93m[!] Database initialization note: {e}\033[0m")

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

    lan_ips = get_lan_ip_addresses()

    if dev_mode:
        print(f"\033[96m[DEV MODE] Starting dual-server development setup...\033[0m")
        backend_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", str(port), "--reload"],
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
        print(f"\033[96m[3/3] Launching Unified LAN Server on 0.0.0.0:{port} (Serving Web App + API)...\033[0m")
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", str(port)],
            cwd=str(ROOT_DIR),
            env=env
        )
        processes.append(server_proc)

    time.sleep(1.5)
    print("\n\033[92m=======================================================================\033[0m")
    print("\033[92m  ⚡ CHRONOS CORE IS ONLINE — LOCAL AREA NETWORK (LAN) HOST ACTIVE ⚡\033[0m")
    print("\033[92m=======================================================================\033[0m")
    print(f"  🖥️  \033[93mHost PC Local:\033[0m           \033[96mhttp://localhost:{port}\033[0m")
    
    if lan_ips:
        print(f"\n  📡 \033[93mLAN Party / Lab PCs URL (Share with Teams):\033[0m")
        for ip in lan_ips:
            print(f"      👉  \033[92;1mhttp://{ip}:{port}\033[0m")
    else:
        print(f"  📡 \033[93mLAN Access URL:\033[0m          \033[96mhttp://<HOST_IP>:{port}\033[0m")

    print(f"\n  🏆 \033[93mAdmin Leaderboard (Projector):\033[0m \033[96mhttp://localhost:{port}/leaderboard\033[0m")
    if lan_ips:
        print(f"      LAN View:                \033[96mhttp://{lan_ips[0]}:{port}/leaderboard\033[0m")

    print(f"  🛠️  \033[93mHost Admin Controls:\033[0m      \033[96mhttp://localhost:{port}/admin\033[0m")
    print(f"  📖 \033[93mAPI Documentation:\033[0m        \033[96mhttp://localhost:{port}/docs\033[0m")
    print(f"  💚 \033[93mLAN Health Diagnostic:\033[0m    \033[96mhttp://localhost:{port}/api/health\033[0m")
    print("\033[92m=======================================================================\033[0m")
    print("  💡 \033[97mInstructions for Lab / LAN Deployment:\033[0m")
    print("     1. Make sure all Lab PCs are connected to the same Wi-Fi or Ethernet switch.")
    print(f"     2. Tell players to open \033[92mhttp://{lan_ips[0] if lan_ips else '<HOST_IP>'}:{port}\033[0m in Chrome/Edge/Firefox.")
    print("     3. Project the Leaderboard on the main screen for real-time scores.")
    print("     4. Press \033[91mCtrl+C\033[0m to stop the server at any time.")
    print("\033[92m=======================================================================\033[0m\n")

    for p in processes:
        p.wait()

if __name__ == "__main__":
    main()

