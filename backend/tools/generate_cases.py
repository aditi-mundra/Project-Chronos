"""
Generate the 24 Round 2 evidence sets and the matching 24 Round 3 cases.

    python backend/tools/generate_cases.py

Writes (deterministically, so the output is reviewable and repeatable):

  round2_cases_all_24/R2-01 ... R2-24/
      case.json                the case (culprit = Project Alpha / Beta / Gamma)
      future_audit.log         the four evidence files Round 3 refers to
      access_history.log
      system_auth_matrix.log
      incident_report.txt
  backend/app/data/round3_cases.json
      one Round 3 case per Round 2 case, 1:1, with evidence_pool entries that
      point at those same four files.

Design (what makes a case solvable):

  * Every case has one culprit project. Three of the four files each contain a
    fact that points at the culprit (supporting files); the fourth carries a
    true-but-unhelpful or misleading fact (the distractor file). Which file is
    the distractor differs from case to case.
  * No single file names the culprit. Credentials are only mapped to projects in
    the registry at the top of access_history.log / system_auth_matrix.log, and the
    change is tied to a terminal and a time that must be matched across files.
  * Decoys: another project holds ROOT_WRITE at a *different* terminal near the
    incident, a third project is DENIED at the incident terminal, and unrelated
    changes / keys fill the logs.

Extra layers (moderate difficulty, all stated in the files themselves):

  * Terminal codes: future_audit.log and system_auth_matrix.log list terminals by code
    (N-xxxx); access_history.log and incident_report.txt use names. The TERMINAL
    REGISTRY at the top of access_history.log maps one to the other.
  * Clock offset: system_auth_matrix.log runs a few seconds ahead of the master clock
    (the offset is printed in its header); its times must be corrected before they are
    compared with the other logs.
  * More decoys: an earlier ROOT_WRITE change at the incident terminal by another
    project, and a mitigation change by a third project right after the incident.

Balance: culprit alpha/beta/gamma 8 each; each file is the distractor 6 times.
"""

from __future__ import annotations

import json
import random
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASES_DIR = ROOT / "round2_cases_all_24"
R3_JSON = ROOT / "backend" / "app" / "data" / "round3_cases.json"

N_CASES = 24

PROJECTS = {
    "alpha": {
        "name": "Project Alpha", "lead": "Dr. Aris Thorne", "sector": "Future Timeline",
        "designation": "Core Architecture & Neural Systems", "clearance": "Level 5 Autonomous Override",
        "hash": "SIGMA-99-0x7F1A",
        "dossier": ("Oversees the Future Timeline framework and autonomous neural kernel. Advocated for allowing "
                    "CHRONOS to proactively edit timeline anchor points to prevent paradoxes."),
        "alibi": "Claimed to be conducting read-only sensor calibration from the upper observation gallery.",
    },
    "beta": {
        "name": "Project Beta", "lead": "Commander V. Reyes", "sector": "Present Timeline",
        "designation": "Perimeter Defense & Sector Lock", "clearance": "Level 4 Emergency Containment",
        "hash": "DELTA-44-0x3B88",
        "dossier": ("Responsible for Present Timeline containment and physical security. Expressed skepticism of "
                    "autonomous AI and ordered physical sector quarantines."),
        "alibi": "Claimed to be securing the physical perimeter following the initial chronon fluctuation.",
    },
    "gamma": {
        "name": "Project Gamma", "lead": "Chief Eng. Sarah Chen", "sector": "Past Timeline",
        "designation": "Historical Archival & Chrono-Sync", "clearance": "Level 4 Synchronization Grid",
        "hash": "EPSILON-12-0x9C04",
        "dossier": ("Maintains the Past Timeline historical records and chronon dampening matrix. Monitored access "
                    "history and resonance frequencies."),
        "alibi": "Claimed to be dampening chronon oscillations from the engineering console.",
    },
}
ORDER = ["alpha", "beta", "gamma"]

# file id -> (filename, Round 3 evidence id, evidence category)
FILES = {
    "audit": ("future_audit.log", "ev_alpha_log", "Timeline Modification", "TIMELINE_MODIFICATION"),
    "access": ("access_history.log", "ev_gamma_access", "Access History", "ACCESS_HISTORY"),
    "auth": ("system_auth_matrix.log", "ev_system_auth", "System Authorization", "SYSTEM_AUTHORIZATION"),
    "incident": ("incident_report.txt", "ev_beta_incident", "Incident Telemetry", "INCIDENT_TIMESTAMP"),
}
DISTRACTOR_CYCLE = ["audit", "access", "auth", "incident"]

