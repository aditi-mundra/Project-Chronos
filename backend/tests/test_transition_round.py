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

    # Start stopwatch
    start_resp = client.post("/api/transition/start", json={"team_id": team_id})
    assert start_resp.status_code == 200
    started_info = start_resp.json()
    assert started_info["stopwatch_status"] == "RUNNING"
    assert started_info["start_time"] is not None

    # Incorrect password attempt
    bad_resp = client.post("/api/transition/verify", json={
        "team_id": team_id,
        "password": "WrongPassword!999"
    })
    assert bad_resp.status_code == 400
    assert "Invalid" in bad_resp.json()["detail"]

    # Verify stopwatch is still running
    mid_info = client.get(f"/api/transition/info?team_id={team_id}").json()
    assert mid_info["stopwatch_status"] == "RUNNING"
    assert not mid_info["is_completed"]

    # Correct password attempt with placeholder Chronos@123
    good_resp = client.post("/api/transition/verify", json={
        "team_id": team_id,
        "password": "Chronos@123"
    })
    assert good_resp.status_code == 200
    good_data = good_resp.json()
    assert good_data["success"] is True
    assert good_data["is_completed"] is True
    assert good_data["elapsed_seconds"] >= 0.0

    # Verify transition state is completed
    final_info = client.get(f"/api/transition/info?team_id={team_id}").json()
    assert final_info["stopwatch_status"] == "COMPLETED"
    assert final_info["is_completed"] is True
    assert final_info["can_proceed"] is True
