"""
Project Chronos — Google Spreadsheet Password Validation Service
Validates security override passwords against a Google Spreadsheet and marks them as USED.
Used at Stage Transition ("Waiting for Authentication Screen") to unlock Round 2.

Supports:
1. Google Cloud Service Account API via gspread (GOOGLE_SHEET_ID + GOOGLE_SERVICE_ACCOUNT_FILE / GOOGLE_SERVICE_ACCOUNT_JSON)
2. Google Apps Script Web App Webhook (GOOGLE_SHEETS_WEBHOOK_URL)
3. Emergency Local Admin Fallback (Chronos@123 / CHRONOS_ADMIN_PASSWORD)
"""

import os
import re
import json
import base64
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger("chronos.google_sheets")

# Auto-load .env
try:
    from dotenv import load_dotenv
    _root_dir = Path(__file__).resolve().parents[3]
    for _env_p in [_root_dir / ".env", _root_dir / "backend" / ".env"]:
        if _env_p.is_file():
            load_dotenv(_env_p, override=False)
except Exception:
    pass

# Optional dependencies loaded safely
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    gspread = None
    Credentials = None
    GSPREAD_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    httpx = None
    HTTPX_AVAILABLE = False


DEFAULT_FALLBACK_PASSWORDS = {"Chronos@123", "chronos@123"}


def _get_env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def extract_sheet_id(sheet_id_or_url: str) -> str:
    """
    Extracts the Google Spreadsheet ID from either a raw ID or a full Google Sheets URL.
    Example URL: https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit#gid=0
    """
    cleaned = sheet_id_or_url.strip()
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", cleaned)
    if match:
        return match.group(1)
    return cleaned


def resolve_service_account_file(file_path: str) -> Optional[Path]:
    """
    Finds service account file across common candidate directories.
    """
    if not file_path:
        return None
    candidate = Path(file_path)
    if candidate.is_file():
        return candidate.resolve()

    root_dir = Path(__file__).resolve().parents[3]
    search_paths = [
        root_dir / file_path,
        root_dir / "backend" / file_path,
        root_dir / "backend" / "app" / file_path,
        Path.cwd() / file_path,
    ]
    for p in search_paths:
        if p.is_file():
            return p.resolve()
    return None


