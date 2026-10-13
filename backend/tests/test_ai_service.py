"""
Round 2 analyst AI: key pool, model cascade and provider fall-over (ai_service.py).

Everything runs against a local fake Groq / Gemini server, so no real key or network is used.

Run from the project root:  python -m unittest backend.tests.test_ai_service -v
"""

import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# The service reads its settings through ai_service.setting (environment, then .env). The tests
# replace that with this dict, so neither a real .env key nor the machine's environment can leak
# in and no test can ever reach a real provider.
ENV = {}

for name in ("GROQ_API_KEYS", "GROQ_API_KEY", "GROQ_MODEL", "GEMINI_API_KEY", "GEMINI_API_KEYS",
             "GEMINI_MODEL", "CHRONOS_AI_DISABLED", "GROQ_API_URL", "GEMINI_API_URL", "AI_TOTAL_TIMEOUT"):
    ENV[name] = ""

from backend.app.services import ai_service  # noqa: E402

ai_service.setting = lambda name, default="": (ENV.get(name) or "").strip() or default

# ---------------------------------------------------------------- fake provider
# behaviour per (provider, key, model) -> HTTP status (200 = answer), set by each test
RULES = {}
HITS = []


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _reply(self, status, body, headers=None):
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(length) or b"{}")
        if self.path.startswith("/groq"):
            provider = "groq"
            key = (self.headers.get("Authorization") or "").replace("Bearer ", "")
            model = body.get("model", "")
        else:
            provider = "gemini"
            key = self.headers.get("x-goog-api-key", "")
            model = self.path.split("/models/")[-1].split(":")[0]
        HITS.append((provider, key, model))
        status = RULES.get((provider, key, model), RULES.get((provider, key, "*"), RULES.get((provider, "*", model), 200)))
        if status == 200:
            text = f"answer from {provider}/{model} via {key}"
            if provider == "groq":
                return self._reply(200, {"choices": [{"message": {"content": text}}]})
            return self._reply(200, {"candidates": [{"content": {"parts": [{"text": text}]}}]})
        if status == 429:
            return self._reply(429, {"error": "rate"}, {"Retry-After": "30"})
        if status == 400:
            return self._reply(400, {"error": {"message": f"The model `{model}` has been decommissioned"}})
        if status == 4001:  # Google: bad key is HTTP 400, not 401
            return self._reply(400, {"error": {"status": "INVALID_ARGUMENT", "message": "API key not valid. Please pass a valid API key."}})
        return self._reply(status, {"error": f"status {status}"})


class AiServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{cls.server.server_port}"
        ENV["GROQ_API_URL"] = f"{base}/groq/chat"
        ENV["GEMINI_API_URL"] = f"{base}/gemini/models/{{model}}:generateContent"
        ENV["GROQ_MODEL"] = "m-main"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        RULES.clear()
        HITS.clear()
        ai_service.reset_for_tests()
        for name in ("GROQ_API_KEYS", "GROQ_API_KEY", "GEMINI_API_KEY", "GEMINI_API_KEYS", "CHRONOS_AI_DISABLED"):
            ENV[name] = ""

    def ask(self, text="who did it"):
        return ai_service.ask_with_metadata("system", [], text)

    # -------------------------------------------------------------- configuration
    def test_no_keys_means_no_call(self):
        self.assertFalse(ai_service.is_configured())
        self.assertIsNone(self.ask()["reply"])
        self.assertEqual(HITS, [])

    def test_placeholders_and_duplicates_are_ignored(self):
        ENV["GROQ_API_KEYS"] = "gsk_key1_here, ,'real-1', real-1, your_key"
        ENV["GROQ_API_KEY"] = "real-2"
        self.assertEqual(ai_service.groq_keys(), ["real-1", "real-2"])

    def test_disabled_switch_never_calls(self):
        ENV["GROQ_API_KEYS"] = "k1"
        ENV["CHRONOS_AI_DISABLED"] = "1"
        self.assertIsNone(self.ask()["reply"])
        self.assertEqual(HITS, [])

    # -------------------------------------------------------------- key pool
    def test_keys_rotate_so_teams_spread_over_the_pool(self):
        ENV["GROQ_API_KEYS"] = "k1,k2,k3"
        used = []
        for i in range(6):
            self.assertIn("answer from groq", self.ask(f"question {i}")["reply"])
            used.append(HITS[-1][1])
        self.assertEqual(set(used), {"k1", "k2", "k3"})
        self.assertEqual(used[:3], sorted(used[:3], key=used[:3].index))  # round robin, no key skipped
        self.assertEqual(len(set(used[:3])), 3)

    def test_rate_limited_key_fails_over_to_the_next_key(self):
        ENV["GROQ_API_KEYS"] = "k1,k2"
        RULES[("groq", "k1", "*")] = 429
        first = self.ask("q1")
        self.assertEqual(first["provider"], "groq")
        self.assertTrue(first["reply"].endswith("via k2"))
        # k1 now rests: the next questions go straight to k2
        HITS.clear()
        self.ask("q2")
        self.ask("q3")
        self.assertEqual({h[1] for h in HITS}, {"k2"})

    def test_rejected_key_is_parked(self):
        ENV["GROQ_API_KEYS"] = "bad,good"
        RULES[("groq", "bad", "*")] = 401
        self.assertTrue(self.ask("q1")["reply"].endswith("via good"))
        HITS.clear()
        self.ask("q2")
        self.assertNotIn("bad", {h[1] for h in HITS})

    # -------------------------------------------------------------- model cascade
    def test_retired_model_falls_to_the_next_model_and_is_remembered(self):
        ENV["GROQ_API_KEYS"] = "k1"
        RULES[("groq", "*", "m-main")] = 400  # decommissioned
        out = self.ask("q1")
        self.assertEqual(out["model"], "openai/gpt-oss-120b")
        HITS.clear()
        self.ask("q2")
        self.assertNotIn("m-main", {h[2] for h in HITS})  # parked, not retried

    def test_empty_answer_moves_to_the_next_model(self):
        ENV["GROQ_API_KEYS"] = "k1"

        calls = []
        original = ai_service._CALLS["groq"]

        def fake(key, model, *a, **k):
            calls.append(model)
            return "" if model == "m-main" else f"text from {model}"

        ai_service._CALLS["groq"] = fake
        try:
            out = self.ask("q1")
        finally:
            ai_service._CALLS["groq"] = original
        self.assertEqual(calls[0], "m-main")
        self.assertEqual(out["reply"], f"text from {calls[1]}")

    # -------------------------------------------------------------- providers
    def test_gemini_answers_when_every_groq_key_fails(self):
        ENV["GROQ_API_KEYS"] = "g1,g2"
        ENV["GEMINI_API_KEY"] = "gem1"
        RULES[("groq", "g1", "*")] = 429
        RULES[("groq", "g2", "*")] = 401
        out = self.ask()
        self.assertEqual(out["provider"], "gemini")
        self.assertTrue(out["reply"].endswith("via gem1"))

    def test_google_style_invalid_key_is_parked_not_blamed_on_the_model(self):
        ENV["GEMINI_API_KEYS"] = "badgem,goodgem"
        RULES[("gemini", "badgem", "*")] = 4001
        out = self.ask("q1")
        self.assertTrue(out["reply"].endswith("via goodgem"))
        self.assertEqual(ai_service.status()["models_resting"], [])  # no model was parked
        HITS.clear()
        self.ask("q2")
        self.assertNotIn("badgem", {h[1] for h in HITS})

    def test_everything_down_returns_nothing(self):
        ENV["GROQ_API_KEYS"] = "g1"
        ENV["GEMINI_API_KEY"] = "gem1"
        RULES[("groq", "g1", "*")] = 500
        RULES[("gemini", "gem1", "*")] = 500
        out = self.ask()
        self.assertIsNone(out["reply"])
        self.assertEqual(ai_service.status()["stats"]["all_failed"], 1)

    def test_same_question_is_served_from_the_cache(self):
        ENV["GROQ_API_KEYS"] = "k1"
        a = self.ask("What does the key log say?")
        hits_after_first = len(HITS)
        b = self.ask("what does the key log say?  ")
        self.assertEqual(a["reply"], b["reply"])
        self.assertEqual(len(HITS), hits_after_first)

    # -------------------------------------------------------------- safety
    def test_status_never_contains_a_key(self):
        ENV["GROQ_API_KEYS"] = "gsk_SECRETSECRET1,gsk_SECRETSECRET2"
        ENV["GEMINI_API_KEY"] = "AIzaSECRETGEM"
        RULES[("groq", "gsk_SECRETSECRET1", "*")] = 401
        self.ask()
        dump = json.dumps(ai_service.status())
        for secret in ("SECRETSECRET", "AIzaSECRET"):
            self.assertNotIn(secret, dump)
        groq = next(p for p in ai_service.status()["providers"] if p["name"] == "groq")
        self.assertEqual(groq["keys"], 2)
        self.assertEqual(groq["keys_resting"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
