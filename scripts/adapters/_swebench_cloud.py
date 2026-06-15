#!/usr/bin/env python3
"""SWE-bench cloud adapter.

This adapter is score-producing only when real prediction data and a
SWE-bench API key are supplied. It never fabricates benchmark scores.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def empty_score() -> dict:
    return {
        "primary": None,
        "metric_name": "resolved_percent",
        "higher_is_better": True,
        "available": False
    }


def result_base(args: argparse.Namespace, status: str) -> dict:
    return {
        "run_id": args.run_id,
        "arm": args.arm,
        "benchmark_id": args.benchmark_id,
        "subset": args.subset,
        "status": status,
        "score": empty_score(),
        "raw_scores": {},
        "task_count": 0,
        "passed": None,
        "failed": None,
        "native_score": None,
        "taskops_metrics": {
            "false_completion_rate": None,
            "evidence_completeness": None,
            "restart_recovery_rate": None,
            "queue_integrity": None,
            "reporting_coverage": None
        },
        "artifacts": [],
        "adapter": {
            "kind": "swebench_cloud",
            "source": "sb-cli",
            "message": None
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }


def parse_report(report_dir: Path) -> dict | None:
    candidates = sorted(report_dir.rglob("*.json"))
    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        score = extract_score(data)
        if score is not None:
            return {"path": path, "data": data, "score": score}
    return None


def extract_score(data: object) -> float | None:
    if isinstance(data, dict):
        for key in ("resolved_percent", "resolve_rate", "pass_rate", "score"):
            value = data.get(key)
            if isinstance(value, (int, float)):
                return float(value)
        resolved = data.get("resolved") or data.get("resolved_ids")
        total = data.get("total") or data.get("total_instances") or data.get("submitted")
        if isinstance(resolved, list) and isinstance(total, int) and total:
            return len(resolved) / total
        if isinstance(resolved, int) and isinstance(total, int) and total:
            return resolved / total
        for value in data.values():
            score = extract_score(value)
            if score is not None:
                return score
    if isinstance(data, list):
        total = len(data)
        if total and all(isinstance(item, dict) for item in data):
            resolved_count = sum(1 for item in data if item.get("resolved") is True or item.get("status") in {"resolved", "passed"})
            if resolved_count:
                return resolved_count / total
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-id", default="swe_bench_verified")
    parser.add_argument("--subset", default="verified")
    parser.add_argument("--arm", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--predictions-path", default=os.environ.get("TASKOPS_BENCH_SWEBENCH_PREDICTIONS"))
    parser.add_argument("--report-dir", default=os.environ.get("TASKOPS_BENCH_SWEBENCH_REPORT_DIR"))
    parser.add_argument("--split", default=os.environ.get("TASKOPS_BENCH_SWEBENCH_SPLIT", "test"))
    parser.add_argument("--wait", type=int, default=int(os.environ.get("TASKOPS_BENCH_SWEBENCH_WAIT", "1")))
    args = parser.parse_args()

    out = Path(args.out)
    result = result_base(args, "blocked")
    report_dir = Path(args.report_dir) if args.report_dir else out.parent / "raw" / "sb-cli-reports"

    if not args.predictions_path:
        result["adapter"]["message"] = "Missing predictions file. Set TASKOPS_BENCH_SWEBENCH_PREDICTIONS or pass --predictions-path."
        result["error"] = "missing_predictions_path"
        write_json(out, result)
        return 2
    predictions = Path(args.predictions_path)
    if not predictions.exists():
        result["adapter"]["message"] = f"Predictions file does not exist: {predictions}"
        result["error"] = "predictions_path_not_found"
        write_json(out, result)
        return 2
    if not os.environ.get("SWEBENCH_API_KEY"):
        result["adapter"]["message"] = "Missing SWEBENCH_API_KEY required by sb-cli."
        result["error"] = "missing_swebench_api_key"
        result["artifacts"].append(str(predictions))
        write_json(out, result)
        return 2

    command = [
        "uvx",
        "--with",
        "typing-extensions",
        "--from",
        "sb-cli",
        "sb-cli",
        "submit",
        "swe-bench_verified",
        args.split,
        "--predictions_path",
        str(predictions),
        "--run_id",
        args.run_id,
        "--output_dir",
        str(report_dir),
        "--wait_for_evaluation",
        str(args.wait),
        "--gen_report",
        "1"
    ]
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    result["adapter"]["command"] = command
    result["adapter"]["stdout"] = completed.stdout[-4000:]
    result["adapter"]["stderr"] = completed.stderr[-4000:]
    result["artifacts"].append(str(predictions))
    result["artifacts"].append(str(report_dir))
    if completed.returncode != 0:
        result["status"] = "failed"
        result["adapter"]["message"] = "sb-cli submit failed."
        result["error"] = "sb_cli_submit_failed"
        write_json(out, result)
        return completed.returncode

    parsed = parse_report(report_dir)
    if parsed is None:
        result["status"] = "failed"
        result["adapter"]["message"] = "sb-cli completed but no parseable score was found in report JSON files."
        result["error"] = "score_not_found"
        write_json(out, result)
        return 1

    score = parsed["score"]
    result["status"] = "completed"
    result["score"] = {
        "primary": score,
        "metric_name": "resolved_percent",
        "higher_is_better": True,
        "available": True
    }
    result["native_score"] = score
    result["raw_scores"] = parsed["data"]
    result["adapter"]["message"] = "SWE-bench cloud evaluation completed."
    result["artifacts"].append(str(parsed["path"]))
    write_json(out, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
