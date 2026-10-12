# PROJECT CHRONOS — LAN Party & Computer Lab Deployment Guide

This guide details how to host and deploy **Project Chronos** across local area networks (LAN), computer labs, hackathon setups, and offline gaming environments.

---

## 🏛️ Topology & Network Architecture

```
                      +------------------------------------------+
                      |          CENTRAL HOST PC / SERVER        |
                      |  - FastAPI Engine (0.0.0.0:8000)         |
                      |  - SQLite3 WAL Database (chronos.db)     |
                      |  - Static React Dist Web Server          |
                      |  - Host Admin Dashboard / Leaderboard    |
                      +------------------------------------------+
                                           |
                   [ Local Area Network / Lab Switch / Wi-Fi Router ]
                                           |
        +------------------+---------------+------------------+
        |                  |                                  |
+---------------+  +---------------+                  +---------------+
|  TEAM 01 PC   |  |  TEAM 02 PC   |                  |  TEAM N PC    |
| (Web Browser) |  | (Web Browser) |   ... (50+ PCs)  | (Web Browser) |
| Chrome / Edge |  | Chrome / Edge |                  | Chrome / Edge |
+---------------+  +---------------+                  +---------------+
        |                                                     |
        +---> Connects to: http://<HOST_IP>:8000 <------------+
```

### Key Highlights
- **Zero Client Setup**: Player PCs require **no installation, no Python, no Node.js, and no software dependencies**. They only need a modern web browser (Google Chrome, Microsoft Edge, Firefox, Safari, Brave, or iPad/Tablet).
- **Single Source of Truth**: All game states, round progression, forensics tokens, and scores are managed in real time by the central host in a high-concurrency SQLite WAL database.
- **100% Offline Compatible**: Once initialized, the entire game runs completely offline without needing active internet access.

---

## 🚀 Quickstart: Hosting the Game in 60 Seconds

### Step 1: Start the Central Host

On the **Host / Instructor / Organizer PC**:

```bash
# Option 1: Using Python Launcher (Cross-Platform: Windows / macOS / Linux)
python3 run.py

# Option 2: Using Shell Script (macOS / Linux)
./start.sh

# Option 3: Using Windows Batch Script (Windows)
start.bat
```

### Step 2: Note the LAN IP Address

When launched, the server automatically scans all network interfaces and outputs the exact LAN Party access URL:

```
=======================================================================
  ⚡ CHRONOS CORE IS ONLINE — LOCAL AREA NETWORK (LAN) HOST ACTIVE ⚡
=======================================================================
  🖥️  Host PC Local:           http://localhost:8000

  📡 LAN Party / Lab PCs URL (Share with Teams):
      👉  http://192.168.1.50:8000

  🏆 Admin Leaderboard (Screen): http://localhost:8000/leaderboard
  🛠️  Host Admin Controls:      http://localhost:8000/admin
  📖 API Documentation:        http://localhost:8000/docs
  💚 LAN Health Diagnostic:    http://localhost:8000/api/health
=======================================================================
```

### Step 3: Share URL with Lab PCs

Share the URL (e.g. `http://192.168.1.50:8000`) with students/teams in the lab.
They open the link, enter their **Team Name** & **PRN / Roll Numbers**, and start the mission!

### Step 4: Display the Live Leaderboard

Connect a projector or secondary monitor to the host PC (or any PC on the network) and open:
```
http://<HOST_IP>:8000/leaderboard
```
This displays the real-time, live-updating Cyberpunk Leaderboard with automated rankings, tie-breakers, and round status.

---

## 🛠️ Lab Network Configuration & Troubleshooting

### 1. Finding the Host IP Manually (if needed)

If you need to verify the IP address manually:

| OS | Command | Expected Output |
| :--- | :--- | :--- |
| **Windows** | `ipconfig` | Look for `IPv4 Address` under your active Ethernet or Wi-Fi adapter (e.g. `192.168.1.X` or `10.X.X.X`) |
| **macOS** | `ipconfig getifaddr en0` | Shows current IP (e.g. `192.168.1.50`) |
| **Linux** | `hostname -I` or `ip a` | Shows network IP addresses |

---

### 2. Firewall Port Configuration

If client PCs cannot reach the server ("Site cannot be reached" / timeout):

#### Windows Host
Run Command Prompt or PowerShell as **Administrator** and run:
```cmd
netsh advfirewall firewall add rule name="CHRONOS LAN Server" dir=in action=allow protocol=TCP localport=8000
```
*(Or click "Allow access" on the Windows Defender Firewall prompt when launching).*

#### macOS Host
Go to **System Settings > Network > Firewall** and ensure incoming connections for Python are allowed, or disable the firewall temporarily during the lab event.

#### Linux Host (UFW)
```bash
sudo ufw allow 8000/tcp
```

---

### 3. College / University Lab Network Types

#### Scenario A: Ethernet Switch LAN (Recommended)
All lab PCs are connected via wired RJ45 Ethernet cables to a network switch.
- **Latency**: < 1ms
- **Action**: Host PC connects to the switch. Client PCs connect immediately using the host's Ethernet IP.

#### Scenario B: Wi-Fi Hotspot / Dedicated Router
The host PC creates a mobile hotspot or connects to a dedicated Wi-Fi router along with all participant laptops.
- **Action**: Turn off **AP Isolation / Client Isolation** on the router settings so wireless clients can talk to each other.

#### Scenario C: University Wi-Fi with Client Isolation
Some campus Wi-Fi networks block peer-to-peer traffic between connected devices.
- **Fix**: Connect the host and client PCs via a physical Ethernet switch or a dedicated offline travel router / mobile hotspot.

---

## 🔍 Connectivity Health Check

Participants or organizers can test LAN connectivity at any time:

1. **In Browser**: Open `http://<HOST_IP>:8000/api/health`
   - Expected JSON Response:
   ```json
   {
     "status": "online",
     "service": "Project Chronos Central Mainframe",
     "mode": "LAN_PARTY_HOST",
     "lan_ready": true
   }
   ```
2. **Ping Test**:
   ```bash
   ping <HOST_IP>
   ```

---

## ⚡ Concurrency & Database Resilience

Project Chronos is engineered for heavy concurrent multi-team traffic:
- **SQLite WAL Mode (`PRAGMA journal_mode = WAL`)**: Concurrent readers never block writers and writers never block readers.
- **30-Second Busy Queue (`PRAGMA busy_timeout = 30000`)**: Prevents "database locked" errors during simultaneous burst submissions (e.g., at round start/end).
- **In-Memory Connection Pooling**: Handles 100+ active teams simultaneously with sub-millisecond response latency.
- **CSV Data Export**: Organizers can download full team records and telemetry anytime via the `/admin` console.
