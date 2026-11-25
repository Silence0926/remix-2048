"""Integration tests for the lightweight leaderboard HTTP API."""

import json
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import leaderboard_server as api


class LeaderboardApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        api.DB_FILE = os.path.join(cls.temp_dir.name, "test.sqlite3")
        api.LEGACY_JSON_FILE = os.path.join(cls.temp_dir.name, "missing-legacy.json")
        api.CORS_ALLOW_ORIGINS = {"https://silence0926.github.io"}
        api.ADMIN_API_KEY = ""
        api.LAST_POST_BY_CLIENT.clear()
        api.ensure_db()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), api.LeaderboardHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = "http://127.0.0.1:{}/api".format(cls.server.server_address[1])

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)
        cls.temp_dir.cleanup()

    def request_json(self, path, method="GET", payload=None, headers=None):
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            self.base_url + path,
            data=body,
            method=method,
            headers=headers or {},
        )
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            return error.code, json.loads(error.read().decode("utf-8"))

    def test_health_reports_database_ready(self):
        status, payload = self.request_json("/health")
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["database"], "ok")

    def test_score_submission_appears_on_leaderboard(self):
        status, payload = self.request_json(
            "/score",
            method="POST",
            payload={
                "name": "Unit Tester",
                "score": 4096,
                "mode": "Classic",
                "size": 4,
                "steps": 25,
                "dailySeed": api.today_seed(),
                "clientId": "unit_test_client",
                "at": "2000-01-01T00:00:00Z",
            },
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])

        board_status, board = self.request_json("/leaderboard?scope=all&limit=5")
        self.assertEqual(board_status, 200)
        self.assertEqual(board["entries"][0]["score"], 4096)
        self.assertNotEqual(board["entries"][0]["at"], "2000-01-01T00:00:00Z")

    def test_invalid_numeric_score_is_rejected(self):
        status, payload = self.request_json(
            "/score",
            method="POST",
            payload={"score": "not-a-number", "clientId": "bad_payload"},
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(status, 400)
        self.assertFalse(payload["ok"])

    def test_unapproved_origin_is_rejected(self):
        status, payload = self.request_json(
            "/health",
            headers={"Origin": "https://untrusted.example"},
        )
        self.assertEqual(status, 403)
        self.assertFalse(payload["ok"])


if __name__ == "__main__":
    unittest.main()
