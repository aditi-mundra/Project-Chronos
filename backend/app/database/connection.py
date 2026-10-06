import sqlite3
import os
from pathlib import Path

# Legacy path handling (keeping local's logic for dynamic environment but simplified)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
PRIMARY_DB_PATH = PROJECT_ROOT / "database" / "chronos.db"

# We'll use the environment variable if set, otherwise the canonical path
DB_PATH = Path(os.getenv("CHRONOS_DB_PATH")) if os.getenv("CHRONOS_DB_PATH") else PRIMARY_DB_PATH
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_connection():
    connection = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 30000")
    connection.execute("PRAGMA synchronous = NORMAL")
    return connection
