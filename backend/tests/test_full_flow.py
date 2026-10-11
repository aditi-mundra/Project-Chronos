"""
Project Chronos — Full End-to-End System Integration Test
Tests Auth -> Round 1 -> Round 2 -> Round 3 -> Completion flow with FastAPI TestClient.
"""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add project root and backend to sys.path
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from backend.app.main import app
from backend.app.database.schema import create_tables, seed_round1_items_if_empty, seed_round2_files_if_empty
from backend.app.database.connection import get_connection
from backend.app.routes.admin import ADMIN_SECRET_TOKEN

ADMIN_HEADERS = {"Authorization": f"Bearer {ADMIN_SECRET_TOKEN}"}

def test_full_chronos_pipeline():
    create_tables()
    seed_round1_items_if_empty()
    seed_round2_files_if_empty()

    client = TestClient(app)

    # 1. API Root Health Check
    res_root = client.get("/api")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "online"

    import uuid
    # 2. Team Login / Registration
    team_name = f"Integration Test Flight {uuid.uuid4().hex[:8]}"
    login_payload = {
        "team_name": team_name,
        "member_1_name": "Test Pilot Alpha",
        "member_2_name": "Test Pilot Beta",
        "member_1_prn": "24101010101",
        "member_2_prn": "25202020202"
    }
    res_login = client.post("/api/auth/login", json=login_payload)
    assert res_login.status_code == 200, f"Login failed: {res_login.text}"
    login_data = res_login.json()
    team_id = login_data["team_id"]
    assert team_id > 0
    assert login_data["team_name"] == team_name

    # 3. Session Check
    res_sess = client.get(f"/api/auth/session?team_id={team_id}")
    assert res_sess.status_code == 200
    sess_data = res_sess.json()
    assert sess_data["team_id"] == team_id

    # 4. Round 1 Items Fetch
    res_r1_items = client.get(f"/api/round1/items?team_id={team_id}")
    assert res_r1_items.status_code == 200
    r1_items = res_r1_items.json()
    assert isinstance(r1_items, list)
    assert len(r1_items) > 0

    # Submit every assigned item and complete Round 1 before advancing.
    for item in r1_items:
        item_id = item.get("id") or item.get("item_id")
        client.post(f"/api/round1/submit?team_id={team_id}&item_id={item_id}&answer=PAST")
    finish_r1 = client.post(f"/api/round1/finish?team_id={team_id}")
    assert finish_r1.status_code == 200, finish_r1.text

    # 5. Start and complete the team's assigned Round 2 case.
    start_r2 = client.post("/api/round2/start", json={"team_id": team_id})
    assert start_r2.status_code == 200, start_r2.text
    res_r2_files = client.get(f"/api/round2/files?team_id={team_id}")
    assert res_r2_files.status_code == 200
    r2_data = res_r2_files.json()
    assert "files" in r2_data or isinstance(r2_data, list)

    conn = get_connection()
    try:
        culprit = conn.execute(
            "SELECT c.culprit FROM round2_team_cases tc "
            "JOIN round2_cases c ON c.case_id = tc.case_id WHERE tc.team_id = ?",
            (team_id,),
        ).fetchone()["culprit"]
    finally:
        conn.close()
    finish_r2 = client.post(
        "/api/round2/submit", json={"team_id": team_id, "suspect": culprit}
    )
    assert finish_r2.status_code == 200, finish_r2.text

    # 6. Round 3 Start
    res_r3_start = client.post("/api/round3/start", json={"team_id": team_id})
    assert res_r3_start.status_code == 200, f"R3 start failed: {res_r3_start.text}"
    r3_start_data = res_r3_start.json()
    assert r3_start_data["status"] == "success"
    assert "scenario" in r3_start_data

    # 7. Round 3 Scenario Retrieval
    res_r3_scen = client.get(f"/api/round3/scenario?team_id={team_id}")
    assert res_r3_scen.status_code == 200
    scen_data = res_r3_scen.json()
    assert len(scen_data["scenario"]["candidates"]) == 3

    # 8. Round 3 Final Submission
    scenario = scen_data["scenario"]
    culprit_index = next(
        index for index, candidate in enumerate(scenario["candidates"])
        if candidate["name"].lower() == culprit.lower()
    )
    selected_candidate = ("alpha", "beta", "gamma")[culprit_index]
    evidence_ids = [item["id"] for item in scenario["evidence_archive"]]
    sub_payload = {
        "team_id": team_id,
        "selected_candidate_id": selected_candidate,
        "selected_evidence_ids": evidence_ids[:2]
    }
    res_r3_sub = client.post("/api/round3/submit", json=sub_payload)
    assert res_r3_sub.status_code == 200, f"R3 submit failed: {res_r3_sub.text}"
    sub_result = res_r3_sub.json()
    assert sub_result["status"] == "success"
    assert sub_result["verdict_recorded"] is True

    # 9. Round 3 Final Verdict & Debrief
    res_verdict = client.get(f"/api/round3/verdict?team_id={team_id}")
    assert res_verdict.status_code == 200
    verdict_data = res_verdict.json()
    assert verdict_data["status"] == "success"
    assert verdict_data["submission"]["selected_candidate_id"] == selected_candidate
    assert verdict_data["verdict_details"]["true_culprit_id"] != ""

    # 10. Admin Leaderboard & CSV Export
    assert client.get("/api/admin/leaderboard").status_code == 401
    res_lb = client.get("/api/admin/leaderboard", headers=ADMIN_HEADERS)
    assert res_lb.status_code == 200
    lb_data = res_lb.json()
    assert isinstance(lb_data, list)
    assert len(lb_data) > 0

    res_csv = client.get("/api/admin/export-csv", headers=ADMIN_HEADERS)
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert "Rank" in res_csv.text

    # 11. Table-level CSV Export (docs/database.md Section 6)
    for tbl in ["teams", "round1_items", "round2_files", "round3_team_cases"]:
        res_tbl_csv = client.get(f"/api/admin/export/csv/{tbl}", headers=ADMIN_HEADERS)
        assert res_tbl_csv.status_code == 200
        assert "text/csv" in res_tbl_csv.headers["content-type"]

    res_invalid_tbl = client.get("/api/admin/export/csv/non_existent_table", headers=ADMIN_HEADERS)
    assert res_invalid_tbl.status_code == 400

    print("================================================================")
    print(" ✔ FULL PIPELINE & LEADERBOARD INTEGRATION TEST PASSED!")
    print("================================================================")

if __name__ == "__main__":
    test_full_chronos_pipeline()

