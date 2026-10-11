"""
Project Chronos — Round 2 Comprehensive Test Suite
Tests Round 2 Case Assignment, Files, AI Analyst Budget & Deductions,
Culprit Submission, Score Synchronization, and State Transitions.
"""

import sys
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.schema import create_tables, seed_round1_items_if_empty
from backend.app.services.round2_service import init_round2
from backend.app.database.connection import get_connection


def test_round2_full_lifecycle():
    create_tables()
    seed_round1_items_if_empty()
    init_round2()

    client = TestClient(app)

    # 1. Register a new team
    team_name = f"R2 Test Pilot {uuid.uuid4().hex[:8]}"
    login_res = client.post("/api/auth/login", json={
        "team_name": team_name,
        "member_1_name": "Detective Alpha",
        "member_2_name": "Detective Beta",
        "member_1_prn": "23000000001",
        "member_2_prn": "24000000002"
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    team_id = login_res.json()["team_id"]

    # 2. Check Round 2 case is already assigned
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT case_id FROM round2_team_cases WHERE team_id = ?", (team_id,))
        case_row = cur.fetchone()
        assert case_row is not None
        case_id = case_row["case_id"]
        assert case_id.startswith("R2-")

        # Get the true culprit for verification later
        cur.execute("SELECT culprit FROM round2_cases WHERE case_id = ?", (case_id,))
        true_culprit = cur.fetchone()["culprit"]
    finally:
        conn.close()

    # 3. List files before starting
    files_res = client.get(f"/api/round2/files?team_id={team_id}")
    assert files_res.status_code == 200
    files = files_res.json()
    assert len(files) == 3
    file_ids = [f["file_id"] for f in files]
    assert "alpha" in file_ids
    assert "beta" in file_ids
    assert "gamma" in file_ids

    # 4. Start Round 2
    start_res = client.post("/api/round2/start", json={"team_id": team_id})
    assert start_res.status_code == 200
    start_data = start_res.json()
    assert start_data["state"] == "ROUND_2_ACTIVE"
    assert start_data["ai"]["max_questions"] == 3
    assert start_data["ai"]["remaining"] == 3
    assert start_data["ai"]["points_remaining"] == 20
    assert start_data["ai"]["next_cost"] == 5

    # 5. Read unlocked file
    read_res = client.get(f"/api/round2/files/alpha?team_id={team_id}")
    assert read_res.status_code == 200
    alpha_content = read_res.json()
    assert len(alpha_content["content_text"]) > 0

    # 6. List suspects
    suspects_res = client.get(f"/api/round2/suspects?team_id={team_id}")
    assert suspects_res.status_code == 200
    suspects = suspects_res.json()
    assert len(suspects) >= 2
    suspect_names = [s["name"] for s in suspects]
    assert true_culprit in suspect_names

    # 7. Ask AI question 1 (-5 pts)
    chat1_res = client.post("/api/round2/chat", json={
        "team_id": team_id,
        "message": "What changes are recorded in Alpha?"
    })
    assert chat1_res.status_code == 200
    c1_data = chat1_res.json()
    assert c1_data["question_number"] == 1
    assert c1_data["points_deducted"] == 5
    assert c1_data["progress"]["ai"]["remaining"] == 2
    assert c1_data["progress"]["ai"]["points_remaining"] == 15
    assert c1_data["progress"]["ai"]["next_cost"] == 5

    # 8. Ask AI question 2 (-5 pts)
    chat2_res = client.post("/api/round2/chat", json={
        "team_id": team_id,
        "message": "What is the timeline in Beta?"
    })
    assert chat2_res.status_code == 200
    c2_data = chat2_res.json()
    assert c2_data["question_number"] == 2
    assert c2_data["points_deducted"] == 5
    assert c2_data["progress"]["ai"]["remaining"] == 1
    assert c2_data["progress"]["ai"]["points_remaining"] == 10
    assert c2_data["progress"]["ai"]["next_cost"] == 10

    # 9. Ask AI question 3 (-10 pts)
    chat3_res = client.post("/api/round2/chat", json={
        "team_id": team_id,
        "message": "Who accessed the terminal in Gamma?"
    })
    assert chat3_res.status_code == 200
    c3_data = chat3_res.json()
    assert c3_data["question_number"] == 3
    assert c3_data["points_deducted"] == 10
    assert c3_data["progress"]["ai"]["remaining"] == 0
    assert c3_data["progress"]["ai"]["points_remaining"] == 0

    # 10. Question 4 should fail (exceeded limit)
    chat4_res = client.post("/api/round2/chat", json={
        "team_id": team_id,
        "message": "One more question please"
    })
    assert chat4_res.status_code == 403

    # 11. Conversation history
    convo_res = client.get(f"/api/round2/conversation?team_id={team_id}")
    assert convo_res.status_code == 200
    history = convo_res.json()
    assert len(history) == 3

    # 12. Submit unknown suspect should fail (400)
    sub_fail = client.post("/api/round2/submit", json={
        "team_id": team_id,
        "suspect": "NonExistentPerson123"
    })
    assert sub_fail.status_code == 400

    # 13. Submit correct culprit (all 3 questions used -> 0 AI pts remaining -> 0 pts awarded)
    sub_res = client.post("/api/round2/submit", json={
        "team_id": team_id,
        "suspect": true_culprit
    })
    assert sub_res.status_code == 200
    sub_data = sub_res.json()
    assert sub_data["submitted"] is True
    assert sub_data["duplicate"] is False
    assert sub_data["progress"]["submitted"] is True
    assert sub_data["progress"]["suspect"] == true_culprit

    # 14. Duplicate submission is idempotent
    sub_dup = client.post("/api/round2/submit", json={
        "team_id": team_id,
        "suspect": true_culprit
    })
    assert sub_dup.status_code == 200
    assert sub_dup.json()["duplicate"] is True

    # 15. Verify database records and score
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT round2_score, r2_score, total_score, current_state FROM teams WHERE id = ?", (team_id,))
        team_row = cur.fetchone()
        assert team_row["round2_score"] == 0.0
        assert team_row["r2_score"] == 0.0
        assert team_row["total_score"] == 0.0
        assert team_row["current_state"] == "ROUND_2_COMPLETED"
    finally:
        conn.close()

    print("✔ Round 2 test passed successfully!")


def test_round2_partial_hints_score():
    """Verify team that only asks 1 question (deducts 5) gets 20 - 5 = 15 points (max 20)."""
    client = TestClient(app)
    team_name = f"R2 Hint Pilot {uuid.uuid4().hex[:8]}"
    login_res = client.post("/api/auth/login", json={
        "team_name": team_name,
        "member_1_name": "Detective Gamma",
        "member_2_name": "Detective Delta",
        "member_1_prn": "25000000003",
        "member_2_prn": "26000000004"
    })
    team_id = login_res.json()["team_id"]

    # Start
    client.post("/api/round2/start", json={"team_id": team_id})

    # Find culprit
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT c.culprit FROM round2_team_cases tc JOIN round2_cases c ON c.case_id = tc.case_id WHERE tc.team_id = ?", (team_id,))
        culprit = cur.fetchone()["culprit"]
    finally:
        conn.close()

    # Ask 1 question (-5)
    client.post("/api/round2/chat", json={"team_id": team_id, "message": "Analyze Alpha logs"})

    # Submit correct culprit -> 20 - 5 = 15 points
    sub_res = client.post("/api/round2/submit", json={"team_id": team_id, "suspect": culprit})
    assert sub_res.status_code == 200

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT round2_score, r2_score, total_score FROM teams WHERE id = ?", (team_id,))
        row = cur.fetchone()
        assert row["round2_score"] == 15.0
        assert row["r2_score"] == 15.0
        assert row["total_score"] == 15.0
    finally:
        conn.close()


def test_round2_perfect_score_no_hints():
    """Verify team that asks 0 questions gets full 20.0 points upon correct culprit submission."""
    client = TestClient(app)
    team_name = f"R2 Perfect Pilot {uuid.uuid4().hex[:8]}"
    login_res = client.post("/api/auth/login", json={
        "team_name": team_name,
        "member_1_name": "Detective Epsilon",
        "member_2_name": "Detective Zeta",
        "member_1_prn": "23000000005",
        "member_2_prn": "24000000006"
    })
    team_id = login_res.json()["team_id"]

    # Start
    client.post("/api/round2/start", json={"team_id": team_id})

    # Find culprit
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT c.culprit FROM round2_team_cases tc JOIN round2_cases c ON c.case_id = tc.case_id WHERE tc.team_id = ?", (team_id,))
        culprit = cur.fetchone()["culprit"]
    finally:
        conn.close()

    # Submit correct culprit directly without asking questions -> 20.0 max points
    sub_res = client.post("/api/round2/submit", json={"team_id": team_id, "suspect": culprit})
    assert sub_res.status_code == 200

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT round2_score, r2_score, total_score FROM teams WHERE id = ?", (team_id,))
        row = cur.fetchone()
        assert row["round2_score"] == 20.0
        assert row["r2_score"] == 20.0
        assert row["total_score"] == 20.0
    finally:
        conn.close()


def test_round2_wrong_culprit_zero_points():
    """Verify wrong culprit submission awards 0 points."""
    client = TestClient(app)
    team_name = f"R2 Wrong Pilot {uuid.uuid4().hex[:8]}"
    login_res = client.post("/api/auth/login", json={
        "team_name": team_name,
        "member_1_name": "Detective Eta",
        "member_2_name": "Detective Theta",
        "member_1_prn": "25000000007",
        "member_2_prn": "26000000008"
    })
    team_id = login_res.json()["team_id"]

    # Start
    client.post("/api/round2/start", json={"team_id": team_id})

    # Get suspects and pick a wrong one
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT c.culprit FROM round2_team_cases tc JOIN round2_cases c ON c.case_id = tc.case_id WHERE tc.team_id = ?", (team_id,))
        culprit = cur.fetchone()["culprit"]
        suspects_res = client.get(f"/api/round2/suspects?team_id={team_id}").json()
        wrong_suspect = next(s["name"] for s in suspects_res if s["name"].lower() != culprit.lower())
    finally:
        conn.close()

    # Submit wrong suspect
    sub_res = client.post("/api/round2/submit", json={"team_id": team_id, "suspect": wrong_suspect})
    assert sub_res.status_code == 200

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT round2_score, r2_score, total_score FROM teams WHERE id = ?", (team_id,))
        row = cur.fetchone()
        assert row["round2_score"] == 0.0
        assert row["r2_score"] == 0.0
        assert row["total_score"] == 0.0
    finally:
        conn.close()

