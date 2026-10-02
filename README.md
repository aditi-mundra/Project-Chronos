# PROJECT CHRONOS — THE GLITCH (2140)

> **Symbitech 2026 — AI Club, Symbiosis Institute of Technology (SIT), Pune**  
> An interactive, 2-player team-based temporal investigation game.

---

## ⚡ Quickstart — Unified One-Command Deployment

You can launch both the **FastAPI Central Server** (Port `8000`) and the **React Vite Client** (Port `5173`) with a single command:

```bash
# Option 1: Using Bash Launcher
./start.sh

# Option 2: Using Python Launcher
python3 run.py
```

### What this single command does automatically:
1. **Pre-flight Checks**: Verifies Python (`fastapi`, `uvicorn`) and Node.js dependencies (`npm install`).
2. **Database Auto-Provisioning**: Creates and checks the unified SQLite schema with Write-Ahead Logging (WAL) and foreign key enforcement.
3. **LAN Network Binding**: Binds backend and frontend to `0.0.0.0` so player workstations across the event venue can connect seamlessly over the local network.
4. **Concurrent Execution**: Launches both services simultaneously with live reload.
5. **Clean Exit**: Pressing `Ctrl + C` gracefully terminates both services.

---

## 🌐 Network Endpoints

| Interface | Local URL | LAN Access URL |
| :--- | :--- | :--- |
| **Player Game Client** | `http://localhost:5173` | `http://<SERVER_IP>:5173` |
| **FastAPI Interactive Docs** | `http://127.0.0.1:8000/docs` | `http://<SERVER_IP>:8000/docs` |
| **Admin Live Leaderboard** | `http://127.0.0.1:8000/api/admin/leaderboard` | `http://<SERVER_IP>:8000/api/admin/leaderboard` |
| **Admin Game Telemetry Logs** | `http://127.0.0.1:8000/api/admin/logs` | `http://<SERVER_IP>:8000/api/admin/logs` |

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
