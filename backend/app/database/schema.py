import csv
import sqlite3
from pathlib import Path

from .connection import get_connection

ROUND1_MANIFEST = Path(__file__).resolve().parents[3] / "backend" / "round1_manifest.csv"
ROUND1_IMAGE_FOLDER = "static/round1"

DEFAULT_ROUND2_FILES = [
    {"file_id": "L1", "project_name": "Project Chronos", "timeline_tag": "T1", "filename": "chrono_log_1.txt", "content_text": "Time loop detected...", "is_locked": 0},
    {"file_id": "L2", "project_name": "Project Chronos", "timeline_tag": "T2", "filename": "chrono_log_2.txt", "content_text": "Anomaly in sector 7.", "is_locked": 0},
]

def create_tables():
    connection = get_connection()

    try:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name TEXT NOT NULL,
                member_1_name TEXT NOT NULL,
                member_2_name TEXT NOT NULL,
                current_state TEXT,
                round1_score INTEGER DEFAULT 0,
                round1_auth_code TEXT,
                round2_score INTEGER DEFAULT 0,
                round3_score INTEGER DEFAULT 0,
                total_score INTEGER DEFAULT 0,
                round1_started_at TEXT,
                round1_completed_at TEXT,
                round2_started_at TEXT,
                round2_completed_at TEXT,
                round3_started_at TEXT,
                round3_completed_at TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS team_fragments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                fragment TEXT,
                unlocked_at TEXT,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            );

            CREATE TABLE IF NOT EXISTS round1_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                image_path TEXT NOT NULL,
                correct_era TEXT NOT NULL CHECK(correct_era IN ('PAST', 'PRESENT', 'FUTURE')),
                clue_text TEXT,
                points_positive FLOAT DEFAULT 2.0,
                points_negative FLOAT DEFAULT 1.0,
                is_active INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS round1_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                selected_era TEXT NOT NULL CHECK(selected_era IN ('PAST', 'PRESENT', 'FUTURE')),
                is_correct INTEGER NOT NULL,
                points_awarded FLOAT NOT NULL,
                submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
                FOREIGN KEY (item_id) REFERENCES round1_items(item_id)
            );

            CREATE TABLE IF NOT EXISTS round1_team_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
                FOREIGN KEY (item_id) REFERENCES round1_items(item_id) ON DELETE CASCADE,
                UNIQUE(team_id, item_id)
            );

            -- Round 2 Tables (from local)
            CREATE TABLE IF NOT EXISTS round2_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT NOT NULL UNIQUE,
                project_name TEXT NOT NULL,
                timeline_tag TEXT NOT NULL,
                filename TEXT NOT NULL,
                content_text TEXT NOT NULL,
                is_locked INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- Round 3 Tables (from local)
            CREATE TABLE IF NOT EXISTS round3_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                base_points FLOAT DEFAULT 20.0
            );

            CREATE TABLE IF NOT EXISTS round3_team_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                case_id TEXT NOT NULL,
                status TEXT DEFAULT 'PENDING',
                valid_evidence_ids TEXT NOT NULL,
                assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS round3_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                selected_candidate_id TEXT NOT NULL,
                selected_evidence_ids TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                points_awarded FLOAT NOT NULL,
                submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                round INTEGER NOT NULL,
                reference_id TEXT,
                answer TEXT,
                is_correct INTEGER,
                points_awarded FLOAT,
                submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS hints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                round INTEGER,
                hint_level INTEGER,
                points_deducted FLOAT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS investments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                option_id TEXT,
                allocation INTEGER,
                submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS game_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_id INTEGER,
                team_id INTEGER,
                event_type TEXT NOT NULL,
                event_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL
            );
        """)

        _migrate_teams_schema(connection)
        connection.commit()
    finally:
        connection.close()


def _migrate_teams_schema(connection):
    """
    Ensures all database.md columns exist and syncs aliases bidirectionally.
    """
    existing_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(teams)")
    }

    column_definitions = {
        "member1_name": "TEXT NOT NULL DEFAULT ''",
        "member2_name": "TEXT NOT NULL DEFAULT ''",
        "member1_prn": "TEXT NOT NULL DEFAULT ''",
        "member2_prn": "TEXT NOT NULL DEFAULT ''",
        "member_1_name": "TEXT NOT NULL DEFAULT ''",
        "member_2_name": "TEXT NOT NULL DEFAULT ''",
        "member_1_prn": "TEXT NOT NULL DEFAULT ''",
        "member_2_prn": "TEXT NOT NULL DEFAULT ''",
        "r1_start_time": "DATETIME",
        "r1_end_time": "DATETIME",
        "r1_time_diff": "FLOAT",
        "r1_score": "FLOAT DEFAULT 0.0",
        "r1_scaled": "FLOAT DEFAULT 0.0",
        "round1_score": "REAL DEFAULT 0.0",
        "round1_auth_code": "TEXT DEFAULT ''",
        "round1_started_at": "TEXT",
        "round1_completed_at": "TEXT",
        "r2_score": "FLOAT DEFAULT 0.0",
        "round2_score": "REAL DEFAULT 0.0",
        "round2_started_at": "TEXT",
        "round2_completed_at": "TEXT",
        "r3_score": "FLOAT DEFAULT 0.0",
        "round3_score": "REAL DEFAULT 0.0",
        "round3_started_at": "TEXT",
        "round3_completed_at": "TEXT",
        "total_score": "REAL DEFAULT 0.0",
        "status": "TEXT DEFAULT 'ACTIVE'",
        "current_state": "TEXT DEFAULT 'READY'",
        "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
    }

    for column, col_type in column_definitions.items():
        if column not in existing_columns:
            try:
                connection.execute(f"ALTER TABLE teams ADD COLUMN {column} {col_type}")
            except Exception:
                pass

    try:
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_teams_team_name_nocase "
            "ON teams(team_name COLLATE NOCASE)"
        )
    except sqlite3.IntegrityError:
        pass


def seed_round1_items_if_empty():
    connection = get_connection()
    try:
        count = connection.execute("SELECT COUNT(*) FROM round1_items").fetchone()[0]
        if count > 0 or not ROUND1_MANIFEST.is_file():
            return 0

        inserted = 0
        with open(ROUND1_MANIFEST, "r", encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                image_file = row.get("image_filename", "").strip() or f"{row['item_id']}.webp"
                connection.execute(
                    """
                    INSERT OR IGNORE INTO round1_items
                    (item_id, item_name, image_path, correct_era,
                     points_positive, points_negative, is_active)
                    VALUES (?, ?, ?, ?, 2.0, 1.0, 1)
                    """,
                    (
                        int(row["item_id"]),
                        row["item_name"].strip(),
                        f"/{ROUND1_IMAGE_FOLDER}/{image_file}",
                        row["correct_era"].strip().upper(),
                    ),
                )
                inserted += 1

        connection.commit()
        print(f"Round 1: seeded {inserted} items from round1_manifest.csv")
        return inserted
    finally:
        connection.close()


def seed_round2_files_if_empty():
    connection = get_connection()
    try:
        count = connection.execute("SELECT COUNT(*) FROM round2_files").fetchone()[0]
        if count > 0:
            return 0

        inserted = 0
        for f in DEFAULT_ROUND2_FILES:
            connection.execute(
                """
                INSERT OR IGNORE INTO round2_files
                (file_id, project_name, timeline_tag, filename, content_text, is_locked)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    f["file_id"],
                    f["project_name"],
                    f["timeline_tag"],
                    f["filename"],
                    f["content_text"],
                    f["is_locked"],
                ),
            )
            inserted += 1
        connection.commit()
        return inserted
    finally:
        connection.close()


if __name__ == "__main__":
    create_tables()
    seed_round1_items_if_empty()
    seed_round2_files_if_empty()
