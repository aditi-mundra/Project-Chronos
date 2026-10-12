/**
 * PROJECT CHRONOS — GOOGLE APPS SCRIPT WEB APP
 * Tailored for Project Chronos Password List (PAST, PRESENT, FUTURE tabs)
 * Spreadsheet: https://docs.google.com/spreadsheets/d/1-CWLrzetSq3HJaMCThkFeomxdU2DUUFau6GWrfmzzdY/
 *
 * Setup Instructions (Takes 60 seconds):
 * 1. Open your spreadsheet: https://docs.google.com/spreadsheets/d/1-CWLrzetSq3HJaMCThkFeomxdU2DUUFau6GWrfmzzdY/
 * 2. In the top menu, click Extensions > Apps Script.
 * 3. Delete any default code in Code.gs and paste this entire file.
 * 4. Click the blue "Deploy" button (top right) > "New deployment".
 * 5. Click the gear icon next to "Select type" and choose "Web app".
 * 6. Set:
 *    - Description: Project Chronos Password Validator
 *    - Execute as: Me
 *    - Who has access: Anyone
 * 7. Click "Deploy" -> "Authorize access" (choose your Google account, click Advanced > Go to Untitled project).
 * 8. Copy the Web App URL (starts with https://script.google.com/macros/s/...).
 * 9. In your Project-Chronos .env file, add:
 *    GOOGLE_SHEETS_WEBHOOK_URL=https://script.google.com/macros/s/.../exec
 */

