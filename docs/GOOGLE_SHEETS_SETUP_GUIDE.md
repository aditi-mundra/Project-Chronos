# Project Chronos — Google Spreadsheet API Integration Guide

## Overview
During the **Stage Transition** between **Round 1** and **Round 2** (the *"Waiting for Authentication Screen"*), teams perform physical reconnaissance to recover sector security passwords/tokens (e.g., `ALPHA-7`, `OMEGA-3`, `CHRONOS-83`).

When a team submits their password on the **"Waiting for Authentication Screen"**:
1. The backend validates the password live against your **Google Spreadsheet**.
2. If valid and unused:
   - It **marks the password as `USED`** directly on the spreadsheet.
   - It records the team name and timestamp in the spreadsheet (`Used By` and `Used At`).
   - It stops the team's reconnaissance stopwatch and **unlocks Round 2 (Chronos Terminal)**.
3. If already claimed by another team:
   - It rejects the submission and notifies the team who already redeemed it.
4. If invalid:
   - It rejects the code with an access denied warning.

---

## Spreadsheet Structure

Create a Google Sheet with the following columns in **Sheet1**:

| Password | Status | Used By | Used At | Zone (Optional) |
| :--- | :--- | :--- | :--- | :--- |
| `ALPHA-7` | `AVAILABLE` | | | `PAST` |
| `BETA-9` | `AVAILABLE` | | | `PRESENT` |
| `OMEGA-3` | `AVAILABLE` | | | `FUTURE` |
| `CHRONOS-83`| `AVAILABLE` | | | `FUTURE` |

> [!NOTE]
> Column names are auto-detected dynamically:
> - **Password column**: detects headers containing `Password`, `Token`, `Key`, `Code` (default: Column A)
> - **Status column**: detects `Status` or `State` (default: Column B)
> - **Used By column**: detects `Used By`, `Team`, `Claimed By` (default: Column C)
> - **Used At column**: detects `Used At`, `Time`, `Date`, `Timestamp` (default: Column D)
> - **Zone column**: detects `Zone`, `Sector`, `Timeline` (optional: Column E)

---

## Integration Setup (Choose Method 1 or Method 2)

### Method 1: Google Cloud Service Account (Official `gspread` API)
*Recommended for full automated backend control.*

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Enable the **Google Sheets API** and **Google Drive API**.
3. Go to **IAM & Admin > Service Accounts** and click **Create Service Account**.
4. Click on the created service account, go to the **Keys** tab, click **Add Key > Create new key**, and select **JSON**.
5. Save the downloaded file as `credentials.json` in your project root:
   ```
   /Users/samarth/Documents/Project-Chronos/credentials.json
   ```
6. Copy the service account email (e.g. `chronos-bot@project-chronos.iam.gserviceaccount.com`).
7. Open your Google Spreadsheet, click **Share**, and grant **Editor** access to that service account email.
8. Add the following to your `.env` file:
   ```env
   GOOGLE_SHEET_ID=your_google_sheet_id_or_url
   GOOGLE_SERVICE_ACCOUNT_FILE=credentials.json
   GOOGLE_SHEET_TAB_NAME=Sheet1
   ```

---

### Method 2: Google Apps Script Web App (Zero-GCP, 1-Click Setup)
*Fastest setup with no Google Cloud Console project or IAM permissions required.*

1. Open your Google Spreadsheet.
2. In the menu, go to **Extensions > Apps Script**.
3. Open [`docs/google_apps_script_template.js`](file:///Users/samarth/Documents/Project-Chronos/docs/google_apps_script_template.js), copy the entire code, and paste it into the Apps Script editor.
4. Click **Deploy > New deployment**.
5. Select **Web app**:
   - **Execute as**: `Me`
   - **Who has access**: `Anyone`
6. Click **Deploy** and authorize permissions.
7. Copy the generated Web App URL (`https://script.google.com/macros/s/.../exec`).
8. Add to your `.env` file:
   ```env
   GOOGLE_SHEETS_WEBHOOK_URL=https://script.google.com/macros/s/.../exec
   ```

---

## Verifying the Integration

Run the built-in diagnostic CLI tool:
```bash
./.venv/bin/python3 backend/test_google_sheets.py
```

Or test with a specific password:
```bash
./.venv/bin/python3 backend/test_google_sheets.py ALPHA-7
```

You can also check the live API health endpoint in your browser:
```
http://localhost:8000/api/transition/sheets-status
```

---

## Emergency Host Fallback
If internet access is lost in the lab or the Google Spreadsheet is temporarily unreachable, the master emergency password set in `.env` (`CHRONOS_ADMIN_PASSWORD=Chronos@123` or default `Chronos@123`) is always accepted as a host override, ensuring no team is ever stranded during a live event.
