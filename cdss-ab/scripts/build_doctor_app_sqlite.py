from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS responses;
DROP TABLE IF EXISTS cdss_advice;
DROP TABLE IF EXISTS assignments;
DROP TABLE IF EXISTS answer_keys;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS doctors;
DROP TABLE IF EXISTS studies;

CREATE TABLE studies (
  study_id TEXT PRIMARY KEY,
  generated_at TEXT NOT NULL,
  source_dataset TEXT,
  design_type TEXT,
  difficulty_counts_json TEXT,
  doctor_count INTEGER,
  records_per_question INTEGER,
  doctor_facing INTEGER NOT NULL DEFAULT 1,
  gold_answers_included INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE doctors (
  study_id TEXT NOT NULL,
  doctor_id TEXT NOT NULL,
  doctor_level TEXT NOT NULL CHECK (doctor_level IN ('senior', 'junior')),
  PRIMARY KEY (study_id, doctor_id),
  FOREIGN KEY (study_id) REFERENCES studies(study_id) ON DELETE CASCADE
);

CREATE TABLE questions (
  study_id TEXT NOT NULL,
  question_id TEXT NOT NULL,
  source_order TEXT,
  difficulty TEXT NOT NULL,
  difficulty_level TEXT,
  question_text TEXT NOT NULL,
  option_a TEXT NOT NULL,
  option_b TEXT NOT NULL,
  option_c TEXT NOT NULL,
  option_d TEXT NOT NULL,
  PRIMARY KEY (study_id, question_id),
  FOREIGN KEY (study_id) REFERENCES studies(study_id) ON DELETE CASCADE
);

CREATE TABLE answer_keys (
  study_id TEXT NOT NULL,
  question_id TEXT NOT NULL,
  gold_answer_idx TEXT NOT NULL CHECK (gold_answer_idx IN ('A', 'B', 'C', 'D')),
  gold_answer_text TEXT,
  source_dataset TEXT,
  PRIMARY KEY (study_id, question_id),
  FOREIGN KEY (study_id, question_id) REFERENCES questions(study_id, question_id) ON DELETE CASCADE
);

CREATE TABLE assignments (
  assignment_id TEXT PRIMARY KEY,
  study_id TEXT NOT NULL,
  doctor_id TEXT NOT NULL,
  doctor_level TEXT NOT NULL CHECK (doctor_level IN ('senior', 'junior')),
  question_id TEXT NOT NULL,
  difficulty TEXT NOT NULL,
  condition TEXT NOT NULL CHECK (condition IN ('T0', 'T1', 'T2')),
  stage_block TEXT NOT NULL CHECK (stage_block IN ('baseline', 'cdss_advice')),
  display_order INTEGER NOT NULL,
  block_order INTEGER NOT NULL,
  session_id TEXT NOT NULL,
  FOREIGN KEY (study_id) REFERENCES studies(study_id) ON DELETE CASCADE,
  FOREIGN KEY (study_id, doctor_id) REFERENCES doctors(study_id, doctor_id) ON DELETE CASCADE,
  FOREIGN KEY (study_id, question_id) REFERENCES questions(study_id, question_id) ON DELETE CASCADE
);

CREATE TABLE cdss_advice (
  assignment_id TEXT PRIMARY KEY,
  cdss_answer_idx TEXT NOT NULL CHECK (cdss_answer_idx IN ('A', 'B', 'C', 'D')),
  cdss_answer_text TEXT,
  advice_text TEXT NOT NULL,
  confidence REAL,
  FOREIGN KEY (assignment_id) REFERENCES assignments(assignment_id) ON DELETE CASCADE
);

CREATE TABLE responses (
  record_id TEXT PRIMARY KEY,
  assignment_id TEXT NOT NULL UNIQUE,
  doctor_id TEXT NOT NULL,
  doctor_level TEXT NOT NULL CHECK (doctor_level IN ('senior', 'junior')),
  question_id TEXT NOT NULL,
  difficulty TEXT NOT NULL,
  condition TEXT NOT NULL CHECK (condition IN ('T0', 'T1', 'T2')),
  stage_block TEXT NOT NULL CHECK (stage_block IN ('baseline', 'cdss_advice')),
  session_id TEXT NOT NULL,
  display_order INTEGER NOT NULL,
  block_order INTEGER NOT NULL,
  has_cdss INTEGER NOT NULL CHECK (has_cdss IN (0, 1)),
  cdss_answer_idx TEXT,
  doctor_answer_idx TEXT NOT NULL CHECK (doctor_answer_idx IN ('A', 'B', 'C', 'D')),
  matches_cdss INTEGER CHECK (matches_cdss IN (0, 1)),
  response_time_seconds INTEGER NOT NULL DEFAULT 0,
  note TEXT,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (assignment_id) REFERENCES assignments(assignment_id) ON DELETE CASCADE
);

CREATE INDEX idx_doctors_level ON doctors(doctor_level);
CREATE INDEX idx_questions_difficulty ON questions(difficulty, difficulty_level);
CREATE INDEX idx_assignments_doctor_order ON assignments(doctor_id, display_order);
CREATE INDEX idx_assignments_condition ON assignments(condition);
CREATE INDEX idx_responses_doctor_order ON responses(doctor_id, display_order);
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a small SQLite database for the CDSS doctor app.")
    parser.add_argument("--study-json", default="doctor_app/data/pilot_study_12q.json")
    parser.add_argument("--source-csv", default="datasets/MedQA-MCMLE-GP-primary-care-reviewed-pro-705.csv")
    parser.add_argument("--responses-json", default="doctor_app/runtime/responses.json")
    parser.add_argument("--output-path", default="database/cdss_pilot_small.sqlite")
    parser.add_argument("--schema-path", default="database/cdss_pilot_small_schema.sql")
    parser.add_argument("--source-label", help="Portable provenance label; defaults to the source path")
    parser.add_argument("--skip-answer-keys", action="store_true")
    parser.add_argument("--skip-responses", action="store_true")
    return parser.parse_args()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def bool_int(value: Any) -> int:
    return 1 if bool(value) else 0


def nullable_bool_int(value: Any) -> int | None:
    if value is None:
        return None
    return 1 if bool(value) else 0


def read_answer_keys(csv_path: Path) -> dict[str, dict[str, str]]:
    if not csv_path.exists():
        return {}
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        return {
            str(row.get("qid", "")).strip(): {
                "gold_answer_idx": str(row.get("answer_idx", "")).strip().upper(),
                "gold_answer_text": str(row.get("answer", "")).strip(),
            }
            for row in csv.DictReader(file)
            if str(row.get("qid", "")).strip()
        }


def insert_study(conn: sqlite3.Connection, study: dict[str, Any]) -> None:
    design = study.get("design", {})
    conn.execute(
        """
        INSERT INTO studies (
          study_id, generated_at, source_dataset, design_type, difficulty_counts_json,
          doctor_count, records_per_question, doctor_facing, gold_answers_included
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            study["study_id"],
            study.get("generated_at", ""),
            study.get("source_dataset", ""),
            design.get("type", ""),
            json.dumps(design.get("difficulty_counts", {}), ensure_ascii=False),
            design.get("doctor_count"),
            design.get("records_per_question"),
            bool_int(design.get("doctor_facing", True)),
            bool_int(design.get("gold_answers_included", False)),
        ),
    )


def insert_doctors(conn: sqlite3.Connection, study_id: str, doctors: list[dict[str, Any]]) -> None:
    conn.executemany(
        "INSERT INTO doctors (study_id, doctor_id, doctor_level) VALUES (?, ?, ?)",
        [(study_id, row["doctor_id"], row["doctor_level"]) for row in doctors],
    )


def insert_questions(conn: sqlite3.Connection, study_id: str, assignments: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    rows: list[tuple[Any, ...]] = []
    for assignment in assignments:
        question = assignment["question"]
        question_id = str(question["question_id"])
        if question_id in seen:
            continue
        seen.add(question_id)
        options = question.get("options", {})
        rows.append(
            (
                study_id,
                question_id,
                question.get("source_order", ""),
                question.get("difficulty", assignment.get("difficulty", "")),
                question.get("difficulty_level", ""),
                question.get("question", ""),
                options.get("A", ""),
                options.get("B", ""),
                options.get("C", ""),
                options.get("D", ""),
            )
        )
    conn.executemany(
        """
        INSERT INTO questions (
          study_id, question_id, source_order, difficulty, difficulty_level,
          question_text, option_a, option_b, option_c, option_d
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def insert_answer_keys(
    conn: sqlite3.Connection,
    study_id: str,
    assignments: list[dict[str, Any]],
    source_csv: Path,
    source_label: str | None = None,
) -> None:
    answer_by_id = read_answer_keys(source_csv)
    question_ids = sorted({str(row["question_id"]) for row in assignments})
    rows = []
    for question_id in question_ids:
        answer = answer_by_id.get(question_id)
        if not answer or answer["gold_answer_idx"] not in {"A", "B", "C", "D"}:
            continue
        rows.append(
            (
                study_id,
                question_id,
                answer["gold_answer_idx"],
                answer["gold_answer_text"],
                source_label if source_label is not None else str(source_csv),
            )
        )
    conn.executemany(
        """
        INSERT INTO answer_keys (
          study_id, question_id, gold_answer_idx, gold_answer_text, source_dataset
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        rows,
    )


def insert_assignments(conn: sqlite3.Connection, study_id: str, assignments: list[dict[str, Any]]) -> None:
    conn.executemany(
        """
        INSERT INTO assignments (
          assignment_id, study_id, doctor_id, doctor_level, question_id, difficulty,
          condition, stage_block, display_order, block_order, session_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["assignment_id"],
                study_id,
                row["doctor_id"],
                row["doctor_level"],
                str(row["question_id"]),
                row["difficulty"],
                row["condition"],
                row["stage_block"],
                row["display_order"],
                row["block_order"],
                row["session_id"],
            )
            for row in assignments
        ],
    )


def insert_cdss_advice(conn: sqlite3.Connection, assignments: list[dict[str, Any]]) -> None:
    rows = []
    for assignment in assignments:
        cdss = assignment.get("cdss")
        if not cdss:
            continue
        rows.append(
            (
                assignment["assignment_id"],
                cdss.get("cdss_answer_idx", ""),
                cdss.get("cdss_answer_text", ""),
                cdss.get("advice_text", ""),
                cdss.get("confidence"),
            )
        )
    conn.executemany(
        """
        INSERT INTO cdss_advice (
          assignment_id, cdss_answer_idx, cdss_answer_text, advice_text, confidence
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        rows,
    )


def insert_responses(conn: sqlite3.Connection, responses_path: Path) -> None:
    payload = load_json(responses_path, {"responses": []})
    rows = []
    valid_assignments = {
        row[0]
        for row in conn.execute("SELECT assignment_id FROM assignments").fetchall()
    }
    for row in payload.get("responses", []):
        if row.get("assignment_id") not in valid_assignments or not row.get("doctor_answer_idx"):
            continue
        rows.append(
            (
                row.get("record_id") or f"R-{row['assignment_id']}",
                row["assignment_id"],
                row["doctor_id"],
                row["doctor_level"],
                str(row["question_id"]),
                row["difficulty"],
                row["condition"],
                row["stage_block"],
                row["session_id"],
                row["display_order"],
                row["block_order"],
                bool_int(row.get("has_cdss")),
                row.get("cdss_answer_idx") or None,
                row["doctor_answer_idx"],
                nullable_bool_int(row.get("matches_cdss")),
                int(row.get("response_time_seconds") or 0),
                row.get("note", ""),
                row.get("updated_at", ""),
            )
        )
    conn.executemany(
        """
        INSERT OR REPLACE INTO responses (
          record_id, assignment_id, doctor_id, doctor_level, question_id, difficulty,
          condition, stage_block, session_id, display_order, block_order, has_cdss,
          cdss_answer_idx, doctor_answer_idx, matches_cdss, response_time_seconds,
          note, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def table_counts(conn: sqlite3.Connection) -> dict[str, int]:
    names = ["studies", "doctors", "questions", "answer_keys", "assignments", "cdss_advice", "responses"]
    return {name: conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0] for name in names}


def main() -> None:
    args = parse_args()
    study_path = (PROJECT_ROOT / args.study_json).resolve()
    source_csv = (PROJECT_ROOT / args.source_csv).resolve()
    responses_path = (PROJECT_ROOT / args.responses_json).resolve()
    output_path = (PROJECT_ROOT / args.output_path).resolve()
    schema_path = (PROJECT_ROOT / args.schema_path).resolve()

    study = load_json(study_path, {})
    if not study:
        raise SystemExit(f"Study JSON not found or empty: {study_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    with sqlite3.connect(output_path) as conn:
        conn.executescript(SCHEMA_SQL)
        insert_study(conn, study)
        insert_doctors(conn, study["study_id"], study["doctors"])
        insert_questions(conn, study["study_id"], study["assignments"])
        if not args.skip_answer_keys:
            insert_answer_keys(conn, study["study_id"], study["assignments"], source_csv, args.source_label)
        insert_assignments(conn, study["study_id"], study["assignments"])
        insert_cdss_advice(conn, study["assignments"])
        if not args.skip_responses:
            insert_responses(conn, responses_path)
        conn.commit()
        counts = table_counts(conn)

    schema_path.write_text(SCHEMA_SQL.strip() + "\n", encoding="utf-8")
    print(f"DATABASE_PATH={output_path}")
    print(f"SCHEMA_PATH={schema_path}")
    for name, count in counts.items():
        print(f"{name}={count}")


if __name__ == "__main__":
    main()
