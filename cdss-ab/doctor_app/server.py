from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import io
import json
import mimetypes
import secrets
import sys
import tempfile
import time
from contextlib import contextmanager
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


APP_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = APP_ROOT.parent
DEFAULT_DATA_PATH = APP_ROOT / "data" / "pilot_study_12q.json"
DEFAULT_ACCOUNTS_PATH = APP_ROOT / "data" / "doctor_accounts.demo.json"
RUNTIME_DIR = APP_ROOT / "runtime"
DEFAULT_RESPONSES_PATH = RUNTIME_DIR / "responses.json"
DEFAULT_BATCH_REGISTRY_PATH = RUNTIME_DIR / "batch_registry.json"
SESSION_COOKIE = "cdss_session"
SESSION_TTL_SECONDS = 12 * 60 * 60
DEFAULT_TIME_LIMIT_SECONDS = 90 * 60
VALID_OPTIONS = {"A", "B", "C", "D"}
CONDITIONS = ("T0", "T1", "T2")
SPEED_WARNING_THRESHOLD_SECONDS = 3


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent, suffix=".tmp") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        temp_path = Path(file.name)
    temp_path.replace(path)


@contextmanager
def responses_store_lock(responses_path: Path):
    lock_path = responses_path.with_name(f"{responses_path.name}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = lock_path.open("a+b")
    try:
        if sys.platform == "win32":
            import msvcrt

            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        try:
            if sys.platform == "win32":
                import msvcrt

                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        finally:
            lock_file.close()


def response_key(row: dict[str, Any]) -> str:
    return f"{row.get('doctor_id', '')}:{row.get('assignment_id', '')}"


def resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve()


def normalize_username(value: Any) -> str:
    return str(value or "").strip().lower()


def verify_password(account: dict[str, Any], password: str) -> bool:
    password_hash = str(account.get("password_hash") or "")
    if password_hash.startswith("pbkdf2_sha256$"):
        try:
            _, iterations_text, salt, expected = password_hash.split("$", 3)
            iterations = int(iterations_text)
            actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations).hex()
        except Exception:
            return False
        return hmac.compare_digest(actual, expected)

    expected_password = str(account.get("password") or "")
    return bool(expected_password) and hmac.compare_digest(
        password.encode("utf-8"),
        expected_password.encode("utf-8"),
    )


def doctor_by_id(study: dict[str, Any], doctor_id: str) -> dict[str, Any] | None:
    for doctor in study.get("doctors", []):
        if str(doctor.get("doctor_id")) == doctor_id:
            return doctor
    return None


def is_admin(account: dict[str, Any]) -> bool:
    return str(account.get("role") or "").lower() == "admin"


def assignments_for_doctor(study: dict[str, Any], doctor_id: str) -> list[dict[str, Any]]:
    rows = [row for row in study.get("assignments", []) if str(row.get("doctor_id")) == doctor_id]
    return sorted(rows, key=lambda item: int(item.get("display_order") or 0))


def public_assignment(assignment: dict[str, Any]) -> dict[str, Any]:
    question = dict(assignment.get("question") or {})
    question.pop("difficulty", None)
    question.pop("difficulty_level", None)
    return {
        "assignment_id": assignment.get("assignment_id", ""),
        "doctor_id": assignment.get("doctor_id", ""),
        "question_id": assignment.get("question_id", ""),
        "condition": assignment.get("condition", ""),
        "stage_block": assignment.get("stage_block", ""),
        "display_order": assignment.get("display_order", ""),
        "block_order": assignment.get("block_order", ""),
        "session_id": assignment.get("session_id", ""),
        "question": question,
        "cdss": assignment.get("cdss"),
    }


def public_study_for_doctor(study: dict[str, Any], account: dict[str, Any]) -> dict[str, Any]:
    doctor_id = str(account["doctor_id"])
    assigned = assignments_for_doctor(study, doctor_id)
    return {
        "study_id": study.get("study_id", ""),
        "batch_id": study.get("batch_id", study.get("study_id", "")),
        "assignments": [public_assignment(row) for row in assigned],
        "summary": {
            "assignment_rows": len(assigned),
            "time_limit_seconds": int(study.get("time_limit_seconds") or DEFAULT_TIME_LIMIT_SECONDS),
        },
        "current_user": {
            "doctor_id": doctor_id,
        },
    }


