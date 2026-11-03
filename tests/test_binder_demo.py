"""Exercise the actual synthetic workflow and reject corrupted output files."""
import importlib.util
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "cdss-ab/scripts/run_binder_demo.py"
spec = importlib.util.spec_from_file_location("binder_demo", SCRIPT)
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


class BinderDemoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        cls.reference_before = demo.hashes(demo.FIXTURE)
        cls.output = cls.root / "complete"
        cls.result = subprocess.run([sys.executable, str(SCRIPT), "--output-dir", str(cls.output)],
                                    capture_output=True, text=True)
        if cls.result.returncode:
            raise RuntimeError(cls.result.stdout + cls.result.stderr)
        cls.reference, cls.strict = demo.load_reference()

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=self.root)
        self.run = Path(self.directory.name) / "run"
        shutil.copytree(self.output / "run-1", self.run)

    def tearDown(self):
        self.assertEqual(demo.hashes(demo.FIXTURE), self.reference_before)
        self.directory.cleanup()

    def verify(self):
        return demo.verify_run(self.run, self.reference, self.strict)

    def test_full_run_verifies_two_runs_and_reports_scope(self):
        self.assertEqual(self.result.returncode, 0)
        self.assertIn("PASS CROSS-PLATFORM", self.result.stdout)
        self.assertIn("does not certify 22-file byte equality", self.result.stdout)
        self.assertIn("No reference was regenerated", self.result.stdout)
        self.assertEqual(len(self.verify()), 22)
        self.assertEqual(demo.hashes(self.output / "run-1"), demo.hashes(self.output / "run-2"))

    def test_output_directory_cannot_be_reused(self):
        before = demo.hashes(self.output)
        repeated = subprocess.run([sys.executable, str(SCRIPT), "--output-dir", str(self.output)],
                                  capture_output=True, text=True)
        self.assertNotEqual(repeated.returncode, 0)
        self.assertIn("FAIL:", repeated.stderr)
        self.assertEqual(demo.hashes(self.output), before)

    def test_corrupted_text_is_rejected(self):
        path = self.run / "report.md"
        path.write_bytes(path.read_bytes() + b"\ncorrupted\n")
        with self.assertRaisesRegex(ValueError, "reference hash mismatch: report.md"):
            self.verify()

    def test_changed_database_value_is_rejected(self):
        # Preserve 12/8/3 counts: complete content checking must still catch this.
        with sqlite3.connect(self.run / "analysis.sqlite") as conn:
            conn.execute("UPDATE responses SET note='corrupted note' WHERE rowid=1")
        with self.assertRaisesRegex(ValueError, "SQLite schema, values"):
            self.verify()

    def test_changed_database_schema_is_rejected(self):
        with sqlite3.connect(self.run / "analysis.sqlite") as conn:
            conn.execute("CREATE TABLE unexpected (value TEXT)")
        with self.assertRaisesRegex(ValueError, "SQLite schema, values"):
            self.verify()

    def test_database_foreign_key_failure_is_rejected(self):
        with sqlite3.connect(self.run / "analysis.sqlite") as conn:
            conn.execute("UPDATE response_changes SET assignment_id='unknown' WHERE rowid=1")
        with self.assertRaisesRegex(ValueError, "foreign key check failed"):
            self.verify()

    def test_unreadable_database_is_rejected(self):
        (self.run / "analysis.sqlite").write_bytes(b"not a SQLite database")
        with self.assertRaises(sqlite3.DatabaseError):
            self.verify()

    def test_manifest_corruption_is_rejected(self):
        path = self.run / "manifest.json"
        original = path.read_text(encoding="utf-8")
        mutations = {
            "hash": lambda m: m["files"]["analysis.sqlite"].update(sha256="0" * 64),
            "size": lambda m: m["files"]["analysis.sqlite"].update(bytes=0),
            "missing file": lambda m: m["files"].pop("analysis.sqlite"),
            "extra file": lambda m: m["files"].update(unexpected={"sha256": "0" * 64, "bytes": 0}),
            "extra entry field": lambda m: m["files"]["analysis.sqlite"].update(unexpected=True),
            "script hash": lambda m: m.update(analysis_script_sha256="0" * 64),
            "metadata": lambda m: m.update(note="changed metadata"),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                value = json.loads(original)
                mutate(value)
                path.write_text(json.dumps(value), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Manifest"):
                    self.verify()

    def test_missing_or_extra_output_is_rejected(self):
        extra = self.run / "unexpected.txt"
        extra.write_text("unexpected", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Output file set"):
            self.verify()
        extra.unlink()
        (self.run / "report.md").unlink()
        with self.assertRaisesRegex(ValueError, "Output file set"):
            self.verify()

    def test_only_physical_database_layout_may_differ(self):
        database = self.run / "analysis.sqlite"
        before = demo.sha256(database)
        with sqlite3.connect(database) as conn:
            current = conn.execute("PRAGMA page_size").fetchone()[0]
            conn.execute(f"PRAGMA page_size={8192 if current != 8192 else 4096}")
            conn.execute("VACUUM")
        self.assertNotEqual(demo.sha256(database), before)
        # A stale manifest must fail even when all database content is identical.
        with self.assertRaisesRegex(ValueError, "Manifest file set"):
            self.verify()
        path = self.run / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["files"]["analysis.sqlite"] = {
            "sha256": demo.sha256(database), "bytes": database.stat().st_size}
        path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertEqual(len(self.verify()), 22)

    def test_runner_does_not_accept_other_snapshots(self):
        rejected = subprocess.run([sys.executable, str(SCRIPT), "--output-dir", str(self.root / "unused"),
                                   "--snapshot", str(demo.FIXTURE / "snapshot")],
                                  capture_output=True, text=True)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("unrecognized arguments", rejected.stderr)
        self.assertFalse((self.root / "unused").exists())


if __name__ == "__main__":
    unittest.main()
