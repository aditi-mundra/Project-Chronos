"""config.setting(): .env parsing, including the BOM that Notepad / PowerShell put at the start."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app import config  # noqa: E402


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self._saved = config._ENV_FILES
        self._tmp = tempfile.mkdtemp(prefix="chronos_cfg_")
        os.environ.pop("CFG_TEST_FIRST", None)
        os.environ.pop("CFG_TEST_KEYS", None)

    def tearDown(self):
        config._ENV_FILES = self._saved
        os.environ.pop("CFG_TEST_FIRST", None)
        os.environ.pop("CFG_TEST_KEYS", None)

    def _write(self, data: bytes) -> None:
        path = Path(self._tmp) / ".env"
        path.write_bytes(data)
        config._ENV_FILES = (path,)

    def test_first_line_is_read_when_the_file_starts_with_a_bom(self):
        self._write(b"\xef\xbb\xbfCFG_TEST_FIRST=secret-one\r\nCFG_TEST_KEYS=a,b\r\n")
        self.assertEqual(config.setting("CFG_TEST_FIRST"), "secret-one")
        self.assertEqual(config.setting("CFG_TEST_KEYS"), "a,b")

    def test_plain_file_comments_and_quotes(self):
        self._write(b"# comment\nCFG_TEST_FIRST=\"quoted\"\n\nCFG_TEST_KEYS='x,y'\n")
        self.assertEqual(config.setting("CFG_TEST_FIRST"), "quoted")
        self.assertEqual(config.setting("CFG_TEST_KEYS"), "x,y")

    def test_environment_wins_over_the_file(self):
        self._write(b"CFG_TEST_FIRST=from-file\n")
        os.environ["CFG_TEST_FIRST"] = "from-env"
        self.assertEqual(config.setting("CFG_TEST_FIRST"), "from-env")

    def test_missing_value_gives_the_default(self):
        self._write(b"OTHER=1\n")
        self.assertEqual(config.setting("CFG_TEST_FIRST", "dflt"), "dflt")


if __name__ == "__main__":
    unittest.main()
