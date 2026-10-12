import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.connection import get_connection
from backend.app.database.schema import create_tables

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    create_tables()
    conn = get_connection()
    try:
        # Clear teams for clean test run
        conn.execute("DELETE FROM teams WHERE team_name LIKE 'TEST_TRANS_%'")
        conn.execute("UPDATE teams SET transition_zone = '', transition_clue_text = ''")
        conn.commit()
    finally:
        conn.close()


def test_transition_six_teams_zone_balance_and_clues():
    """
    Test that across 6 teams:
    - Exactly 2 teams get PAST
    - Exactly 2 teams get PRESENT
    - Exactly 2 teams get FUTURE
    - Distinct clues from docs/clues.md are provided to teams in the same zone.
    """
    team_ids = []
    # Register 6 test teams
    for i in range(1, 7):
        resp = client.post("/api/auth/login", json={
            "team_name": f"TEST_TRANS_TEAM_{i}",
            "member_1_name": f"Operator A{i}",
            "member_2_name": f"Operator B{i}",
            "member_1_prn": f"2400000000{i}",
            "member_2_prn": f"2500000000{i}",
        })
        assert resp.status_code == 200, resp.text
        team_ids.append(resp.json()["team_id"])

    assert len(team_ids) == 6

    zones = {}
    clues_by_zone = {}

    for tid in team_ids:
        resp = client.get(f"/api/transition/info?team_id={tid}")
        assert resp.status_code == 200, resp.text
        data = resp.json()

        z = data["zone"]
        assert z in ("PAST", "PRESENT", "FUTURE")
        zones[z] = zones.get(z, 0) + 1

        clues_by_zone.setdefault(z, []).append(data["clue_number"])
        assert len(data["clue_text"]) > 10
        assert f"{z.title()} Zone" in data["destination"]

    # Compulsory condition: exactly 2 teams per zone
    assert zones.get("PAST") == 2, f"Expected 2 PAST teams, got {zones.get('PAST')}"
    assert zones.get("PRESENT") == 2, f"Expected 2 PRESENT teams, got {zones.get('PRESENT')}"
    assert zones.get("FUTURE") == 2, f"Expected 2 FUTURE teams, got {zones.get('FUTURE')}"

    # Verify that the two teams in each zone got distinct clues
    for z in ("PAST", "PRESENT", "FUTURE"):
        assert len(set(clues_by_zone[z])) == 2, f"Teams in {z} did not receive distinct clues: {clues_by_zone[z]}"


def test_transition_stopwatch_and_password():
    """
    Test that the stopwatch starts, runs, and stops only when Chronos@123 is entered.
    """
    # Register a test team
    resp = client.post("/api/auth/login", json={
        "team_name": "TEST_TRANS_STOPWATCH",
        "member_1_name": "Op 1",
        "member_2_name": "Op 2",
        "member_1_prn": "24111111111",
        "member_2_prn": "25222222222",
    })
    assert resp.status_code == 200
    team_id = resp.json()["team_id"]

    # Check initial info
    info = client.get(f"/api/transition/info?team_id={team_id}").json()
    assert info["stopwatch_status"] == "NOT_STARTED"
    assert not info["is_completed"]

    # REQUIREMENT: Entering password BEFORE starting stopwatch must be rejected
    pre_resp = client.post("/api/transition/verify", json={
        "team_id": team_id,
        "password": "Chronos@123"
    })
    assert pre_resp.status_code == 400
    assert "stopwatch" in pre_resp.json()["detail"].lower()

    # Start stopwatch
    start_resp = client.post("/api/transition/start", json={"team_id": team_id})
    assert start_resp.status_code == 200
    started_info = start_resp.json()
    assert started_info["stopwatch_status"] == "RUNNING"
    assert started_info["start_time"] is not None

    # Incorrect password attempt (Attempt 1)
    bad_resp = client.post("/api/transition/verify", json={
        "team_id": team_id,
        "password": "WrongPassword!999"
    })
    assert bad_resp.status_code == 400
    assert "Attempt 1 of 3 failed" in bad_resp.json()["detail"]

    # Verify stopwatch is still running and attempts updated
    mid_info = client.get(f"/api/transition/info?team_id={team_id}").json()
    assert mid_info["stopwatch_status"] == "RUNNING"
    assert not mid_info["is_completed"]
    assert mid_info["transition_attempts"] == 1
    assert mid_info["attempts_remaining"] == 2

    # Correct password on Attempt 2 -> Graded 10 points
    good_resp = client.post("/api/transition/verify", json={
        "team_id": team_id,
        "password": "Chronos@123"
    })
    assert good_resp.status_code == 200
    good_data = good_resp.json()
    assert good_data["success"] is True
    assert good_data["is_completed"] is True
    assert good_data["points_awarded"] == 10.0
    assert good_data["attempts_used"] == 2
    assert good_data["elapsed_seconds"] >= 0.0

    # Verify transition state is completed with 10 points
    final_info = client.get(f"/api/transition/info?team_id={team_id}").json()
    assert final_info["stopwatch_status"] == "COMPLETED"
    assert final_info["is_completed"] is True
    assert final_info["can_proceed"] is True
    assert final_info["transition_score"] == 10.0