GREEK = ["Delta", "Epsilon", "Zeta", "Theta", "Kappa", "Lambda", "Sigma", "Tau", "Rho", "Omega"]
KEY_WORDS = ["ORION", "VEGA", "HELIX", "ZENITH", "QUASAR", "NOVA", "PULSAR", "ONYX", "LYRA", "ATLAS"]
BENIGN_SETTINGS = [
    ("log verbosity", "NORMAL -> VERBOSE"), ("retry policy", "STANDARD -> LIMITED"),
    ("cache TTL", "300 -> 600"), ("health probe interval", "30 -> 15"),
    ("archive compaction window", "NIGHTLY -> WEEKLY"), ("queue depth limit", "512 -> 1024"),
    ("heartbeat timeout", "5 -> 8"), ("snapshot retention", "7 -> 14"),
]

THEMES = [
    dict(id="kernel_rewrite", title="Sector-0 Kernel Divergence", node="Terminal Node {g}-{n}",
         action="root-level configuration rewrite", setting="safety governor policy",
         change="ENFORCED -> DISABLED", symptom="chronon flux surge of {v}%", v=(3000, 9000),
         what="a root-level configuration rewrite disabled the safety governors"),
    dict(id="bridge_decouple", title="Sector-4 Temporal Bridge Decoupling", node="Console SEC-{n2}",
         action="forced decoupling of the temporal stabilization bridge", setting="bridge coupling state",
         change="COUPLED -> FORCED_DECOUPLE", symptom="loss of {v} transit buffers", v=(6, 40),
         what="the temporal stabilization bridge was forcibly decoupled"),
    dict(id="frequency_injection", title="Quantum Resonance Harmonics Sabotage", node="Frequency Station CH-{n}",
         action="resonance modulation script injection", setting="frequency matrix",
         change="BASELINE -> +{v} MHz", symptom="boundary layer rupture at +{v} MHz", v=(200, 640),
         what="a modulation script pushed the sync grid into the destructive dissonance band"),
    dict(id="archive_purge", title="Archive Vault Anchor Purge", node="Archive Vault AV-{n}",
         action="bulk purge of timeline anchor records", setting="anchor record store",
         change="RETAINED -> PURGED ({v} records)", symptom="{v} anchor records missing from the index", v=(120, 900),
         what="timeline anchor records were purged in bulk"),
    dict(id="anchor_recalibration", title="Anchor Relay Offset Recalibration", node="Anchor Relay AR-{n}",
         action="recalibration of temporal anchor offsets", setting="anchor offset table",
         change="0 -> {v} ms", symptom="anchor drift of {v} ms across the relay chain", v=(40, 480),
         what="the anchor offset table was recalibrated by hand"),
    dict(id="paradox_filter", title="Paradox Filter Array Bypass", node="Filter Array PF-{n}",
         action="paradox filter bypass", setting="paradox filter mode",
         change="ACTIVE -> BYPASS", symptom="{v} unresolved causal loops detected", v=(14, 90),
         what="the paradox filter array was switched to bypass"),
    dict(id="sync_governor", title="Cross-Timeline Sync Governor Shutdown", node="Sync Governor SG-{n}",
         action="shutdown of the cross-timeline sync governor", setting="sync governor state",
         change="RUNNING -> HALTED", symptom="desynchronisation of {v} timeline channels", v=(3, 12),
         what="the cross-timeline sync governor was halted"),
    dict(id="buffer_flush", title="Transit Buffer Emergency Flush", node="Transit Buffer TB-{n}",
         action="forced flush of the transit buffer", setting="transit buffer content",
         change="HELD -> FLUSHED ({v} MB)", symptom="transit buffer overrun of {v} MB", v=(80, 700),
         what="the transit buffer was flushed outside its maintenance window"),
]


def hms(sec: int) -> str:
    sec %= 86400
    return f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


