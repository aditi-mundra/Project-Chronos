"""
Round 2: CHRONOS terminal investigation (Round 2 Backend PRD).

The backend is the source of truth. The frontend only renders what these
functions return. Everything below is decided here, never in the browser:

  * evidence access        (case files, is_locked, team must have started Round 2)
  * AI question limit      (max 3 per team)
  * AI point deductions    (5 / 5 / 10, from a 20 point AI budget)
  * culprit validation     (+30 correct, +0 wrong, one submission per team)
  * the Round 2 score      (culprit points + AI points kept, max 50)
  * the Round 2 timer

Tables used: round2_cases / round2_case_files / round2_case_suspects /
round2_team_cases (the 24 cases, see round2_cases.py), round2_chat_messages and
round2_submissions. They are created on first use, so this module needs no
change to the shared schema file.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from ..database.connection import get_connection
from . import gemini_service, round2_cases

# --- rules from the PRD ----------------------------------------------------
MAX_AI_QUESTIONS = 3
AI_DEDUCTIONS = (5, 5, 10)            # question 1, 2, 3
AI_BUDGET = 20
# Grading system: Round 2 maximum is 20 points (AI investigation budget 20, 5/5/10 deductions)
CULPRIT_POINTS = 20
MAX_ROUND2_SCORE = 20

# The PRD does not give a Round 2 duration. 20 minutes is a placeholder until
# the final event specification exists; override with ROUND2_DURATION_SECONDS.
DURATION_SECONDS = int(os.environ.get("ROUND2_DURATION_SECONDS", "1200"))

ACTIVE_STATE = "ROUND_2_ACTIVE"
COMPLETED_STATE = "ROUND_2_COMPLETED"
TIMEOUT_STATE = "TIMEOUT"

# The shared project is not consistent about state spelling (Round 1 writes
# ROUND1_COMPLETED, PROJECT_REFERENCE.md says ROUND_1_COMPLETED), so states are
# compared with underscores removed.
STARTABLE = {"ROUND1COMPLETED", "ROUND2LOCKED", "READY", "LOGGEDIN", "ROUND1ACTIVE"}


def _norm(state) -> str:
    return (state or "").replace("_", "").upper()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat(timespec="seconds")


def _parse(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace(" ", "T"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _seconds_left(started_at: str) -> int:
    deadline = _parse(started_at) + timedelta(seconds=DURATION_SECONDS)
    return max(0, int((deadline - _now()).total_seconds()))


# --- tables ------------------------------------------------------------------

def ensure_tables(connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS round2_chat_messages (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id          TEXT NOT NULL,
            question_number  INTEGER NOT NULL,
            user_prompt      TEXT NOT NULL,
            ai_response      TEXT NOT NULL DEFAULT '',
            points_deducted  INTEGER NOT NULL,
            created_at       TEXT NOT NULL,
            UNIQUE (team_id, question_number)
        );

        CREATE TABLE IF NOT EXISTS round2_submissions (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id              TEXT NOT NULL UNIQUE,
            suspect              TEXT NOT NULL DEFAULT '',
            suspect_identified   TEXT NOT NULL DEFAULT '',
            is_correct           INTEGER NOT NULL,
            points_awarded       INTEGER NOT NULL,
            ai_points_remaining  INTEGER NOT NULL,
            round2_score         INTEGER NOT NULL DEFAULT 0,
            round2_total_score   REAL NOT NULL DEFAULT 0.0,
            submitted_at         TEXT NOT NULL
        );
        """
    )

    existing_cols = {r["name"] for r in connection.execute("PRAGMA table_info(round2_submissions)").fetchall()}
    if "suspect" not in existing_cols:
        connection.execute("ALTER TABLE round2_submissions ADD COLUMN suspect TEXT DEFAULT ''")
        if "suspect_identified" in existing_cols:
            connection.execute("UPDATE round2_submissions SET suspect = suspect_identified")
    if "suspect_identified" not in existing_cols:
        connection.execute("ALTER TABLE round2_submissions ADD COLUMN suspect_identified TEXT DEFAULT ''")
        if "suspect" in existing_cols:
            connection.execute("UPDATE round2_submissions SET suspect_identified = suspect")
    if "round2_score" not in existing_cols:
        connection.execute("ALTER TABLE round2_submissions ADD COLUMN round2_score INTEGER DEFAULT 0")
        if "round2_total_score" in existing_cols:
            connection.execute("UPDATE round2_submissions SET round2_score = CAST(round2_total_score AS INTEGER)")
    if "round2_total_score" not in existing_cols:
        connection.execute("ALTER TABLE round2_submissions ADD COLUMN round2_total_score REAL DEFAULT 0.0")
        if "round2_score" in existing_cols:
            connection.execute("UPDATE round2_submissions SET round2_total_score = CAST(round2_score AS REAL)")

    teams_cols = {r["name"] for r in connection.execute("PRAGMA table_info(teams)").fetchall()}
    if "ai_model_used" not in teams_cols:
        connection.execute("ALTER TABLE teams ADD COLUMN ai_model_used TEXT DEFAULT ''")
    if "ai_api_live" not in teams_cols:
        connection.execute("ALTER TABLE teams ADD COLUMN ai_api_live TEXT DEFAULT ''")

    chat_cols = {r["name"] for r in connection.execute("PRAGMA table_info(round2_chat_messages)").fetchall()}
    if "model_used" not in chat_cols:
        connection.execute("ALTER TABLE round2_chat_messages ADD COLUMN model_used TEXT DEFAULT ''")
    if "is_live" not in chat_cols:
        connection.execute("ALTER TABLE round2_chat_messages ADD COLUMN is_live INTEGER DEFAULT 1")
    if "api_live" not in chat_cols:
        connection.execute("ALTER TABLE round2_chat_messages ADD COLUMN api_live TEXT DEFAULT 'YES'")

    # The 24 cases: create their tables and load the case folders (no-op once loaded).
    round2_cases.ensure_case_tables(connection)
    round2_cases.seed_cases(connection)
    connection.commit()


