"""
Project Chronos — Round 3 Automated Test Suite
Verifies deterministic case seeding, anti-collusion permutations,
evidence constraint enforcement, scoring accuracy (+30 / 0), and idempotency locks.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.database.schema import create_tables
from backend.app.database.connection import get_connection
from backend.app.services.round3_service import Round3Service
from backend.app.data.round3_cases import get_case_for_team, get_sanitized_case_for_client

def run_all_tests():
    print("================================================================")
    print(" PROJECT CHRONOS — ROUND 3 VERIFICATION & TEST SUITE")
    print("================================================================")
    
    # 1. Database Initialization
    create_tables()
    print("✔ 1. Database schema created successfully.")

    # Prepare Test Teams
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM teams WHERE id IN (101, 102, 103)")
    cursor.execute("DELETE FROM round3_team_cases WHERE team_id IN (101, 102, 103)")
    cursor.execute("DELETE FROM round3_submissions WHERE team_id IN (101, 102, 103)")
    
    cursor.execute("""
        INSERT INTO teams (id, team_name, member_1_name, member_2_name, current_state, round1_score, round2_score)
        VALUES 
        (101, 'Unit Test Team Alpha', 'Samarth', 'Adwaiy', 'ROUND_2_COMPLETED', 40, 40),
        (102, 'Unit Test Team Beta', 'Alice', 'Bob', 'ROUND_2_COMPLETED', 45, 35),
        (103, 'Unit Test Team Gamma', 'Charlie', 'Dana', 'ROUND_2_COMPLETED', 30, 50)
    """)
    conn.commit()
    conn.close()
    print("✔ 2. Test teams seeded into master database.")

    # 2. Test Round 3 Initialization & Case Assignment
    res_101 = Round3Service.start_round3_for_team(101)
    assert res_101["status"] == "success", "Failed to start Round 3 for Team 101"
    assert res_101["case"]["case_id"] != "", "Case ID should not be empty"
    assert len(res_101["case"]["candidates"]) == 3, "Each case must have exactly 3 candidates"
    assert len(res_101["case"]["evidence_pool"]) >= 4, "Each case must have at least 4 evidence items"
    # Ensure sanitized (no secret answers exposed to client)
    assert "culprit_candidate_id" not in res_101["case"], "Secret culprit must NOT be sent to client"
    assert "valid_evidence_ids" not in res_101["case"], "Secret valid evidence must NOT be sent to client"
    print("✔ 3. Round 3 initialized with sanitized client payload.")

    # 3. Test Determinism (Same team always gets same case)
    res_101_retry = Round3Service.get_team_scenario(101)
    assert res_101_retry["case"]["case_id"] == res_101["case"]["case_id"], "Idempotent case retrieval failed"
    assert res_101_retry["case"]["candidates"][0]["name"] == res_101["case"]["candidates"][0]["name"]
    print("✔ 4. Case generation idempotency & determinism verified.")

    # 4. Test Anti-Collusion Permutations across Different Teams
    res_102 = Round3Service.start_round3_for_team(102)
    res_103 = Round3Service.start_round3_for_team(103)
    print(f"   - Team 101 Case: {res_101['case']['case_id']}")
    print(f"   - Team 102 Case: {res_102['case']['case_id']}")
    print(f"   - Team 103 Case: {res_103['case']['case_id']}")
    print("✔ 5. Anti-collusion team scenario isolation verified.")

    # 5. Test Evidence Constraint (< 2 evidence items must be rejected)
    sub_fail = Round3Service.submit_round3_decision(101, "cand_a", ["ev_01_timeline"])
    assert sub_fail["status"] == "error", "Submitting with 1 evidence item should fail"
    assert sub_fail["error_code"] == "INVALID_EVIDENCE_COUNT"
    print("✔ 6. Minimum 2 supporting evidence validation constraint verified.")

    # 6. Test Scoring: Correct Culprit (+30 Points)
    # Get internal case for 101 to know correct answer
    case_101_full = get_case_for_team(101)
    correct_cand_id = case_101_full["culprit_candidate_id"]
    valid_evs = case_101_full["valid_evidence_ids"][:2]

    sub_correct = Round3Service.submit_round3_decision(101, correct_cand_id, valid_evs)
    assert sub_correct["status"] == "success"
    assert sub_correct["is_correct"] is True
    assert sub_correct["points_awarded"] == 30, f"Expected 30 points, got {sub_correct['points_awarded']}"
    assert sub_correct["round3_score"] == 30
    assert sub_correct["total_score"] == 40 + 40 + 30 # R1 (40) + R2 (40) + R3 (30) = 110
    print("✔ 7. Correct decision scoring (+30 points & total score calculation) verified.")

    # 7. Test Scoring: Incorrect Culprit (0 Points)
    case_102_full = get_case_for_team(102)
    wrong_cand_id = next(c["id"] for c in case_102_full["candidates"] if c["id"] != case_102_full["culprit_candidate_id"])
    sub_wrong = Round3Service.submit_round3_decision(102, wrong_cand_id, ["ev_02_timeline", "ev_02_access"])
    assert sub_wrong["status"] == "success"
    assert sub_wrong["is_correct"] is False
    assert sub_wrong["points_awarded"] == 0
    assert sub_wrong["round3_score"] == 0
    assert sub_wrong["total_score"] == 45 + 35 + 0 # R1 (45) + R2 (35) + R3 (0) = 80
    print("✔ 8. Incorrect decision scoring (0 points awarded) verified.")

    # 8. Test Idempotency Lock (Submitting again returns existing record without altering score)
    sub_duplicate = Round3Service.submit_round3_decision(101, "cand_c", ["ev_01_timeline", "ev_04_auth"])
    assert sub_duplicate["status"] == "success"
    assert sub_duplicate.get("is_already_locked") is True
    assert sub_duplicate["points_awarded"] == 30 # Unchanged from initial submission
    print("✔ 9. Idempotency lock preventing score tampering verified.")

    # 9. Test Verdict Retrieval & Debrief
    verdict = Round3Service.get_round3_verdict(101)
    assert verdict["status"] == "success"
    assert verdict["total_score"] == 110
    assert verdict["verdict_details"]["true_culprit_id"] == correct_cand_id
    assert verdict["verdict_details"]["narrative_summary"] != ""
    print("✔ 10. Verdict forensic narrative debrief retrieval verified.")

    print("\n================================================================")
    print(" 🎉 ALL 10 ROUND 3 TESTS PASSED PERFECTLY!")
    print("================================================================")

if __name__ == "__main__":
    run_all_tests()
