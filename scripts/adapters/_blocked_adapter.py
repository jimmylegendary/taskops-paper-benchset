#!/usr/bin/env python3
"""Adapter that records explicit non-scored benchmark blockers.

This is not a stub: it writes a benchmark result explaining why the selected
benchmark cannot currently produce a real score through this repo.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_audit(benchmark_id: str) -> dict:
    audit = json.loads((ROOT / "data" / "harness_audit.json").read_text(encoding="utf-8"))
    for row in audit.get("benchmarks", []):
        if row.get("benchmark_id") == benchmark_id:
            return row
    return {
        "benchmark_id": benchmark_id,
        "status": "blocked_until_pinned",
        "scoring_path": "No harness audit row found.",
        "adapter_work": ["Add harness audit row"],
        "requirements": []
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-id", required=True)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--subset")
    args, extra = parser.parse_known_args()

    audit = load_audit(args.benchmark_id)
    audit_status = audit.get("status")
    status = "failed" if audit_status == "reported_only" else "blocked"
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "run_id": args.run_id,
        "arm": args.arm,
        "benchmark_id": args.benchmark_id,
        "subset": args.subset,
        "status": status,
        "score": {
            "primary": None,
            "metric_name": audit.get("primary_metric") or "benchmark_specific_score",
            "higher_is_better": True,
            "available": False
        },
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
        "artifacts": ["data/harness_audit.json"],
        "adapter": {
            "kind": "blocked_adapter",
            "audit_status": audit_status,
            "message": "No real score was produced. See harness audit and adapter_work for required setup.",
            "scoring_path": audit.get("scoring_path"),
            "adapter_work": audit.get("adapter_work", []),
            "requirements": audit.get("requirements", []),
            "extra_args": extra
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "error": f"benchmark_not_scoreable_yet:{audit_status}"
    }
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"ok": False, "status": status, "out": str(out), "audit_status": audit_status}, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