def test_transition_graded_attempts_and_auto_advance():
    """
    Test the complete graded scoring and 3-attempt auto-advance matrix:
    - Attempt 1 correct: 20 points
    - Attempt 2 correct: 10 points
    - Attempt 3 correct: 5 points
    - Attempt 3 failed: 0 points and automatically advances to Round 2
    """
    # 1. Team 1: First Attempt Success (20 Points)
    r1 = client.post("/api/auth/login", json={
        "team_name": "TEST_TRANS_TIER1",
        "member_1_name": "A1",
        "member_2_name": "A2",
        "member_1_prn": "24333333331",
        "member_2_prn": "25333333332",
    }).json()
    t1 = r1["team_id"]
    client.post("/api/transition/start", json={"team_id": t1})
    v1 = client.post("/api/transition/verify", json={"team_id": t1, "password": "Chronos@123"}).json()
    assert v1["success"] is True
    assert v1["points_awarded"] == 20.0
    assert v1["attempts_used"] == 1

    # 2. Team 2: Third Attempt Success (5 Points)
    r2 = client.post("/api/auth/login", json={
        "team_name": "TEST_TRANS_TIER3",
        "member_1_name": "B1",
        "member_2_name": "B2",
        "member_1_prn": "24444444441",
        "member_2_prn": "25444444442",
    }).json()
    t2 = r2["team_id"]
    client.post("/api/transition/start", json={"team_id": t2})
    # Fail 1
    f1 = client.post("/api/transition/verify", json={"team_id": t2, "password": "BAD_1"})
    assert f1.status_code == 400
    # Fail 2
    f2 = client.post("/api/transition/verify", json={"team_id": t2, "password": "BAD_2"})
    assert f2.status_code == 400
    # Succeed 3
    v3 = client.post("/api/transition/verify", json={"team_id": t2, "password": "Chronos@123"}).json()
    assert v3["success"] is True
    assert v3["points_awarded"] == 5.0
    assert v3["attempts_used"] == 3

    # 3. Team 3: 3 Inaccurate Responses -> Auto-advance with 0 Points
    r3 = client.post("/api/auth/login", json={
        "team_name": "TEST_TRANS_FAIL3",
        "member_1_name": "C1",
        "member_2_name": "C2",
        "member_1_prn": "24555555551",
        "member_2_prn": "25555555552",
    }).json()
    t3 = r3["team_id"]
    client.post("/api/transition/start", json={"team_id": t3})
    # Fail 1
    assert client.post("/api/transition/verify", json={"team_id": t3, "password": "WRONG_1"}).status_code == 400
    # Fail 2
    assert client.post("/api/transition/verify", json={"team_id": t3, "password": "WRONG_2"}).status_code == 400
    # Fail 3 -> HTTP 200 with auto_advanced: True and 0 points!
    v_fail3 = client.post("/api/transition/verify", json={"team_id": t3, "password": "WRONG_3"})
    assert v_fail3.status_code == 200
    data_fail3 = v_fail3.json()
    assert data_fail3["success"] is True
    assert data_fail3["is_completed"] is True
    assert data_fail3["auto_advanced"] is True
    assert data_fail3["points_awarded"] == 0.0
    assert data_fail3["attempts_used"] == 3

    # Verify Team 3 can proceed to Round 2
    info_fail3 = client.get(f"/api/transition/info?team_id={t3}").json()
    assert info_fail3["stopwatch_status"] == "COMPLETED"
    assert info_fail3["can_proceed"] is True
    assert info_fail3["transition_score"] == 0.0
    assert info_fail3["transition_attempts"] == 3

    # Attempt 4 must be BLOCKED / Never exceed 3 attempts
    v_fail4 = client.post("/api/transition/verify", json={"team_id": t3, "password": "ATTEMPT_4_SHOULD_BE_BLOCKED"})
    assert v_fail4.status_code == 200
    assert v_fail4.json()["is_completed"] is True
    assert v_fail4.json()["attempts_used"] == 3

    info_fail4 = client.get(f"/api/transition/info?team_id={t3}").json()
    assert info_fail4["transition_attempts"] == 3
    assert info_fail4["is_completed"] is True