function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({
    status: "online",
    service: "Project Chronos Google Sheets Authenticator",
    spreadsheet: "Project Chronos - Password List",
    sheets: ["PAST - PASSWORDS", "PRESENT - PASSWORDS", "FUTURE - PASSWORDS"]
  })).setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  var lock = LockService.getScriptLock();
  // Wait up to 10 seconds to handle concurrent team submissions safely
  lock.tryLock(10000);

  try {
    if (!e || !e.postData || !e.postData.contents) {
      return jsonResponse({ success: false, valid: false, error: "Empty request payload." });
    }

    var body = JSON.parse(e.postData.contents);
    var action = body.action || "validate_and_use";

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var allSheets = ss.getSheets();

    // -------------------------------------------------------------
    // ACTION: Dynamically append passwords to a sheet
    // -------------------------------------------------------------
    if (action === "add_passwords") {
      var pwList = body.passwords || [];
      var targetZone = (body.zone || "PAST").trim().toUpperCase();
      var targetSheet = null;

      for (var s = 0; s < allSheets.length; s++) {
        if (allSheets[s].getName().toUpperCase().indexOf(targetZone) !== -1) {
          targetSheet = allSheets[s];
          break;
        }
      }
      if (!targetSheet) targetSheet = allSheets[0];

      var dataRange = targetSheet.getDataRange().getValues();
      var existing = {};
      var maxSN = 0;

      for (var r = 1; r < dataRange.length; r++) {
        var rData = dataRange[r];
        if (rData[1]) existing[String(rData[1]).trim().toUpperCase()] = true;
        var snVal = parseInt(rData[0], 10);
        if (!isNaN(snVal) && snVal > maxSN) maxSN = snVal;
      }
      if (maxSN === 0) maxSN = Math.max(0, dataRange.length - 2);

      var added = [];
      var skipped = [];

      for (var p = 0; p < pwList.length; p++) {
        var pwStr = String(pwList[p] || "").trim();
        if (!pwStr) continue;
        if (existing[pwStr.toUpperCase()]) {
          skipped.push(pwStr);
        } else {
          maxSN++;
          // Standard row format: [SN, Password, Status (false)]
          targetSheet.appendRow([maxSN, pwStr, false]);
          added.push(pwStr);
          existing[pwStr.toUpperCase()] = true;
        }
      }

      return jsonResponse({
        success: true,
        sheet_name: targetSheet.getName(),
        added: added,
        skipped: skipped,
        total_added: added.length
      });
    }

    // -------------------------------------------------------------
    // ACTION: Validate password and mark as USED
    // -------------------------------------------------------------
    var inputPw = (body.password || "").trim().toUpperCase();
    var teamId = body.team_id || "UNKNOWN";
    var teamName = body.team_name || ("Team " + teamId);
    var preferredZone = (body.zone || "").trim().toUpperCase();

    if (!inputPw) {
      return jsonResponse({ success: false, valid: false, error: "Password cannot be empty." });
    }

    // Order sheets: search preferred zone first if given
    var sheetsToSearch = [];
    if (preferredZone) {
      for (var i = 0; i < allSheets.length; i++) {
        if (allSheets[i].getName().toUpperCase().indexOf(preferredZone) !== -1) {
          sheetsToSearch.push(allSheets[i]);
        }
      }
      for (var j = 0; j < allSheets.length; j++) {
        if (allSheets[j].getName().toUpperCase().indexOf(preferredZone) === -1) {
          sheetsToSearch.push(allSheets[j]);
        }
      }
    } else {
      sheetsToSearch = allSheets;
    }

    var matchedSheet = null;
    var matchedRowIdx = -1;
    var colPw = 1;      // Default Column B (0-indexed: 1)
    var colStatus = 2;  // Default Column C (0-indexed: 2)
    var colTeam = 3;    // Column D (0-indexed: 3)
    var colTime = 4;    // Column E (0-indexed: 4)
    var headerRowIdx = 1; // Default row index 1 (Row 2 in sheet)
    var matchedRowData = null;

    // Search across sheets
    for (var s = 0; s < sheetsToSearch.length; s++) {
      var sheet = sheetsToSearch[s];
      var data = sheet.getDataRange().getValues();
      if (!data || data.length === 0) continue;

      // Find header row (usually Row 2: SN, Password, Status)
      var hIdx = 1;
      for (var r = 0; r < Math.min(5, data.length); r++) {
        var rCells = data[r];
        var hasPw = false;
        var hasOther = false;
        for (var c = 0; c < rCells.length; c++) {
          var cellVal = String(rCells[c] || "").toLowerCase().trim();
          if (cellVal.indexOf("pass") !== -1 || cellVal.indexOf("token") !== -1 || cellVal.indexOf("code") !== -1) {
            hasPw = true;
          }
          if (cellVal === "sn" || cellVal === "id" || cellVal === "#" || cellVal.indexOf("status") !== -1 || cellVal === "used") {
            hasOther = true;
          }
        }
        if (hasPw && hasOther) {
          hIdx = r;
          break;
        }
      }

      var hRow = data[hIdx];
      var pwC = 1;
      var stC = 2;
      for (var c = 0; c < hRow.length; c++) {
        var cell = String(hRow[c]).toLowerCase();
        if (cell.indexOf("pass") !== -1) pwC = c;
        else if (cell.indexOf("status") !== -1 || cell === "used") stC = c;
      }

      // Scan data rows
      for (var rowNum = hIdx + 1; rowNum < data.length; rowNum++) {
        var row = data[rowNum];
        var cellPw = String(row[pwC] || "").trim().toUpperCase();
        if (cellPw === inputPw) {
          matchedSheet = sheet;
          matchedRowIdx = rowNum;
          headerRowIdx = hIdx;
          colPw = pwC;
          colStatus = stC;
          colTeam = Math.max(pwC, stC) + 1;
          colTime = colTeam + 1;
          matchedRowData = row;
          break;
        }
      }

      if (matchedSheet) break;
    }

    if (!matchedSheet || matchedRowIdx === -1) {
      return jsonResponse({
        success: false,
        valid: false,
        error: "Invalid security code. Code not found in central registry."
      });
    }

    // Check if already used
    var currentStatus = String(matchedRowData[colStatus] || "").trim().toUpperCase();
    var currentTeam = String(matchedRowData[colTeam] || "").trim();

    // In this sheet, Status starts as FALSE. If TRUE, USED, or team is set, it's used.
    var isAlreadyUsed = (
      currentStatus === "TRUE" ||
      currentStatus === "USED" ||
      currentStatus === "REDEEMED" ||
      (currentTeam !== "" && currentStatus !== "FALSE")
    );

    if (isAlreadyUsed) {
      var claimedBy = currentTeam || "another unit";
      return jsonResponse({
        success: false,
        valid: false,
        is_used: true,
        error: "This password has already been used by " + claimedBy + "."
      });
    }

    // Mark as USED on the Google Spreadsheet!
    var targetSheetRowNum = matchedRowIdx + 1; // 1-based index
    var nowTimestamp = Utilities.formatDate(new Date(), "GMT", "yyyy-MM-dd HH:mm:ss 'UTC'");

    // Update header labels for Column D and E if missing
    var headerRowData = matchedSheet.getRange(headerRowIdx + 1, 1, 1, 5).getValues()[0];
    if (!headerRowData[colTeam]) {
      matchedSheet.getRange(headerRowIdx + 1, colTeam + 1).setValue("Used By");
    }
    if (!headerRowData[colTime]) {
      matchedSheet.getRange(headerRowIdx + 1, colTime + 1).setValue("Used At");
    }

    // Mark status TRUE in checkbox / cell, write Team, write Timestamp
    matchedSheet.getRange(targetSheetRowNum, colStatus + 1).setValue(true);
    matchedSheet.getRange(targetSheetRowNum, colTeam + 1).setValue(teamName + " (ID: " + teamId + ")");
    matchedSheet.getRange(targetSheetRowNum, colTime + 1).setValue(nowTimestamp);

    // Extract zone from sheet name (e.g. "PAST - PASSWORDS" -> "PAST")
    var sheetName = matchedSheet.getName().toUpperCase();
    var detectedZone = null;
    if (sheetName.indexOf("PAST") !== -1) detectedZone = "PAST";
    else if (sheetName.indexOf("PRESENT") !== -1) detectedZone = "PRESENT";
    else if (sheetName.indexOf("FUTURE") !== -1) detectedZone = "FUTURE";

    return jsonResponse({
      success: true,
      valid: true,
      message: "Security code authenticated. Registered as USED on Google Spreadsheet.",
      password: matchedRowData[colPw],
      zone: detectedZone,
      sheet_name: matchedSheet.getName(),
      row_index: targetSheetRowNum
    });

  } catch (err) {
    return jsonResponse({
      success: false,
      valid: false,
      error: "Apps Script error: " + err.toString()
    });
  } finally {
    lock.releaseLock();
  }
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
