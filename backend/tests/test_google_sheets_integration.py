import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from backend.app.main import app
from backend.app.database.schema import create_tables
from backend.app.database.connection import get_connection
from backend.app.services.google_sheets_service import (
    google_sheets_service,
    extract_sheet_id,
    GoogleSheetService,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def init_db():
    create_tables()
    conn = get_connection()
    try:
        conn.execute("DELETE FROM teams WHERE team_name LIKE 'TEST_SHEETS_%'")
        conn.commit()
    finally:
        conn.close()


def test_extract_sheet_id():
    raw_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
    assert extract_sheet_id(raw_id) == raw_id

    url_edit = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit#gid=0"
    assert extract_sheet_id(url_edit) == raw_id

    url_view = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view"
    assert extract_sheet_id(url_view) == raw_id


def test_column_detection_helpers():
    service = GoogleSheetService()

    # Standard headers
    rows_standard = [
        ["Password", "Status", "Used By", "Used At", "Zone"],
        ["ALPHA-7", "AVAILABLE", "", "", "PAST"],
    ]
    col_pw, col_status, col_team, col_time, col_zone, start_idx = service._detect_columns(rows_standard)
    assert col_pw == 0
    assert col_status == 1
    assert col_team == 2
    assert col_time == 3
    assert col_zone == 4
    assert start_idx == 1

    # Permuted headers
    rows_permuted = [
        ["Token", "Timeline Sector", "Current Status", "Claimed By Unit", "Redeemed At"],
        ["OMEGA-9", "FUTURE", "ACTIVE", "", ""],
    ]
    col_pw, col_status, col_team, col_time, col_zone, start_idx = service._detect_columns(rows_permuted)
    assert col_pw == 0
    assert col_zone == 1
    assert col_status == 2
    assert col_team == 3
    assert col_time == 4
    assert start_idx == 1

    # No headers (raw data starting row 1)
    rows_raw = [
        ["ALPHA-1", "AVAILABLE", "", ""],
        ["BETA-2", "AVAILABLE", "", ""],
    ]
    col_pw, col_status, col_team, col_time, col_zone, start_idx = service._detect_columns(rows_raw)
    assert col_pw == 0
    assert col_status == 1
    assert start_idx == 0


def test_unconfigured_fallback_mode():
    service = GoogleSheetService()

    # Unknown password fails
    res_bad = service.validate_and_use_password("NON_EXISTENT_PASSWORD", 1, "Team 1")
    assert not res_bad["valid"]
    assert "Invalid" in res_bad["error"]

    # Admin fallback succeeds
    res_admin = service.validate_and_use_password("Chronos@123", 1, "Team 1")
    assert res_admin["valid"]


def test_google_sheet_mock_validation_and_reflection():
    """
    Mocks gspread client and tests:
    - Successfully validates unused password and calls update_cell on Google Sheet
    - Rejects already used password
    - Rejects invalid password
    """
    service = GoogleSheetService()

    # Mock spreadsheet data
    mock_values = [
        ["Password", "Status", "Used By", "Used At", "Zone"],
        ["SECTOR-ALPHA", "AVAILABLE", "", "", "PAST"],
        ["SECTOR-BETA", "USED", "Team Beta (ID: 5)", "2026-10-12 12:00:00 UTC", "PRESENT"],
    ]

    mock_worksheet = MagicMock()
    mock_worksheet.get_all_values.return_value = mock_values

    mock_client = MagicMock()
    service._get_gspread_client = MagicMock(return_value=mock_client)
    service._get_worksheets = MagicMock(return_value=[mock_worksheet])
    service._get_worksheet = MagicMock(return_value=mock_worksheet)

    # 1. Valid unused password
    res = service.validate_via_service_account("SECTOR-ALPHA", 10, "Team Alpha")
    assert res["valid"] is True
    assert res["password"] == "SECTOR-ALPHA"
    assert res["zone"] == "PAST"
    assert res["row_index"] == 2  # Row 2 in sheet (1-based)

    # Check update_cell was called for Status, Team, and Timestamp
    assert mock_worksheet.update_cell.call_count >= 3
    calls = mock_worksheet.update_cell.call_args_list
    # Status updated to TRUE or USED on row 2, col 2
    assert calls[0].args in [(2, 2, "TRUE"), (2, 2, "USED")]
    # Used By updated on row 2, col 3
    assert "Team Alpha" in calls[1].args[2]

    # 2. Already used password
    res_used = service.validate_via_service_account("SECTOR-BETA", 11, "Team Gamma")
    assert res_used["valid"] is False
    assert res_used.get("is_used") is True
    assert "already been used" in res_used["error"]
    assert "Team Beta" in res_used["error"]

    # 3. Invalid password
    res_invalid = service.validate_via_service_account("UNKNOWN-PASS", 12, "Team Delta")
    assert res_invalid["valid"] is False
    assert "not recognized" in res_invalid["error"].lower()


def test_transition_api_with_google_sheet_mock():
    """
    Tests POST /api/transition/verify endpoint end-to-end with mocked Google Spreadsheet service.
    """
    # Register a team
    resp = client.post("/api/auth/login", json={
        "team_name": "TEST_SHEETS_TEAM_A",
        "member_1_name": "Player 1",
        "member_2_name": "Player 2",
        "member_1_prn": "24999999991",
        "member_2_prn": "25999999992",
    })
    assert resp.status_code == 200
    team_id = resp.json()["team_id"]

    # Start stopwatch
    client.post("/api/transition/start", json={"team_id": team_id})

    # Mock google_sheets_service.validate_and_use_password
    with patch("backend.app.services.transition_service.google_sheets_service.validate_and_use_password") as mock_val:
        # 1. Invalid attempt
        mock_val.return_value = {
            "valid": False,
            "error": "Password not found in central registry."
        }
        res_fail = client.post("/api/transition/verify", json={
            "team_id": team_id,
            "password": "WRONG_PASSWORD"
        })
        assert res_fail.status_code == 400
        assert "not found" in res_fail.json()["detail"]

        # 2. Already used attempt
        mock_val.return_value = {
            "valid": False,
            "is_used": True,
            "error": "This security password has already been used by Team Apex."
        }
        res_already_used = client.post("/api/transition/verify", json={
            "team_id": team_id,
            "password": "USED_PASSWORD"
        })
        assert res_already_used.status_code == 400
        assert "already been used" in res_already_used.json()["detail"]

        # 3. Valid unused password
        mock_val.return_value = {
            "valid": True,
            "message": "Security password authenticated. Recorded in Google Spreadsheet.",
            "password": "VALID_TOKEN_123",
            "source": "GOOGLE_SPREADSHEET_API",
            "zone": "PAST"
        }
        res_ok = client.post("/api/transition/verify", json={
            "team_id": team_id,
            "password": "VALID_TOKEN_123"
        })
        assert res_ok.status_code == 200
        data = res_ok.json()
        assert data["success"] is True
        assert data["is_completed"] is True

        # Check team info has transition COMPLETED and password saved
        info = client.get(f"/api/transition/info?team_id={team_id}").json()
        assert info["stopwatch_status"] == "COMPLETED"
        assert info["is_completed"] is True
        assert info["can_proceed"] is True
        assert info["password_used"] == "VALID_TOKEN_123"


def test_sheets_status_diagnostic_endpoint():
    res = client.get("/api/transition/sheets-status")
    assert res.status_code == 200
    data = res.json()
    assert "configured" in data
    assert "method" in data
    assert "connected" in data


def test_dynamic_passwords_add_and_validation():
    """
    Tests dynamic password injection (dummy1..dummy5) into GoogleSheetService:
    - Adds dummy1..dummy5 to PAST zone
    - Validates dummy1 for Team 1
    - Rejects reuse of dummy1 for Team 2
    - Validates dummy2 for Team 2
    """
    service = GoogleSheetService()
    pws = ["dummy1", "dummy2", "dummy3", "dummy4", "dummy5"]
    add_res = service.add_passwords(pws, zone="PAST")
    assert add_res["success"] is True

    # 1. First use of dummy1 succeeds
    v1 = service.validate_and_use_password("dummy1", team_id=1, team_name="Team 1", zone="PAST")
    assert v1["valid"] is True
    assert v1["zone"] == "PAST"
    assert "dummy1" in v1["password"].lower()

    # 2. Reuse of dummy1 fails
    v1_reuse = service.validate_and_use_password("dummy1", team_id=2, team_name="Team 2", zone="PAST")
    assert v1_reuse["valid"] is False
    assert v1_reuse.get("is_used") is True
    assert "already been used" in v1_reuse["error"]

    # 3. dummy2 is still available
    v2 = service.validate_and_use_password("dummy2", team_id=2, team_name="Team 2", zone="PAST")
    assert v2["valid"] is True

    # 4. Unknown password fails
    v_unknown = service.validate_and_use_password("not_in_list", team_id=3, team_name="Team 3")
    assert v_unknown["valid"] is False


def test_service_account_dynamic_expansion_mock():
    """
    Tests gspread append_rows and dynamic row scanning for dynamically added rows beyond row 50.
    """
    service = GoogleSheetService()

    # Initial sheet with 50 rows
    initial_rows = [
        ["Project Chronos - Passwords (PAST)", "", ""],
        ["SN", "Password", "Status"],
    ]
    for i in range(1, 51):
        initial_rows.append([str(i), f"ORIG_PASS_{i}", "FALSE"])

    mock_worksheet = MagicMock()
    mock_worksheet.title = "PAST - PASSWORDS"
    mock_worksheet.get_all_values.return_value = list(initial_rows)

    mock_client = MagicMock()
    service._get_gspread_client = MagicMock(return_value=mock_client)
    service._get_worksheets = MagicMock(return_value=[mock_worksheet])

    # Add dummy1..dummy5
    res = service.add_passwords_via_service_account(["dummy1", "dummy2", "dummy3", "dummy4", "dummy5"], zone="PAST")
    assert res["success"] is True
    assert res["total_added"] == 5

    # Check append_rows was called
    assert mock_worksheet.append_rows.call_count == 1
    appended = mock_worksheet.append_rows.call_args[0][0]
    assert len(appended) == 5
    assert appended[0] == ["51", "dummy1", "FALSE"]
    assert appended[4] == ["55", "dummy5", "FALSE"]

    # Simulate sheet containing 55 rows now
    expanded_rows = list(initial_rows) + appended
    mock_worksheet.get_all_values.return_value = expanded_rows

    # Dynamic loop should scan all 55 rows and find dummy1 at index 52 (row 53)
    val_res = service.validate_via_service_account("dummy1", 77, "Team Rocket", zone="PAST")
    assert val_res["valid"] is True
    assert val_res["password"] == "dummy1"
    assert val_res["row_index"] == 53

    # Check that update_cell was called for row 53
    calls = mock_worksheet.update_cell.call_args_list
    updated_rows = [c.args[0] for c in calls]
    assert 53 in updated_rows


def test_api_add_passwords_and_verify_flow():
    """
    End-to-end API test:
    - POST /api/transition/add-passwords
    - Team starts stopwatch
    - POST /api/transition/verify with dummy1
    - Team unlocks Round 2
    """
    # 1. Add passwords via API
    add_resp = client.post("/api/transition/add-passwords", json={
        "passwords": ["dummy1", "dummy2", "dummy3", "dummy4", "dummy5"],
        "zone": "PAST"
    })
    assert add_resp.status_code == 200
    assert add_resp.json()["success"] is True

    # 2. Login team
    resp = client.post("/api/auth/login", json={
        "team_name": "TEST_SHEETS_DUMMY_TEAM",
        "member_1_name": "Alice",
        "member_2_name": "Bob",
        "member_1_prn": "24888888881",
        "member_2_prn": "25888888882",
    })
    assert resp.status_code == 200
    team_id = resp.json()["team_id"]

    # 3. Start stopwatch
    client.post("/api/transition/start", json={"team_id": team_id})

    # 4. Verify with dummy1
    v_resp = client.post("/api/transition/verify", json={
        "team_id": team_id,
        "password": "dummy1"
    })
    assert v_resp.status_code == 200
    assert v_resp.json()["success"] is True
    assert v_resp.json()["is_completed"] is True

    # 5. Check transition info
    info = client.get(f"/api/transition/info?team_id={team_id}").json()
    assert info["stopwatch_status"] == "COMPLETED"
    assert info["can_proceed"] is True
    assert "dummy1" in info["password_used"].lower()

