"""
Project Chronos — Central Database Connection
Configures SQLite3 connection with high-concurrency WAL mode, busy timeouts,
foreign key integrity, and dynamic environment path resolution.
"""

import os
import sqlite3
from pathlib import Path

# Resolve Project Root and Default Database Paths
PROJECT_ROOT = Path(__file__).resolve().parents[3]
PRIMARY_DB_PATH = PROJECT_ROOT / "database" / "chronos.db"
LEGACY_DB_PATH = PROJECT_ROOT / "backend" / "chronos.db"

# Select DB path from env, primary database/ folder, or fallback to backend/
if os.getenv("CHRONOS_DB_PATH"):
    DB_PATH = Path(os.getenv("CHRONOS_DB_PATH")).resolve()
elif LEGACY_DB_PATH.exists() and not PRIMARY_DB_PATH.exists():
    DB_PATH = LEGACY_DB_PATH
else:
    DB_PATH = PRIMARY_DB_PATH

# Ensure target directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_connection() -> sqlite3.Connection:
    """
    Establishes and returns a hardened SQLite connection:
    - Sets timeout=30.0 to prevent database locking errors during concurrent LAN submissions.
    - Enables PRAGMA foreign_keys = ON for relational integrity.
    - Enables Write-Ahead Logging (PRAGMA journal_mode = WAL) for concurrent read/write throughput.
    - Sets PRAGMA busy_timeout = 30000 (30 seconds).
    - Sets PRAGMA synchronous = NORMAL for optimal WAL disk performance.
    """
    connection = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    
    # Configure SQLite high-concurrency pragmas
    connection.execute("PRAGMA foreign_keys = ON;")
    connection.execute("PRAGMA journal_mode = WAL;")
    connection.execute("PRAGMA busy_timeout = 30000;")
    connection.execute("PRAGMA synchronous = NORMAL;")
    
    return connection
