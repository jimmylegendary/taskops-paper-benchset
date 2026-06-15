#!/usr/bin/env python3
"""Shared placeholder adapter.

Real benchmark adapters should replace these stubs. The stub still writes the
normal result contract so orchestration and reporting can be tested before
expensive harnesses are configured.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-id", required=True)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--subset")
    args, extra = parser.parse_known_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "run_id": args.run_id,
        "arm": args.arm,
        "benchmark_id": args.benchmark_id,
        "subset": args.subset,
        "status": "not_configured",
        "score": {
            "primary": null_score(),
            "metric_name": null_score(),
            "higher_is_better": True,
            "available": False
        },
        "raw_scores": {},
        "task_count": 0,
        "passed": null_score(),
        "failed": null_score(),
        "native_score": null_score(),
        "taskops_metrics": {
            "false_completion_rate": null_score(),
            "evidence_completeness": null_score(),
            "restart_recovery_rate": null_score(),
            "queue_integrity": null_score(),
            "reporting_coverage": null_score()
        },
        "artifacts": [],
        "adapter": {
            "kind": "stub",
            "message": "Replace this adapter with the benchmark-native harness before reporting results.",
            "extra_args": extra
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "status": "not_configured", "out": str(out)}, indent=2))
    return 0


def null_score():
    return None


if __name__ == "__main__":
    raise SystemExit(main())
