import csv
import sqlite3
from pathlib import Path

from .connection import get_connection

ROUND1_MANIFEST = Path(__file__).resolve().parents[2] / "round1_manifest.csv"
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

            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                round INTEGER,
                reference_id TEXT,
                answer TEXT,
                is_correct INTEGER,
                points_awarded INTEGER,
                submitted_at TEXT,
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

            CREATE TABLE IF NOT EXISTS hints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                round INTEGER,
                hint_level INTEGER,
                points_deducted INTEGER,
                created_at TEXT,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            );

            CREATE TABLE IF NOT EXISTS investments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                option_id TEXT,
                allocation INTEGER,
                submitted_at TEXT,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            );

            CREATE TABLE IF NOT EXISTS game_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER,
                event_type TEXT,
                event_data TEXT,
                created_at TEXT,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            );
        """)

        
        _migrate_teams_for_auth(connection)
        connection.commit()
    finally:
        connection.close()


def _migrate_teams_for_auth(connection):
    """
    Additive, idempotent changes required by login/authentication.

    - member_1_prn / member_2_prn: PRNs are verified (never modified) when an
      existing team name logs in again.
    - Unique team_name (case-insensitive): a team name can belong to only one team.
    """
    existing_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(teams)")
    }

    for column in ("member_1_prn", "member_2_prn"):
        if column not in existing_columns:
            connection.execute(
                f"ALTER TABLE teams ADD COLUMN {column} TEXT NOT NULL DEFAULT ''"
            )

    try:
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_teams_team_name_nocase "
            "ON teams(team_name COLLATE NOCASE)"
        )
    except sqlite3.IntegrityError:
        # Pre-existing duplicate team names (old test data): skip the index rather
        # than fail startup. The login service still checks names case-insensitively.
        pass


def seed_round1_items_if_empty():
    """
    Load the Round 1 items from round1_manifest.csv when (and only when) the
    round1_items table is empty, so a fresh database on a new PC works without a manual
    seed step. Existing items are never touched. Returns the number of rows inserted.
    """
    connection = get_connection()

    try:
        count = connection.execute("SELECT COUNT(*) FROM round1_items").fetchone()[0]

        if count > 0 or not ROUND1_MANIFEST.is_file():
            return 0

        inserted = 0

        with open(ROUND1_MANIFEST, "r", encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                connection.execute(
                    """
                    INSERT OR IGNORE INTO round1_items
                    (item_id, item_name, image_path, correct_era,
                     points_positive, points_negative, is_active)
                    VALUES (?, ?, ?, ?, 2, 1, 1)
                    """,
                    (
                        int(row["item_id"]),
                        row["item_name"].strip(),
                        f"/{ROUND1_IMAGE_FOLDER}/{row['image_filename'].strip()}",
                        row["correct_era"].strip().upper(),
                    ),
                )
                inserted += 1

        connection.commit()
        print(f"Round 1: seeded {inserted} items from round1_manifest.csv")
        return inserted
    finally:
        connection.close()
