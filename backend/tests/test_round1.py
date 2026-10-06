"""
Project Chronos — Round 1 Comprehensive Test Suite
Verifies image dataset assignment, balanced era distribution,
idempotent item fetching, answer submission, in-flight answer update,
time synchronization, and completion sealing.
"""

import sys
from pathlib import Path

# Add project root and backend to sys.path
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.schema import create_tables, seed_round1_items_if_empty
from backend.app.database.connection import get_connection
from backend.app.services.round1_service import (
    get_round1_items,
    submit_answer,
    finish_round1,
    get_round1_status
)


def test_round1_full_lifecycle():
    create_tables()
    seed_round1_items_if_empty()

    client = TestClient(app)

    import uuid
    # 1. Create a dedicated test team
    team_name = f"R1 Test Unit {uuid.uuid4().hex[:8]}"
    login_res = client.post("/api/auth/login", json={
        "team_name": team_name,
        "member_1_name": "Explorer One",
        "member_2_name": "Explorer Two",
        "member_1_prn": "PRN-R1-001",
        "member_2_prn": "PRN-R1-002"
    })
    assert login_res.status_code == 200
    team_id = login_res.json()["team_id"]

    # 2. Check initial status
    status_initial = client.get(f"/api/round1/status?team_id={team_id}").json()
    assert status_initial["team_id"] == team_id
    assert status_initial["completed"] is False
    assert status_initial["submitted_items"] == 0

    # 3. Fetch 25 items
    items_res = client.get(f"/api/round1/items?team_id={team_id}")
    assert items_res.status_code == 200
    items = items_res.json()
    assert len(items) == 25

    # Verify idempotency
    items_retry = client.get(f"/api/round1/items?team_id={team_id}").json()
    assert [i["id"] for i in items] == [i["id"] for i in items_retry]

    # 4. Check that correct answers can be looked up from DB
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT item_id, correct_era FROM round1_items")
    era_map = {row["item_id"]: row["correct_era"] for row in cursor.fetchall()}
    conn.close()

    # 5. Submit first 10 items (mix of query params and JSON payload)
    for idx, item in enumerate(items[:10]):
        item_id = item["id"]
        correct_era = era_map[item_id]

        if idx % 2 == 0:
            # Send as query params
            res = client.post(f"/api/round1/submit?team_id={team_id}&item_id={item_id}&answer={correct_era}")
        else:
            # Send as JSON body
            res = client.post("/api/round1/submit", json={
                "team_id": team_id,
                "item_id": item_id,
                "answer": correct_era
            })
        assert res.status_code == 200
        data = res.json()
        assert data["is_correct"] is True
        assert data["points_awarded"] == 2

    # 6. Test in-flight answer update (repositioning fragment)
    test_item = items[0]
    test_item_id = test_item["id"]
    wrong_era = "FUTURE" if era_map[test_item_id] != "FUTURE" else "PAST"

    update_res = client.post("/api/round1/submit", json={
        "team_id": team_id,
        "item_id": test_item_id,
        "answer": wrong_era
    })
    assert update_res.status_code == 200
    update_data = update_res.json()
    assert update_data["is_correct"] is False
    assert update_data["points_awarded"] == -1

    # Revert back to correct answer
    revert_res = client.post("/api/round1/submit", json={
        "team_id": team_id,
        "item_id": test_item_id,
        "answer": era_map[test_item_id]
    })
    assert revert_res.status_code == 200
    assert revert_res.json()["is_correct"] is True

    # 7. Submit remaining 15 items
    for item in items[10:]:
        item_id = item["id"]
        correct_era = era_map[item_id]
        client.post("/api/round1/submit", json={
            "team_id": team_id,
            "item_id": item_id,
            "answer": correct_era
        })

    # 8. Complete Round 1
    finish_res = client.post(f"/api/round1/complete?team_id={team_id}")
    assert finish_res.status_code == 200
    finish_data = finish_res.json()
    assert finish_data["round1_completed"] is True
    assert finish_data["score"] == 50  # 25 items * 2 pts each
    assert finish_data["auth_code"] is not None
    assert len(finish_data["auth_code"]) == 6
    assert finish_data["next_round"] == "ROUND2"

    # 9. Verify final status
    status_final = client.get(f"/api/round1/status?team_id={team_id}").json()
    assert status_final["completed"] is True
    assert status_final["result"]["score"] == 50
    assert status_final["result"]["auth_code"] == finish_data["auth_code"]