_ready = set()   # database files whose Round 2 tables were already checked by this process


def _db_key(connection) -> str:
    return str(connection.execute("PRAGMA database_list").fetchone()[2])


def _prepare(connection) -> None:
    key = _db_key(connection)
    if key not in _ready:
        ensure_tables(connection)
        _ready.add(key)


def init_round2() -> None:
    """Server start-up: create the Round 2 tables, load the 24 cases, and give a
    case to every team that does not have one yet (teams created before Round 2
    was installed). New teams get theirs when they register (auth_service)."""
    connection = get_connection()
    try:
        _prepare(connection)
        missing = connection.execute(
            "SELECT id FROM teams WHERE id NOT IN (SELECT team_id FROM round2_team_cases)"
        ).fetchall()
        for row in missing:
            round2_cases.assign_case(connection, row["id"])
        connection.commit()
    finally:
        connection.close()


class _Db:
    """Connection with the Round 2 tables guaranteed to exist."""

    def __enter__(self):
        self.connection = get_connection()
        try:
            _prepare(self.connection)
        except Exception:
            self.connection.close()
            raise
        return self.connection

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.connection.close()


def _log(connection, team_id, event_type, data) -> None:
    connection.execute(
        "INSERT INTO game_logs (team_id, event_type, event_data, created_at) VALUES (?, ?, ?, ?)",
        (team_id, event_type, json.dumps(data), _now_iso()),
    )


