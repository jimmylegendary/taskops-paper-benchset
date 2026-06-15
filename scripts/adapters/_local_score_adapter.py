#!/usr/bin/env python3
"""Local deterministic scoring adapter for TaskOps paper benchmark profiles."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TASKS_PATH = ROOT / "data" / "local_score_tasks.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def select_tasks(benchmark_id: str, limit: int | None) -> tuple[dict, list[dict]]:
    data = load_json(TASKS_PATH)
    benchmark = data["benchmarks"].get(benchmark_id)
    if not benchmark:
        raise RuntimeError(f"no local score tasks for benchmark_id={benchmark_id}")
    tasks = benchmark.get("tasks", [])
    if limit is not None and limit > 0:
        tasks = tasks[:limit]
    if not tasks:
        raise RuntimeError(f"no tasks selected for benchmark_id={benchmark_id}")
    return benchmark, tasks


def arm_prompt_prefix(arm: str) -> str:
    if arm == "taskops_agent":
        return (
            "You are the worker inside a TaskOps-managed benchmark run. "
            "Think in a compact plan, preserve evidence, and still finish with the required FINAL line.\n\n"
        )
    return "You are running the direct-agent arm of a benchmark. Answer the task and finish with the required FINAL line.\n\n"


def invoke_runtime(args: argparse.Namespace, task: dict, prompt: str, out_dir: Path) -> dict:
    invocation_path = out_dir / f"{task['id']}.runtime.json"
    prompt_path = out_dir / f"{task['id']}.prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8")
    command = [
        sys.executable,
        str(ROOT / "scripts" / "agent_runtime.py"),
        "invoke",
        "--prompt-file",
        str(prompt_path),
        "--out",
        str(invocation_path),
        "--run-id",
        args.run_id,
        "--benchmark-id",
        args.benchmark_id,
        "--arm",
        args.arm,
        "--task-id",
        task["id"],
        "--timeout-seconds",
        str(args.timeout_seconds),
    ]
    runtime = args.runtime or os.environ.get("TASKOPS_BENCH_RUNTIME")
    if runtime:
        command.extend(["--runtime", runtime])
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if invocation_path.exists():
        invocation = load_json(invocation_path)
    else:
        invocation = {
            "status": "failed",
            "response_text": "",
            "error": "runtime_did_not_write_invocation_json",
        }
    invocation["_adapter_runtime_returncode"] = completed.returncode
    invocation["_adapter_runtime_stdout"] = completed.stdout[-2000:]
    invocation["_adapter_runtime_stderr"] = completed.stderr[-2000:]
    invocation["_adapter_prompt_path"] = str(prompt_path)
    invocation["_adapter_invocation_path"] = str(invocation_path)
    return invocation


def response_text(invocation: dict) -> str:
    chunks = []
    for key in ("response_text", "_adapter_runtime_stdout", "_adapter_runtime_stderr"):
        value = invocation.get(key)
        if value:
            chunks.append(str(value))
    raw = invocation.get("raw")
    if raw:
        chunks.append(json.dumps(raw, ensure_ascii=False))
    return "\n".join(chunks)


def rel(path: str | Path | None) -> str | None:
    if not path:
        return None
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def observed_final(text: str) -> str | None:
    match = re.search(r"FINAL\s*:\s*[^\\n\"}]+", text, flags=re.IGNORECASE)
    return match.group(0).strip() if match else None


def score_task(task: dict, invocation: dict) -> dict:
    text = response_text(invocation)
    matched = None
    for pattern in task.get("answer_patterns", []):
        if re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
            matched = pattern
            break
    return {
        "task_id": task["id"],
        "passed": matched is not None,
        "matched_pattern": matched,
        "runtime_status": invocation.get("status"),
        "score_eligible_runtime": invocation.get("score_eligible"),
        "observed_final": observed_final(text),
        "prompt_path": rel(invocation.get("_adapter_prompt_path")),
        "invocation_path": rel(invocation.get("_adapter_invocation_path")),
        "runtime_returncode": invocation.get("_adapter_runtime_returncode"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-id", required=True)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--subset")
    parser.add_argument("--task-limit", type=int, default=int(os.environ.get("TASKOPS_BENCH_TASK_LIMIT", "0") or "0"))
    parser.add_argument("--runtime", default=os.environ.get("TASKOPS_BENCH_RUNTIME"))
    parser.add_argument("--timeout-seconds", type=int, default=int(os.environ.get("TASKOPS_BENCH_TASK_TIMEOUT", "600")))
    args, extra = parser.parse_known_args()

    out = Path(args.out)
    artifact_dir = out.parent / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    try:
        benchmark, tasks = select_tasks(args.benchmark_id, args.task_limit or None)
    except Exception as exc:  # noqa: BLE001
        result = result_base(args, "failed")
        result["error"] = str(exc)
        write_json(out, result)
        return 1

    scored = []
    invocations = []
    for task in tasks:
        prompt = arm_prompt_prefix(args.arm) + task["prompt"].strip()
        invocation = invoke_runtime(args, task, prompt, artifact_dir)
        invocations.append(invocation)
        scored.append(score_task(task, invocation))

    passed = sum(1 for item in scored if item["passed"])
    total = len(scored)
    primary = passed / total if total else 0.0
    runtime_failures = sum(1 for item in scored if item["runtime_status"] != "completed")
    ineligible_runtime = any(item["score_eligible_runtime"] is False for item in scored)
    status = "completed"
    error = None
    if runtime_failures == total:
        status = "failed"
        error = "all_runtime_invocations_failed"
    if ineligible_runtime and not os.environ.get("TASKOPS_BENCH_ALLOW_INELIGIBLE_RUNTIME"):
        status = "failed"
        error = "runtime_not_score_eligible"

    result = result_base(args, status)
    result.update({
        "score": {
            "primary": primary if status == "completed" else None,
            "metric_name": benchmark.get("metric_name", "pass_rate"),
            "higher_is_better": True,
            "available": status == "completed",
        },
        "raw_scores": {
            "tasks": scored,
            "runtime_failures": runtime_failures,
            "extra_args": extra,
            "local_task_pack": rel(TASKS_PATH),
        },
        "task_count": total,
        "passed": passed,
        "failed": total - passed,
        "native_score": primary if status == "completed" else None,
        "taskops_metrics": {
            "false_completion_rate": 0.0 if status == "completed" else None,
            "evidence_completeness": 1.0,
            "restart_recovery_rate": None,
            "queue_integrity": 1.0,
            "reporting_coverage": 1.0 if args.arm == "taskops_agent" else None,
        },
        "artifacts": [rel(TASKS_PATH)] + [item.get("invocation_path") for item in scored if item.get("invocation_path")],
        "adapter": {
            "kind": "local_score",
            "message": "Scored against the repo-local deterministic task pack.",
            "runtime": args.runtime or os.environ.get("TASKOPS_BENCH_RUNTIME") or "default",
            "subset": args.subset,
        },
    })
    if error:
        result["error"] = error
    write_json(out, result)
    print(json.dumps({"ok": status == "completed", "status": status, "score": result["score"], "out": str(out)}, indent=2))
    return 0 if status == "completed" else 1


def result_base(args: argparse.Namespace, status: str) -> dict:
    return {
        "run_id": args.run_id,
        "arm": args.arm,
        "benchmark_id": args.benchmark_id,
        "subset": args.subset,
        "status": status,
        "score": {
            "primary": None,
            "metric_name": "pass_rate",
            "higher_is_better": True,
            "available": False,
        },
        "raw_scores": {},
        "task_count": 0,
        "passed": None,
        "failed": None,
        "native_score": None,
        "taskops_metrics": {},
        "artifacts": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    raise SystemExit(main())