class Case:
    """All facts of one case, derived deterministically from its index."""

    def __init__(self, i: int):
        self.i = i
        self.id = f"R2-{i + 1:02d}"
        self.r3id = f"R3-{i + 1:02d}"
        rng = random.Random(7100 + i * 31)
        self.rng = rng
        self.culprit = ORDER[i % 3]
        self.d1, self.d2 = [p for p in ORDER if p != self.culprit]
        if i % 2:
            self.d1, self.d2 = self.d2, self.d1
        self.theme = THEMES[i % len(THEMES)]
        self.distractor = DISTRACTOR_CYCLE[(i // 3) % 4]
        self.supporting = [f for f in FILES if f != self.distractor]

        t = self.theme
        self.v = rng.randint(*t["v"])
        g = rng.choice(GREEK)
        self.node = t["node"].format(g=g, n=rng.randint(1, 9), n2=f"{rng.randint(1, 9):02d}")
        node2 = t["node"].format(g=rng.choice([x for x in GREEK if x != g]), n=rng.randint(1, 9),
                                 n2=f"{rng.randint(10, 19)}")
        self.node2 = node2 if node2 != self.node else node2 + "B"
        self.change_text = t["change"].format(v=self.v)
        self.symptom = t["symptom"].format(v=self.v)

        self.T = rng.randint(18 * 3600 + 20 * 60, 23 * 3600 + 30 * 60)
        self.dt_access = rng.randint(8, 19)      # culprit session before the change
        self.dt_key = rng.randint(22, 58)        # key armed before the change
        self.dt_sym = rng.randint(6, 21)         # first symptom after the change
        self.sess = f"s-{rng.randint(1000, 9999)}"
        self.chg = f"CHG-{rng.randint(1000, 9999)}"
        self.key = f"KEY-{rng.choice(KEY_WORDS)}-{rng.randint(1000, 9999)}"
        other = [w for w in KEY_WORDS]
        self.key_old = f"KEY-{rng.choice(other)}-{rng.randint(1000, 9999)}"
        self.key_dec = f"KEY-{rng.choice(other)}-{rng.randint(1000, 9999)}"
        self.log_start = self.T - 2 * 3600          # every record in the files falls inside this window
        self.log_end = self.T + rng.randint(9, 16) * 60

        # extra layers
        self.skew = rng.randint(18, 47)             # auth matrix clock runs ahead by this many seconds
        self.dt_early = rng.randint(6 * 60, 9 * 60)  # D1's earlier change at the incident terminal
        self.dt_post = rng.randint(50, 80)           # D2's mitigation change after the incident
        self.bterms = [f"Operator Desk OD-{rng.randint(1, 9)}", f"Diagnostics Bay DB-{rng.randint(1, 9)}",
                       f"Terminal Node Iota-{rng.randint(1, 9)}", f"Maintenance Console MC-{rng.randint(1, 9)}"]
        self._codes: dict[str, str] = {}
        self._code_rng = random.Random(9000 + i * 7)

    def code(self, terminal: str) -> str:
        """The terminal code used by the audit log and the authorization matrix."""
        if terminal not in self._codes:
            used = set(self._codes.values())
            while True:
                candidate = f"N-{self._code_rng.randint(1000, 9999)}"
                if candidate not in used:
                    break
            self._codes[terminal] = candidate
        return self._codes[terminal]

    # convenient accessors
    def cred(self, p):
        return PROJECTS[p]["hash"]

    @property
    def title(self):
        return self.theme["title"]


# ----------------------------------------------------------------------------- files

def registry_block(c: Case) -> list[str]:
    lines = ["REGISTERED PROJECT CREDENTIALS"]
    for p in ORDER:
        d = PROJECTS[p]
        lines.append(f"{d['name']} | {d['sector']} | Lead: {d['lead']} | Credential: {d['hash']}")
    return lines


def terminal_registry(c: Case) -> list[str]:
    names = list(dict.fromkeys(c.bterms + [c.node, c.node2]))
    lines = ["TERMINAL REGISTRY (terminal code | terminal name)"]
    for n in sorted(names, key=c.code):
        lines.append(f"{c.code(n)} | {n}")
    return lines


def build_audit(c: Case) -> str:
    rng = random.Random(c.i * 17 + 5)
    rows = []  # (time, lines)
    base = c.T - rng.randint(70, 110) * 60
    for k in range(3):
        s_, ch = rng.choice(BENIGN_SETTINGS)
        p = rng.choice(ORDER)
        tt = base + k * rng.randint(9, 17) * 60
        rows.append((tt, [f"{hms(tt)} | CHG-{rng.randint(1000, 9999)} | NODE {c.code(rng.choice(c.bterms))}",
                          f"  SETTING: {s_} | CHANGE: {ch}", f"  STATUS: APPLIED | CREDENTIAL: {c.cred(p)}"]))
    # D2: an old change that was reverted
    s_, ch = rng.choice(BENIGN_SETTINGS)
    tr = c.T - rng.randint(35, 50) * 60
    rows.append((tr, [f"{hms(tr)} | CHG-{rng.randint(1000, 9999)} | NODE {c.code(c.node2)}",
                      f"  SETTING: {s_} | CHANGE: {ch}", f"  STATUS: REVERTED | CREDENTIAL: {c.cred(c.d2)}"]))
    # D1: an unrelated change at the other terminal a few minutes before
    s_, ch = rng.choice(BENIGN_SETTINGS)
    t1 = c.T - rng.randint(150, 420)
    rows.append((t1, [f"{hms(t1)} | CHG-{rng.randint(1000, 9999)} | NODE {c.code(c.node2)}",
                      f"  SETTING: {s_} | CHANGE: {ch}", f"  STATUS: APPLIED | CREDENTIAL: {c.cred(c.d1)}"]))
    # D1 again: an earlier, unrelated change at the incident terminal itself
    s_, ch = rng.choice(BENIGN_SETTINGS)
    te = c.T - c.dt_early
    rows.append((te, [f"{hms(te)} | CHG-{rng.randint(1000, 9999)} | NODE {c.code(c.node)}",
                      f"  SETTING: {s_} | CHANGE: {ch}", f"  STATUS: APPLIED | CREDENTIAL: {c.cred(c.d1)}"]))
    # the incident change
    if c.distractor == "audit":
        who = "CREDENTIAL: delegated (scheduler task, initiating session not recorded)"
    else:
        who = f"CREDENTIAL: {c.cred(c.culprit)}"
    rows.append((c.T, [f"{hms(c.T)} | {c.chg} | NODE {c.code(c.node)}",
                       f"  ACTION: {c.theme['action']}",
                       f"  SETTING: {c.theme['setting']} | CHANGE: {c.change_text}",
                       f"  STATUS: APPLIED | {who}"]))
    # D2 again: a mitigation hold right after the incident (looks involved, came too late)
    tp = c.T + c.dt_post
    rows.append((tp, [f"{hms(tp)} | CHG-{rng.randint(1000, 9999)} | NODE {c.code(c.node)}",
                      "  SETTING: mitigation hold | CHANGE: NONE -> HOLD",
                      f"  STATUS: APPLIED | CREDENTIAL: {c.cred(c.d2)}"]))
    rows.sort(key=lambda r: r[0])
    out = ["CHRONOS // CHANGE AUDIT LOG // future_audit.log",
           f"CASE {c.id}", f"WINDOW: {hms(c.log_start)} - {hms(c.log_end)}", "",
           "Every applied configuration change is listed with the credential that applied it.",
           "Nodes are listed by terminal code; the TERMINAL REGISTRY is kept in access_history.log.",
           "A credential is a project's biometric token; the registry is kept in access_history.log.", ""]
    for _, lines in rows:
        out.extend(lines)
        out.append("")
    out.append("END OF AUDIT WINDOW")
    return "\n".join(out) + "\n"


def build_access(c: Case) -> str:
    rng = random.Random(c.i * 19 + 9)
    ev = []  # (time, text)
    terms = c.bterms
    for k in range(4):
        p = rng.choice(ORDER)
        tt = c.T - rng.randint(30, 105) * 60 + k * 41
        ev.append((tt, f"{hms(tt)} | SESSION s-{rng.randint(1000, 9999)} | {c.cred(p)} | {rng.choice(terms)}"
                       f" | AUTHENTICATED | {rng.choice(['READ_ONLY', 'DIAGNOSTIC'])}"))
    # D1: ROOT_WRITE at the *other* terminal close to the incident
    t1 = c.T - rng.randint(40, 70)
    ev.append((t1, f"{hms(t1)} | SESSION s-{rng.randint(1000, 9999)} | {c.cred(c.d1)} | {c.node2}"
                   f" | AUTHENTICATED | ROOT_WRITE"))
    # D1 earlier: ROOT_WRITE at the incident terminal minutes before (an unrelated change)
    te = c.T - c.dt_early - rng.randint(8, 15)
    ev.append((te, f"{hms(te)} | SESSION s-{rng.randint(1000, 9999)} | {c.cred(c.d1)} | {c.node}"
                   f" | AUTHENTICATED | ROOT_WRITE"))
    # D2: denied at the incident terminal
    t2 = c.T - rng.randint(75, 140)
    ev.append((t2, f"{hms(t2)} | SESSION s-{rng.randint(1000, 9999)} | {c.cred(c.d2)} | {c.node}"
                   f" | DENIED | ROOT_WRITE (insufficient scope)"))
    # D2 after the incident: ROOT_WRITE for the mitigation hold
    tp = c.T + c.dt_post - rng.randint(10, 18)
    ev.append((tp, f"{hms(tp)} | SESSION s-{rng.randint(1000, 9999)} | {c.cred(c.d2)} | {c.node}"
                   f" | AUTHENTICATED | ROOT_WRITE"))
    gap = None
    if c.distractor == "access":
        g0 = c.T - c.dt_access - rng.randint(4, 9)
        g1 = c.T + rng.randint(4, 9)
        gap = (g0, g1)
    else:
        ts = c.T - c.dt_access
        ev.append((ts, f"{hms(ts)} | SESSION {c.sess} | {c.cred(c.culprit)} | {c.node}"
                       f" | AUTHENTICATED | ROOT_WRITE"))
    ev.sort(key=lambda r: r[0])
    out = ["CHRONOS // ACCESS AND SESSION HISTORY // access_history.log",
           f"CASE {c.id}", f"ARCHIVE WINDOW: {hms(c.log_start)} - {hms(c.log_end)}", ""]
    out.extend(registry_block(c))
    out += [""]
    out.extend(terminal_registry(c))
    out += ["", "SCOPES: READ_ONLY < DIAGNOSTIC < ROOT_WRITE", "", "SESSION RECORDS"]
    placed = False
    for tt, text in ev:
        if gap and not placed and tt > gap[0]:
            out.append(f"{hms(gap[0])} - {hms(gap[1])} | LOG BUFFER OVERFLOW | records in this interval were not recovered")
            placed = True
        out.append(text)
    if gap and not placed:
        out.append(f"{hms(gap[0])} - {hms(gap[1])} | LOG BUFFER OVERFLOW | records in this interval were not recovered")
    out += ["", "END OF ARCHIVE"]
    return "\n".join(out) + "\n"


def build_auth(c: Case) -> str:
    """Times in this log are printed on the matrix's own clock: master time + c.skew."""
    rng = random.Random(c.i * 23 + 3)
    K = c.skew

    def at(t):
        return hms(t + K)

    ev = []
    t_old = c.T - rng.randint(70, 100) * 60
    ev.append((t_old, f"{at(t_old)} | {c.key_old} | ARMED | BY {c.cred(c.d1)} | VALID 120s | USED: maintenance window"))
    ev.append((t_old + 95, f"{at(t_old + 95)} | {c.key_old} | DISARMED | after use"))
    t_dec = c.T - rng.randint(150, 240)
    ev.append((t_dec, f"{at(t_dec)} | {c.key_dec} | ARMED | BY {c.cred(c.d2)} | VALID 120s | USED: none"))
    ev.append((t_dec + 120, f"{at(t_dec + 120)} | {c.key_dec} | EXPIRED | never used"))
    if c.distractor == "auth":
        ev.append((c.T - 90, f"{at(c.T - 90)} | {c.key} | STANDING AUTHORIZATION | maintenance window MW-"
                             f"{c.i + 11} | no individual arming recorded"))
    else:
        ta = c.T - c.dt_key
        ev.append((ta, f"{at(ta)} | {c.key} | ARMED | BY {c.cred(c.culprit)} | VALID 120s"))
    ev.append((c.T, f"{at(c.T)} | {c.key} | USED | terminal {c.code(c.node)} | {c.chg}"))
    tp = c.T + c.dt_post - 6
    ev.append((tp, f"{at(tp)} | KEY-HOLD-{rng.randint(1000, 9999)} | ARMED | BY {c.cred(c.d2)} | VALID 120s"))
    ev.sort(key=lambda r: r[0])
    out = ["CHRONOS // SYSTEM AUTHORIZATION MATRIX // system_auth_matrix.log",
           f"CASE {c.id}", f"WINDOW: {hms(c.log_start)} - {hms(c.log_end)} (master clock)",
           f"CLOCK OFFSET: +{K} s (times in this log run ahead of the master clock; subtract the offset "
           f"before comparing them with other logs)", ""]
    out.extend(registry_block(c))
    out += ["", "A key must be armed by a credential before it can be used. A key is valid for the stated",
            "period after arming; a standing authorization is not tied to one credential.",
            "Terminals are listed by terminal code (see TERMINAL REGISTRY in access_history.log).", "", "KEY EVENTS"]
    out.extend(text for _, text in ev)
    out += ["", "END OF MATRIX"]
    return "\n".join(out) + "\n"


def build_incident(c: Case) -> str:
    rng = random.Random(c.i * 29 + 1)
    ts = c.T + c.dt_sym
    out = ["CHRONOS // INCIDENT REPORT // incident_report.txt",
           f"CASE {c.id}", f"INCIDENT: {c.title}", "",
           "SUMMARY",
           f"{c.theme['what'][0].upper() + c.theme['what'][1:]}. The effect spread across the timeline network.", "",
           "INCIDENT TIMELINE",
           f"{hms(ts)} | First abnormal reading: {c.symptom}",
           f"{hms(ts + rng.randint(11, 24))} | Monitoring reports a sustained inconsistency",
           f"{hms(ts + rng.randint(40, 70))} | Automatic reconciliation fails to restore the baseline",
           f"{hms(ts + rng.randint(100, 150))} | Cross-timeline results leave the normal operating range", "",
           "ORIGIN ANALYSIS"]
    if c.distractor == "incident":
        out += [f"The first abnormal reading cannot be traced to a single source. Candidate nodes: {c.node} and {c.node2}.",
                "No change record could be matched to the reading with certainty."]
    else:
        out += [f"The first abnormal reading originates at {c.node}.",
                f"It matches change {c.chg} applied at {hms(c.T)} ({c.theme['action']}).",
                f"No other change within the incident window touched the {c.theme['setting']}."]
    out += ["", "OBSERVATIONS",
            f"A mitigation hold was applied at {c.node} at {hms(c.T + c.dt_post)}; it did not restore the baseline.",
            "Baseline checks before the incident were within their normal range.",
            "Operators on shift reported no scheduled maintenance for this subsystem.", "",
            "END OF REPORT"]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------- round 3 data

def r3_case(c: Case) -> dict:
    t = c.theme
    cp = PROJECTS[c.culprit]
    ev_pool = []
    if c.distractor == "audit":
        a = (f"{t['action'][0].upper() + t['action'][1:]} applied on {c.node}; the initiating credential was not "
             f"captured (delegated scheduler task).")
        a_label = f"Change Record {c.chg} (initiator not recorded)"
    else:
        a = f"{t['action'][0].upper() + t['action'][1:]} applied on {c.node} under credential {c.cred(c.culprit)}."
        a_label = f"Change Record {c.chg}"
    ev_pool.append(("audit", a_label, hms(c.T), a))

    if c.distractor == "access":
        g = f"credential {c.cred(c.d1)} held ROOT_WRITE at {c.node2} shortly before the change"
        ev_pool.append(("access", "Session Log Gap",
                        hms(c.T - c.dt_access - 6),
                        f"Session records around the change were lost to a log buffer overflow; recovered records show {g}."))
    else:
        ev_pool.append(("access", f"Session at {c.node}", hms(c.T - c.dt_access),
                        f"Credential {c.cred(c.culprit)} authenticated at {c.node} with ROOT_WRITE scope."))

    if c.distractor == "auth":
        ev_pool.append(("auth", f"Standing Authorization for {c.key}", hms(c.T - 90),
                        f"{c.key} ran under a standing maintenance authorization; no individual arming was recorded "
                        f"(log clock +{c.skew} s)."))
    else:
        ev_pool.append(("auth", f"Key {c.key} Armed", hms(c.T - c.dt_key),
                        f"{c.key} was armed by credential {c.cred(c.culprit)} {c.dt_key} seconds before the change "
                        f"(log clock +{c.skew} s)."))

    if c.distractor == "incident":
        ev_pool.append(("incident", "Origin Not Narrowed", hms(c.T + c.dt_sym),
                        f"First abnormal reading ({c.symptom}); the source could not be narrowed beyond "
                        f"{c.node} and {c.node2}."))
    else:
        ev_pool.append(("incident", f"Origin Traced to {c.node}", hms(c.T + c.dt_sym),
                        f"First abnormal reading ({c.symptom}) traced to {c.node} and change {c.chg}."))

    pool = []
    for fid, label, ts, desc in ev_pool:
        fname, evid, cat, code = FILES[fid]
        pool.append({"id": evid, "category": cat, "category_code": code, "source_file": fname,
                     "label": label, "timestamp": f"{ts} UTC", "description": desc})

    # candidate dossiers: base fields + a discrepancy that is true in the files
    cands = []
    for p in ORDER:
        d = PROJECTS[p]
        if p == c.culprit:
            if c.distractor == "access":
                disc = f"Credential {d['hash']} is recorded on change {c.chg} at {c.node} at {hms(c.T)} UTC."
            else:
                disc = (f"Credential {d['hash']} authenticated at {c.node} at {hms(c.T - c.dt_access)} UTC "
                        f"with ROOT_WRITE scope.")
        elif p == c.d1:
            disc = (f"Credential {d['hash']} held ROOT_WRITE at {c.node2} shortly before {hms(c.T)} UTC and "
                    f"applied an unrelated change there.")
        else:
            disc = (f"Credential {d['hash']} was denied ROOT_WRITE at {c.node} and armed {c.key_dec} without "
                    f"using it before it expired.")
        cands.append({"id": p, "name": d["name"], "lead_name": d["lead"], "timeline_sector": d["sector"],
                      "designation": d["designation"], "clearance_level": d["clearance"],
                      "biometric_hash": d["hash"], "dossier": d["dossier"], "discrepancy": disc,
                      "alibi": d["alibi"]})

    valid = [FILES[f][1] for f in c.supporting]
    supports = ", ".join(FILES[f][0] for f in c.supporting)
    narrative = (
        f"Forensic evidence establishes that {cp['name']} ({cp['lead']}, {cp['sector']}) carried out the "
        f"{t['action']} on {c.node} at {hms(c.T)} UTC, using credential {cp['hash']} and key {c.key}. "
        f"The supporting records are {supports}; the {FILES[c.distractor][0]} record did not point to the "
        f"responsible project. The {c.symptom} followed {c.dt_sym} seconds later."
    )
    return {
        "case_id": c.r3id,
        "r2_case_id": c.id,
        "case_code": f"{c.culprit.upper()}-{t['id'].upper().replace('_', '-')}-{c.i + 1:02d}",
        "title": c.title,
        "incident_brief": (
            f"Your Round 2 evidence files record an incident at about {hms(c.T)} UTC: {t['what']}. "
            f"Identify which project is responsible and select the evidence files that support your accusation."
        ),
        "candidates": cands,
        "evidence_pool": pool,
        "culprit_candidate_id": c.culprit,
        "valid_evidence_ids": valid,
        "narrative_summary": narrative,
    }


def case_json(c: Case) -> dict:
    return {
        "case_id": c.id,
        "archetype": c.theme["id"],
        "incident": c.title,
        "culprit": PROJECTS[c.culprit]["name"],
        "candidates": [
            {"name": PROJECTS[p]["name"], "user_id": p.upper(), "role": PROJECTS[p]["sector"]} for p in ORDER
        ],
        "player_files": {fid: FILES[fid][0] for fid in FILES},
        "supporting_files": [FILES[f][0] for f in c.supporting],
        "intended_deduction": (
            "Match the incident change to its terminal (codes in the audit log, names elsewhere) and time "
            "(correct the matrix clock offset), then find which credential applied or authorised it. "
            "Three files point at the responsible project; one does not."
        ),
    }


def main() -> None:
    for old in CASES_DIR.glob("R2-*"):
        if old.is_dir():
            shutil.rmtree(old)
    r3 = []
    for i in range(N_CASES):
        c = Case(i)
        folder = CASES_DIR / c.id
        folder.mkdir(parents=True)
        (folder / "case.json").write_text(json.dumps(case_json(c), indent=2) + "\n", encoding="utf-8")
        (folder / FILES["audit"][0]).write_text(build_audit(c), encoding="utf-8")
        (folder / FILES["access"][0]).write_text(build_access(c), encoding="utf-8")
        (folder / FILES["auth"][0]).write_text(build_auth(c), encoding="utf-8")
        (folder / FILES["incident"][0]).write_text(build_incident(c), encoding="utf-8")
        r3.append(r3_case(c))
    R3_JSON.write_text(json.dumps(r3, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {N_CASES} Round 2 cases and {len(r3)} Round 3 cases")


if __name__ == "__main__":
    main()
