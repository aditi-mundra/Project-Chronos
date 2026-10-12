"""
Round 1: a team's 25 items never contain the same object twice (the manifest has several
pictures of a gramophone, CRT television, 3D printer, ...), always cover all three eras,
and the Round 1 clock is 5 minutes.

Run from the project root:  python -m unittest backend.tests.test_round1_unique_items -v
Uses a throw-away SQLite file (CHRONOS_DB_PATH); the real event database is never opened.
"""

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_TMP = tempfile.mkdtemp(prefix="chronos_r1_unique_")
os.environ["CHRONOS_DB_PATH"] = str(Path(_TMP) / "chronos_test.db")
sys.path.insert(0, str(ROOT))

from backend.app.database.schema import create_tables, seed_round1_items_if_empty  # noqa: E402
from backend.app.services import round1_service  # noqa: E402

DB = os.environ["CHRONOS_DB_PATH"]


class Round1UniqueItems(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_tables()
        seed_round1_items_if_empty()
        connection = sqlite3.connect(DB)
        for team_id in range(1, 61):
            connection.execute(
                "INSERT INTO teams (id, team_name, member_1_name, member_2_name, current_state) "
                "VALUES (?, ?, 'a', 'b', 'READY')",
                (team_id, f"Team {team_id}"),
            )
        connection.commit()
        connection.close()

    def test_round_is_five_minutes(self):
        self.assertEqual(round1_service.ROUND1_DURATION_SECONDS, 5 * 60)

    def test_no_object_twice_and_all_eras_present(self):
        connection = sqlite3.connect(DB)
        connection.row_factory = sqlite3.Row
        try:
            for team_id in range(1, 61):
                items = round1_service.get_round1_items(team_id)
                self.assertIsInstance(items, list, items)
                self.assertEqual(len(items), 25)
                self.assertEqual(len({i["id"] for i in items}), 25)

                rows = connection.execute(
                    "SELECT r.item_name, r.correct_era FROM round1_team_items t "
                    "JOIN round1_items r ON r.item_id = t.item_id WHERE t.team_id = ?",
                    (team_id,),
                ).fetchall()
                names = [r["item_name"].strip().lower() for r in rows]
                self.assertEqual(len(names), len(set(names)), f"team {team_id} got a repeated object: {names}")
                self.assertEqual({r["correct_era"] for r in rows}, {"PAST", "PRESENT", "FUTURE"})
        finally:
            connection.close()

    def test_assignment_is_stable_on_reload(self):
        first = sorted(i["id"] for i in round1_service.get_round1_items(1))
        again = sorted(i["id"] for i in round1_service.get_round1_items(1))
        self.assertEqual(first, again)


if __name__ == "__main__":
    unittest.main()