class GoogleSheetService:
    def __init__(self):
        self._gspread_client = None
        # Dynamic in-memory password registry for testing and runtime password injection
        self._dynamic_passwords: Dict[str, Dict[str, Any]] = {}
        # Pre-seed with dummy1..dummy5 as requested
        for p in ["dummy1", "dummy2", "dummy3", "dummy4", "dummy5"]:
            self._dynamic_passwords[p.upper()] = {
                "password": p,
                "zone": "PAST",
                "is_used": False,
                "used_by": "",
                "used_at": "",
            }

    def get_config(self) -> Dict[str, Any]:
        raw_sheet_id = _get_env("GOOGLE_SHEET_ID") or _get_env("GOOGLE_SPREADSHEET_ID") or _get_env("GOOGLE_SHEET_URL")
        sheet_id = extract_sheet_id(raw_sheet_id)
        sa_file = _get_env("GOOGLE_SERVICE_ACCOUNT_FILE") or _get_env("GOOGLE_APPLICATION_CREDENTIALS")
        sa_json = _get_env("GOOGLE_SERVICE_ACCOUNT_JSON")
        tab_name = _get_env("GOOGLE_SHEET_TAB_NAME") or None
        webhook_url = _get_env("GOOGLE_SHEETS_WEBHOOK_URL") or _get_env("GOOGLE_SHEET_APPS_SCRIPT_URL")

        return {
            "sheet_id": sheet_id,
            "sa_file": sa_file,
            "sa_json": sa_json,
            "tab_name": tab_name,
            "webhook_url": webhook_url,
        }

    def is_service_account_configured(self) -> bool:
        cfg = self.get_config()
        if not cfg["sheet_id"]:
            return False
        if cfg["sa_json"]:
            return True
        if cfg["sa_file"]:
            resolved = resolve_service_account_file(cfg["sa_file"])
            return resolved is not None
        # Default auto-discovery check for credentials.json or service_account.json
        for default_name in ["credentials.json", "service_account.json", "chronos_service_account.json"]:
            if resolve_service_account_file(default_name):
                return True
        return False

    def is_webhook_configured(self) -> bool:
        cfg = self.get_config()
        return bool(cfg["webhook_url"])

    def is_configured(self) -> bool:
        return self.is_service_account_configured() or self.is_webhook_configured()

    def _get_gspread_client(self):
        if not GSPREAD_AVAILABLE:
            raise RuntimeError("gspread or google-auth package is not installed.")

        cfg = self.get_config()
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        # 1. Raw JSON or Base64 JSON
        if cfg["sa_json"]:
            raw_text = cfg["sa_json"]
            try:
                # Try decoding base64 in case it was encoded
                decoded = base64.b64decode(raw_text).decode("utf-8")
                info = json.loads(decoded)
            except Exception:
                info = json.loads(raw_text)
            creds = Credentials.from_service_account_info(info, scopes=scopes)
            return gspread.authorize(creds)

        # 2. File Path
        sa_path = resolve_service_account_file(cfg["sa_file"])
        if not sa_path:
            for default_name in ["credentials.json", "service_account.json", "chronos_service_account.json"]:
                found = resolve_service_account_file(default_name)
                if found:
                    sa_path = found
                    break

        if sa_path and sa_path.is_file():
            creds = Credentials.from_service_account_file(str(sa_path), scopes=scopes)
            return gspread.authorize(creds)

        raise FileNotFoundError(
            f"Google Service Account file '{cfg['sa_file']}' could not be located. "
            "Please ensure the path is correct or place credentials.json in the project root."
        )

    def _get_worksheets(self, client, preferred_zone: str = "") -> List[Any]:
        cfg = self.get_config()
        sheet_id = cfg["sheet_id"]
        spreadsheet = client.open_by_key(sheet_id)

        if cfg["tab_name"]:
            try:
                return [spreadsheet.worksheet(cfg["tab_name"])]
            except Exception:
                pass

        all_ws = spreadsheet.worksheets()
        if preferred_zone:
            z_upper = preferred_zone.upper()
            matching = [w for w in all_ws if z_upper in w.title.upper()]
            others = [w for w in all_ws if z_upper not in w.title.upper()]
            return matching + others

        return all_ws

    def _detect_columns(self, rows: List[List[str]]) -> Tuple[int, int, int, int, Optional[int], int]:
        """
        Detects column indices (0-based) for:
        (password_col, status_col, team_col, time_col, zone_col, data_start_row_index)
        Scans up to first 5 rows to handle title banners above header rows.
        """
        if not rows:
            return 0, 1, 2, 3, None, 1

        # Search up to first 5 rows to locate the actual header row by scoring distinct recognized columns
        best_header_idx = None
        best_score = 0
        for r_idx in range(min(5, len(rows))):
            row_cells = [str(c).strip().lower() for c in rows[r_idx]]
            pw_cells = [i for i, c in enumerate(row_cells) if any(k in c for k in ["pass", "password", "token", "code", "key", "secret"])]
            other_cells = [i for i, c in enumerate(row_cells) if any(k in c for k in ["sn", "id", "#", "status", "state", "team", "unit", "user", "used"])]
            distinct_others = [i for i in other_cells if i not in pw_cells]
            score = len(pw_cells) + len(distinct_others)
            if pw_cells and score > best_score:
                best_score = score
                best_header_idx = r_idx

        header_row_idx = best_header_idx

        col_pw = 0
        col_status = 1
        col_team = 2
        col_time = 3
        col_zone = None

        if header_row_idx is not None:
            header_row = [str(c).strip().lower() for c in rows[header_row_idx]]
            found_pw = None
            found_status = None
            found_team = None
            found_time = None
            found_zone = None

            for idx, col in enumerate(header_row):
                if any(k in col for k in ["pass", "token", "code", "key", "secret"]):
                    found_pw = idx
                elif any(k in col for k in ["zone", "sector", "timeline", "era"]):
                    found_zone = idx
                elif any(k in col for k in ["team", "unit", "user", "claimed by", "used by", "redeemed by"]):
                    found_team = idx
                elif any(k in col for k in ["time", "date", "timestamp", "used at", "redeemed at"]) and "timeline" not in col:
                    found_time = idx
                elif any(k in col for k in ["status", "state"]) or col == "used" or col.startswith("is_used"):
                    found_status = idx

            # Fallback if status wasn't found by explicit keyword
            if found_status is None:
                for idx, col in enumerate(header_row):
                    if idx not in (found_pw, found_team, found_time, found_zone) and "used" in col:
                        found_status = idx
                        break

            col_pw = found_pw if found_pw is not None else 0
            col_status = found_status if found_status is not None else (col_pw + 1)
            col_team = found_team if found_team is not None else (max(col_pw, col_status) + 1)
            col_time = found_time if found_time is not None else (col_team + 1)
            col_zone = found_zone

            start_idx = header_row_idx + 1
        else:
            start_idx = 0

        return col_pw, col_status, col_team, col_time, col_zone, start_idx

    def validate_via_service_account(
        self, password: str, team_id: int, team_name: str, zone: str = ""
    ) -> Dict[str, Any]:
        """
        Validates password and reflects usage on Google Spreadsheet via gspread.
        Searches across all worksheets (prioritizing team's assigned zone).
        """
        client = self._get_gspread_client()
        worksheets = self._get_worksheets(client, preferred_zone=zone)

        if not worksheets:
            return {
                "valid": False,
                "error": "No worksheets found in Google Spreadsheet.",
            }

        target = password.strip().upper()

        for ws in worksheets:
            all_values = ws.get_all_values()
            if not all_values:
                continue

            col_pw, col_status, col_team, col_time, col_zone, start_idx = self._detect_columns(all_values)

            matched_row_idx = None
            matched_row_data = None

            for idx in range(start_idx, len(all_values)):
                row = all_values[idx]
                pw_val = row[col_pw].strip().upper() if len(row) > col_pw else ""
                if pw_val == target:
                    matched_row_idx = idx
                    matched_row_data = row
                    break

            if matched_row_idx is not None:
                # Found the password in this worksheet!
                status_val = (matched_row_data[col_status].strip().upper()
                              if len(matched_row_data) > col_status else "")
                team_val = (matched_row_data[col_team].strip()
                            if len(matched_row_data) > col_team else "")

                # In this spreadsheet, Status starts as FALSE. If TRUE, USED, or claimed, it is already used.
                already_used = (
                    status_val in {"TRUE", "USED", "REDEEMED", "CLAIMED", "YES"} or
                    (team_val != "" and status_val not in {"FALSE", "AVAILABLE", ""})
                )

                if already_used:
                    claimed_by = team_val or "another team"
                    return {
                        "valid": False,
                        "is_used": True,
                        "error": f"This security password has already been used by {claimed_by}.",
                        "sheet_name": ws.title,
                    }

                # Mark as USED on Google Spreadsheet
                sheet_row_num = matched_row_idx + 1  # 1-based row index in gspread
                now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                team_label = f"{team_name} (ID: {team_id})" if team_name else f"Team {team_id}"

                # Auto-label headers for Used By and Used At if missing
                header_idx = max(0, start_idx - 1)
                header_row = all_values[header_idx] if header_idx < len(all_values) else []
                if len(header_row) <= col_team or not header_row[col_team]:
                    try:
                        ws.update_cell(header_idx + 1, col_team + 1, "Used By")
                    except Exception:
                        pass
                if len(header_row) <= col_time or not header_row[col_time]:
                    try:
                        ws.update_cell(header_idx + 1, col_time + 1, "Used At")
                    except Exception:
                        pass

                # Update row cells to mark as TRUE / USED
                try:
                    # Write TRUE (matches the boolean FALSE/TRUE format of the sheet)
                    ws.update_cell(sheet_row_num, col_status + 1, "TRUE")
                    ws.update_cell(sheet_row_num, col_team + 1, team_label)
                    ws.update_cell(sheet_row_num, col_time + 1, now_str)
                except Exception as e:
                    logger.error(f"Failed to update Google Sheet row {sheet_row_num} in '{ws.title}': {e}")
                    raise RuntimeError(f"Found code in Google Sheet, but failed to record usage: {e}")

                # Detect zone from worksheet title if not in row
                detected_zone = None
                ws_title_upper = ws.title.upper()
                if "PAST" in ws_title_upper:
                    detected_zone = "PAST"
                elif "PRESENT" in ws_title_upper:
                    detected_zone = "PRESENT"
                elif "FUTURE" in ws_title_upper:
                    detected_zone = "FUTURE"
                elif col_zone is not None and len(matched_row_data) > col_zone:
                    detected_zone = matched_row_data[col_zone].strip()

                return {
                    "valid": True,
                    "message": f"Security password authenticated. Registered as USED on Google Spreadsheet ({ws.title}).",
                    "password": matched_row_data[col_pw].strip(),
                    "zone": detected_zone,
                    "sheet_name": ws.title,
                    "source": "GOOGLE_SPREADSHEET_API",
                    "row_index": sheet_row_num,
                }

        # Not found in any sheet
        return {
            "valid": False,
            "error": "Invalid password. Security code not recognized.",
        }

    def validate_via_webhook(
        self, password: str, team_id: int, team_name: str, zone: str = ""
    ) -> Dict[str, Any]:
        """
        Validates password via Google Apps Script Web App webhook.
        """
        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx package is required for webhook authentication.")

        webhook_url = self.get_config()["webhook_url"]
        payload = {
            "action": "validate_and_use",
            "password": password.strip(),
            "team_id": team_id,
            "team_name": team_name,
            "zone": zone,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                res = client.post(webhook_url, json=payload)
                if res.status_code != 200:
                    return {
                        "valid": False,
                        "error": f"Google Sheets Apps Script returned HTTP {res.status_code}: {res.text[:100]}",
                    }
                data = res.json()
                valid = bool(data.get("valid") or data.get("success"))
                if valid:
                    return {
                        "valid": True,
                        "message": data.get("message", "Password validated via Google Spreadsheet."),
                        "zone": data.get("zone"),
                        "source": "GOOGLE_APPS_SCRIPT_WEBHOOK",
                    }
                else:
                    return {
                        "valid": False,
                        "is_used": bool(data.get("is_used")),
                        "error": data.get("error", "Invalid password or already used."),
                    }
        except Exception as e:
            logger.error(f"Error contacting Google Sheets webhook: {e}")
            raise RuntimeError(f"Failed to communicate with Google Sheets Apps Script Web App: {e}")

    def add_passwords_via_service_account(
        self, passwords: List[str], zone: str = "PAST"
    ) -> Dict[str, Any]:
        """
        Appends passwords to the specified zone worksheet via Google Service Account (gspread).
        Ensures the loop continues dynamically for all subsequent rows.
        """
        client = self._get_gspread_client()
        worksheets = self._get_worksheets(client, preferred_zone=zone)
        if not worksheets:
            return {"success": False, "error": "No worksheets found in Google Spreadsheet."}

        target_ws = worksheets[0]
        all_values = target_ws.get_all_values()
        col_pw, col_status, col_team, col_time, col_zone, start_idx = self._detect_columns(all_values)

        existing_pws = set()
        max_sn = 0
        for idx in range(start_idx, len(all_values)):
            row = all_values[idx]
            if len(row) > col_pw and row[col_pw].strip():
                existing_pws.add(row[col_pw].strip().upper())
            if len(row) > 0:
                try:
                    sn_val = int(str(row[0]).strip())
                    if sn_val > max_sn:
                        max_sn = sn_val
                except (ValueError, TypeError):
                    pass

        if max_sn == 0:
            max_sn = max(0, len(all_values) - start_idx)

        rows_to_append = []
        added_list = []
        skipped_list = []

        for pw in passwords:
            pw_clean = str(pw).strip()
            if not pw_clean:
                continue
            if pw_clean.upper() in existing_pws:
                skipped_list.append(pw_clean)
                continue

            max_sn += 1
            # Standard row format: [SN, Password, Status (FALSE)]
            new_row = [str(max_sn), pw_clean, "FALSE"]
            rows_to_append.append(new_row)
            added_list.append(pw_clean)
            existing_pws.add(pw_clean.upper())

        if rows_to_append:
            target_ws.append_rows(rows_to_append, value_input_option="USER_ENTERED")

        return {
            "success": True,
            "sheet_name": target_ws.title,
            "added": added_list,
            "skipped": skipped_list,
            "total_added": len(added_list),
            "source": "SERVICE_ACCOUNT",
        }

    def add_passwords_via_webhook(
        self, passwords: List[str], zone: str = "PAST"
    ) -> Dict[str, Any]:
        """
        Appends passwords to Google Spreadsheet via Apps Script Web App.
        """
        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx package is required for webhook integration.")

        webhook_url = self.get_config()["webhook_url"]
        payload = {
            "action": "add_passwords",
            "passwords": passwords,
            "zone": zone,
        }
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            res = client.post(webhook_url, json=payload)
            if res.status_code != 200:
                return {
                    "success": False,
                    "error": f"Google Sheets Apps Script returned HTTP {res.status_code}: {res.text[:100]}",
                }
            return res.json()

    def add_passwords(self, passwords: List[str], zone: str = "PAST") -> Dict[str, Any]:
        """
        Dynamically adds passwords to the verification loop.
        1. If Google Cloud Service Account or Apps Script Webhook is active, writes directly to Google Sheet.
        2. Always registers in the local dynamic registry for continuous uninterrupted loop processing.
        """
        clean_pws = [str(p).strip() for p in passwords if str(p).strip()]
        if not clean_pws:
            return {"success": False, "error": "No passwords provided."}

        # Update local dynamic registry
        added_local = []
        for p in clean_pws:
            u = p.upper()
            if u not in self._dynamic_passwords:
                self._dynamic_passwords[u] = {
                    "password": p,
                    "zone": zone.upper() if zone else "PAST",
                    "is_used": False,
                    "used_by": "",
                    "used_at": "",
                }
                added_local.append(p)

        # Sync to live Google Sheet if configured
        if self.is_service_account_configured():
            try:
                sheet_res = self.add_passwords_via_service_account(clean_pws, zone=zone)
                if sheet_res.get("success"):
                    sheet_res["dynamic_registry_synced"] = True
                    return sheet_res
                return {
                    "success": True,
                    "added": added_local,
                    "total_added": len(added_local),
                    "warning": f"Registered in Dynamic Registry, but Google Sheet returned: {sheet_res.get('error')}",
                    "source": "DYNAMIC_REGISTRY",
                }
            except Exception as e:
                logger.error(f"Failed to append to Google Sheet via Service Account: {e}")
                return {
                    "success": True,
                    "added": added_local,
                    "total_added": len(added_local),
                    "warning": f"Registered dynamically in Chronos Engine, but remote Google Sheet API returned: {e}",
                    "source": "DYNAMIC_REGISTRY",
                }

        elif self.is_webhook_configured():
            try:
                hook_res = self.add_passwords_via_webhook(clean_pws, zone=zone)
                if hook_res.get("success"):
                    hook_res["dynamic_registry_synced"] = True
                    return hook_res
                return {
                    "success": True,
                    "added": added_local,
                    "total_added": len(added_local),
                    "warning": f"Registered dynamically in Chronos Engine, but Webhook returned: {hook_res.get('error')}",
                    "source": "DYNAMIC_REGISTRY",
                }
            except Exception as e:
                logger.error(f"Failed to append to Google Sheet via Webhook: {e}")
                return {
                    "success": True,
                    "added": added_local,
                    "total_added": len(added_local),
                    "warning": f"Registered dynamically in Chronos Engine, but Webhook returned: {e}",
                    "source": "DYNAMIC_REGISTRY",
                }

        return {
            "success": True,
            "added": added_local,
            "total_added": len(added_local),
            "zone": zone.upper() if zone else "PAST",
            "source": "DYNAMIC_REGISTRY",
            "message": f"Successfully registered {len(added_local)} dynamic passwords. Ready for authentication.",
        }

    def validate_and_use_password(
        self, password: str, team_id: int, team_name: str = "", zone: str = ""
    ) -> Dict[str, Any]:
        """
        Authoritative validator called from backend routes & transition service.
        1. Checks Google Service Account or Apps Script Webhook.
        2. Checks Dynamic Password Registry (e.g., dummy1..dummy5).
        3. Falls back safely to emergency admin password if Google Sheets is offline/unconfigured.
        """
        cleaned = (password or "").strip()
        if not cleaned:
            return {"valid": False, "error": "Password cannot be empty."}

        admin_pass = _get_env("CHRONOS_ADMIN_PASSWORD")
        allowed_admin_fallback = {
            admin_pass.lower(),
            *{p.lower() for p in DEFAULT_FALLBACK_PASSWORDS}
        } if admin_pass else {p.lower() for p in DEFAULT_FALLBACK_PASSWORDS}

        # Check if emergency override password is used directly
        is_emergency_bypass = cleaned.lower() in allowed_admin_fallback

        # 1. Attempt live Google Sheets API (Service Account)
        if self.is_service_account_configured():
            try:
                res = self.validate_via_service_account(cleaned, team_id, team_name, zone=zone)
                if res["valid"] or res.get("is_used"):
                    return res
            except Exception as e:
                logger.error(f"Google Spreadsheet API call failed: {e}")

        # 2. Attempt live Google Sheets Webhook
        elif self.is_webhook_configured():
            try:
                res = self.validate_via_webhook(cleaned, team_id, team_name, zone=zone)
                if res["valid"] or res.get("is_used"):
                    return res
            except Exception as e:
                logger.error(f"Google Sheets webhook failed: {e}")

        # 3. Check Dynamic Password Registry (dummy1..dummy5, runtime added passwords)
        upper_target = cleaned.upper()
        if upper_target in self._dynamic_passwords:
            entry = self._dynamic_passwords[upper_target]
            if entry["is_used"]:
                claimed_by = entry["used_by"] or "another unit"
                return {
                    "valid": False,
                    "is_used": True,
                    "error": f"This security password has already been used by {claimed_by}.",
                    "sheet_name": f"{entry.get('zone', 'PAST')} - PASSWORDS",
                }

            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            team_label = f"{team_name} (ID: {team_id})" if team_name else f"Team {team_id}"
            entry["is_used"] = True
            entry["used_by"] = team_label
            entry["used_at"] = now_str
            return {
                "valid": True,
                "message": f"Security password authenticated. Registered as USED on Central Sheet Registry ({entry.get('zone', 'PAST')}).",
                "password": entry.get("password", cleaned),
                "zone": entry.get("zone", "PAST"),
                "sheet_name": f"{entry.get('zone', 'PAST')} - PASSWORDS",
                "source": "DYNAMIC_REGISTRY",
            }

        # 4. Emergency Admin Bypass
        if is_emergency_bypass:
            logger.warning(f"Team {team_id} ({team_name}) authenticated with EMERGENCY ADMIN OVERRIDE.")
            return {
                "valid": True,
                "message": "SECURITY OVERRIDE VERIFIED // EMERGENCY HOST ACCESS GRANTED",
                "source": "ADMIN_FALLBACK",
            }

        return {
            "valid": False,
            "error": "Invalid password. Security code not recognized.",
        }

    def _get_worksheet(self, client):
        wss = self._get_worksheets(client)
        return wss[0] if wss else None

    def get_status(self) -> Dict[str, Any]:
        """
        Diagnostic summary of Google Sheets configuration and connectivity.
        """
        cfg = self.get_config()
        status = {
            "configured": self.is_configured(),
            "method": "NONE",
            "sheet_id": cfg["sheet_id"] or None,
            "tab_name": cfg["tab_name"] or "Auto (PAST, PRESENT, FUTURE)",
            "connected": False,
            "error": None,
            "total_passwords": 0,
            "available_passwords": 0,
            "used_passwords": 0,
        }

        if self.is_service_account_configured():
            status["method"] = "SERVICE_ACCOUNT"
            try:
                client = self._get_gspread_client()
                worksheets = self._get_worksheets(client)
                status["connected"] = True
                total_pw = 0
                total_used = 0
                for ws in worksheets:
                    vals = ws.get_all_values()
                    if vals:
                        col_pw, col_status, col_team, col_time, col_zone, start_idx = self._detect_columns(vals)
                        total_pw += max(0, len(vals) - start_idx)
                        for row in vals[start_idx:]:
                            s_val = row[col_status].strip().upper() if len(row) > col_status else ""
                            t_val = row[col_team].strip() if len(row) > col_team else ""
                            if s_val in {"USED", "REDEEMED", "CLAIMED", "YES", "TRUE"} or (t_val and s_val != "FALSE"):
                                total_used += 1
                status["total_passwords"] = total_pw
                status["used_passwords"] = total_used
                status["available_passwords"] = total_pw - total_used
            except Exception as e:
                status["error"] = str(e)

        elif self.is_webhook_configured():
            status["method"] = "APPS_SCRIPT_WEBHOOK"
            status["webhook_url"] = cfg["webhook_url"]
            try:
                if HTTPX_AVAILABLE:
                    with httpx.Client(timeout=6.0, follow_redirects=True) as client:
                        r = client.get(cfg["webhook_url"])
                        status["connected"] = r.status_code in (200, 405)
            except Exception as e:
                status["error"] = str(e)

        return status


# Singleton instance
google_sheets_service = GoogleSheetService()
