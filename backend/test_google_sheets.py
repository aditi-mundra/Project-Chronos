#!/usr/bin/env python3
"""
Project Chronos — Google Spreadsheet Integration Diagnostic Tool
Run: python3 backend/test_google_sheets.py
"""

import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

try:
    from dotenv import load_dotenv
    for p in [ROOT_DIR / ".env", ROOT_DIR / "backend" / ".env"]:
        if p.is_file():
            load_dotenv(p, override=False)
except Exception:
    pass

from backend.app.services.google_sheets_service import google_sheets_service


def print_banner():
    print("\033[96m" + "=" * 65)
    print("  CHRONOS CORE // GOOGLE SPREADSHEET DIAGNOSTIC ENGINE")
    print("=" * 65 + "\033[0m")


def main():
    print_banner()
    cfg = google_sheets_service.get_config()

    print("\n\033[93m[1/3] Environment Configuration:\033[0m")
    print(f"  • GOOGLE_SHEET_ID:            {cfg['sheet_id'] or '\033[90m(not configured)\033[0m'}")
    print(f"  • GOOGLE_SERVICE_ACCOUNT_FILE: {cfg['sa_file'] or '\033[90m(not configured)\033[0m'}")
    print(f"  • GOOGLE_SHEET_TAB_NAME:       {cfg['tab_name'] or 'Sheet1 (default)'}")
    print(f"  • GOOGLE_SHEETS_WEBHOOK_URL:   {cfg['webhook_url'] or '\033[90m(not configured)\033[0m'}")

    print("\n\033[93m[2/3] Integration Status:\033[0m")
    status = google_sheets_service.get_status()
    print(f"  • Configured:                  {status['configured']}")
    print(f"  • Active Method:               {status['method']}")
    print(f"  • Connected:                   {'\033[92mYES\033[0m' if status['connected'] else '\033[91mNO\033[0m'}")

    if status.get("error"):
        print(f"  • Error Diagnostic:            \033[91m{status['error']}\033[0m")

    if status["connected"]:
        print(f"  • Total Passwords in Sheet:    {status['total_passwords']}")
        print(f"  • Available / Unused:          \033[92m{status['available_passwords']}\033[0m")
        print(f"  • Already Used:                \033[93m{status['used_passwords']}\033[0m")

    print("\n\033[93m[3/3] Validation Test:\033[0m")
    test_pw = sys.argv[1] if len(sys.argv) > 1 else "Chronos@123"
    print(f"  Testing validation with password: '{test_pw}'...")

    res = google_sheets_service.validate_and_use_password(
        password=test_pw,
        team_id=999,
        team_name="DIAGNOSTIC_TEST_TEAM"
    )

    if res.get("valid"):
        print(f"  \033[92m[✔] Success: {res.get('message')}\033[0m (Source: {res.get('source')})")
    else:
        print(f"  \033[91m[✘] Rejected: {res.get('error')}\033[0m")

    print("\n\033[96m" + "=" * 65 + "\033[0m\n")


if __name__ == "__main__":
    main()
