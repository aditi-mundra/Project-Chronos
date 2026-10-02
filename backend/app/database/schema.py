"""
Project Chronos — Database Schema Definition
Central SQLite Table creation with Foreign Keys, Indexing, and Cascade rules.
"""

from .connection import get_connection

def create_tables():
    """
    Initializes the unified database schema for Project Chronos.
    Supports Master Teams, Round 1 items/submissions, Round 2 logs/chat/submissions,
    Round 3 team cases/submissions, and Telemetry game_logs.
    """
    connection = get_connection()
    try:
        connection.executescript("""
            -- =========================================================================
            -- 1. Master Teams Table
            -- =========================================================================
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name TEXT NOT NULL UNIQUE,
                member_1_name TEXT NOT NULL,
                member_2_name TEXT NOT NULL,
                member_1_prn TEXT DEFAULT '',
                member_2_prn TEXT DEFAULT '',
                current_state TEXT DEFAULT 'REGISTERED',
                status TEXT DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'FINISHED', 'DISQUALIFIED')),
                
                -- Round 1 Metrics
                round1_score INTEGER DEFAULT 0,
                r1_start_time TEXT,
                r1_end_time TEXT,
                r1_time_diff REAL DEFAULT 0.0,
                round1_started_at TEXT,
                round1_completed_at TEXT,
                
                -- Round 2 Metrics
                round2_score INTEGER DEFAULT 0,
                round2_started_at TEXT,
                round2_completed_at TEXT,
                
                -- Round 3 Metrics
                round3_score INTEGER DEFAULT 0,
                round3_started_at TEXT,
                round3_completed_at TEXT,
                
                -- Aggregated Total (Max 130)
                total_score INTEGER DEFAULT 0,
                
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            -- =========================================================================
            -- 2. Round 1 Subsystem
            -- =========================================================================
            CREATE TABLE IF NOT EXISTS round1_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                image_path TEXT NOT NULL,
                correct_era TEXT NOT NULL CHECK(correct_era IN ('PAST', 'PRESENT', 'FUTURE')),
                clue_text TEXT,
                points_positive REAL DEFAULT 2.0,
                points_negative REAL DEFAULT 1.0,
                is_active INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS round1_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                selected_era TEXT NOT NULL CHECK(selected_era IN ('PAST', 'PRESENT', 'FUTURE')),
                is_correct INTEGER NOT NULL,
                points_awarded REAL NOT NULL,
                submitted_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
                FOREIGN KEY (item_id) REFERENCES round1_items(item_id)
            );

            CREATE TABLE IF NOT EXISTS team_fragments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                fragment TEXT,
                unlocked_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
            );

            -- =========================================================================
            -- 3. Round 2 Subsystem
            -- =========================================================================
            CREATE TABLE IF NOT EXISTS round2_files (
                file_id TEXT PRIMARY KEY,
                project_name TEXT NOT NULL,
                timeline_tag TEXT NOT NULL,
                filename TEXT NOT NULL,
                content_text TEXT NOT NULL,
                is_locked INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS round2_chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                question_number INTEGER NOT NULL,
                user_prompt TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                points_deducted REAL NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS round2_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                suspect_identified TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                points_awarded REAL NOT NULL,
                ai_points_remaining REAL NOT NULL,
                round2_total_score REAL NOT NULL,
                submitted_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
            );

            -- =========================================================================
            -- 4. Round 3 Subsystem (Dynamic Cases & Final Decision)
            -- =========================================================================
            CREATE TABLE IF NOT EXISTS round3_team_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER UNIQUE NOT NULL,
                case_id TEXT NOT NULL,
                case_data TEXT NOT NULL, -- JSON string of the assigned scenario (sanitized)
                culprit_candidate_id TEXT NOT NULL, -- Secret correct candidate ID
                valid_evidence_ids TEXT NOT NULL,   -- JSON array of valid evidence IDs
                assigned_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS round3_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                selected_candidate_id TEXT NOT NULL,
                selected_evidence_ids TEXT NOT NULL, -- JSON array of submitted evidence IDs
                is_correct INTEGER NOT NULL,          -- 1 if Correct (+30), 0 if Wrong
                points_awarded REAL NOT NULL,
                submitted_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
            );

            -- Unified Submissions Table for Cross-Round Archiving
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                round INTEGER NOT NULL,
                reference_id TEXT,
                answer TEXT,
                is_correct INTEGER,
                points_awarded REAL,
                submitted_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS hints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                round INTEGER,
                hint_level INTEGER,
                points_deducted REAL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS investments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                option_id TEXT,
                allocation INTEGER,
                submitted_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
            );

            -- =========================================================================
            -- 5. Audit & Telemetry Subsystem
            -- =========================================================================
            CREATE TABLE IF NOT EXISTS game_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER,
                event_type TEXT NOT NULL,
                event_data TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL
            );

            -- Indexes for Performance
            CREATE INDEX IF NOT EXISTS idx_teams_state ON teams(current_state);
            CREATE INDEX IF NOT EXISTS idx_r3_cases_team ON round3_team_cases(team_id);
            CREATE INDEX IF NOT EXISTS idx_r3_subs_team ON round3_submissions(team_id);
            CREATE INDEX IF NOT EXISTS idx_logs_team ON game_logs(team_id);
        """)
        connection.commit()
    finally:
        connection.close()

if __name__ == "__main__":
    create_tables()
    print("Database tables initialized successfully.")
