"""Exercise the actual temporary demo server through its HTTP interface."""
import csv
from http.cookiejar import CookieJar
import importlib.util
import io
import json
from pathlib import Path
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import build_opener, HTTPCookieProcessor, Request


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("interactive_demo", ROOT / "cdss-ab/scripts/serve_interactive_demo.py")
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


class InteractiveDemoTest(unittest.TestCase):
    def setUp(self):
        self.context = demo.demo_server(0)
        self.server = self.context.__enter__()
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.cookies = CookieJar()
        self.client = build_opener(HTTPCookieProcessor(self.cookies))

    def tearDown(self):
        runtime = self.server.data_path.parent
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.context.__exit__(None, None, None)
        self.assertFalse(runtime.exists(), "The temporary session must be removed after shutdown")

    def request(self, path, payload=None, method=None, expected=200):
        request = Request(self.base + path, method=method, headers={"Content-Type": "application/json"},
                          data=json.dumps(payload).encode() if payload is not None else None)
        try:
            response = self.client.open(request, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            self.assertEqual(response.status, expected, path)
            content = response.read()
            content_type = response.headers.get("Content-Type", "")
            return json.loads(content) if content_type.startswith("application/json;") else content

    def login(self, username="doctor", password="demo", expected=200):
        return self.request("/api/login", {"username": username, "password": password}, expected=expected)

    def test_doctor_revision_admin_summary_and_exports(self):
        self.login(password="wrong", expected=401)
        self.assertEqual(self.login()["user"]["role"], "doctor")
        study = self.request("/api/study")
        assignments = study["assignments"]
        self.assertEqual(len(assignments), 3)
        self.assertEqual([row["condition"] for row in assignments], ["T0", "T1", "T2"])
        self.assertIsNone(assignments[0]["cdss"])
        self.assertEqual(assignments[1]["cdss"]["cdss_answer_idx"], "B")
        self.assertEqual(assignments[2]["cdss"]["cdss_answer_idx"], "B")
        self.assertNotIn("source_dataset", study)
        self.assertNotIn("gold_answer_idx", json.dumps(study))
        self.request("/api/admin/stats", expected=403)
        self.request("/api/admin/export.csv", expected=403)
        self.request("/api/responses", {"response": {"assignment_id": "OTHER-Q1", "doctor_answer_idx": "A"}}, expected=403)
        for row, answer in zip(assignments, ("A", "B", "B")):
            self.request("/api/responses", {"response": {
                "assignment_id": row["assignment_id"], "doctor_answer_idx": answer,
                "response_time_seconds": 5, "updated_at": "2026-01-01T00:00:00Z",
            }})
        self.request("/api/responses", {"response": {
            "assignment_id": assignments[2]["assignment_id"], "doctor_answer_idx": "A",
            "response_time_seconds": 10, "updated_at": "2026-01-01T00:00:05Z",
            "changes": [{"from": "B", "to": "A", "changed_at": "2026-01-01T00:00:05Z"}],
        }})
        responses = self.request("/api/responses")["responses"]
        self.assertEqual(len(responses), 3, "A revision must update, not duplicate, a response")
        self.assertEqual(len(responses[2]["changes"]), 1)
        self.request("/api/logout", {})
        self.request("/api/responses", expected=401)
        self.assertEqual(self.login("admin")["user"]["role"], "admin")
        stats = self.request("/api/admin/stats")
        self.assertEqual(stats["batch"]["response_count"], 3)
        self.assertEqual(stats["batch"]["completion_rate"], 1)
        self.assertEqual(stats["metrics"]["overall"]["correct"], 3)
        self.assertEqual(stats["metrics"]["by_condition"]["T2"]["matches_cdss"], 0)
        csv_rows = list(csv.DictReader(io.StringIO(self.request("/api/admin/export.csv").decode("utf-8-sig"))))
        jsonl_rows = [json.loads(line) for line in self.request("/api/admin/export.jsonl").decode().splitlines()]
        self.assertEqual(len(csv_rows), 3)
        self.assertEqual(len(jsonl_rows), 3)
        self.assertEqual([row["gold_answer_idx"] for row in jsonl_rows], ["A", "B", "A"])
        self.assertEqual(csv_rows[2]["change_count"], "1")
        self.assertEqual(jsonl_rows[2]["change_count"], 1)
        self.request("/api/responses", {"response": {}}, expected=403)

    def test_private_paths_and_authentication_boundaries(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        self.assertNotIn(demo.APP_ROOT, self.server.accounts_path.parents)
        self.assertEqual(self.server.accounts_path.parent.stat().st_mode & 0o777, 0o700)
        accounts = json.loads(self.server.accounts_path.read_text())["accounts"]
        self.assertEqual({row["username"] for row in accounts}, {"doctor", "admin"})
        self.assertTrue(all(row["password_hash"].startswith("pbkdf2_sha256$") for row in accounts))
        self.assertEqual(self.request("/api/health")["response_count"], 0)
        for path in ("/api/study", "/api/responses", "/api/admin/stats", "/api/admin/export.csv", "/api/admin/export.jsonl"):
            self.request(path, expected=401)
        for path in ("/server.py", "/data/accounts.json", "/runtime/responses.json", "/../examples/interactive-demo/study.json",
                     "/%2e%2e/examples/interactive-demo/study.json", "/index.html/../server.py",
                     "/accounts.json", "/answer_source.csv", str(self.server.accounts_path)):
            self.request(path, expected=404)
        self.assertIn(b"doctor", self.request("/"))
        self.assertIn(b"admin", self.request("/index.html"))
        self.assertIn(b"api/login", self.request("/app.js?v=test"))
        self.assertIn(b".login-card", self.request("/styles.css"))


if __name__ == "__main__":
    unittest.main()
