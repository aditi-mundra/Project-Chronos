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
                                  YEAR 2140 // MAINFRAME
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
echo -e "${CYAN}[1/4] Checking Python & Backend Dependencies...${NC}"
if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    echo -e "${YELLOW}[i] Installing backend dependencies from backend/requirements.txt...${NC}"
    python3 -m pip install -r backend/requirements.txt --quiet || pip install -r backend/requirements.txt --quiet
fi

# Initialize Database Schema if needed
python3 -c "from backend.app.database.schema import create_tables; create_tables(); print('[✔] Database schema verified.')"

# 2. Launch FastAPI Backend
echo -e "${CYAN}[2/4] Launching FastAPI Backend on 0.0.0.0:8000 (LAN accessible)...${NC}"
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 3. Check for Node & npm
echo -e "${CYAN}[3/4] Checking Node.js & Frontend Environment...${NC}"
if ! command -v npm &>/dev/null; then
    echo -e "\n${RED}[!] Node.js / npm not detected on system PATH.${NC}"
    echo -e "${YELLOW}To run the React Frontend, install Node.js using:${NC}"
    echo -e "  - Homebrew: ${CYAN}brew install node${NC}"
    echo -e "  - Conda:    ${CYAN}conda install -c conda-forge nodejs${NC}"
    echo -e "\n${GREEN}[i] FastAPI Backend is live at http://127.0.0.1:8000/docs${NC}"
    echo -e "Press ${RED}Ctrl+C${NC} to exit."
    wait
else
    # 4. Frontend Dependencies & Launch
    echo -e "${CYAN}[4/4] Launching React Vite Frontend on 0.0.0.0:5173 (LAN accessible)...${NC}"
    if [ ! -d "frontend/node_modules" ]; then
        echo -e "${YELLOW}[i] Installing node modules in frontend/...${NC}"
        (cd frontend && npm install)
    fi
    (cd frontend && npm run dev -- --host 0.0.0.0 --port 5173) &
    FRONTEND_PID=$!

    sleep 2
    echo -e "\n${GREEN}================================================================${NC}"
    echo -e "${GREEN}  CHRONOS CORE IS ONLINE & READY${NC}"
    echo -e "${GREEN}================================================================${NC}"
    echo -e "  🌐 ${YELLOW}Local Client:${NC}       ${CYAN}http://localhost:5173${NC}"
    echo -e "  📡 ${YELLOW}API Docs:${NC}           ${CYAN}http://127.0.0.1:8000/docs${NC}"
    echo -e "  🏆 ${YELLOW}Admin Leaderboard:${NC}  ${CYAN}http://127.0.0.1:8000/api/admin/leaderboard${NC}"
    echo -e "${GREEN}================================================================${NC}"
    echo -e "Press ${RED}Ctrl+C${NC} to stop all servers simultaneously.\n"

    wait
fi
