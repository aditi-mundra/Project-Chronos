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
        "member_1_prn": "PRN-10101",
        "member_2_prn": "PRN-20202"
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

    # Submit answers for Round 1
    for item in r1_items[:5]:
        item_id = item.get("id") or item.get("item_id")
        client.post(f"/api/round1/submit?team_id={team_id}&item_id={item_id}&answer=PAST")

    # 5. Round 2 Files Check
    res_r2_files = client.get(f"/api/round2/files?team_id={team_id}")
    assert res_r2_files.status_code == 200
    r2_data = res_r2_files.json()
    assert "files" in r2_data or isinstance(r2_data, list)

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
    sub_payload = {
        "team_id": team_id,
        "selected_candidate_id": "alpha",
        "selected_evidence_ids": ["ev_01_future", "ev_02_incident"]
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
    assert verdict_data["submission"]["selected_candidate_id"] == "alpha"
    assert verdict_data["verdict_details"]["true_culprit_id"] != ""

    # 10. Admin Leaderboard & CSV Export
    res_lb = client.get("/api/admin/leaderboard")
    assert res_lb.status_code == 200
    lb_data = res_lb.json()
    assert isinstance(lb_data, list)
    assert len(lb_data) > 0

    res_csv = client.get("/api/admin/export-csv")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert "Rank" in res_csv.text

    # 11. Table-level CSV Export (docs/database.md Section 6)
    for tbl in ["teams", "round1_items", "round2_files", "round3_team_cases"]:
        res_tbl_csv = client.get(f"/api/admin/export/csv/{tbl}")
        assert res_tbl_csv.status_code == 200
        assert "text/csv" in res_tbl_csv.headers["content-type"]

    res_invalid_tbl = client.get("/api/admin/export/csv/non_existent_table")
    assert res_invalid_tbl.status_code == 400

    # 12. Query Helpers Verification (docs/database.md Section 5)
    from datetime import datetime, timezone
    from backend.app.database.queries import update_team_scores, record_round1_completion
    conn = get_connection()
    try:
        t0 = datetime.now(timezone.utc)
        t1 = datetime.now(timezone.utc)
        record_round1_completion(conn, team_id, 24.0, t0, t1)
        update_team_scores(conn, team_id)
        
        cur = conn.cursor()
        cur.execute("SELECT r1_score, round1_score, total_score, r1_time_diff FROM teams WHERE id = ?", (team_id,))
        row = cur.fetchone()
        assert row["r1_score"] == 24.0
        assert row["round1_score"] == 24.0
        assert row["r1_time_diff"] is not None
    finally:
        conn.close()

    print("================================================================")
    print(" ✔ FULL PIPELINE & LEADERBOARD INTEGRATION TEST PASSED!")
    print("================================================================")

if __name__ == "__main__":
    test_full_chronos_pipeline()