def _team(connection, team_id):
    row = connection.execute("SELECT * FROM teams WHERE id = ?", (str(team_id).strip(),)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Team not found.")
    return row


def _require_started(connection, team_id):
    team = _team(connection, team_id)
    if not team["round2_started_at"]:
        raise HTTPException(status_code=409, detail="Round 2 has not started for this team.")
    return team


def _case(connection, team):
    """The team's case. Normally assigned in start_round2; a team that started
    before cases existed gets one the first time it is needed."""
    return round2_cases.assign_case(connection, team["id"])


def _require_open(connection, team_id):
    """Team is inside Round 2, inside its deadline, and has not submitted yet."""
    team = _require_started(connection, team_id)
    state = _norm(team["current_state"])

    if state == _norm(COMPLETED_STATE):
        raise HTTPException(status_code=409, detail="Round 2 is already complete for this team.")
    if state == _norm(TIMEOUT_STATE):
        raise HTTPException(status_code=403, detail="Round 2 time has expired.")

    if _seconds_left(team["round2_started_at"]) <= 0:
        connection.execute(
            "UPDATE teams SET current_state = ?, updated_at = ? WHERE id = ?",
            (TIMEOUT_STATE, _now_iso(), team["id"]),
        )
        _log(connection, team["id"], "TIMEOUT", {"round": 2})
        connection.commit()  # keep the timeout even though we raise next
        raise HTTPException(status_code=403, detail="Round 2 time has expired.")

    return team


def expire_if_needed(connection, team):
    """Persist a Round 2 timeout and return the current team row."""
    if (
        _norm(team["current_state"]) == _norm(ACTIVE_STATE)
        and team["round2_started_at"]
        and _seconds_left(team["round2_started_at"]) <= 0
    ):
        now = _now_iso()
        connection.execute(
            "UPDATE teams SET current_state = ?, updated_at = ? WHERE id = ?",
            (TIMEOUT_STATE, now, team["id"]),
        )
        _log(connection, team["id"], "TIMEOUT", {"round": 2})
        connection.commit()
        return _team(connection, team["id"])
    return team


# --- progress ----------------------------------------------------------------

WELCOME = (
    "CHRONOS Analyst online. I can summarise the three evidence files, cross-reference "
    "them and point out contradictions. I will not name a culprit: that decision is yours. "
    "You may ask up to 3 questions."
)


def _progress(connection, team) -> dict:
    tid = str(team["id"])
    rows = connection.execute(
        "SELECT COUNT(*) AS n "
        "FROM round2_chat_messages WHERE team_id = ?",
        (tid,),
    ).fetchone()
    used = rows["n"]
    sub = connection.execute("SELECT * FROM round2_submissions WHERE team_id = ?", (tid,)).fetchone()
    started = team["round2_started_at"]

    return {
        "team_id": team["id"],
        "team_name": team["team_name"],
        "state": team["current_state"],
        "ai": {
            "max_questions": MAX_AI_QUESTIONS,
            "used": used,
            "remaining": MAX_AI_QUESTIONS - used,
        },
        # Players never see whether they were right or what they scored. The score
        # is stored in the database for the admin leaderboard only; no player
        # endpoint returns it.
        "submitted": sub is not None,
        "suspect": None if sub is None else (sub["suspect"] if ("suspect" in sub.keys() and sub["suspect"]) else sub["suspect_identified"]),
        "seconds_left": _seconds_left(started) if started else None,
        "deadline": (_parse(started) + timedelta(seconds=DURATION_SECONDS)).isoformat(timespec="seconds")
                    if started else None,
        "welcome": WELCOME,
    }


def start_round2(team_id):
    with _Db() as connection:
        team = _team(connection, team_id)
        state = _norm(team["current_state"])

        # Refresh / re-entry never restarts the timer.
        if team["round2_started_at"] or state in {_norm(ACTIVE_STATE), _norm(COMPLETED_STATE), _norm(TIMEOUT_STATE)}:
            return _progress(connection, expire_if_needed(connection, team))

        if state not in STARTABLE:
            raise HTTPException(
                status_code=409,
                detail=f"Round 2 cannot start from state {team['current_state']}.",
            )

        # Every new game gets a case this team has not played before.
        case = round2_cases.assign_case(connection, team["id"])

        ai_model = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
        ai_live = "YES" if gemini_service.is_available() else "NO"
        connection.execute(
            "UPDATE teams SET current_state = ?, round2_started_at = ?, ai_model_used = COALESCE(NULLIF(ai_model_used, ''), ?), ai_api_live = COALESCE(NULLIF(ai_api_live, ''), ?), updated_at = ? WHERE id = ?",
            (ACTIVE_STATE, _now_iso(), ai_model, ai_live, _now_iso(), team["id"]),
        )
        _log(connection, team["id"], "ROUND_STARTED", {"round": 2, "case": case["case_id"]})
        return _progress(connection, _team(connection, team["id"]))


def get_progress(team_id):
    with _Db() as connection:
        team = expire_if_needed(connection, _require_started(connection, team_id))
        return _progress(connection, team)


# --- evidence ----------------------------------------------------------------

def _redact(name: str) -> str:
    return "".join("█" if i % 3 == 2 else c for i, c in enumerate(name))


def list_files(team_id):
    """Metadata only. Locked files appear as locked, with no real name or content."""
    with _Db() as connection:
        team = _team(connection, team_id)
        rows = round2_cases.case_files(connection, _case(connection, team)["case_id"])

    files = []
    for n, row in enumerate(rows, start=1):
        locked = bool(row["is_locked"])
        files.append({
            "file_id": f"LOCKED_{n}" if locked else row["file_id"],
            "project_name": round2_cases.project_name(row["file_id"]),
            "timeline_tag": row["timeline_tag"],
            "filename": _redact(row["filename"]) if locked else row["filename"],
            "is_locked": locked,
        })
    return files


def read_file(team_id, file_id):
    with _Db() as connection:
        team = _team(connection, team_id)
        rows = round2_cases.case_files(connection, _case(connection, team)["case_id"])

    row = next((r for r in rows if r["file_id"] == file_id and not r["is_locked"]), None)
    if row is None:
        raise HTTPException(status_code=404, detail="File not found or access denied")
    return {
        "file_id": row["file_id"],
        "project_name": round2_cases.project_name(row["file_id"]),
        "timeline_tag": row["timeline_tag"],
        "filename": row["filename"],
        "content_text": row["content_text"],
        "is_locked": False,
    }


def list_suspects(team_id):
    with _Db() as connection:
        team = _team(connection, team_id)
        rows = round2_cases.case_suspects(connection, _case(connection, team)["case_id"])
    # Names, ids and roles only. The culprit never leaves the database.
    return [{"name": r["suspect_name"], "user_id": r["user_id"], "role": r["role"]} for r in rows]


# --- AI analyst ----------------------------------------------------------------

def _evidence_for_prompt(connection, case_id) -> str:
    rows = [r for r in round2_cases.case_files(connection, case_id) if not r["is_locked"]]
    return "\n\n".join(
        f"[{round2_cases.project_name(r['file_id']).upper()} / {r['timeline_tag'].upper()} / {r['filename']}]\n{r['content_text']}"
        for r in rows
    ) or "(no evidence available)"


def _system_prompt(evidence: str) -> str:
    return (
        "You are the CHRONOS Analyst, an AI forensic advisor inside a 2140 timeline-corruption investigation.\n"
        "The players are Temporal Engineers (mostly non-technical). Your primary mission is to translate complex "
        "telemetry and system logs into clear, intuitive, and interpretable explanations so anyone can follow the story.\n\n"
        "TIMELINE ARCHITECTURE:\n"
        "- ALPHA (Future Timeline): Records scheduled configuration deltas and parameter modifications. "
        "Explain that an 'APPROVED' state only indicates the system workflow permitted the change—it does NOT mean the change was safe. "
        "A change that was 'PENDING' or 'REVERTED' may also hold critical clues.\n"
        "- BETA (Present Timeline): Documents the real-time incident report, symptom observations, and chronon flux metrics. "
        "Explain that this shows the exact moment when timeline stability collapsed.\n"
        "- GAMMA (Past Timeline): Contains user session audits and access history. Remind players that a user who merely "
        "performed a 'READ' operation did not alter timeline parameters, whereas a 'MODIFY' or commit altered system state.\n\n"
        "STRICT INVESTIGATION RULES (CRITICAL):\n"
        "1. DO NOT GIVE AWAY THE ANSWER. Under NO circumstances are you to name the culprit, accuse any suspect, "
        "confirm or deny if a suspect is guilty or innocent, or reveal Project Omega.\n"
        "2. If asked who did it or if a suspect is guilty, politely refuse in plain language and guide them: "
        "tell them which files to cross-reference (e.g. match the timestamp of the critical Alpha change to the active user session in Gamma).\n"
        "3. EXPLAIN LOGS CLEARLY: When players ask about specific files, timestamps, parameters, or session tokens, "
        "read the evidence below, quote the relevant lines, and explain what happened in plain, non-technical terms.\n"
        "4. Tone: Helpful, sharp forensic terminal AI persona. Answer in at most 3 to 4 clear, plain sentences.\n\n"
        "EVIDENCE DATABASE:\n" + evidence
    )


_ACCUSATION = re.compile(
    r"culprit|responsible|guilty|did it|is the one|behind (the|this)|caused (it|this|the)|"
    r"perpetrator|the person who|it was|prime suspect|most likely",
    re.IGNORECASE,
)

_OFF_SCOPE_KEYWORDS = re.compile(
    r"\b(weather|capital of|poem|story|song|essay|joke|translate|homework|dating|recipe)\b|"
    r"\b(who is (the )?(president|prime minister|ceo|elon|modi|biden|trump)|how are you)\b|"
    r"\b(python|javascript|typescript|c\+\+|java|html|css|web scrap|scrape)\b|"
    r"\bwrite (me )?(a )?(python )?(code|script|program)\b|"
    r"\b(solve \d|\d+\s*[\+\-\*\/]\s*\d+)\b",
    re.IGNORECASE
)


def _leaks_culprit(reply: str, culprit_name: str, culprit_user_id: str) -> bool:
    """Backstop for the prompt: a reply that names the culprit (name or user id)
    while accusing is dropped."""
    low = reply.lower()
    names_culprit = (
        culprit_name.lower() in low
        or culprit_name.split()[-1].lower() in low
        or culprit_user_id.lower() in low
    )
    return names_culprit and bool(_ACCUSATION.search(reply))


def _case_aware_fallback_reply(message: str, case: dict = None) -> str:
    """
    Tier-3 Zero-Downtime Forensics Engine:
    Delivers clear, non-technical analytical interpretations when external AI is offline.
    """
    q = message.lower().strip()

    # 1. Strict Scope Guardrail Enforcement
    if _OFF_SCOPE_KEYWORDS.search(q):
        return ("QUERY OUT OF SCOPE. Chronos Analyst terminal is restricted solely to the timeline corruption "
                "investigation. Consult Project Alpha, Beta, and Gamma logs.")

    # 2. Culprit Accusation Shield
    is_asking_culprit = (
        bool(re.search(r"culprit|guilty|responsible|suspect|blame|do it|did it|caused", q))
        or (bool(re.search(r"\bwho\b", q)) and not bool(re.search(r"gamma|access|session|log|terminal", q)))
    )
    if is_asking_culprit:
        return ("I cannot name a culprit—that deduction belongs to your team. To solve it, check what parameter changed in Alpha, "
                "see the exact time telemetry collapsed in Beta, and identify which user was active in Gamma at that precise minute.")

    # 3. Project Alpha Telemetry Analysis (Future Timeline)
    if re.search(r"alpha|change|config|parameter|authori|approv|status|delta", q):
        return ("Alpha tracks planned configuration changes in the Future timeline. Remember: an 'APPROVED' status simply means the automated workflow allowed the change, "
                "not that it was safe. Pay close attention to changes marked PENDING or REVERTED around the incident time.")

    # 4. Project Beta Incident Anomaly Analysis (Present Timeline)
    if re.search(r"beta|incident|symptom|detect|report|flux|reading|error", q):
        return ("Beta documents the real-time crash in the Present timeline. Look at the exact timestamp when stability dropped or chronon flux spiked. "
                "That timestamp is your anchor: whatever caused the failure happened immediately before that moment.")

    # 5. Project Gamma Session & Access Audit (Past Timeline)
    if re.search(r"gamma|access|history|user|session|export|read|modify|terminal|node", q):
        return ("Gamma audits user sessions in the Past timeline. Important clue: a 'READ' operation only views files without touching system code, "
                "whereas a 'MODIFY' or commit alters timeline parameters. Match the active users to the critical Alpha change time.")

    # 6. Chronological Sequencing Analysis
    if re.search(r"time|when|:\d\d|before|after|order|timestamp|sequence", q):
        return ("Line up the timestamps across all three timelines: first, see the earliest error recorded in Beta; second, find what change was committed in Alpha just before it; "
                "and third, see which user account was authenticated in Gamma during that exact window.")

    # 7. Default Correlation Prompt
    return ("Cross-reference the 3 files: what parameter changed (Alpha / Future), when the system collapsed (Beta / Present), "
            "and who was logged into the terminal at that moment (Gamma / Past).")


def chat(team_id, message):
    message = (message or "").strip()[:300]
    if not message:
        raise HTTPException(status_code=400, detail="Message is empty.")

    # 1. Reserve the question slot BEFORE calling the AI. The limit, the point
    #    deduction and the recorded row are all fixed here, server-side. The
    #    UNIQUE (team_id, question_number) constraint makes two simultaneous
    #    questions from one team safe.
    with _Db() as connection:
        team = _require_open(connection, team_id)
        tid = str(team["id"])
        used = connection.execute(
            "SELECT COUNT(*) FROM round2_chat_messages WHERE team_id = ?", (tid,)
        ).fetchone()[0]

        if used >= MAX_AI_QUESTIONS:
            raise HTTPException(status_code=403, detail="No AI questions remaining.")

        number = used + 1
        deduction = AI_DEDUCTIONS[used]
        try:
            connection.execute(
                "INSERT INTO round2_chat_messages "
                "(team_id, question_number, user_prompt, ai_response, points_deducted, created_at) "
                "VALUES (?, ?, ?, '', ?, ?)",
                (tid, number, message, deduction, _now_iso()),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="Another question is already being processed.")

        history_rows = connection.execute(
            "SELECT user_prompt, ai_response FROM round2_chat_messages "
            "WHERE team_id = ? AND question_number < ? ORDER BY question_number",
            (tid, number),
        ).fetchall()
        history = []
        for r in history_rows:
            history.append({"role": "user", "text": r["user_prompt"]})
            history.append({"role": "assistant", "text": r["ai_response"]})
        case = _case(connection, team)
        evidence = _evidence_for_prompt(connection, case["case_id"])
        culprit_name = case["culprit"]
        culprit_user_id = next(
            (r["user_id"] for r in round2_cases.case_suspects(connection, case["case_id"])
             if r["suspect_name"].lower() == culprit_name.lower()), "")
        _log(connection, team["id"], "HINT_USED", {"round": 2, "question": number, "points_deducted": deduction})

    # 2. Ask Groq Multi-Key Pool outside the transaction so a slow API never holds a DB lock.
    ai_meta = gemini_service.ask_with_metadata(_system_prompt(evidence), history, message)
    reply = ai_meta.get("reply")
    model_used = ai_meta.get("model_used") or os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
    is_live = bool(ai_meta.get("is_live", False))
    source = "groq_live_ai"

    if not reply or _leaks_culprit(reply, culprit_name, culprit_user_id):
        reply = _case_aware_fallback_reply(message, case)
        source = "chronos_forensics_engine"
        if not ai_meta.get("reply"):
            model_used = "offline_forensics"
            is_live = False

    api_live_str = "YES" if is_live else "NO"

    # 3. Store the answer on the reserved row and update team AI metadata.
    with _Db() as connection:
        connection.execute(
            "UPDATE round2_chat_messages SET ai_response = ?, model_used = ?, is_live = ?, api_live = ? WHERE team_id = ? AND question_number = ?",
            (reply, model_used, 1 if is_live else 0, api_live_str, tid, number),
        )
        connection.execute(
            "UPDATE teams SET ai_model_used = ?, ai_api_live = ? WHERE id = ?",
            (model_used, api_live_str, int(tid)),
        )
        progress = _progress(connection, _team(connection, tid))

    return {
        "reply": reply,
        "source": source,
        "question_number": number,
        "progress": progress,
    }


def get_ai_status() -> dict:
    """Safe diagnostic endpoint returning AI health and Groq provider metrics."""
    return gemini_service.get_ai_diagnostic_status()


def get_conversation(team_id):
    with _Db() as connection:
        team = _require_started(connection, team_id)
        rows = connection.execute(
            "SELECT question_number, user_prompt, ai_response "
            "FROM round2_chat_messages WHERE team_id = ? ORDER BY question_number",
            (str(team["id"]),),
        ).fetchall()
    return [dict(r) for r in rows]


# --- culprit submission ----------------------------------------------------------

def _match_suspect(connection, case_id, value: str):
    v = (value or "").strip().lower()
    return next(
        ({"name": r["suspect_name"], "user_id": r["user_id"]}
         for r in round2_cases.case_suspects(connection, case_id)
         if v in (r["user_id"].lower(), r["suspect_name"].lower())),
        None,
    )


def conclude_investigation(team_id):
    with _Db() as connection:
        team = _require_started(connection, team_id)
        tid = str(team["id"])
        case = _case(connection, team)

        existing = connection.execute("SELECT 1 FROM round2_submissions WHERE team_id = ?", (tid,)).fetchone()
        if existing:
            return _submit_response(_progress(connection, team), duplicate=True)

        team = _require_open(connection, team_id)

        used_lost = connection.execute(
            "SELECT COALESCE(SUM(points_deducted), 0) FROM round2_chat_messages WHERE team_id = ?", (tid,)
        ).fetchone()[0]
        ai_points_remaining = max(0, AI_BUDGET - used_lost)
        round2_score = max(0, min(MAX_ROUND2_SCORE, ai_points_remaining))

        try:
            connection.execute(
                "INSERT INTO round2_submissions "
                "(team_id, suspect, suspect_identified, is_correct, points_awarded, ai_points_remaining, round2_score, round2_total_score, submitted_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (tid, "INVESTIGATION_CONCLUDED", "INVESTIGATION_CONCLUDED", 1, round2_score, ai_points_remaining, round2_score, float(round2_score), _now_iso()),
            )
        except sqlite3.IntegrityError:
            return _submit_response(_progress(connection, _team(connection, tid)), duplicate=True)

        now = _now_iso()
        connection.execute(
            "UPDATE teams SET round2_score = ?, r2_score = ?, "
            "current_state = ?, round2_completed_at = ?, updated_at = ? WHERE id = ?",
            (round2_score, round2_score, COMPLETED_STATE, now, now, team["id"]),
        )
        from ..database.queries import update_team_scores
        update_team_scores(connection, team["id"])
        _log(connection, team["id"], "INVESTIGATION_CONCLUDED",
             {"round": 2, "case": case["case_id"], "ai_points_remaining": ai_points_remaining})
        _log(connection, team["id"], "ROUND_COMPLETED", {"round": 2, "score": round2_score})

        return _submit_response(_progress(connection, _team(connection, tid)), duplicate=False)


def submit_culprit(team_id, suspect_value):
    if not suspect_value or str(suspect_value).strip() == "INVESTIGATION_CONCLUDED":
        return conclude_investigation(team_id)

    with _Db() as connection:
        team = _require_started(connection, team_id)
        tid = str(team["id"])
        case = _case(connection, team)

        # Only this case's four candidates are valid answers.
        suspect = _match_suspect(connection, case["case_id"], suspect_value)
        if suspect is None:
            raise HTTPException(status_code=400, detail="Unknown suspect.")

        existing = connection.execute("SELECT 1 FROM round2_submissions WHERE team_id = ?", (tid,)).fetchone()
        if existing:  # a duplicate submission never awards points twice
            return _submit_response(_progress(connection, team), duplicate=True)

        team = _require_open(connection, team_id)

        used_lost = connection.execute(
            "SELECT COALESCE(SUM(points_deducted), 0) FROM round2_chat_messages WHERE team_id = ?", (tid,)
        ).fetchone()[0]
        ai_points_remaining = AI_BUDGET - used_lost

        correct = suspect["name"].strip().lower() == case["culprit"].strip().lower()
        # Round 2 Grading: 20 maximum, 0 minimum.
        # Correct culprit awards remaining AI budget (20 minus deductions: 20, 15, 10, or 0).
        # Wrong culprit awards 0 points.
        points = ai_points_remaining if correct else 0
        round2_score = max(0, min(MAX_ROUND2_SCORE, points))

        try:
            connection.execute(
                "INSERT INTO round2_submissions "
                "(team_id, suspect, suspect_identified, is_correct, points_awarded, ai_points_remaining, round2_score, round2_total_score, submitted_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (tid, suspect["name"], suspect["name"], int(correct), points, ai_points_remaining, round2_score, float(round2_score), _now_iso()),
            )
        except sqlite3.IntegrityError:
            return _submit_response(_progress(connection, _team(connection, tid)), duplicate=True)

        now = _now_iso()
        connection.execute(
            "UPDATE teams SET round2_score = ?, r2_score = ?, "
            "current_state = ?, round2_completed_at = ?, updated_at = ? WHERE id = ?",
            (round2_score, round2_score, COMPLETED_STATE, now, now, team["id"]),
        )
        from ..database.queries import update_team_scores
        update_team_scores(connection, team["id"])
        _log(connection, team["id"], "ANSWER_SUBMITTED",
             {"round": 2, "case": case["case_id"], "suspect": suspect["name"], "correct": correct})
        if correct:
            _log(connection, team["id"], "OMEGA_DISCOVERED", {"round": 2})
        _log(connection, team["id"], "ROUND_COMPLETED", {"round": 2, "score": round2_score})

        return _submit_response(_progress(connection, _team(connection, tid)), duplicate=False)


def _submit_response(progress: dict, duplicate: bool) -> dict:
    # Deliberately no correctness, points or score: players are not told how
    # they did. Those values live in round2_submissions / teams for the admin.
    return {
        "submitted": True,
        "duplicate": duplicate,
        "progress": progress,
    }
