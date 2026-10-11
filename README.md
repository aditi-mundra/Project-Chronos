# PROJECT CHRONOS — THE GLITCH (2140)

> **Symbitech 2026 — AI Club, Symbiosis Institute of Technology (SIT), Pune**  
> An interactive, 2-player team-based temporal investigation game.

---

## ⚡ Quickstart — LAN Party & Computer Lab Deployment

Project Chronos is engineered for seamless **Local Area Network (LAN) hosting** across college computer labs, hackathons, and offline gaming events.

### 🎮 Host the Game on LAN in 1 Command:

```bash
# Option 1: Python Launcher (Cross-platform: Windows, Mac, Linux)
python3 run.py

# Option 2: Shell Script (macOS / Linux)
./start.sh

# Option 3: Windows Batch File (Windows)
start.bat
```

### 📡 What Happens Automatically:
1. **Auto LAN IP Discovery**: Detects all active IPv4 network interfaces on the host (Ethernet, Wi-Fi) and prints the exact shareable player URLs.
2. **Unified Single-Process Server**: Serves the optimized React UI and FastAPI API from a single process (`0.0.0.0:8000`).
3. **Zero Client Installation**: Player PCs need **no downloads or software installed**; players simply open `http://<HOST_IP>:8000` in their browser.
4. **Offline Resilience**: Runs 100% offline once launched, immune to venue internet drops.
5. **Database Concurrency**: Uses SQLite with Write-Ahead Logging (WAL) to support 50+ concurrent team PCs with sub-millisecond latency.

---

## 🌐 Network Endpoints for Event Hosts & Players

| Interface | Host PC Local | Player & Lab LAN URL |
| :--- | :--- | :--- |
| **🎮 Player Game Client** | `http://localhost:8000` | `http://<HOST_IP>:8000` |
| **🏆 Live Leaderboard (Projector)** | `http://localhost:8000/leaderboard` | `http://<HOST_IP>:8000/leaderboard` |
| **🛠️ Master Admin Dashboard** | `http://localhost:8000/admin` | `http://<HOST_IP>:8000/admin` |
| **📖 Interactive API Docs** | `http://localhost:8000/docs` | `http://<HOST_IP>:8000/docs` |
| **💚 LAN Connectivity Health Check** | `http://localhost:8000/api/health` | `http://<HOST_IP>:8000/api/health` |

> 📖 **Full Guide**: For detailed network topology, firewall rules, lab switches, and multi-PC troubleshooting, check out the [LAN Deployment Guide](docs/LAN_DEPLOYMENT_GUIDE.md).

---

## 🗄️ Database Architecture & Resilience

- **Engine**: SQLite3 (`chronos.db` on central server).
- **Concurrency & Lock Resistance**:
  - `PRAGMA journal_mode = WAL;` (Write-Ahead Logging for non-blocking concurrent reads/writes).
  - `PRAGMA busy_timeout = 30000;` (30-second lock queue).
  - `sqlite3.connect(..., timeout=30.0, check_same_thread=False)`.
  - `PRAGMA synchronous = NORMAL;` (optimal SSD/NVMe write performance).
- **Dynamic Path Configuration**: Override database path via environment variable:
  ```bash
  export CHRONOS_DB_PATH="/path/to/custom_chronos.db"
  ```

---

## 🚀 Production Deployment

For the actual event, it is recommended to build the frontend and serve everything from the single FastAPI backend process. This eliminates the need to run the Vite dev server (`npm run dev`) and ensures better performance.

1. **Build the Frontend Client**
   Navigate to the frontend directory and create a production build. This will generate optimized static files in `frontend/dist`.
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

2. **Launch the Production Server**
   Run the backend using Uvicorn. FastAPI is configured to automatically serve the `frontend/dist` directory for all unmatched routes, meaning it will serve the React app on port `8000` alongside the API.
   ```bash
   pip install -r backend/requirements.txt
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
   ```

3. **Client Access**
   - Players: `http://<SERVER_IP>:8000`
   - Host/Admin Leaderboard: `http://<SERVER_IP>:8000/leaderboard` (or `/admin`)

---

## 🎮 Game Architecture & Rounds

1. **Round 0**: Team Registration & Cinematic Briefing.
2. **Round 1 (Timeline Fragmentation)**: Image-based classification puzzle (+2 / -1 points, Max 50).
3. **Round 2 (CHRONOS Terminal)**: Physical token search + Digital audit log investigation with restricted Gemini Assistant (+30 culprit + max 20 AI balance, Max 50).
4. **Round 3 (Final Decision / Wisdom Round)**: Deterministically seeded suspect matrix & evidence grid (+30 points, Max 30).
5. **Completion**: Cumulative score reveal (Max 130 Points), time-based tie-breakers, and forensic narrative resolution.

---

## 🧪 Automated Testing

Run the full automated test suite to verify case generation, anti-collusion permutations, evidence constraints, and scoring integrity:

```bash
python3 backend/tests/test_round3.py
```
