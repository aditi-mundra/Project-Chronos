/**
 * Project Chronos - Transition Round password service (Google Apps Script web app).
 *
 * Bound to the "Project Chronos - Password List" sheet. The Chronos backend calls it with
 *   POST { secret, action: "consume", zone: "past" | "present" | "future", password }
 * and gets back JSON:
 *   { ok: true }               password found in that zone's tab and not used yet -> its
 *                              Status checkbox is now ticked (used)
 *   { ok: false }              wrong password, wrong zone, or already used
 *   { error: "..." }           bad secret / bad request / script not configured
 *
 * SETUP (once):
 *  1. In the sheet: Extensions > Apps Script. Replace the editor's code with this file.
 *  2. Project Settings (gear) > Script Properties > add  CHRONOS_SECRET = <a long random string>
 *     (the same value goes into the backend's TRANSITION_SHEET_SECRET).
 *  3. Deploy > New deployment > type "Web app": Execute as "Me", Who has access "Anyone".
 *     Authorize when asked. Copy the Web app URL (ends in /exec) into TRANSITION_SHEET_URL.
 *  4. After changing this code, use Deploy > Manage deployments > Edit > New version.
 *
 * Tabs are matched by name prefix, case-insensitive: "PAST - PASSWORDS" matches zone "past".
 * Layout per tab: row 1 title, row 2 headers, rows 3+ = SN | Password | Status (checkbox).
 */

var FIRST_DATA_ROW = 3;
var PASSWORD_COL = 2; // B
var STATUS_COL = 3;   // C

function doPost(e) {
  var lock = LockService.getScriptLock();
  try {
    var req = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    var secret = PropertiesService.getScriptProperties().getProperty('CHRONOS_SECRET');
    if (!secret) return out_({ error: 'CHRONOS_SECRET is not set in Script Properties' });
    if (!req.secret || req.secret !== secret) return out_({ error: 'unauthorized' });
    if (req.action !== 'consume') return out_({ error: 'unknown action' });

    var zone = String(req.zone || '').toLowerCase();
    var password = String(req.password || '').trim().toUpperCase();
    if (['past', 'present', 'future'].indexOf(zone) < 0 || !password) {
      return out_({ error: 'bad request' });
    }

    var sheet = findTab_(zone);
    if (!sheet) return out_({ error: 'no tab for zone ' + zone });

    lock.waitLock(20000); // one consume at a time: a password can be used only once
    var lastRow = sheet.getLastRow();
    if (lastRow < FIRST_DATA_ROW) return out_({ ok: false });

    var rows = lastRow - FIRST_DATA_ROW + 1;
    var values = sheet.getRange(FIRST_DATA_ROW, PASSWORD_COL, rows, STATUS_COL - PASSWORD_COL + 1).getValues();
    for (var i = 0; i < values.length; i++) {
      var candidate = String(values[i][0]).trim().toUpperCase();
      if (candidate === password) {
        if (values[i][1] === true) return out_({ ok: false }); // already used
        sheet.getRange(FIRST_DATA_ROW + i, STATUS_COL).setValue(true);
        SpreadsheetApp.flush();
        return out_({ ok: true });
      }
    }
    return out_({ ok: false });
  } catch (err) {
    return out_({ error: String(err) });
  } finally {
    try { lock.releaseLock(); } catch (ignore) {}
  }
}

function findTab_(zone) {
  var sheets = SpreadsheetApp.getActiveSpreadsheet().getSheets();
  for (var i = 0; i < sheets.length; i++) {
    if (sheets[i].getName().toLowerCase().indexOf(zone) === 0) return sheets[i];
  }
  return null;
}

function out_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