def read_source_answers(study: dict[str, Any]) -> dict[str, dict[str, Any]]:
    source_dataset = str(study.get("source_dataset") or "")
    if not source_dataset:
        return {}
    source_path = resolve_path(source_dataset)
    if not source_path.exists():
        return {}

    answers: dict[str, dict[str, Any]] = {}
    if source_path.suffix.lower() == ".jsonl":
        with source_path.open("r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                row = json.loads(line)
                qid = str(row.get("qid") or row.get("question_id") or "")
                if qid:
                    answers[qid] = row
    elif source_path.suffix.lower() == ".csv":
        import csv as _csv
        with source_path.open("r", encoding="utf-8-sig", newline="") as file:
            for row in _csv.DictReader(file):
                qid = str(row.get("qid") or row.get("question_id") or "")
                if qid:
                    answers[qid] = row
    return answers


def pct(numerator: int | float, denominator: int | float) -> float | None:
    if not denominator:
        return None
    return round(float(numerator) / float(denominator), 4)


def rate_delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return round(left - right, 4)


def summarize_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    correct = sum(1 for row in rows if row.get("doctor_is_correct") is True)
    matches_cdss_rows = [row for row in rows if row.get("matches_cdss") is not None]
    matches_cdss = sum(1 for row in matches_cdss_rows if row.get("matches_cdss") is True)
    times = [int(row.get("response_time_seconds") or 0) for row in rows]
    total_time = sum(times)
    return {
        "responses": total,
        "correct": correct,
        "accuracy": pct(correct, total),
        "matches_cdss": matches_cdss,
        "matches_cdss_rate": pct(matches_cdss, len(matches_cdss_rows)),
        "avg_response_time_seconds": round(total_time / total, 1) if total else None,
        "min_response_time_seconds": min(times) if times else None,
    }


def grouped_summary(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        buckets.setdefault(str(row.get(key) or ""), []).append(row)
    return [
        {key: bucket_key, **summarize_group(bucket_rows)}
        for bucket_key, bucket_rows in sorted(buckets.items())
    ]


def condition_summaries(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        condition: summarize_group([row for row in rows if row.get("condition") == condition])
        for condition in CONDITIONS
    }


EXPORT_COLUMNS = [
    "record_id",
    "study_id",
    "batch_id",
    "assignment_id",
    "doctor_id",
    "doctor_level",
    "question_id",
    "difficulty",
    "condition",
    "stage_block",
    "session_id",
    "display_order",
    "block_order",
    "has_cdss",
    "cdss_answer_idx",
    "doctor_answer_idx",
    "gold_answer_idx",
    "doctor_is_correct",
    "matches_cdss",
    "response_time_seconds",
    "note",
    "change_count",
    "updated_at",
]


def score_responses(study: dict[str, Any], responses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    assignments = study.get("assignments", [])
    assignment_by_id = {str(row.get("assignment_id")): row for row in assignments}
    answers_by_qid = read_source_answers(study)
    batch_id = str(study.get("batch_id", study.get("study_id", "")))
    t1_gold_by_qid = {
        str(row.get("question_id")): str((row.get("cdss") or {}).get("cdss_answer_idx") or "").strip().upper()
        for row in assignments
        if row.get("condition") == "T1" and (row.get("cdss") or {}).get("cdss_answer_idx")
    }

    scored: list[dict[str, Any]] = []
    for response in responses:
        assignment = assignment_by_id.get(str(response.get("assignment_id") or ""))
        if not assignment:
            continue
        qid = str(assignment.get("question_id") or response.get("question_id") or "")
        answer = answers_by_qid.get(qid, {})
        gold = str(answer.get("answer_idx") or t1_gold_by_qid.get(qid) or "").strip().upper()
        doctor_answer = str(response.get("doctor_answer_idx") or "").strip().upper()
        condition = str(assignment.get("condition") or response.get("condition") or "")
        cdss_answer = str((assignment.get("cdss") or {}).get("cdss_answer_idx") or response.get("cdss_answer_idx") or "")
        scored.append(
            {
                **response,
                "batch_id": response.get("batch_id") or batch_id,
                "study_id": response.get("study_id") or study.get("study_id", ""),
                "assignment_id": assignment.get("assignment_id", ""),
                "doctor_id": assignment.get("doctor_id", response.get("doctor_id", "")),
                "doctor_level": assignment.get("doctor_level", response.get("doctor_level", "")),
                "question_id": qid,
                "difficulty": assignment.get("difficulty", response.get("difficulty", "")),
                "condition": condition,
                "gold_answer_idx": gold,
                "doctor_answer_idx": doctor_answer,
                "doctor_is_correct": bool(gold and doctor_answer == gold),
                "cdss_answer_idx": cdss_answer,
                "matches_cdss": doctor_answer == cdss_answer if cdss_answer else None,
                "change_count": len(response.get("changes") or []),
            }
        )
    return scored


def export_row_value(row: dict[str, Any], column: str) -> Any:
    value = row.get(column)
    if column in {"has_cdss", "doctor_is_correct", "matches_cdss"}:
        if value is None:
            return ""
        return value
    if value is None:
        return ""
    return value


def build_export_csv(rows: list[dict[str, Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=EXPORT_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: export_row_value(row, column) for column in EXPORT_COLUMNS})
    return buffer.getvalue()


def build_export_jsonl(rows: list[dict[str, Any]]) -> str:
    lines = [json.dumps({column: row.get(column) for column in EXPORT_COLUMNS}, ensure_ascii=False) for row in rows]
    return "\n".join(lines) + ("\n" if lines else "")


def export_filename(study: dict[str, Any], suffix: str) -> str:
    batch_id = str(study.get("batch_id", study.get("study_id", "export")) or "export")
    safe_batch_id = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in batch_id)
    return f"doctor_responses_{safe_batch_id}.{suffix}"


def build_admin_stats(study: dict[str, Any], responses_path: Path, batch_registry_path: Path) -> dict[str, Any]:
    assignments = study.get("assignments", [])
    responses = read_json(responses_path, {"responses": []}).get("responses", [])
    batch_id = str(study.get("batch_id", study.get("study_id", "")))
    selected_questions = {str(row.get("question_id")) for row in assignments}
    answers_by_qid = read_source_answers(study)
    scored = score_responses(study, responses)

    by_condition = condition_summaries(scored)
    t0 = by_condition.get("T0", {}).get("accuracy")
    t1 = by_condition.get("T1", {}).get("accuracy")
    t2 = by_condition.get("T2", {}).get("accuracy")
    t2_rows = [row for row in scored if row.get("condition") == "T2"]
    t2_matches = sum(1 for row in t2_rows if row.get("matches_cdss") is True)

    question_rows = []
    for qid in sorted(selected_questions, key=lambda value: int(value) if value.isdigit() else value):
        q_assignments = [row for row in assignments if str(row.get("question_id")) == qid]
        q_responses = [row for row in scored if str(row.get("question_id")) == qid]
        answer = answers_by_qid.get(qid, {})
        condition_summary = condition_summaries(q_responses)
        q_assignment = q_assignments[0] if q_assignments else {}
        q_question = q_assignment.get("question") or {}
        q_cdss_t1 = next(
            (a.get("cdss") for a in q_assignments if a.get("condition") == "T1" and a.get("cdss")),
            None,
        ) or {}
        q_cdss_t2 = next(
            (a.get("cdss") for a in q_assignments if a.get("condition") == "T2" and a.get("cdss")),
            None,
        ) or {}
        gold = str(answer.get("answer_idx") or q_cdss_t1.get("cdss_answer_idx") or "")
        question_rows.append(
            {
                "question_id": qid,
                "difficulty": q_assignments[0].get("difficulty", "") if q_assignments else "",
                "assigned": len(q_assignments),
                "responses": len(q_responses),
                "gold_answer_idx": gold,
                "accuracy": summarize_group(q_responses)["accuracy"],
                "t0_accuracy": condition_summary["T0"]["accuracy"],
                "t1_accuracy": condition_summary["T1"]["accuracy"],
                "t2_accuracy": condition_summary["T2"]["accuracy"],
                "t2_matches_cdss_rate": condition_summary["T2"]["matches_cdss_rate"],
                "question_text": str(q_question.get("question") or ""),
                "options": q_question.get("options") or {},
                "cdss_t1": str(q_cdss_t1.get("advice_text") or ""),
                "cdss_t2": str(q_cdss_t2.get("advice_text") or ""),
            }
        )

    by_doctor = grouped_summary(scored, "doctor_id")
    for doctor_row in by_doctor:
        min_t = doctor_row.get("min_response_time_seconds")
        doctor_row["speed_warning"] = min_t is not None and min_t < SPEED_WARNING_THRESHOLD_SECONDS

    batch_registry = read_json(batch_registry_path, {"batches": []})
    return {
        "batch": {
            "batch_id": batch_id,
            "study_id": study.get("study_id", ""),
            "selected_question_count": len(selected_questions),
            "assignment_count": len(assignments),
            "response_count": len(scored),
            "completion_rate": pct(len(scored), len(assignments)),
            "doctor_count": len(study.get("doctors", [])),
            "difficulty_counts": (study.get("design") or {}).get("difficulty_counts", {}),
        },
        "metrics": {
            "overall": summarize_group(scored),
            "by_condition": by_condition,
            "t1_minus_t0_accuracy": rate_delta(t1, t0),
            "t2_minus_t0_accuracy": rate_delta(t2, t0),
            "t2_matches_cdss_rate": pct(t2_matches, len(t2_rows)),
        },
        "tables": {
            "by_doctor": by_doctor,
            "by_doctor_level": grouped_summary(scored, "doctor_level"),
            "by_difficulty": grouped_summary(scored, "difficulty"),
            "by_question": question_rows,
        },
        "registry": batch_registry,
    }


def register_batch_run(batch_registry_path: Path, study: dict[str, Any], data_path: Path) -> None:
    assignments = study.get("assignments", [])
    records_by_doctor: dict[str, int] = {}
    conditions_by_doctor: dict[str, dict[str, int]] = {}
    for row in assignments:
        doctor_id = str(row.get("doctor_id", ""))
        condition = str(row.get("condition", ""))
        records_by_doctor[doctor_id] = records_by_doctor.get(doctor_id, 0) + 1
        conditions_by_doctor.setdefault(doctor_id, {})
        conditions_by_doctor[doctor_id][condition] = conditions_by_doctor[doctor_id].get(condition, 0) + 1

    entry = {
        "registered_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "batch_id": study.get("batch_id", study.get("study_id", "")),
        "study_id": study.get("study_id", ""),
        "data_path": str(data_path),
        "source_dataset": study.get("source_dataset", ""),
        "source_assignment_csv": study.get("source_assignment_csv", ""),
        "source_advice_jsonl": study.get("source_advice_jsonl", ""),
        "selected_question_count": len({str(row.get("question_id")) for row in assignments}),
        "assignment_count": len(assignments),
        "doctor_count": len(study.get("doctors", [])),
        "difficulty_counts": (study.get("design") or {}).get("difficulty_counts", {}),
        "records_per_doctor": dict(sorted(records_by_doctor.items())),
        "conditions_per_doctor": {
            doctor_id: dict(sorted(counts.items()))
            for doctor_id, counts in sorted(conditions_by_doctor.items())
        },
        "selection": study.get("selection", {}),
        "assignment_summary": study.get("summary", {}),
    }

    payload = read_json(batch_registry_path, {"batches": []})
    batches = [row for row in payload.get("batches", []) if row.get("batch_id") != entry["batch_id"]]
    batches.append(entry)
    write_json_atomic(batch_registry_path, {"batches": batches})


class DoctorAppHandler(BaseHTTPRequestHandler):
    server_version = "CDSSDoctorApp/0.2"

    @property
    def data_path(self) -> Path:
        return self.server.data_path  # type: ignore[attr-defined]

    @property
    def accounts_path(self) -> Path:
        return self.server.accounts_path  # type: ignore[attr-defined]

    @property
    def responses_path(self) -> Path:
        return self.server.responses_path  # type: ignore[attr-defined]

    @property
    def batch_registry_path(self) -> Path:
        return self.server.batch_registry_path  # type: ignore[attr-defined]

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.handle_health()
            return
        if parsed.path == "/api/me":
            account = self.require_account()
            if account is None:
                return
            self.send_json({"ok": True, "user": self.public_account(account)})
            return
        if parsed.path == "/api/study":
            account = self.require_account()
            if account is None:
                return
            if is_admin(account):
                self.send_json({"ok": False, "error": "admin account cannot answer study"}, status=403)
                return
            self.send_json(public_study_for_doctor(read_json(self.data_path, {}), account))
            return
        if parsed.path == "/api/admin/stats":
            account = self.require_admin()
            if account is None:
                return
            self.send_json(build_admin_stats(read_json(self.data_path, {}), self.responses_path, self.batch_registry_path))
            return
        if parsed.path == "/api/admin/responses":
            account = self.require_admin()
            if account is None:
                return
            responses = read_json(self.responses_path, {"responses": []}).get("responses", [])
            rows = sorted(
                responses,
                key=lambda item: (
                    str(item.get("doctor_id") or ""),
                    int(item.get("display_order") or 0),
                ),
            )
            self.send_json({"responses": rows, "total": len(rows)})
            return
        if parsed.path == "/api/admin/export.csv":
            account = self.require_admin()
            if account is None:
                return
            self.handle_admin_export("csv")
            return
        if parsed.path == "/api/admin/export.jsonl":
            account = self.require_admin()
            if account is None:
                return
            self.handle_admin_export("jsonl")
            return
        if parsed.path == "/api/responses":
            account = self.require_account()
            if account is None:
                return
            responses = read_json(self.responses_path, {"responses": []}).get("responses", [])
            doctor_id = str(account["doctor_id"])
            self.send_json({"responses": [row for row in responses if str(row.get("doctor_id")) == doctor_id]})
            return
        self.serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/login":
            self.handle_login()
            return
        if parsed.path == "/api/logout":
            self.handle_logout()
            return
        if parsed.path == "/api/responses":
            self.handle_save_response()
            return
        self.send_error(404)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/admin/responses":
            self.handle_admin_delete_responses()
            return
        self.send_error(404)

    def handle_health(self) -> None:
        study = read_json(self.data_path, {})
        responses = read_json(self.responses_path, {"responses": []}).get("responses", [])
        accounts = self.load_accounts()
        self.send_json(
            {
                "ok": True,
                "study_id": study.get("study_id", ""),
                "batch_id": study.get("batch_id", study.get("study_id", "")),
                "doctor_count": len(study.get("doctors", [])),
                "selected_question_count": len({str(row.get("question_id")) for row in study.get("assignments", [])}),
                "assignment_count": len(study.get("assignments", [])),
                "account_count": len(accounts),
                "response_count": len(responses),
            }
        )

    def handle_login(self) -> None:
        payload = self.read_payload()
        if payload is None:
            return

        username = normalize_username(payload.get("username"))
        password = str(payload.get("password") or "")
        account = self.load_accounts().get(username)
        if not account or not account.get("active", True) or not verify_password(account, password):
            self.send_json({"ok": False, "error": "Incorrect username or password"}, status=401)
            return

        study = read_json(self.data_path, {})
        doctor_id = str(account.get("doctor_id") or "")
        if is_admin(account):
            account = {**account, "username": username, "doctor_id": ""}
        elif not doctor_id or doctor_by_id(study, doctor_id) is None:
            self.send_json({"ok": False, "error": "Account has no assigned participant"}, status=403)
            return
        else:
            account = {**account, "username": username, "doctor_id": doctor_id}
        token = secrets.token_urlsafe(32)
        self.server.sessions[token] = {  # type: ignore[attr-defined]
            "account": account,
            "created_at": time.time(),
            "last_seen": time.time(),
        }
        self.send_json({"ok": True, "user": self.public_account(account)}, headers=[self.cookie_header(token)])

    def handle_logout(self) -> None:
        token = self.session_token()
        if token:
            self.server.sessions.pop(token, None)  # type: ignore[attr-defined]
        self.send_json({"ok": True}, headers=[self.clear_cookie_header()])

    def handle_admin_export(self, export_format: str) -> None:
        study = read_json(self.data_path, {})
        responses = read_json(self.responses_path, {"responses": []}).get("responses", [])
        scored = score_responses(study, responses)

        expected = len(study.get("assignments", []))
        actual = len(scored)
        status = "OK" if actual == expected else f"警告：期望 {expected} 条，实际 {actual} 条"
        print(f"[导出] batch_id={study.get('batch_id') or study.get('study_id') or '-'} "
              f"记录数={actual}/{expected} {status}")

        if export_format == "csv":
            body = build_export_csv(scored).encode("utf-8-sig")
            content_type = "text/csv; charset=utf-8"
            suffix = "csv"
        else:
            body = build_export_jsonl(scored).encode("utf-8")
            content_type = "application/jsonl; charset=utf-8"
            suffix = "jsonl"
        self.send_attachment(body, export_filename(study, suffix), content_type)

    def handle_admin_delete_responses(self) -> None:
        account = self.require_admin()
        if account is None:
            return
        payload = self.read_payload()
        if payload is None:
            return

        delete_all = payload.get("delete_all") is True
        record_id = str(payload.get("record_id") or "").strip()
        if delete_all:
            if payload.get("confirmation") != "DELETE_ALL":
                self.send_json({"ok": False, "error": "Deleting all records requires confirmation"}, status=400)
                return
        elif not record_id:
            self.send_json({"ok": False, "error": "record_id is required"}, status=400)
            return

        with responses_store_lock(self.responses_path):
            data = read_json(self.responses_path, {"responses": []})
            existing = data.get("responses", [])
            if not isinstance(existing, list):
                self.send_json({"ok": False, "error": "Invalid response store format"}, status=500)
                return
            deleted = [
                row for row in existing
                if delete_all or str(row.get("record_id") or "") == record_id
            ]
            if not deleted:
                self.send_json({"ok": False, "error": "Response record not found"}, status=404)
                return
            remaining = [row for row in existing if row not in deleted]
            backup_dir = self.responses_path.parent / "deleted_response_backups"
            backup_path = backup_dir / f"deleted_{time.time_ns()}.json"
            write_json_atomic(
                backup_path,
                {
                    "deleted_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "deleted_by": normalize_username(account.get("username")),
                    "delete_all": delete_all,
                    "record_id": record_id,
                    "responses": deleted,
                },
            )
            write_json_atomic(self.responses_path, {"responses": remaining})

        self.send_json(
            {
                "ok": True,
                "deleted_count": len(deleted),
                "remaining_count": len(remaining),
            }
        )

    def handle_save_response(self) -> None:
        account = self.require_account()
        if account is None:
            return
        if is_admin(account):
            self.send_json({"ok": False, "error": "admin account cannot submit responses"}, status=403)
            return
        payload = self.read_payload()
        if payload is None:
            return

        row = payload.get("response") if isinstance(payload, dict) else None
        if not isinstance(row, dict):
            self.send_json({"ok": False, "error": "payload must contain a response object"}, status=400)
            return

        study = read_json(self.data_path, {})
        batch_id = str(study.get("batch_id", study.get("study_id", "")))
        assignments = {str(item.get("assignment_id")): item for item in assignments_for_doctor(study, str(account["doctor_id"]))}
        assignment = assignments.get(str(row.get("assignment_id") or ""))
        if assignment is None:
            self.send_json({"ok": False, "error": "assignment does not belong to current account"}, status=403)
            return

        answer = str(row.get("doctor_answer_idx") or "").strip().upper()
        if answer not in VALID_OPTIONS:
            self.send_json({"ok": False, "error": "doctor_answer_idx must be A/B/C/D"}, status=400)
            return

        cdss_answer = str((assignment.get("cdss") or {}).get("cdss_answer_idx") or "")
        try:
            response_time_seconds = int(row.get("response_time_seconds") or 0)
        except (TypeError, ValueError):
            self.send_json({"ok": False, "error": "response_time_seconds must be an integer"}, status=400)
            return
        time_limit_seconds = int(study.get("time_limit_seconds") or DEFAULT_TIME_LIMIT_SECONDS)
        if response_time_seconds < 0 or response_time_seconds > time_limit_seconds:
            self.send_json(
                {"ok": False, "error": f"response_time_seconds must be between 0 and {time_limit_seconds}"},
                status=400,
            )
            return
        raw_changes = row.get("changes")
        changes = [
            entry for entry in (raw_changes if isinstance(raw_changes, list) else [])
            if isinstance(entry, dict)
            and str(entry.get("from", "")).strip().upper() in VALID_OPTIONS
            and str(entry.get("to", "")).strip().upper() in VALID_OPTIONS
        ]
        clean_row = {
            "record_id": str(row.get("record_id") or f"R-{assignment['assignment_id']}"),
            "study_id": study.get("study_id", ""),
            "batch_id": batch_id,
            "assignment_id": assignment["assignment_id"],
            "doctor_id": assignment["doctor_id"],
            "doctor_level": assignment["doctor_level"],
            "question_id": assignment["question_id"],
            "difficulty": assignment["difficulty"],
            "condition": assignment["condition"],
            "stage_block": assignment["stage_block"],
            "session_id": assignment["session_id"],
            "display_order": assignment["display_order"],
            "block_order": assignment["block_order"],
            "has_cdss": bool(assignment.get("cdss")),
            "cdss_answer_idx": cdss_answer,
            "doctor_answer_idx": answer,
            "matches_cdss": answer == cdss_answer if cdss_answer else None,
            "response_time_seconds": response_time_seconds,
            "note": str(row.get("note") or ""),
            "changes": changes,
            "updated_at": str(row.get("updated_at") or ""),
        }

        with responses_store_lock(self.responses_path):
            data = read_json(self.responses_path, {"responses": []})
            by_key = {response_key(existing): existing for existing in data.get("responses", [])}
            by_key[response_key(clean_row)] = clean_row
            responses = sorted(by_key.values(), key=lambda item: (str(item.get("doctor_id", "")), int(item.get("display_order") or 0)))
            write_json_atomic(self.responses_path, {"responses": responses})
        self.send_json({"ok": True, "saved": response_key(clean_row), "total": len(responses)})

    def read_payload(self) -> dict[str, Any] | None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > 2 * 1024 * 1024:
                self.send_json({"ok": False, "error": "request body is too large"}, status=413)
                return None
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception as error:
            self.send_json({"ok": False, "error": f"invalid json: {error}"}, status=400)
            return None
        if not isinstance(payload, dict):
            self.send_json({"ok": False, "error": "json payload must be an object"}, status=400)
            return None
        return payload

    def load_accounts(self) -> dict[str, dict[str, Any]]:
        payload = read_json(self.accounts_path, {"accounts": []})
        accounts: dict[str, dict[str, Any]] = {}
        for item in payload.get("accounts", []):
            if not isinstance(item, dict):
                continue
            username = normalize_username(item.get("username"))
            role = str(item.get("role") or "doctor").lower()
            doctor_id = str(item.get("doctor_id") or "").strip()
            if not username:
                continue
            if role == "admin" or doctor_id:
                accounts[username] = {**item, "username": username, "doctor_id": doctor_id, "role": role}
        return accounts

    def require_account(self) -> dict[str, Any] | None:
        token = self.session_token()
        if not token:
            self.send_json({"ok": False, "error": "not authenticated"}, status=401)
            return None
        session = self.server.sessions.get(token)  # type: ignore[attr-defined]
        if not session or time.time() - float(session.get("last_seen", 0)) > SESSION_TTL_SECONDS:
            self.server.sessions.pop(token, None)  # type: ignore[attr-defined]
            self.send_json({"ok": False, "error": "session expired"}, status=401, headers=[self.clear_cookie_header()])
            return None

        session["last_seen"] = time.time()
        account = session.get("account", {})
        username = normalize_username(account.get("username"))
        latest = self.load_accounts().get(username)
        if not latest or not latest.get("active", True):
            self.server.sessions.pop(token, None)  # type: ignore[attr-defined]
            self.send_json({"ok": False, "error": "account disabled"}, status=401, headers=[self.clear_cookie_header()])
            return None
        return {**latest, "username": username}

    def require_admin(self) -> dict[str, Any] | None:
        account = self.require_account()
        if account is None:
            return None
        if not is_admin(account):
            self.send_json({"ok": False, "error": "admin account required"}, status=403)
            return None
        return account

    def session_token(self) -> str:
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        morsel = cookie.get(SESSION_COOKIE)
        return morsel.value if morsel else ""

    def cookie_header(self, token: str) -> tuple[str, str]:
        return (
            "Set-Cookie",
            f"{SESSION_COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={SESSION_TTL_SECONDS}",
        )

    def clear_cookie_header(self) -> tuple[str, str]:
        return ("Set-Cookie", f"{SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0")

    def public_account(self, account: dict[str, Any]) -> dict[str, str]:
        return {
            "username": str(account.get("username", "")),
            "doctor_id": str(account.get("doctor_id", "")),
            "role": str(account.get("role") or "doctor"),
        }

    def serve_static(self, request_path: str) -> None:
        relative = "index.html" if request_path in ("", "/") else request_path.lstrip("/")
        # The public demo serves only UI assets, never Python, fixture, or runtime files.
        if relative not in {"index.html", "app.js", "styles.css"}:
            self.send_error(404)
            return
        target = (APP_ROOT / relative).resolve()
        app_root = APP_ROOT.resolve()
        try:
            target.relative_to(app_root)
        except ValueError:
            self.send_error(404)
            return
        if not target.exists() or target.is_dir():
            self.send_error(404)
            return

        mime_type, _ = mimetypes.guess_type(str(target))
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(data)

    def send_json(
        self,
        data: Any,
        status: int = 200,
        headers: list[tuple[str, str]] | None = None,
    ) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        for key, value in headers or []:
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def send_attachment(self, body: bytes, filename: str, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the CDSS doctor answer prototype.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-path", default=str(DEFAULT_DATA_PATH.relative_to(PROJECT_ROOT)))
    parser.add_argument("--accounts-path", default=str(DEFAULT_ACCOUNTS_PATH.relative_to(PROJECT_ROOT)))
    parser.add_argument("--responses-path", default=str(DEFAULT_RESPONSES_PATH.relative_to(PROJECT_ROOT)))
    parser.add_argument("--batch-registry-path", default=str(DEFAULT_BATCH_REGISTRY_PATH.relative_to(PROJECT_ROOT)))
    args = parser.parse_args()

    data_path = resolve_path(args.data_path)
    accounts_path = resolve_path(args.accounts_path)
    responses_path = resolve_path(args.responses_path)
    batch_registry_path = resolve_path(args.batch_registry_path)
    responses_path.parent.mkdir(parents=True, exist_ok=True)
    batch_registry_path.parent.mkdir(parents=True, exist_ok=True)
    study = read_json(data_path, {})
    if study:
        register_batch_run(batch_registry_path, study, data_path)
    server = ThreadingHTTPServer((args.host, args.port), DoctorAppHandler)
    server.data_path = data_path  # type: ignore[attr-defined]
    server.accounts_path = accounts_path  # type: ignore[attr-defined]
    server.responses_path = responses_path  # type: ignore[attr-defined]
    server.batch_registry_path = batch_registry_path  # type: ignore[attr-defined]
    server.sessions = {}  # type: ignore[attr-defined]
    print(f"Serving doctor app at http://{args.host}:{args.port}/")
    print(f"DATA_PATH={data_path}")
    print(f"ACCOUNTS_PATH={accounts_path}")
    print(f"RESPONSES_PATH={responses_path}")
    print(f"BATCH_REGISTRY_PATH={batch_registry_path}")
    server.serve_forever()


if __name__ == "__main__":
    main()
