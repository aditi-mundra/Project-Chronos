import sqlite3
import os
from pathlib import Path

# Canonical database path resolution
PROJECT_ROOT = Path(__file__).resolve().parents[3]
PRIMARY_DB_PATH = PROJECT_ROOT / "database" / "chronos.db"

# Resolve CHRONOS_DB_PATH relative to PROJECT_ROOT if relative, otherwise use primary
raw_db_path = os.getenv("CHRONOS_DB_PATH")
if raw_db_path:
    p = Path(raw_db_path)
    DB_PATH = p if p.is_absolute() else (PROJECT_ROOT / p).resolve()
else:
    DB_PATH = PRIMARY_DB_PATH

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_connection():
    connection = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 30000")
    connection.execute("PRAGMA synchronous = NORMAL")
    return connection
