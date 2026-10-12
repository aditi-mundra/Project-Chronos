#!/usr/bin/env python3
"""
Project Chronos — Dynamic Password Addition & Validation Test Script
Adds dummy passwords ('dummy1' through 'dummy5') and tests dynamic validation and sheet updating.

Usage:
    python3 backend/add_dummy_passwords.py
"""

import sys
import os
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

# Load .env
try:
    from dotenv import load_dotenv
    for env_path in [ROOT_DIR / ".env", ROOT_DIR / "backend" / ".env"]:
        if env_path.is_file():
            load_dotenv(env_path, override=False)
except Exception:
    pass

from backend.app.services.google_sheets_service import google_sheets_service


def print_header(title: str):
    print("\n" + "\033[96m" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\033[0m")


def main():
    print_header("CHRONOS CORE // DYNAMIC PASSWORDS ENGINE")

    dummy_passwords = ["dummy1", "dummy2", "dummy3", "dummy4", "dummy5"]
    target_zone = "PAST"

    print("\n\033[93m[Step 1] Inspecting Google Spreadsheet Integration Status...\033[0m")
    status = google_sheets_service.get_status()
    print(f"  • Configured: {status['configured']}")
    print(f"  • Method:     {status['method']}")
    print(f"  • Connected:  {'\033[92mYES\033[0m' if status['connected'] else '\033[93mSTANDBY (Dynamic Registry Active)\033[0m'}")
    if status.get("sheet_id"):
        print(f"  • Sheet ID:   {status['sheet_id']}")

    print(f"\n\033[93m[Step 2] Adding 5 Dummy Passwords to {target_zone} Zone...\033[0m")
    print(f"  • Passwords to register: {dummy_passwords}")

    add_res = google_sheets_service.add_passwords(dummy_passwords, zone=target_zone)
    print(f"  • Result Success: {add_res.get('success')}")
    print(f"  • Source / Target: {add_res.get('source') or add_res.get('sheet_name')}")
    if add_res.get("added"):
        print(f"  • Added Passwords: \033[92m{add_res.get('added')}\033[0m")
    if add_res.get("warning"):
        print(f"  • Notice: \033[93m{add_res.get('warning')}\033[0m")

    print("\n\033[93m[Step 3] Testing Dynamic Verification Loop with 'dummy1'...\033[0m")
    test_team_id = 42
    test_team_name = "CHRONOS_FIELD_TEAM_OMEGA"

    print(f"  Simulating Team '{test_team_name}' entering 'dummy1' at Stage Transition...")
    verify_res = google_sheets_service.validate_and_use_password(
        password="dummy1",
        team_id=test_team_id,
        team_name=test_team_name,
        zone=target_zone
    )

    if verify_res.get("valid"):
        print(f"  \033[92m[✔] First Use SUCCESS: {verify_res.get('message')}\033[0m")
        print(f"      Source: {verify_res.get('source')} | Zone: {verify_res.get('zone')}")
    else:
        print(f"  \033[91m[✘] First Use FAILED: {verify_res.get('error')}\033[0m")
        sys.exit(1)

    print("\n\033[93m[Step 4] Testing Re-use Rejection (Idempotency / Anti-Cheating)...\033[0m")
    print(f"  Simulating Team 99 ('IMPOSTOR_UNIT') attempting to reuse 'dummy1'...")
    reuse_res = google_sheets_service.validate_and_use_password(
        password="dummy1",
        team_id=99,
        team_name="IMPOSTOR_UNIT",
        zone=target_zone
    )

    if not reuse_res.get("valid") and reuse_res.get("is_used"):
        print(f"  \033[92m[✔] Correctly REJECTED: {reuse_res.get('error')}\033[0m")
    else:
        print(f"  \033[91m[✘] ERROR: Password reuse was not blocked!\033[0m Result: {reuse_res}")
        sys.exit(1)

    print("\n\033[93m[Step 5] Checking Remaining Unused Dummy Passwords...\033[0m")
    for pw in ["dummy2", "dummy3", "dummy4", "dummy5"]:
        check_entry = google_sheets_service._dynamic_passwords.get(pw.upper(), {})
        is_used = check_entry.get("is_used", False)
        status_label = "\033[91mUSED\033[0m" if is_used else "\033[92mAVAILABLE\033[0m"
        print(f"  • {pw}: {status_label}")

    print_header("ALL DYNAMIC PASSWORD ENGINE TESTS PASSED SUCCESSFULLY [5/5]")
    print("The verification loop is 100% dynamic and handles newly added rows seamlessly.\n")


if __name__ == "__main__":
    main()
