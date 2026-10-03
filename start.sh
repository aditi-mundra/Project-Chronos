#!/usr/bin/env bash
# ==============================================================================
# PROJECT CHRONOS — UNIFIED ONE-COMMAND LAUNCHER & DEPLOYMENT SCRIPT
# Starts FastAPI Backend (Port 8000) & Vite Frontend (Port 5173) concurrently.
# ==============================================================================

set -e

# Terminal Colors
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${PURPLE}"
cat << "EOF"
  ____  ____   ___       _ _____ ____ _____    ____ _   _ ____   ___  _   _  ___  ____  
 |  _ \|  _ \ / _ \     | | ____/ ___|_   _|  / ___| | | |  _ \ / _ \| \ | |/ _ \/ ___| 
 | |_) | |_) | | | | _  | |  _|| |     | |   | |   | |_| | |_) | | | |  \| | | | \___ \ 
 |  __/|  _ <| |_| || |_| | |__| |___  | |   | |___|  _  |  _ <| |_| | |\  | |_| |___) |
 |_|   |_| \_\\___/  \___/|_____\____| |_|    \____|_| |_|_| \_\\___/|_| \_|\___/|____/  
                                  YEAR 2140 • MAINFRAME
EOF
echo -e "${NC}"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Ensure Python path includes root
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Resolve PATH to include Homebrew, NVM, and standard system paths
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/opt/anaconda3/bin:$HOME/.nvm/versions/node/$(ls $HOME/.nvm/versions/node 2>/dev/null | tail -n 1)/bin:$PATH"

# Cleanup on Ctrl+C / Exit
cleanup() {
    echo -e "\n${YELLOW}[!] Shutting down Project Chronos processes...${NC}"
    if [ -n "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    echo -e "${GREEN}[✔] All services stopped safely.${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 1. Backend Pre-flight
echo -e "${CYAN}[1/3] Checking Python & Backend Dependencies...${NC}"
if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    echo -e "${YELLOW}[i] Installing backend dependencies from backend/requirements.txt...${NC}"
    python3 -m pip install -r backend/requirements.txt --quiet || pip install -r backend/requirements.txt --quiet
fi

# Initialize Database Schema if needed
python3 -c "from backend.app.database.schema import create_tables; create_tables(); print('[✔] Database schema verified.')"

# 2. Check and compile Frontend assets if needed
if [ ! -f "frontend/dist/index.html" ]; then
    echo -e "${CYAN}[2/3] Building React Frontend assets into frontend/dist/...${NC}"
    if command -v npm &>/dev/null; then
        if [ ! -d "frontend/node_modules" ]; then
            (cd frontend && npm install)
        fi
        (cd frontend && npm run build)
        echo -e "${GREEN}[✔] Frontend production build compiled successfully.${NC}"
    else
        echo -e "${YELLOW}[!] Warning: npm not found. If frontend/dist is missing, install node/npm to build UI.${NC}"
    fi
fi

# 3. Launch Unified Single Server (Port 8000)
echo -e "${CYAN}[3/3] Launching Unified Single Server on 0.0.0.0:8000 (Serving Web App + API)...${NC}"
sleep 1
echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN}  CHRONOS CORE IS ONLINE & READY (UNIFIED SINGLE SERVER)${NC}"
echo -e "${GREEN}================================================================${NC}"
echo -e "  🌐 ${YELLOW}Web App & Game:${NC}     ${CYAN}http://localhost:8000${NC}"
echo -e "  📡 ${YELLOW}API Docs:${NC}           ${CYAN}http://localhost:8000/docs${NC}"
echo -e "  🏆 ${YELLOW}Admin Leaderboard:${NC}  ${CYAN}http://localhost:8000/api/admin/leaderboard${NC}"
echo -e "${GREEN}================================================================${NC}"
echo -e "Press ${RED}Ctrl+C${NC} to stop server.\n"

exec python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
