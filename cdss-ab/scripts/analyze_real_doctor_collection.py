"""Audit and analyze an immutable doctor-app collection snapshot, without API writes."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LOCAL_TZ = timezone(timedelta(hours=8))
CONDITIONS = ("T0", "T1", "T2")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp has no timezone: {value}")
    return parsed


def write_csv(path, rows, columns=None):
    columns = columns or list(rows[0])
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def summary(rows, **labels):
    cdss_rows = [r for r in rows if r["has_cdss"]]
    times = [r["response_time_seconds"] for r in rows]
    return dict(
        **labels,
        n=len(rows),
        correct=sum(r["doctor_is_correct"] for r in rows),
        accuracy=sum(r["doctor_is_correct"] for r in rows) / len(rows) if rows else None,
        cdss_n=len(cdss_rows),
        cdss_matches=sum(r["matches_cdss"] for r in cdss_rows),
        cdss_match_rate=sum(r["matches_cdss"] for r in cdss_rows) / len(cdss_rows) if cdss_rows else None,
        median_response_seconds=statistics.median(times) if times else None,
        total_response_seconds=sum(times),
        short_lt5_count=sum(t < 5 for t in times),
        revised_count=sum(r["change_count"] > 0 for r in rows),
    )


def grouped(rows, fields):
    buckets = defaultdict(list)
    for row in rows:
        buckets[tuple(row[field] for field in fields)].append(row)
    return [summary(bucket, **dict(zip(fields, key))) for key, bucket in sorted(buckets.items())]


def pct(value):
    return "未收集" if value is None else f"{value:.1%}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-dir", required=True)
    parser.add_argument("--bootstrap-reps", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20261019)
    parser.add_argument("--generated-at", help="Explicit timezone-aware provenance time for reproducible output; not wall-clock execution time")
    args = parser.parse_args()
    if args.bootstrap_reps < 1:
        parser.error("--bootstrap-reps must be positive")
    generated_at = timestamp(args.generated_at).astimezone(LOCAL_TZ).isoformat() if args.generated_at else datetime.now(LOCAL_TZ).isoformat()
    out = Path(args.snapshot_dir).resolve()
    snap = out / "snapshot"
    # Refuse to overwrite a completed analysis or to operate on a live input file.
    if (out / "manifest.json").exists():
        raise SystemExit("Completed archive exists. Create a new snapshot directory for another run.")
    study = read_json(snap / "study.json")
    payload = read_json(snap / "responses.json")
    raw = payload["responses"]
    assignments = study["assignments"]
    errors = []
    with (snap / "answer_source.csv").open(encoding="utf-8-sig", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    source = {str(r["qid"]): r for r in source_rows}
    if len(source) != len(source_rows):
        errors.append("Duplicate qid in answer source")
    assignment_by_id = {a["assignment_id"]: a for a in assignments}
    if len(assignment_by_id) != len(assignments):
        errors.append("Duplicate assignment_id in study")
    doctors = {d["doctor_id"]: d["doctor_level"] for d in study["doctors"]}
    for field in ("assignment_id", "record_id"):
        errors.extend(f"Duplicate {field}: {key}" for key, count in Counter(r.get(field) for r in raw).items() if count > 1)
    pairs = Counter((r.get("doctor_id"), str(r.get("question_id"))) for r in raw)
    errors.extend(f"Duplicate doctor/question: {key}" for key, count in pairs.items() if count > 1)
    for a in assignments:
        qid = str(a["question_id"])
        gold = source.get(qid, {}).get("answer_idx")
        if gold not in ("A", "B", "C", "D"):
            errors.append(f"Missing/invalid answer key: {qid}")
            continue
        question = a["question"]
        if question["question"] != source[qid]["question"] or any(question["options"][v] != source[qid][v] for v in "ABCD"):
            errors.append(f"Question/option mismatch: {a['assignment_id']}")
        cdss = (a.get("cdss") or {}).get("cdss_answer_idx", "")
        if a["condition"] == "T0" and a.get("cdss"):
            errors.append(f"T0 unexpectedly has CDSS: {a['assignment_id']}")
        if a["condition"] == "T1" and cdss != gold:
            errors.append(f"T1 answer differs from gold: {a['assignment_id']}")
        if a["condition"] == "T2" and (cdss not in ("A", "B", "C", "D") or cdss == gold):
            errors.append(f"T2 answer not a valid incorrect option: {a['assignment_id']}")
    scored = []
    for r in raw:
        aid = r.get("assignment_id")
        if aid not in assignment_by_id:
            errors.append(f"Unknown assignment: {aid}")
            continue
        a = assignment_by_id[aid]
        for field in ("doctor_id", "doctor_level", "question_id", "difficulty", "condition", "stage_block", "session_id", "display_order", "block_order"):
            if str(r.get(field)) != str(a[field]):
                errors.append(f"Metadata mismatch {aid}/{field}")
        if r.get("study_id") != study["study_id"] or r.get("batch_id") != study.get("batch_id", study["study_id"]):
            errors.append(f"Wrong study/batch: {aid}")
        answer = r.get("doctor_answer_idx", "")
        if answer not in ("A", "B", "C", "D"):
            errors.append(f"Invalid answer: {aid}")
        seconds = r.get("response_time_seconds")
        if type(seconds) is not int or seconds < 0:
            errors.append(f"Invalid response time: {aid}")
        try:
            timestamp(r["updated_at"])
        except (KeyError, ValueError, TypeError):
            errors.append(f"Invalid timestamp: {aid}")
        gold = source.get(str(a["question_id"]), {}).get("answer_idx")
        cdss = (a.get("cdss") or {}).get("cdss_answer_idx", "")
        matched = answer == cdss if cdss else None
        if r.get("has_cdss") != bool(cdss) or r.get("cdss_answer_idx", "") != cdss or r.get("matches_cdss") != matched:
            errors.append(f"CDSS metadata mismatch: {aid}")
        changes = r.get("changes", [])
        previous = None
        for change in changes:
            if change.get("from") not in ("A", "B", "C", "D") or change.get("to") not in ("A", "B", "C", "D"):
                errors.append(f"Invalid change options: {aid}")
            if previous and change["from"] != previous:
                errors.append(f"Broken answer-change chain: {aid}")
            previous = change.get("to")
            try:
                timestamp(change["changed_at"])
            except (ValueError, KeyError, TypeError):
                errors.append(f"Invalid change timestamp: {aid}")
        if changes and changes[-1]["to"] != answer:
            errors.append(f"Change history differs from final answer: {aid}")
        scored.append({**r, "gold_answer_idx": gold, "doctor_is_correct": answer == gold,
                       "matches_cdss": matched, "change_count": len(changes), "short_lt5_seconds": seconds < 5})
    audit = {"status": "FAIL" if errors else "PASS", "errors": errors,
             "responses": len(raw), "planned_assignments": len(assignments),
             "validated_material_assignments": len(assignments),
             "answer_key_source": "snapshot/answer_source.csv; no T1 fallback",
             "automatic_exclusions": 0}
    dump(out / "audit.json", audit)
    if errors:
        raise SystemExit(json.dumps(audit, ensure_ascii=False, indent=2))
    scored.sort(key=lambda r: (r["doctor_id"], int(r["display_order"])))
    first_advice = {}
    for doc in doctors:
        times = [timestamp(r["updated_at"]) for r in scored if r["doctor_id"] == doc and r["condition"] != "T0"]
        if times:
            first_advice[doc] = min(times)
    changes_flat = []
    baseline_sensitivity = []
    for r in scored:
        row = dict(r)
        cutoff = first_advice.get(r["doctor_id"])
        post_advice = [c for c in r.get("changes", []) if cutoff and timestamp(c["changed_at"]) >= cutoff]
        r["baseline_revised_after_first_advice_save"] = r["condition"] == "T0" and bool(post_advice)
        if r["baseline_revised_after_first_advice_save"]:
            row["doctor_answer_idx"] = post_advice[0]["from"]
            row["doctor_is_correct"] = row["doctor_answer_idx"] == r["gold_answer_idx"]
        baseline_sensitivity.append(row)
        for index, c in enumerate(r.get("changes", []), 1):
            changes_flat.append({"assignment_id": r["assignment_id"], "doctor_id": r["doctor_id"],
                "question_id": r["question_id"], "condition": r["condition"], "change_order": index,
                **c, "from_correct": c["from"] == r["gold_answer_idx"], "to_correct": c["to"] == r["gold_answer_idx"],
                "after_first_advice_save": bool(cutoff and timestamp(c["changed_at"]) >= cutoff)})
    completion = []
    for doc, level in sorted(doctors.items()):
        rows = [r for r in scored if r["doctor_id"] == doc]
        times = [timestamp(r["updated_at"]) for r in rows]
        entry = {"doctor_id": doc, "doctor_level": level,
            "assigned": sum(a["doctor_id"] == doc for a in assignments), "answered": len(rows),
            **{c: sum(r["condition"] == c for r in rows) for c in CONDITIONS},
            "accumulated_minutes": sum(r["response_time_seconds"] for r in rows) / 60 if rows else None,
            "first_latest_save_local": min(times).astimezone(LOCAL_TZ).isoformat() if times else None,
            "last_latest_save_local": max(times).astimezone(LOCAL_TZ).isoformat() if times else None,
            "latest_save_span_minutes": (max(times) - min(times)).total_seconds() / 60 if times else None,
            "short_lt5_count": sum(r["short_lt5_seconds"] for r in rows),
            "revised_records": sum(r["change_count"] > 0 for r in rows)}
        completion.append(entry)
    summaries = {
        "by_condition": grouped(scored, ("condition",)),
        "by_doctor_condition": grouped(scored, ("doctor_id", "condition")),
        "by_difficulty_condition": grouped(scored, ("difficulty", "condition")),
        "by_level_condition": grouped(scored, ("doctor_level", "condition")),
        "sensitivity_exclude_lt5": grouped([r for r in scored if not r["short_lt5_seconds"]], ("condition",)),
        "sensitivity_t0_before_late_revisions": grouped(baseline_sensitivity, ("condition",)),
    }
    contrasts = []
    # Paired *questions*, answered by different doctors; never interpreted as individual transitions.
    for level in sorted(set(doctors.values())):
        level_rows = [r for r in scored if r["doctor_level"] == level]
        by_q = defaultdict(lambda: defaultdict(list))
        for r in level_rows:
            by_q[r["question_id"]][r["condition"]].append(r)
        complete = {q: cells for q, cells in by_q.items() if all(len(cells[c]) == 1 for c in CONDITIONS)}
        if not complete:
            continue
        values = np.array([[cells[c][0]["doctor_is_correct"] for c in CONDITIONS] for q, cells in sorted(complete.items())], dtype=float)
        rng = np.random.default_rng(args.seed)
        indices = rng.integers(0, len(values), size=(args.bootstrap_reps, len(values)))
        for left, right in (("T1", "T0"), ("T2", "T0"), ("T1", "T2")):
            differences = values[:, CONDITIONS.index(left)] - values[:, CONDITIONS.index(right)]
            bootstrap = differences[indices].mean(axis=1)
            lo, hi = np.quantile(bootstrap, [.025, .975])
            contrasts.append({"doctor_level": level, "contrast": f"{left}-{right}",
                "matched_questions": len(values), "accuracy_difference": float(differences.mean()),
                "question_bootstrap_ci_low": float(lo), "question_bootstrap_ci_high": float(hi),
                "bootstrap_reps": args.bootstrap_reps, "seed": args.seed,
                "interpretation": "Exploratory question-sampling variability conditional on these doctors; not doctor-population CI or causal inference"})
    question_rows = []
    for qid in sorted({r["question_id"] for r in scored}, key=int):
        subset = [r for r in scored if r["question_id"] == qid]
        qrow = {"question_id": qid, "difficulty": subset[0]["difficulty"], "gold_answer_idx": subset[0]["gold_answer_idx"]}
        for c in CONDITIONS:
            cells = [r for r in subset if r["condition"] == c]
            qrow[c + "_n"] = len(cells)
            qrow[c + "_correct"] = sum(r["doctor_is_correct"] for r in cells)
            qrow[c + "_doctor_ids"] = ",".join(r["doctor_id"] for r in cells)
            qrow[c + "_answers"] = ",".join(r["doctor_answer_idx"] for r in cells)
        question_rows.append(qrow)
    dump(out / "scored_responses.json", {"responses": scored})
    (out / "scored_responses.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in scored), encoding="utf-8")
    export_fields = [k for k in scored[0] if k != "changes"]
    write_csv(out / "scored_responses.csv", scored, export_fields)
    write_csv(out / "completion.csv", completion)
    for name, rows in summaries.items():
        if rows:
            write_csv(out / f"{name}.csv", rows)
    if changes_flat:
        write_csv(out / "answer_changes.csv", changes_flat)
    write_csv(out / "by_question.csv", question_rows)
    if contrasts:
        write_csv(out / "question_paired_contrasts.csv", contrasts)
    db = out / "analysis.sqlite"
    subprocess.run([sys.executable, str(ROOT / "scripts/build_doctor_app_sqlite.py"),
        "--study-json", str(snap / "study.json"), "--source-csv", str(snap / "answer_source.csv"),
        "--responses-json", str(snap / "responses.json"), "--output-path", str(db),
        "--schema-path", str(out / "schema.sql"), "--source-label", "snapshot/answer_source.csv"], check=True, cwd=ROOT, capture_output=True, text=True)
    with sqlite3.connect(db) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert not conn.execute("PRAGMA foreign_key_check").fetchall()
        assert conn.execute("SELECT COUNT(*) FROM responses").fetchone()[0] == len(scored)
        sql_correct = conn.execute("SELECT SUM(r.doctor_answer_idx=k.gold_answer_idx) FROM responses r JOIN assignments a ON a.assignment_id=r.assignment_id JOIN answer_keys k ON k.study_id=a.study_id AND k.question_id=a.question_id").fetchone()[0]
        assert sql_correct == sum(r["doctor_is_correct"] for r in scored)
        conn.execute("CREATE TABLE response_changes (assignment_id TEXT, change_order INTEGER, from_answer TEXT, to_answer TEXT, changed_at TEXT, FOREIGN KEY(assignment_id) REFERENCES responses(assignment_id))")
        conn.executemany("INSERT INTO response_changes VALUES (?,?,?,?,?)", [(r["assignment_id"], r["change_order"], r["from"], r["to"], r["changed_at"]) for r in changes_flat])
        conn.execute("CREATE VIEW scored_responses AS SELECT r.*, k.gold_answer_idx, (r.doctor_answer_idx=k.gold_answer_idx) AS doctor_is_correct FROM responses r JOIN assignments a ON a.assignment_id=r.assignment_id JOIN answer_keys k ON k.study_id=a.study_id AND k.question_id=a.question_id")
        conn.commit()
        full_schema = conn.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' ORDER BY CASE type WHEN 'table' THEN 0 WHEN 'index' THEN 1 ELSE 2 END, rowid").fetchall()
    (out / "schema.sql").write_text("PRAGMA foreign_keys = ON;\n\n" + "\n\n".join(row[0] + ";" for row in full_schema) + "\n", encoding="utf-8")
    result = {"study_id": study["study_id"], "generated_at": generated_at,
        "generation_time_source": "explicit-provenance-time" if args.generated_at else "wall-clock",
        "audit": audit, "overall": summary(scored), "completion": completion, **summaries,
        "question_paired_contrasts": contrasts, "answer_changes": changes_flat,
        "t0_revised_after_first_advice_save": sum(r["baseline_revised_after_first_advice_save"] for r in scored),
        "sql_independent_correct_count": sql_correct}
    dump(out / "summary.json", result)
    lines = ["# 作答快照核查与描述性分析", "", f"生成时间参数：{result['generated_at']}（{result['generation_time_source']}）", "",
        "## 收集范围", "",
        f"共 {len(scored)} 条作答、{sum(c['answered'] > 0 for c in completion)} 位医生、{len(question_rows)} 道题。计划分配 {len(assignments)} 条。账号分组来自分配配置，不是实际资历证明。", "",
        "| 医生账号 | 已答/分配 | T0/T1/T2 | 页面累计计时（分钟） | 小于5秒的记录 | 修改过的题数 |",
        "|---|---:|---|---:|---:|---:|"]
    for c in completion:
        duration = f"{c['accumulated_minutes']:.1f}" if c['accumulated_minutes'] is not None else "未收集"
        lines.append(f"| {c['doctor_id']} | {c['answered']}/{c['assigned']} | {c['T0']}/{c['T1']}/{c['T2']} | {duration} | {c['short_lt5_count']} | {c['revised_records']} |")
    lines += ["", "## 数据核查", "",
        "核查通过：无重复作答键、无未知分配、无无效选项、分配元数据一致；题干与选项与源题库逐一一致；分配题目的标准答案齐全；T1建议均与标准答案一致、T2建议均为错误选项。SQLite完整性与外键检查通过，SQL独立复算正确数与JSON分析一致。",
        "", "所有原始记录保留，未按速度、正确率或修改行为自动排除。短时作答只作复核标记，不据此判断作答无效。", "",
        "## 条件结果", "", "| 条件 | 正确数/作答数 | 正确率 | 与CDSS选项一致数/有CDSS题数 | 选项一致率 |",
        "|---|---:|---:|---:|---:|"]
    for s in summaries["by_condition"]:
        match_count = f"{s['cdss_matches']}/{s['cdss_n']}" if s["cdss_n"] else "不适用"
        match_rate = pct(s["cdss_match_rate"]) if s["cdss_n"] else "不适用"
        lines.append(f"| {s['condition']} | {s['correct']}/{s['n']} | {pct(s['accuracy'])} | {match_count} | {match_rate} |")
    lines += ["", "T0为无建议，T1为正确建议，T2为错误建议。T2选项一致率表示最终选项与错误建议一致，不能仅凭一致性判定医生的主观采纳动机。", "",
        "| 比较 | 正确率差（百分点） | 题目bootstrap 95%区间（百分点） | 配对题数 |",
        "|---|---:|---:|---:|"]
    for c in contrasts:
        lines.append(f"| {c['doctor_level']} {c['contrast']} | {100*c['accuracy_difference']:+.1f} | [{100*c['question_bootstrap_ci_low']:+.1f}, {100*c['question_bootstrap_ci_high']:+.1f}] | {c['matched_questions']} |")
    lines += ["", f"bootstrap抽样单位为题目，{args.bootstrap_reps}次，随机种子{args.seed}；同一题三条件由不同医生回答，并在重采样时一起保留。这些区间仅描述固定当前医生条件下题目重采样的波动，不代表医生总体的不确定性，未报告显著性检验。", "",
        "## 医生内条件结果", "", "| 医生 | 条件 | 正确数/题数 | 正确率 |", "|---|---|---:|---:|"]
    for s in summaries["by_doctor_condition"]:
        lines.append(f"| {s['doctor_id']} | {s['condition']} | {s['correct']}/{s['n']} | {pct(s['accuracy'])} |")
    lines += ["", "## 数据质量与敏感性分析", "",
        f"共{len(changes_flat)}次答案修改，涉及{sum(r['change_count'] > 0 for r in scored)}道题；其中{result['t0_revised_after_first_advice_save']}道T0题在该医生首次保存CDSS阶段答案后修改。原始修改历史保存在JSON与answer_changes.csv/SQLite response_changes表中。", "",
        "页面计时是每次保存时累加的页面停留秒数，不能验证是否一直前台停留、是否离开页面或实际开始时间。updated_at为最后一次保存时间，可能被回看或修改覆盖；保存时间跨度不能替代总考试时间。90分钟要求的执行情况需结合现场记录确认。", "",
        "以下为事后探索性敏感性分析，不取代保留全部记录的主分析。T0回溯仅撤销在首次CDSS答案保存之后记录的修改；未记录精确首次曝光时间，不能保证完全无后续建议影响。", "",
        "| 分析口径 | 条件 | 正确数/题数 | 正确率 |", "|---|---|---:|---:|"]
    for label, key in (("排除页面累计计时<5秒", "sensitivity_exclude_lt5"), ("回溯T0后期修改", "sensitivity_t0_before_late_revisions")):
        for s in summaries[key]:
            lines.append(f"| {label} | {s['condition']} | {s['correct']}/{s['n']} | {pct(s['accuracy'])} |")
    lines += ["", "## 解释范围", "",
        "1. 结果仅描述本快照中的作答；合成快照不代表真实医生或临床试点。",
        "2. 同一医生同一题仅答一次，不能计算同一人同一题的C→I/I→C转换率，也不能用跨医生差异冒充个人变化。",
        "3. T0固定在前、T1/T2固定在后，T1/T2相对T0的差异可能同时受到阶段、熟悉度和疲劳影响，不能直接解释为纯因果效应。",
        "4. 条件、参与者和题目可能存在重复结构；不能将每条作答视为独立受试者。",
        "5. 未采集医生置信度、信任或验证行为，不能推断这些机制；账号S/J仅是配置分组。", "",
        "## 后续步骤", "",
        "真实研究应由研究者核对方案、材料授权、参与者信息与现场记录，并归档独立备份。合成示例仅用于软件验证。", "",
        "## 产物与复现", "",
        "snapshot/为原始答案、study与标准答案源；manifest.json记录SHA256。scored_responses.csv/JSONL为带金标准的分析数据；summary.json为结构化汇总；analysis.sqlite包含完整分配、已收集作答、标准答案和修改历史。analysis.xlsx由独立构建器生成，用于人工核对。", "",
        f"复现：先创建新的snapshot目录并复制三份输入，再运行 scripts/analyze_real_doctor_collection.py --snapshot-dir <新目录> --bootstrap-reps {args.bootstrap_reps} --seed {args.seed}。已完成目录不会被覆盖。", ""]
    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    files = {p.relative_to(out).as_posix(): {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size}
             for p in sorted(out.rglob("*")) if p.is_file()}
    dump(out / "manifest.json", {"created_at": result["generated_at"], "files": files,
        "analysis_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "note": "Input snapshot and analysis outputs before optional workbook generation; originals remain live and unmodified."})
    print(json.dumps({"output_dir": str(out), "audit": audit, "overall": result["overall"],
        "by_condition": result["by_condition"], "contrasts": contrasts}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
