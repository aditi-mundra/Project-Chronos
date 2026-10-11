"""
Quality checks for the 24 Round 2 evidence sets and the 24 matching Round 3 cases.

    python -m unittest backend.tests.test_cases -v

They read the generated files only (no server, no database) and include a small
solver that derives the culprit from the evidence files alone, to prove that every
case is solvable and has a single answer.
"""

import json
import re
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

CASES_DIR = ROOT / "round2_cases_all_24"
R3_FILE = ROOT / "backend" / "app" / "data" / "round3_cases.json"

FILE_NAMES = {"future_audit.log", "access_history.log", "system_auth_matrix.log", "incident_report.txt"}
PROJECT_BY_NAME = {"Project Alpha": "alpha", "Project Beta": "beta", "Project Gamma": "gamma"}
EV_BY_FILE = {
    "future_audit.log": "ev_alpha_log",
    "access_history.log": "ev_gamma_access",
    "system_auth_matrix.log": "ev_system_auth",
    "incident_report.txt": "ev_beta_incident",
}

HASH = re.compile(r"[A-Z]+-\d\d-0x[0-9A-F]{4}")
CHG = re.compile(r"CHG-\d{4}")
KEY = re.compile(r"KEY-[A-Z]+-\d{4}")


def secs(hms: str) -> int:
    h, m, s = (int(x) for x in hms.split(":"))
    return h * 3600 + m * 60 + s


def load_cases():
    cases = {}
    for folder in sorted(CASES_DIR.glob("R2-*")):
        data = json.loads((folder / "case.json").read_text(encoding="utf-8"))
        files = {p.name: p.read_text(encoding="utf-8") for p in folder.iterdir() if p.name != "case.json"}
        cases[folder.name] = (data, files)
    return cases


def solve(files: dict) -> dict:
    """Return {project: number of independent files that point at it} using only the files,
    the way a player has to: terminal codes via the registry, the matrix clock offset
    corrected, credentials mapped through the project registry."""
    access, auth, audit = files["access_history.log"], files["system_auth_matrix.log"], files["future_audit.log"]
    registry = {m.group(2): m.group(1)
                for m in re.finditer(r"^(Project \w+) \|.*Credential: (\S+)$", access, re.M)}
    assert len(registry) == 3
    to_project = {h: PROJECT_BY_NAME[n] for h, n in registry.items()}
    code_to_name = {m.group(1): m.group(2).strip()
                    for m in re.finditer(r"^(N-\d{4}) \| (.+)$", access, re.M)}
    assert len(code_to_name) >= 5, "terminal registry missing"

    om = re.search(r"^CLOCK OFFSET: \+(\d+) s", auth, re.M)
    assert om, "clock offset not stated"
    offset = int(om.group(1))

    # the incident change: the only audit record that carries an ACTION line
    m = re.search(r"^(\d\d:\d\d:\d\d) \| (CHG-\d{4}) \| NODE (N-\d{4})\n  ACTION: .+\n.+\n  STATUS: APPLIED \| (.+)$",
                  audit, re.M)
    assert m, "incident change not found"
    t_change, chg, node_code, who = secs(m.group(1)), m.group(2), m.group(3), m.group(4)
    node = code_to_name[node_code]

    votes = Counter()
    # 1. the audit record names the credential (unless it was delegated)
    h = HASH.search(who)
    if h:
        votes[to_project[h.group(0)]] += 1
    # 2. an authenticated ROOT_WRITE session at that terminal in the minute before the change
    for sm in re.finditer(r"^(\d\d:\d\d:\d\d) \| SESSION \S+ \| (\S+) \| (.+?) \| AUTHENTICATED \| ROOT_WRITE$",
                          access, re.M):
        if sm.group(3).strip() == node and 0 < t_change - secs(sm.group(1)) <= 60:
            votes[to_project[sm.group(2)]] += 1
    # 3. the key used for that change (matrix clock corrected) was armed by a credential
    um = re.search(rf"^(\d\d:\d\d:\d\d) \| ({KEY.pattern}) \| USED \| terminal (N-\d{{4}}) \| {chg}$", auth, re.M)
    assert um, "key use not found"
    assert secs(um.group(1)) - offset == t_change, "matrix clock offset does not line up with the audit log"
    assert um.group(3) == node_code
    am = re.search(rf"^\d\d:\d\d:\d\d \| {um.group(2)} \| ARMED \| BY (\S+) ", auth, re.M)
    if am:
        votes[to_project[am.group(1)]] += 1
    return votes


class CaseDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = load_cases()
        cls.r3 = json.loads(R3_FILE.read_text(encoding="utf-8"))

    def test_structure(self):
        self.assertEqual(len(self.cases), 24)
        self.assertEqual(len(self.r3), 24)
        for cid, (data, files) in self.cases.items():
            self.assertEqual(set(files), FILE_NAMES, f"{cid}: only the four Round 3 files may exist")
            self.assertEqual(set(data["player_files"].values()), FILE_NAMES, cid)
            self.assertIn(data["culprit"], PROJECT_BY_NAME, cid)
            self.assertEqual({c["name"] for c in data["candidates"]}, set(PROJECT_BY_NAME), cid)
            for name, text in files.items():
                self.assertGreater(len(text.splitlines()), 12, f"{cid}/{name} is too short")

    def test_balance(self):
        culprits = Counter(d["culprit"] for d, _ in self.cases.values())
        self.assertEqual(set(culprits.values()), {8}, culprits)
        distractors = Counter()
        for d, _ in self.cases.values():
            missing = FILE_NAMES - set(d["supporting_files"])
            self.assertEqual(len(missing), 1)
            distractors[missing.pop()] += 1
        self.assertEqual(set(distractors.values()), {6}, distractors)

    def test_round3_matches_round2(self):
        by_r2 = {c["r2_case_id"]: c for c in self.r3}
        self.assertEqual(set(by_r2), set(self.cases))
        for cid, (data, files) in self.cases.items():
            c3 = by_r2[cid]
            self.assertEqual(c3["culprit_candidate_id"], PROJECT_BY_NAME[data["culprit"]], cid)
            self.assertEqual({c["id"] for c in c3["candidates"]}, {"alpha", "beta", "gamma"})
            sources = {e["source_file"] for e in c3["evidence_pool"]}
            self.assertEqual(sources, FILE_NAMES, f"{cid}: Round 3 must cite exactly the four Round 2 files")
            self.assertEqual({e["id"] for e in c3["evidence_pool"]}, set(EV_BY_FILE.values()))
            valid_files = {e["source_file"] for e in c3["evidence_pool"] if e["id"] in c3["valid_evidence_ids"]}
            self.assertEqual(valid_files, set(data["supporting_files"]), cid)
            self.assertEqual(len(c3["valid_evidence_ids"]), 3, cid)
            # every identifier an evidence item quotes really appears in its source file
            for e in c3["evidence_pool"]:
                text = files[e["source_file"]]
                for pattern in (HASH, CHG, KEY):
                    for token in pattern.findall(e["description"] + " " + e["label"]):
                        self.assertIn(token, text, f"{cid}: {token} not in {e['source_file']}")

    def test_supporting_files_vary_between_cases(self):
        sets = {tuple(sorted(d["supporting_files"])) for d, _ in self.cases.values()}
        self.assertEqual(len(sets), 4)

    def test_every_case_is_solvable_and_unique(self):
        for cid, (data, files) in self.cases.items():
            votes = solve(files)
            culprit = PROJECT_BY_NAME[data["culprit"]]
            winners = [p for p, n in votes.items() if n >= 2]
            self.assertEqual(winners, [culprit], f"{cid}: votes={dict(votes)}")
            # a decoy project never gets two independent confirmations
            for p, n in votes.items():
                if p != culprit:
                    self.assertLess(n, 2, cid)

    def test_extra_difficulty_layers_present(self):
        for cid, (data, files) in self.cases.items():
            access, auth, audit = files["access_history.log"], files["system_auth_matrix.log"], files["future_audit.log"]
            incident = files["incident_report.txt"]
            # terminal codes in audit/auth, names in access/incident, registry maps them
            self.assertRegex(audit, r"NODE N-\d{4}", cid)
            self.assertNotRegex(audit, r"NODE (Terminal|Console|Archive|Frequency|Anchor|Filter|Sync|Transit)", cid)
            self.assertIn("TERMINAL REGISTRY", access, cid)
            self.assertRegex(auth, r"CLOCK OFFSET: \+\d+ s", cid)
            # decoys: an earlier change by another project at the incident terminal and a later mitigation hold
            self.assertIn("mitigation hold", audit, cid)
            self.assertIn("mitigation hold", incident, cid)
            roots = re.findall(r"\| AUTHENTICATED \| ROOT_WRITE$", access, re.M)
            self.assertGreaterEqual(len(roots), 3 if "LOG BUFFER OVERFLOW" in access else 4, cid)
            self.assertIn("DENIED", access, cid)

    def test_no_file_names_the_culprit_outright(self):
        for cid, (data, files) in self.cases.items():
            for name, text in files.items():
                self.assertNotRegex(text.lower(), r"culprit|responsible project|guilty", f"{cid}/{name}")

    def test_old_evidence_is_gone(self):
        for folder in CASES_DIR.glob("R2-*"):
            names = {p.name for p in folder.iterdir()}
            self.assertFalse(any(n.startswith(("alpha_", "beta_", "gamma_")) for n in names), folder.name)
            self.assertFalse(any(n.startswith("future_") and n != "future_audit.log" for n in names), folder.name)


class LeakCheckTests(unittest.TestCase):
    def test_leak_check_is_sentence_level(self):
        from backend.app.services.round2_service import _leaks_culprit

        name, uid = "Project Alpha", "ALPHA"
        # a bare mention of the project is fine: the logs mention every project
        self.assertFalse(_leaks_culprit("The registry lists Project Alpha, Beta and Gamma credentials.", name, uid))
        self.assertFalse(_leaks_culprit("Check which credential applied the change. Alpha appears in the registry.", name, uid))
        # an accusation that pairs the project with blame is not
        self.assertTrue(_leaks_culprit("Project Alpha is the one responsible for the purge.", name, uid))
        self.assertTrue(_leaks_culprit("It was Alpha.", name, uid))


if __name__ == "__main__":
    unittest.main(verbosity=2)
