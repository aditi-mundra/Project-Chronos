"""
Project Chronos: Round 3 cases.

One Round 3 case per Round 2 case (24, 1:1). They are generated together with the
Round 2 evidence files by backend/tools/generate_cases.py, so the files named in a
Round 3 evidence item are exactly the files the team investigated in Round 2:

  system_changes.log, login_records.log, security_keys.log, incident_report.txt

Each case has one culprit among Project Alpha / Beta / Gamma and the subset of those
files that supports the accusation (valid_evidence_ids). The set of supporting files
differs from case to case.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

_DATA_FILE = Path(__file__).with_name("round3_cases.json")

ROUND_3_CANONICAL_CASES: List[Dict[str, Any]] = json.loads(_DATA_FILE.read_text(encoding="utf-8"))

# Backward compatibility alias
ROUND_3_SCENARIO_TEMPLATES = ROUND_3_CANONICAL_CASES

_BY_R2_ID = {c["r2_case_id"]: c for c in ROUND_3_CANONICAL_CASES}


def get_case_for_team(team_id: int, r2_case_id: Optional[str] = None) -> Dict[str, Any]:
    """The Round 3 case that matches the team's Round 2 case.

    r2_case_id is the team's assigned Round 2 case (R2-01 ... R2-24). A team that
    has none (it never started Round 2) falls back to a stable choice from its id.
    """
    case = _BY_R2_ID.get(r2_case_id or "")
    if case is None:
        idx = (team_id - 1) % len(ROUND_3_CANONICAL_CASES) if team_id > 0 else 0
        case = ROUND_3_CANONICAL_CASES[idx]
    data = copy.deepcopy(case)
    data["assigned_team_id"] = team_id
    return data


def get_sanitized_case_for_client(case_data: Dict[str, Any]) -> Dict[str, Any]:
    """Strips secret answers before sending to client."""
    client_case = copy.deepcopy(case_data)
    for secret in ("culprit_candidate_id", "valid_evidence_ids", "narrative_summary", "r2_case_id"):
        client_case.pop(secret, None)
    return client_case
