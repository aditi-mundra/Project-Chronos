import csv
import sqlite3
from pathlib import Path

from .connection import get_connection

ROUND1_MANIFEST = Path(__file__).resolve().parents[3] / "backend" / "round1_manifest.csv"
ROUND1_IMAGE_FOLDER = "static/round1"


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
                ai_model_used TEXT DEFAULT '',
                ai_api_live TEXT DEFAULT '',
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
                team_id INTEGER NOT NULL UNIQUE,
                case_id TEXT NOT NULL,
                status TEXT DEFAULT 'PENDING',
                case_data TEXT NOT NULL DEFAULT '{}',
                culprit_candidate_id TEXT NOT NULL DEFAULT '',
                valid_evidence_ids TEXT NOT NULL DEFAULT '[]',
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
        _migrate_round3_schema(connection)
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
        "ai_model_used": "TEXT DEFAULT ''",
        "ai_api_live": "TEXT DEFAULT ''",
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
            """
            UPDATE teams
            SET ai_model_used = COALESCE(NULLIF(ai_model_used, ''), 'openai/gpt-oss-120b'),
                ai_api_live = COALESCE(NULLIF(ai_api_live, ''), 'YES')
            WHERE ai_model_used IS NULL OR ai_model_used = '' OR ai_api_live IS NULL OR ai_api_live = ''
            """
        )
    except Exception:
        pass

    try:
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_teams_team_name_nocase "
            "ON teams(team_name COLLATE NOCASE)"
        )
    except sqlite3.IntegrityError:
        pass


def _migrate_round3_schema(connection):
    """Bring older Round 3 databases up to the schema used by the service."""
    connection.execute("""
        CREATE TABLE IF NOT EXISTS round3_team_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER NOT NULL UNIQUE,
            case_id TEXT NOT NULL,
            status TEXT DEFAULT 'PENDING',
            case_data TEXT NOT NULL DEFAULT '{}',
            culprit_candidate_id TEXT NOT NULL DEFAULT '',
            valid_evidence_ids TEXT NOT NULL DEFAULT '[]',
            assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
        );
    """)
    team_case_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(round3_team_cases)")
    }
    additions = {
        "status": "TEXT DEFAULT 'PENDING'",
        "case_data": "TEXT NOT NULL DEFAULT '{}'",
        "culprit_candidate_id": "TEXT NOT NULL DEFAULT ''",
        "valid_evidence_ids": "TEXT NOT NULL DEFAULT '[]'",
        "assigned_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
    }
    for column, definition in additions.items():
        if column not in team_case_columns:
            try:
                connection.execute(
                    f"ALTER TABLE round3_team_cases ADD COLUMN {column} {definition}"
                )
            except Exception:
                pass

    # One active Round 3 case and one final decision per team. Existing
    # installations may contain duplicates from the old implementation, so
    # retain the newest row before adding the integrity constraints.
    connection.execute(
        "DELETE FROM round3_team_cases WHERE id NOT IN "
        "(SELECT MAX(id) FROM round3_team_cases GROUP BY team_id)"
    )
    connection.execute(
        "DELETE FROM round3_submissions WHERE id NOT IN "
        "(SELECT MAX(id) FROM round3_submissions GROUP BY team_id)"
    )
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_round3_team_cases_team_id "
        "ON round3_team_cases(team_id)"
    )
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_round3_submissions_team_id "
        "ON round3_submissions(team_id)"
    )
    connection.commit()


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
    """Initializes Round 2 cases and tables (safe no-op if already loaded)."""
    try:
        from ..services.round2_service import init_round2
        init_round2()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    create_tables()
    seed_round1_items_if_empty()
    seed_round2_files_if_empty()
