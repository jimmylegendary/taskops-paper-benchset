#!/usr/bin/env python3
"""Adapter that writes Qwen3.6-27B reported benchmark scores.

This is for baseline table materialization. It does not claim a fresh benchmark
execution and it must not be used as evidence of TaskOps lift.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORTED_PATH = ROOT / "data" / "qwen3_6_27b_reported_results.json"


def load_reported_score(benchmark_id: str) -> dict:
    data = json.loads(REPORTED_PATH.read_text(encoding="utf-8"))
    matches = [row for row in data.get("reported_results", []) if row.get("benchmark_id") == benchmark_id]
    if not matches:
        raise RuntimeError(f"no Qwen3.6-27B reported score for benchmark_id={benchmark_id}")
    return matches[0]


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-id", required=True)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--subset")
    args, extra = parser.parse_known_args()

    out = Path(args.out)
    try:
        row = load_reported_score(args.benchmark_id)
    except Exception as exc:  # noqa: BLE001 - benchmark runner needs a result artifact.
        result = {
            "run_id": args.run_id,
            "arm": args.arm,
            "benchmark_id": args.benchmark_id,
            "subset": args.subset,
            "status": "blocked",
            "score": {
                "primary": None,
                "metric_name": "reported_qwen3_6_27b_score",
                "higher_is_better": True,
                "available": False,
            },
            "raw_scores": {},
            "task_count": 0,
            "passed": None,
            "failed": None,
            "native_score": None,
            "taskops_metrics": {},
            "artifacts": ["data/qwen3_6_27b_reported_results.json"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "adapter": {
                "kind": "reported_qwen",
                "message": "No reported Qwen3.6-27B score is available for this benchmark id.",
                "extra_args": extra,
            },
            "error": str(exc),
        }
        write_json(out, result)
        print(json.dumps({"ok": False, "status": "blocked", "out": str(out), "error": str(exc)}, indent=2))
        return 2

    score = float(row["score"])
    result = {
        "run_id": args.run_id,
        "arm": args.arm,
        "benchmark_id": args.benchmark_id,
        "subset": args.subset,
        "status": "completed",
        "score": {
            "primary": score,
            "metric_name": row.get("unit", "reported_score"),
            "higher_is_better": True,
            "available": True,
            "source": "reported_qwen3_6_27b",
        },
        "raw_scores": {
            "reported_row": row,
            "source_file": "data/qwen3_6_27b_reported_results.json",
            "extra_args": extra,
        },
        "task_count": 0,
        "passed": None,
        "failed": None,
        "native_score": score,
        "taskops_metrics": {
            "false_completion_rate": None,
            "evidence_completeness": 1.0,
            "restart_recovery_rate": None,
            "queue_integrity": 1.0,
            "reporting_coverage": None,
        },
        "artifacts": ["data/qwen3_6_27b_reported_results.json"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "adapter": {
            "kind": "reported_qwen",
            "message": "Materialized Qwen3.6-27B reported benchmark score. This is baseline data, not a fresh TaskOps evaluation run.",
            "subset": args.subset,
        },
    }
    write_json(out, result)
    print(json.dumps({"ok": True, "status": "completed", "score": result["score"], "out": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
