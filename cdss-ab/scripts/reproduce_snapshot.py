"""Run a snapshot twice and verify every file against each other and a trusted baseline."""
import argparse
import hashlib
import json
import platform
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "cdss-ab/examples/reproducibility"


def hashes(directory):
    return {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(directory.rglob("*")) if p.is_file()}


def compare(actual, expected, label):
    failed = False
    for name in sorted(set(actual) | set(expected)):
        ok = name in actual and name in expected and actual[name] == expected[name]
        print(f"{'PASS' if ok else 'FAIL'} {label} {name} sha256={actual.get(name, 'MISSING')}", flush=True)
        failed |= not ok
    if failed:
        raise ValueError(f"{label}: file set or SHA-256 mismatch")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=FIXTURE / "snapshot")
    parser.add_argument("--reference", type=Path, default=FIXTURE / "reference-sha256.json")
    parser.add_argument("--output-dir", type=Path, required=True, help="New directory; never overwritten")
    parser.add_argument("--seed", type=int, default=20261019)
    parser.add_argument("--bootstrap-reps", type=int, default=1000)
    parser.add_argument("--generated-at", default="2026-01-01T00:00:00+00:00",
                        help="Fixed provenance time, not actual execution time")
    args = parser.parse_args()
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    source = args.snapshot.resolve()
    output = args.output_dir.resolve()
    if source == output or source in output.parents or output in source.parents:
        parser.error("Output and snapshot directories must be separate")
    before = hashes(source)
    if set(before) != {"study.json", "responses.json", "answer_source.csv"}:
        parser.error("Snapshot must contain exactly study.json, responses.json and answer_source.csv")
    import numpy
    if numpy.__version__ != "2.2.6":
        parser.error("Install requirements.lock: NumPy 2.2.6 is required")
    output.mkdir(parents=True, exist_ok=False)
    print(f"Execution time (not in hashed outputs): {datetime.now(timezone.utc).isoformat()}", flush=True)
    print(f"Python={platform.python_version()} NumPy={numpy.__version__} SQLite={sqlite3.sqlite_version} OS={platform.system()} arch={platform.machine()}", flush=True)
    print(f"seed={args.seed} bootstrap_reps={args.bootstrap_reps} explicit_provenance_time={args.generated_at}", flush=True)
    runs = []
    for number in (1, 2):
        run = output / f"run-{number}"
        shutil.copytree(source, run / "snapshot")
        proc = subprocess.run([sys.executable, str(ROOT / "cdss-ab/scripts/analyze_real_doctor_collection.py"),
                               "--snapshot-dir", str(run), "--seed", str(args.seed),
                               "--bootstrap-reps", str(args.bootstrap_reps), "--generated-at", args.generated_at],
                              capture_output=True, text=True)
        if proc.returncode:
            print(proc.stdout, proc.stderr)
            raise RuntimeError(f"Analysis run {number} failed: {proc.returncode}")
        summary = json.loads((run / "summary.json").read_text())
        with sqlite3.connect(f"{(run / 'analysis.sqlite').as_uri()}?mode=ro", uri=True) as conn:
            count, correct = conn.execute("SELECT COUNT(*), SUM(r.doctor_answer_idx=k.gold_answer_idx) FROM responses r JOIN assignments a ON a.assignment_id=r.assignment_id JOIN answer_keys k ON k.study_id=a.study_id AND k.question_id=a.question_id").fetchone()
        if (count, correct) != (summary['overall']['n'], summary['overall']['correct']):
            raise ValueError("Python/SQL count mismatch")
        print(f"PASS run-{number} Python/SQL responses={count} correct={correct}", flush=True)
        compare(hashes(run / "snapshot"), before, f"run-{number} input-preservation")
        runs.append(hashes(run))
    compare(hashes(source), before, "source-preservation")
    compare(runs[0], runs[1], "repeat")
    compare(runs[0], reference, "reference-run-1")
    compare(runs[1], reference, "reference-run-2")
    print(f"PASS ALL: {len(runs[0])} files per run, including SQLite and manifest; two runs match the reference byte-for-byte.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
