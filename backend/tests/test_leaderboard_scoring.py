"""
Unit and integration tests for Leaderboard scoring and total score calculations,
specifically verifying handling of negative Round 1 scores, Round 2, and Round 3 scores.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.connection import get_connection
from backend.app.database.schema import create_tables
from backend.app.database.queries import update_team_scores, record_round1_completion
from backend.app.routes.admin import ADMIN_SECRET_TOKEN, fetch_leaderboard_data

ADMIN_HEADERS = {"Authorization": f"Bearer {ADMIN_SECRET_TOKEN}"}


def test_leaderboard_total_calculation_with_negative_round1():
    create_tables()
    client = TestClient(app)

    conn = get_connection()
    try:
        # Create test teams with diverse scores including negative Round 1 scores
        # Team Neg1: Round 1 = -15, Round 2 = 10, Round 3 = 30 -> Total = 25
        # Team Neg2: Round 1 = -8, Round 2 = 0, Round 3 = 0 -> Total = -8
        # Team Pos1: Round 1 = 20, Round 2 = 15, Round 3 = 30 -> Total = 65
        # Team Zero: Round 1 = 0, Round 2 = 0, Round 3 = 0 -> Total = 0
        conn.execute("DELETE FROM teams WHERE team_name LIKE 'TEST_LB_%'")
        conn.commit()

        teams_data = [
            ("TEST_LB_NEG1", -15.0, 10.0, 30.0),
            ("TEST_LB_NEG2", -8.0, 0.0, 0.0),
            ("TEST_LB_POS1", 20.0, 15.0, 30.0),
            ("TEST_LB_ZERO", 0.0, 0.0, 0.0),
        ]

        team_ids = {}
        for name, r1, r2, r3 in teams_data:
            cur = conn.execute("""
                INSERT INTO teams (
                    team_name, member_1_name, member_2_name,
                    member_1_prn, member_2_prn, current_state,
                    round1_score, r1_score, round2_score, r2_score,
                    round3_score, r3_score, total_score
                ) VALUES (?, 'M1', 'M2', 'PRN1', 'PRN2', 'COMPLETED', ?, ?, ?, ?, ?, ?, 0.0)
            """, (name, r1, r1, r2, r2, r3, r3))
            team_ids[name] = cur.lastrowid
        conn.commit()

        # Update scores via query helper
        for tid in team_ids.values():
            update_team_scores(conn, tid)

        # Check DB total_score directly
        for name, r1, r2, r3 in teams_data:
            tid = team_ids[name]
            row = conn.execute("SELECT round1_score, r1_score, round2_score, round3_score, total_score FROM teams WHERE id = ?", (tid,)).fetchone()
            expected_total = round(r1 + r2 + r3, 2)
            assert row["total_score"] == expected_total, f"Team {name} total_score expected {expected_total}, got {row['total_score']}"

        # Verify password protection on /api/admin/login
        assert client.post("/api/admin/login", json={"password": "wrong"}).status_code == 401
        assert client.post("/api/admin/login", json={"password": "admin"}).status_code == 401
        login_res = client.post("/api/admin/login", json={"password": "Chronos@123"})
        assert login_res.status_code == 200
        assert login_res.json()["token"] == ADMIN_SECRET_TOKEN

        # Fetch leaderboard data via API endpoint
        assert client.get("/api/admin/leaderboard").status_code == 401
        res = client.get("/api/admin/leaderboard", headers=ADMIN_HEADERS)
        assert res.status_code == 200
        lb = res.json()
        assert isinstance(lb, list)

        # Filter to our test teams
        test_lb_teams = {t["team_name"]: t for t in lb if t["team_name"].startswith("TEST_LB_")}
        assert len(test_lb_teams) == 4

        # Validate total score in API response
        assert test_lb_teams["TEST_LB_POS1"]["total_score"] == 65.0
        assert test_lb_teams["TEST_LB_POS1"]["round1_score"] == 20.0

        assert test_lb_teams["TEST_LB_NEG1"]["total_score"] == 25.0
        assert test_lb_teams["TEST_LB_NEG1"]["round1_score"] == -15.0
        assert test_lb_teams["TEST_LB_NEG1"]["round2_score"] == 10.0
        assert test_lb_teams["TEST_LB_NEG1"]["round3_score"] == 30.0

        assert test_lb_teams["TEST_LB_ZERO"]["total_score"] == 0.0

        assert test_lb_teams["TEST_LB_NEG2"]["total_score"] == -8.0
        assert test_lb_teams["TEST_LB_NEG2"]["round1_score"] == -8.0

        # Validate ranking order: 65 > 25 > 0 > -8
        lb_subset = [t["team_name"] for t in lb if t["team_name"].startswith("TEST_LB_")]
        assert lb_subset == ["TEST_LB_POS1", "TEST_LB_NEG1", "TEST_LB_ZERO", "TEST_LB_NEG2"]

        # Validate CSV export endpoint
        res_csv = client.get("/api/admin/export-csv", headers=ADMIN_HEADERS)
        assert res_csv.status_code == 200
        assert "TEST_LB_NEG1" in res_csv.text
        assert "25.0" in res_csv.text
        assert "-15.0" in res_csv.text
        assert "-8.0" in res_csv.text

    finally:
        conn.execute("DELETE FROM teams WHERE team_name LIKE 'TEST_LB_%'")
        conn.commit()
        conn.close()


def test_authoritative_grading_bounds_enforcement():
    """
    Verify authoritative grading bounds are strictly enforced across DB queries,
    leaderboard API calculations, and CSV exports:
    - Round 1: [-25.0, 50.0]
    - Round 2: [0.0, 20.0]
    - Round 3: [0.0, 30.0]
    - Total: [-25.0, 100.0]
    """
    create_tables()
    client = TestClient(app)

    conn = get_connection()
    try:
        conn.execute("DELETE FROM teams WHERE team_name LIKE 'TEST_BOUNDS_%'")
        conn.commit()

        # Insert teams with values exceeding limits
        # High extreme: R1 = 70.0, R2 = 50.0, R3 = 45.0
        cur_hi = conn.execute("""
            INSERT INTO teams (
                team_name, member_1_name, member_2_name,
                member_1_prn, member_2_prn, current_state,
                round1_score, r1_score, round2_score, r2_score,
                round3_score, r3_score, total_score
            ) VALUES ('TEST_BOUNDS_HIGH', 'H1', 'H2', 'PRN_H1', 'PRN_H2', 'COMPLETED',
                      70.0, 70.0, 50.0, 50.0, 45.0, 45.0, 0.0)
        """)
        hi_id = cur_hi.lastrowid

        # Low extreme: R1 = -40.0, R2 = -10.0, R3 = -5.0
        cur_lo = conn.execute("""
            INSERT INTO teams (
                team_name, member_1_name, member_2_name,
                member_1_prn, member_2_prn, current_state,
                round1_score, r1_score, round2_score, r2_score,
                round3_score, r3_score, total_score
            ) VALUES ('TEST_BOUNDS_LOW', 'L1', 'L2', 'PRN_L1', 'PRN_L2', 'COMPLETED',
                      -40.0, -40.0, -10.0, -10.0, -5.0, -5.0, 0.0)
        """)
        lo_id = cur_lo.lastrowid
        conn.commit()

        # Update scores via query helper
        update_team_scores(conn, hi_id)
        update_team_scores(conn, lo_id)

        # Verify DB clamping
        hi_row = conn.execute("SELECT round1_score, round2_score, round3_score, total_score FROM teams WHERE id = ?", (hi_id,)).fetchone()
        assert hi_row["round1_score"] == 50.0
        assert hi_row["round2_score"] == 20.0
        assert hi_row["round3_score"] == 30.0
        assert hi_row["total_score"] == 100.0

        lo_row = conn.execute("SELECT round1_score, round2_score, round3_score, total_score FROM teams WHERE id = ?", (lo_id,)).fetchone()
        assert lo_row["round1_score"] == -25.0
        assert lo_row["round2_score"] == 0.0
        assert lo_row["round3_score"] == 0.0
        assert lo_row["total_score"] == -25.0

        # Verify API endpoint returns clamped data and limit metadata
        res = client.get("/api/admin/leaderboard", headers=ADMIN_HEADERS)
        assert res.status_code == 200
        lb = res.json()
        lookup = {t["team_name"]: t for t in lb if t["team_name"].startswith("TEST_BOUNDS_")}

        assert lookup["TEST_BOUNDS_HIGH"]["round1_score"] == 50.0
        assert lookup["TEST_BOUNDS_HIGH"]["round2_score"] == 20.0
        assert lookup["TEST_BOUNDS_HIGH"]["round3_score"] == 30.0
        assert lookup["TEST_BOUNDS_HIGH"]["total_score"] == 100.0
        assert lookup["TEST_BOUNDS_HIGH"]["r1_max"] == 50.0
        assert lookup["TEST_BOUNDS_HIGH"]["r1_min"] == -25.0
        assert lookup["TEST_BOUNDS_HIGH"]["r2_max"] == 20.0
        assert lookup["TEST_BOUNDS_HIGH"]["r2_min"] == 0.0
        assert lookup["TEST_BOUNDS_HIGH"]["r3_max"] == 30.0
        assert lookup["TEST_BOUNDS_HIGH"]["r3_min"] == 0.0
        assert lookup["TEST_BOUNDS_HIGH"]["total_max"] == 100.0
        assert lookup["TEST_BOUNDS_HIGH"]["total_min"] == -25.0

        assert lookup["TEST_BOUNDS_LOW"]["round1_score"] == -25.0
        assert lookup["TEST_BOUNDS_LOW"]["round2_score"] == 0.0
        assert lookup["TEST_BOUNDS_LOW"]["round3_score"] == 0.0
        assert lookup["TEST_BOUNDS_LOW"]["total_score"] == -25.0

        # Verify CSV export header limits
        res_csv = client.get("/api/admin/export-csv", headers=ADMIN_HEADERS)
        assert res_csv.status_code == 200
        assert "Round 1 Score (Max 50 / Min -25)" in res_csv.text
        assert "Round 2 Score (Max 20)" in res_csv.text
        assert "Round 3 Score (Max 30)" in res_csv.text
        assert "Total Score (Max 100)" in res_csv.text

    finally:
        conn.execute("DELETE FROM teams WHERE team_name LIKE 'TEST_BOUNDS_%'")
        conn.commit()
        conn.close()

