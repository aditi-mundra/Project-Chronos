"""
Transition Round passwords live in a Google Sheet ("Project Chronos - Password List"), one tab
per zone (PAST / PRESENT / FUTURE - PASSWORDS) with a Status checkbox per password.

The sheet is reached through a small Google Apps Script web app bound to the sheet
(backend/tools/google_sheet_password_service.gs). The backend never holds Google credentials:
it POSTs {secret, action, zone, password} and the script, under a lock, finds the password in
that zone's tab, ticks its Status checkbox and answers {ok: true}. A password whose Status is
already ticked, or that is not in the zone's tab, answers {ok: false}. So a password works
exactly once, and ticking Status is what "used" means.

Settings (environment or .env, see config.py):
  TRANSITION_SHEET_URL     the web app's /exec URL
  TRANSITION_SHEET_SECRET  shared secret, also stored in the script's Script Properties
"""

import json
import urllib.error
import urllib.request

from ..config import setting

REQUEST_TIMEOUT_SECONDS = 15


class PasswordServiceError(Exception):
    """The password sheet could not be reached or answered with an error."""


def consume_password(zone: str, password: str) -> bool:
    """
    True when `password` is a valid, unused password of `zone`; it is marked used in the
    sheet as part of the same call. False when it is wrong or already used.
    Raises PasswordServiceError when the sheet cannot give a definite answer (so the caller
    must not count the attempt).
    """
    url = setting("TRANSITION_SHEET_URL")
    secret = setting("TRANSITION_SHEET_SECRET")
    if not url or not secret:
        raise PasswordServiceError(
            "Password sheet is not configured (TRANSITION_SHEET_URL / TRANSITION_SHEET_SECRET)."
        )

    body = json.dumps(
        {"secret": secret, "action": "consume", "zone": zone, "password": password}
    ).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        # Apps Script answers a POST with a redirect to the result; urllib follows it.
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as err:
        raise PasswordServiceError(f"Password sheet unreachable: {err}") from err

    if not isinstance(data, dict) or data.get("error"):
        raise PasswordServiceError(
            f"Password sheet error: {data.get('error') if isinstance(data, dict) else 'bad response'}"
        )
    return bool(data.get("ok"))
