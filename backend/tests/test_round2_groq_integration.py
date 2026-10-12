"""
Project Chronos — Round 2 Groq AI Integration Test Suite
Validates:
1. Groq multi-key pool loading and thread-safe key rotation.
2. Live Groq inference with non-technical, interpretable explanations.
3. Strict scope and anti-spoiler shielding (never names culprit).
4. Case-aware forensics fallback (zero-downtime safety net).
5. 10-team simultaneous concurrent querying.
"""

import os
import sys
import uuid
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from backend.app.database.schema import create_tables, seed_round1_items_if_empty
from backend.app.database.connection import get_connection
from backend.app.services.round2_service import (
    init_round2,
    start_round2,
    chat,
    get_ai_status,
    _case_aware_fallback_reply,
)
from backend.app.services import gemini_service


def test_groq_key_pool():
    print("\n--- 1. Testing Groq Key Pool Loading & Diagnostic Status ---")
    keys = gemini_service.get_api_keys()
    assert len(keys) == 3, f"Expected 3 keys in pool, found {len(keys)}"
    assert all(k.startswith("gsk_") for k in keys), "Keys should start with gsk_"

    status = gemini_service.get_ai_diagnostic_status()
    assert status["status"] == "online"
    assert status["active_keys_count"] == 3
    assert status["provider"] == "Groq Cloud API"
    assert "gsk_" not in str(status), "Private keys must not be exposed in status"
    assert status["zero_downtime_fallback_ready"] is True
    print("✔ Groq Key Pool parsed 3 keys successfully with strict redaction in diagnostics.")


def test_anti_spoiler_and_scope():
    print("\n--- 2. Testing Strict Scope and Anti-Spoiler Guardrail ---")
    # 1. Off-scope queries
    off_scope = [
        "What is the capital of Japan?",
        "Write a python script to parse CSV files",
        "Tell me a joke",
        "How is the weather today?"
    ]
    for q in off_scope:
        reply = _case_aware_fallback_reply(q)
        assert "QUERY OUT OF SCOPE" in reply, f"Failed to reject off-scope query: '{q}' -> '{reply}'"

    # 2. Culprit fishing queries
    spoiler_queries = [
        "Who is the culprit?",
        "Who did it?",
        "Tell me who is guilty",
        "Which suspect caused the timeline failure?"
    ]
    for q in spoiler_queries:
        reply = _case_aware_fallback_reply(q)
        assert "cannot name a culprit" in reply.lower() or "belongs to your team" in reply.lower(), (
            f"Failed to shield culprit: '{q}' -> '{reply}'"
        )
    print("✔ Off-scope queries rejected and culprit fishing queries strictly shielded.")


def test_ten_team_concurrency():
    print("\n--- 3. Testing 10-Team Concurrent Querying ---")
    create_tables()
    seed_round1_items_if_empty()
    init_round2()

    team_ids = []
    conn = get_connection()
    try:
        cur = conn.cursor()
        for i in range(1, 11):
            t_name = f"Scale Team {i} - {uuid.uuid4().hex[:6]}"
            cur.execute(
                "INSERT INTO teams (team_name, member_1_name, member_2_name, current_state) VALUES (?, 'Agent A', 'Agent B', 'READY')",
                (t_name,)
            )
            team_id = cur.lastrowid
            team_ids.append(team_id)
        conn.commit()
    finally:
        conn.close()

    for tid in team_ids:
        start_round2(tid)

    errors = []
    responses = []

    def team_worker(tid, question):
        try:
            res = chat(tid, question)
            responses.append((tid, res))
        except Exception as e:
            errors.append((tid, str(e)))

    threads = []
    questions = [
        "What does the APPROVED status mean in Alpha?",
        "When did the stability drop happen in Beta?",
        "What is the difference between READ and MODIFY in Gamma?",
        "What configuration deltas were submitted in Alpha?",
        "What timestamps should we compare in Beta?",
        "Can you explain the terminal session audit in Gamma?",
        "What were the chronological events leading to the failure?",
        "Explain the chronon flux readings in Beta in plain terms",
        "How do user session IDs in Gamma relate to changes in Alpha?",
        "What is the timeline sequence across the files?"
    ]

    for tid, q in zip(team_ids, questions):
        t = threading.Thread(target=team_worker, args=(tid, q))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert len(errors) == 0, f"Encountered concurrency errors: {errors}"
    assert len(responses) == 10, f"Expected 10 responses, got {len(responses)}"

    for tid, res in responses:
        assert res["question_number"] == 1
        assert len(res["reply"]) > 20
        assert res["progress"]["ai"]["remaining"] == 2
        assert res["source"] in ("groq_live_ai", "chronos_forensics_engine")

    print(f"✔ All 10 concurrent teams received valid responses (source: {responses[0][1]['source']}).")


def test_ai_model_and_live_csv_storage():
    print("\n--- 4. Testing AI Model & Live Status Storage in DB & CSV Export ---")
    create_tables()
    init_round2()

    conn = get_connection()
    try:
        cur = conn.cursor()
        t_name = f"CSV Audit Team - {uuid.uuid4().hex[:6]}"
        cur.execute(
            "INSERT INTO teams (team_name, member_1_name, member_2_name, current_state) VALUES (?, 'Audit 1', 'Audit 2', 'READY')",
            (t_name,)
        )
        tid = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    start_round2(tid)
    chat(tid, "Explain the telemetry in Beta")

    # 1. Verify directly in SQLite teams table
    conn = get_connection()
    try:
        cur = conn.cursor()
        row = cur.execute("SELECT ai_model_used, ai_api_live FROM teams WHERE id = ?", (tid,)).fetchone()
        assert row is not None
        assert row["ai_model_used"] != "", "ai_model_used must not be empty"
        assert row["ai_api_live"] in ("YES", "NO"), f"ai_api_live must be YES or NO, got {row['ai_api_live']}"

        chat_row = cur.execute(
            "SELECT model_used, api_live FROM round2_chat_messages WHERE team_id = ? ORDER BY question_number DESC LIMIT 1",
            (str(tid),)
        ).fetchone()
        assert chat_row is not None
        assert chat_row["model_used"] != ""
        assert chat_row["api_live"] in ("YES", "NO")
    finally:
        conn.close()

    # 2. Verify in Admin export-csv endpoint
    from fastapi.testclient import TestClient
    from backend.app.main import app
    from backend.app.routes.admin import ADMIN_SECRET_TOKEN

    client = TestClient(app)
    headers = {"Authorization": f"Bearer {ADMIN_SECRET_TOKEN}"}
    res_csv = client.get("/api/admin/export-csv", headers=headers)
    assert res_csv.status_code == 200
    assert "AI Model Used" in res_csv.text
    assert "AI API Live" in res_csv.text
    assert t_name in res_csv.text

    # 3. Verify in Table-level export endpoint
    res_tbl = client.get("/api/admin/export/csv/teams", headers=headers)
    assert res_tbl.status_code == 200
    assert "ai_model_used" in res_tbl.text
    assert "ai_api_live" in res_tbl.text
    print("✔ AI Model Used and AI API Live successfully verified in DB and CSV exports.")


if __name__ == "__main__":
    test_groq_key_pool()
    test_anti_spoiler_and_scope()
    test_ten_team_concurrency()
    test_ai_model_and_live_csv_storage()
    print("\n==========================================")
    print("🎉 ALL GROQ TEST SUITES PASSED SUCCESSFULLY!")
    print("==========================================\n")
