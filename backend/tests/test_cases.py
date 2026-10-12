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

CHANGES, LOGINS, KEYS, INCIDENT = "system_changes.log", "login_records.log", "security_keys.log", "incident_report.txt"
FILE_NAMES = {CHANGES, LOGINS, KEYS, INCIDENT}
PROJECT_BY_NAME = {"Project Alpha": "alpha", "Project Beta": "beta", "Project Gamma": "gamma"}
EV_BY_FILE = {
    CHANGES: "ev_changes",
    LOGINS: "ev_logins",
    KEYS: "ev_keys",
    INCIDENT: "ev_incident",
}

BADGE = re.compile(r"B-\d{4}")
CHG = re.compile(r"Change #\d{4}")
KEY = re.compile(r"Key [A-Z]+-\d{4}")
PROJECT_NAME = re.compile(r"Project (Alpha|Beta|Gamma)")


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
    the way a player has to: the badge registry (only in login_records.log), terminal codes via
    the terminal list, the key log's fast clock corrected."""
    logins, keys, changes = files[LOGINS], files[KEYS], files[CHANGES]
    to_project = {m.group(1): PROJECT_BY_NAME[m.group(2)]
                  for m in re.finditer(r"^(B-\d{4}) \| (Project \w+) \|", logins, re.M)}
    assert len(to_project) == 3, "badge registry missing"
    code_to_name = {m.group(1): m.group(2).strip()
                    for m in re.finditer(r"^(T-\d{4}) \| (.+)$", logins, re.M)}
    assert len(code_to_name) >= 5, "terminal list missing"

    om = re.search(r"^CLOCK NOTE: .*runs (\d+) seconds FAST", keys, re.M)
    assert om, "clock offset not stated"
    offset = int(om.group(1))

    # the incident change is the one a key was USED for
    um = re.search(r"^(\d\d:\d\d:\d\d) \| Key (\S+) \| USED at terminal (T-\d{4}) \| Change #(\d{4})$",
                   keys, re.M)
    assert um, "key use not found"
    t_change, key_name, node_code, chg = secs(um.group(1)) - offset, um.group(2), um.group(3), um.group(4)
    node = code_to_name[node_code]

    m = re.search(rf"^(\d\d:\d\d:\d\d) \| Change #{chg} \| Terminal (T-\d{{4}})\n.+\n  Result: APPLIED \| Badge: (.+)$",
                  changes, re.M)
    assert m, "incident change not found"
    assert secs(m.group(1)) == t_change, "key log clock offset does not line up with the change log"
    assert m.group(2) == node_code

    votes = Counter()
    # 1. the change log names the badge (unless it was run by a scheduled task)
    b = BADGE.search(m.group(3))
    if b:
        votes[to_project[b.group(0)]] += 1
    # 2. a FULL CONTROL login at that terminal in the minute before the change
    for sm in re.finditer(r"^(\d\d:\d\d:\d\d) \| Badge (B-\d{4}) \| (.+?) \| LOGGED IN \| FULL CONTROL$",
                          logins, re.M):
        if sm.group(3).strip() == node and 0 < t_change - secs(sm.group(1)) <= 60:
            votes[to_project[sm.group(2)]] += 1
    # 3. the key used for that change was armed by a badge (not a standing authorization)
    am = re.search(rf"^\d\d:\d\d:\d\d \| Key {re.escape(key_name)} \| ARMED by badge (B-\d{{4}}) ", keys, re.M)
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
                for pattern in (BADGE, CHG, KEY):
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
            logins, keys, changes = files[LOGINS], files[KEYS], files[CHANGES]
            incident = files[INCIDENT]
            # terminal codes in changes/keys, names in logins/incident, the terminal list maps them
            self.assertRegex(changes, r"Terminal T-\d{4}", cid)
            self.assertNotRegex(changes, r"Terminal (Node|Console|Archive|Frequency|Anchor|Filter|Sync|Transit)", cid)
            self.assertIn("TERMINAL LIST", logins, cid)
            self.assertRegex(keys, r"runs \d+ seconds FAST", cid)
            # decoys: a later mitigation hold by another project and refused / extra FULL CONTROL logins
            self.assertIn("mitigation hold", changes, cid)
            self.assertIn("mitigation hold", incident, cid)
            full = re.findall(r"\| LOGGED IN \| FULL CONTROL$", logins, re.M)
            self.assertGreaterEqual(len(full), 3 if "RECORDS LOST" in logins else 4, cid)
            self.assertIn("REFUSED", logins, cid)

    def test_no_single_file_is_enough(self):
        """The badge registry is the only place that links a badge to a project, so the
        change / key / incident files cannot name a project on their own, and the login file
        alone does not say which login is the incident."""
        for cid, (data, files) in self.cases.items():
            for name in (CHANGES, KEYS, INCIDENT):
                self.assertIsNone(PROJECT_NAME.search(files[name]), f"{cid}/{name} names a project")
                self.assertNotIn("BADGE REGISTRY (which", files[name], cid)
            self.assertIn("BADGE REGISTRY", files[LOGINS], cid)
            # login_records alone: at least two different projects have FULL CONTROL logins
            registry = {m.group(1): m.group(2) for m in
                        re.finditer(r"^(B-\d{4}) \| (Project \w+) \|", files[LOGINS], re.M)}
            holders = {registry[m.group(1)] for m in
                       re.finditer(r"Badge (B-\d{4}) \|.*\| LOGGED IN \| FULL CONTROL$", files[LOGINS], re.M)}
            self.assertGreaterEqual(len(holders), 2, f"{cid}: login_records alone points at one project")
            # and Round 3 evidence is split the same way: only the logins item has the registry
            c3 = next(c for c in self.r3 if c["r2_case_id"] == cid)
            for e in c3["evidence_pool"]:
                has_registry = "registry" in e["description"].lower()
                self.assertEqual(has_registry, e["source_file"] == LOGINS, f"{cid}: {e['id']}")
                if e["source_file"] != LOGINS:
                    self.assertIsNone(PROJECT_NAME.search(e["description"] + e["label"]), f"{cid}: {e['id']}")
            for cand in c3["candidates"]:
                self.assertNotRegex(json.dumps(cand), r"B-\d{4}")

    def test_plain_language(self):
        """No kernel / credential-hash / scope jargon in what players read."""
        banned = re.compile(r"ROOT_WRITE|READ_ONLY|[Cc]redential|CREDENTIAL|0x[0-9A-F]{4}|NODE N-|CHG-|KEY-[A-Z]+-|AUTHENTICATED|s-\d{4}")
        for cid, (data, files) in self.cases.items():
            for name, text in files.items():
                self.assertIsNone(banned.search(text), f"{cid}/{name}: {banned.search(text)}")

    def test_no_file_names_the_culprit_outright(self):
        for cid, (data, files) in self.cases.items():
            for name, text in files.items():
                self.assertNotRegex(text.lower(), r"culprit|responsible project|guilty", f"{cid}/{name}")

    def test_old_evidence_is_gone(self):
        for folder in CASES_DIR.glob("R2-*"):
            names = {p.name for p in folder.iterdir()}
            self.assertFalse(any(n.startswith(("alpha_", "beta_", "gamma_")) for n in names), folder.name)
            self.assertFalse(any(n.startswith("future_") for n in names), folder.name)
            self.assertFalse({"future_audit.log", "access_history.log", "system_auth_matrix.log"} & names, folder.name)


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
