"""Round 2 -> Round 3 integration and integrity tests."""

import sys
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.database.connection import get_connection
from backend.app.database.schema import create_tables
from backend.app.main import app
from backend.app.services.round2_service import init_round2


def _new_team(client: TestClient) -> int:
    suffix = uuid.uuid4().int % 100_000_000
    response = client.post(
        "/api/auth/login",
        json={
            "team_name": f"R3 Integration {suffix}",
            "member_1_name": "Test One",
            "member_2_name": "Test Two",
            "member_1_prn": f"24{suffix:08d}1",
            "member_2_prn": f"25{suffix:08d}2",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["team_id"]


def _complete_round2(client: TestClient, team_id: int):
    assert client.post("/api/round2/start", json={"team_id": team_id}).status_code == 200
    with get_connection() as connection:
        case = connection.execute(
            "SELECT c.* FROM round2_team_cases tc "
            "JOIN round2_cases c ON c.case_id = tc.case_id WHERE tc.team_id = ?",
            (team_id,),
        ).fetchone()
        suspects = connection.execute(
            "SELECT suspect_name FROM round2_case_suspects WHERE case_id = ? ORDER BY id",
            (case["case_id"],),
        ).fetchall()
        files = connection.execute(
            "SELECT file_id FROM round2_case_files WHERE case_id = ? AND is_locked = 0 ORDER BY id",
            (case["case_id"],),
        ).fetchall()

    response = client.post(
        "/api/round2/submit", json={"team_id": team_id, "suspect": case["culprit"]}
    )
    assert response.status_code == 200, response.text
    return case, [row["suspect_name"] for row in suspects], [row["file_id"] for row in files]


def test_round3_requires_round2_completion():
    create_tables()
    init_round2()
    client = TestClient(app)
    team_id = _new_team(client)

    response = client.post("/api/round3/start", json={"team_id": team_id})
    assert response.status_code == 409


def test_round3_uses_the_assigned_round2_case():
    create_tables()
    init_round2()
    client = TestClient(app)
    team_id = _new_team(client)
    round2_case, suspect_names, file_ids = _complete_round2(client, team_id)

    start = client.post("/api/round3/start", json={"team_id": team_id})
    assert start.status_code == 200, start.text
    payload = start.json()
    scenario = payload["scenario"]

    assert scenario["case_id"] == round2_case["case_id"]
    assert {candidate["name"] for candidate in scenario["candidates"]} == set(suspect_names)
    assert all(candidate.get("user_id") for candidate in scenario["candidates"])
    assert all(candidate.get("role") for candidate in scenario["candidates"])
    scenario_text = str(scenario).lower()
    assert any(name.lower() in scenario_text for name in suspect_names)
    assert [item["id"] for item in scenario["evidence_archive"]] == [
        f"r2_{file_id.lower()}" for file_id in file_ids
    ]
    assert "culprit_candidate_id" not in scenario
    assert "valid_evidence_ids" not in scenario
    assert "culprit" not in scenario["round2_investigation"]["case_info"]

    culprit_candidate = next(
        c["id"] for c in scenario["candidates"]
        if c["name"].lower() == round2_case["culprit"].lower()
    )
    evidence_ids = [item["id"] for item in scenario["evidence_archive"]]

    submitted = client.post(
        "/api/round3/submit",
        json={
            "team_id": team_id,
            "selected_candidate_id": culprit_candidate,
            "selected_evidence_ids": [],
        },
    )
    assert submitted.status_code == 200, submitted.text
    result = submitted.json()
    assert "is_correct" not in result
    assert "points_awarded" not in result
    assert "round3_score" not in result
    assert "total_score" not in result

    duplicate = client.post(
        "/api/round3/submit",
        json={
            "team_id": team_id,
            "selected_candidate_id": culprit_candidate,
            "selected_evidence_ids": evidence_ids[:2],
        },
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["is_already_locked"] is True

    verdict = client.get(f"/api/round3/verdict?team_id={team_id}")
    assert verdict.status_code == 200
    verdict_data = verdict.json()
    assert "round1_score" not in verdict_data
    assert "round2_score" not in verdict_data
    assert "round3_score" not in verdict_data
    assert "total_score" not in verdict_data
    assert verdict_data["verdict_details"]["true_culprit_id"] == culprit_candidate
    assert verdict_data["verdict_details"]["true_culprit_name"] == round2_case["culprit"]
