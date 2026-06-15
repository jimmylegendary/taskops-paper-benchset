#!/usr/bin/env python3
"""TaskOps-backed benchmark-suite orchestration helper."""

from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CONFIG = ROOT / "config"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"{path} does not contain expected text: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def run_cmd(args: list[str], cwd: Path = ROOT, capture: bool = True) -> subprocess.CompletedProcess:
    kwargs = {"cwd": str(cwd), "text": True}
    if capture:
        kwargs.update({"stdout": subprocess.PIPE, "stderr": subprocess.PIPE})
    return subprocess.run(args, check=True, **kwargs)


def run_cmd_json(args: list[str], cwd: Path = ROOT) -> dict:
    completed = run_cmd(args, cwd=cwd, capture=True)
    return json.loads(completed.stdout)


def taskops_available() -> bool:
    return shutil.which("taskops") is not None


def benchmark_sources() -> dict[str, dict]:
    return {item["id"]: item for item in load_json(DATA / "benchmark_sources.json")["sources"]}


def run_matrix() -> dict:
    return load_json(DATA / "run_matrix.json")


def adapter_config() -> dict:
    return load_json(CONFIG / "adapters.json")["adapters"]


def parse_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    values = [item.strip() for item in value.split(",") if item.strip()]
    return values or None


def resolve_mode(mode: str, arms: str, benchmarks: list[str] | None = None) -> list[dict]:
    matrix = run_matrix()
    sources = benchmark_sources()
    adapters = adapter_config()
    if mode not in matrix["suite_modes"]:
        raise SystemExit(f"unknown mode: {mode}")
    arm_ids = [arm["id"] for arm in matrix["arms"]]
    selected_arms = arm_ids if arms == "both" else [arms]
    for arm in selected_arms:
        if arm not in arm_ids:
            raise SystemExit(f"unknown arm: {arm}")

    items = []
    order = 1
    benchmark_filter = set(benchmarks or [])
    for benchmark in matrix["suite_modes"][mode]["benchmarks"]:
        benchmark_id = benchmark["benchmark_id"]
        if benchmark_filter and benchmark_id not in benchmark_filter:
            continue
        if benchmark_id not in sources:
            raise SystemExit(f"run matrix references unknown benchmark: {benchmark_id}")
        for arm in selected_arms:
            result_path = f"results/{{run_id}}/{arm}/{benchmark_id}/result.json"
            items.append({
                "order": order,
                "mode": mode,
                "arm": arm,
                "benchmark_id": benchmark_id,
                "task_count": benchmark.get("task_count"),
                "source": sources[benchmark_id],
                "adapter": adapters.get(benchmark_id, {}),
                "result_path_template": result_path
            })
            order += 1
    missing = benchmark_filter - {item["benchmark_id"] for item in items}
    if missing:
        raise SystemExit(f"unknown or unavailable benchmark(s) for mode={mode}: {', '.join(sorted(missing))}")
    return items


def task_id_for(item: dict) -> str:
    safe_benchmark = item["benchmark_id"].replace("_", "-")
    return f"bench-{item['arm'].replace('_', '-')}-{safe_benchmark}"


def build_task_spec(mode: str, arms: str, run_id: str, benchmarks: list[str] | None = None) -> dict:
    tasks = []
    for item in resolve_mode(mode, arms, benchmarks=benchmarks):
        source = item["source"]
        adapter = item["adapter"]
        benchmark_id = item["benchmark_id"]
        arm = item["arm"]
        result_path = item["result_path_template"].format(run_id=run_id)
        task_count = item["task_count"]
        command = adapter.get("command_template", "UNCONFIGURED").format(
            arm=arm,
            run_id=run_id,
            result_path=result_path,
            benchmark_id=benchmark_id,
            task_count=task_count
        )
        title = f"Run {source['name']} ({arm})"
        objective = (
            f"Run benchmark `{benchmark_id}` for arm `{arm}` using Qwen/Qwen3.6-27B. "
            f"Task count target: {task_count}. Write benchmark-native outputs and the normalized result contract to `{result_path}`."
        )
        responsibility = (
            "Own adapter setup, execution, native benchmark scoring, normalized result writing, "
            "and TaskOps orchestration metric capture for this benchmark arm."
        )
        completion = (
            f"`{result_path}` exists and contains run_id, arm, benchmark_id, status, native_score, "
            "taskops_metrics, and artifacts; failures must be explicit rather than silently marked complete."
        )
        tasks.append({
            "id": task_id_for(item),
            "title": title,
            "objective": objective,
            "responsibility": responsibility,
            "completionCriteria": completion,
            "status": "pending",
            "runReadiness": "runnable",
            "runReadinessReason": (
                "Benchmark arm has a fixed manifest entry and an adapter contract. "
                f"Configured={bool(adapter.get('configured'))}; command={command}"
            ),
            "understandingLevel": "known",
            "order": item["order"]
        })
    return {
        "versionId": "tgv-root-v2",
        "version": "v2",
        "summary": f"{mode} benchmark matrix for {arms} arms",
        "selected": True,
        "logSeedLine": f"Generated by scripts/taskops_bench.py for mode={mode}, arms={arms}, run_id={run_id}.",
        "tasks": tasks
    }


def init_work(args: argparse.Namespace) -> None:
    if not taskops_available():
        raise SystemExit("taskops CLI is not on PATH")
    work_dir = Path(args.work_dir).resolve()
    if work_dir.exists():
        if not args.force:
            raise SystemExit(f"{work_dir} already exists; pass --force to replace")
        shutil.rmtree(work_dir)
    run_id = args.run_id or f"{args.mode}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    objective = (
        f"Run the TaskOps paper benchmark suite in mode={args.mode}, arms={args.arms}, "
        "comparing direct-agent and TaskOps-managed Qwen3.6-27B execution where selected."
    )
    run_cmd([
        "taskops", "init", str(work_dir),
        "--id", f"taskops-bench-{args.mode}",
        "--title", f"TaskOps Bench {args.mode}",
        "--objective", objective,
        "--language", "en"
    ])
    benchmarks = parse_csv(getattr(args, "benchmarks", None))
    spec = build_task_spec(args.mode, args.arms, run_id, benchmarks=benchmarks)
    generated_dir = work_dir / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    spec_path = generated_dir / "root-benchmark-matrix.spec.json"
    write_json(spec_path, spec)
    write_json(generated_dir / "run-metadata.json", {
        "run_id": run_id,
        "mode": args.mode,
        "arms": args.arms,
        "benchmarks": benchmarks or "all",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_repo": "https://github.com/jimmylegendary/taskops-paper-benchset"
    })
    run_cmd(["taskops", "decompose", str(work_dir), "--task-group-id", "tg-root", "--spec", str(spec_path)])
    # `taskops decompose` writes the new version, but the initial snapshot still
    # points at the empty init version. For a generated benchmark work graph the
    # matrix version is the active truth, so promote it immediately.
    replace_once(work_dir / "task-groups" / "tg-root" / "index.md", "activeVersionId: tgv-root-v1", "activeVersionId: tgv-root-v2")
    replace_once(work_dir / "task-groups" / "tg-root" / "versions" / "tgv-root-v1" / "index.md", "selected: true", "selected: false")
    replace_once(work_dir / "snapshots" / "snapshot-root-v1.md", "versionId: tgv-root-v1", "versionId: tgv-root-v2")
    run_cmd(["taskops", "validate", str(work_dir)])
    run_cmd(["taskops", "summary", str(work_dir)])
    run_cmd(["taskops", "queue", "sync", str(work_dir), "--json"])
    print(json.dumps({
        "ok": True,
        "work_dir": str(work_dir),
        "run_id": run_id,
        "mode": args.mode,
        "arms": args.arms,
        "benchmarks": benchmarks or "all",
        "task_count": len(spec["tasks"])
    }, indent=2))


def list_items(args: argparse.Namespace) -> None:
    items = resolve_mode(args.mode, args.arms, benchmarks=parse_csv(getattr(args, "benchmarks", None)))
    print(json.dumps({
        "mode": args.mode,
        "arms": args.arms,
        "count": len(items),
        "items": [
            {
                "task_id": task_id_for(item),
                "arm": item["arm"],
                "benchmark_id": item["benchmark_id"],
                "name": item["source"]["name"],
                "task_count": item["task_count"],
                "adapter_configured": bool(item["adapter"].get("configured"))
            }
            for item in items
        ]
    }, indent=2))


def adapter_status(args: argparse.Namespace) -> None:
    items = resolve_mode(args.mode, args.arms, benchmarks=parse_csv(getattr(args, "benchmarks", None)))
    print(json.dumps({
        "mode": args.mode,
        "arms": args.arms,
        "adapters": [
            {
                "benchmark_id": item["benchmark_id"],
                "arm": item["arm"],
                "configured": bool(item["adapter"].get("configured")),
                "kind": item["adapter"].get("kind"),
                "expected_repo": item["adapter"].get("expected_repo"),
                "command_template": item["adapter"].get("command_template")
            }
            for item in items
        ]
    }, indent=2))


def smoke(args: argparse.Namespace) -> None:
    with tempfile.TemporaryDirectory(prefix="taskops-bench-smoke-") as tmp:
        work_dir = Path(tmp) / "work"
        init_args = argparse.Namespace(
            work_dir=str(work_dir),
            mode=args.mode,
            arms=args.arms,
            run_id="smoke",
            force=False
        )
        init_work(init_args)
        for i in range(args.steps):
            out = run_cmd([
                "taskops", "runner", "once", str(work_dir),
                "--runtime", "dry-run",
                "--runner-id", "taskops-bench-smoke",
                "--report-sink", "ledger",
                "--json"
            ])
            print(out.stdout.strip())
            if '"claimed": false' in out.stdout:
                break
        run_cmd(["taskops", "validate", str(work_dir)])
        print(json.dumps({"ok": True, "smoke_work_dir": str(work_dir), "steps": args.steps}, indent=2))


def item_lookup(mode: str, arms: str, benchmarks: list[str] | None = None) -> dict[str, dict]:
    return {task_id_for(item): item for item in resolve_mode(mode, arms, benchmarks=benchmarks)}


def render_adapter_command(item: dict, run_id: str, result_path: str) -> list[str]:
    template = item["adapter"].get("command_template")
    if not template:
        raise RuntimeError(f"No adapter command_template for {item['benchmark_id']}")
    command = template.format(
        arm=item["arm"],
        run_id=run_id,
        result_path=result_path,
        benchmark_id=item["benchmark_id"],
        task_count=item.get("task_count"),
    )
    return shlex.split(command)


def validate_result_contract(path: Path, *, run_id: str, arm: str, benchmark_id: str, allow_not_configured: bool = False) -> dict:
    if not path.exists():
        raise RuntimeError(f"adapter did not write result JSON: {path}")
    result = load_json(path)
    required = [
        "run_id",
        "arm",
        "benchmark_id",
        "status",
        "score",
        "raw_scores",
        "task_count",
        "native_score",
        "taskops_metrics",
        "artifacts",
    ]
    missing = [key for key in required if key not in result]
    if missing:
        raise RuntimeError(f"{path} is missing required result keys: {', '.join(missing)}")
    mismatches = {
        "run_id": (result.get("run_id"), run_id),
        "arm": (result.get("arm"), arm),
        "benchmark_id": (result.get("benchmark_id"), benchmark_id),
    }
    bad = [key for key, (actual, expected) in mismatches.items() if actual != expected]
    if bad:
        details = ", ".join(f"{key}={mismatches[key][0]!r} expected {mismatches[key][1]!r}" for key in bad)
        raise RuntimeError(f"{path} identity mismatch: {details}")
    if not isinstance(result["taskops_metrics"], dict):
        raise RuntimeError(f"{path} taskops_metrics must be an object")
    if not isinstance(result["artifacts"], list):
        raise RuntimeError(f"{path} artifacts must be a list")
    if not isinstance(result["score"], dict):
        raise RuntimeError(f"{path} score must be an object")
    if not isinstance(result["raw_scores"], dict):
        raise RuntimeError(f"{path} raw_scores must be an object")

    status = result.get("status")
    if status not in {"completed", "failed", "blocked", "not_configured"}:
        raise RuntimeError(f"{path} has invalid status: {status!r}")
    if status == "not_configured":
        if allow_not_configured:
            return result
        raise RuntimeError(f"{path} is not a real benchmark score: status=not_configured")
    if status != "completed":
        return result

    score = result["score"]
    primary = score.get("primary")
    if not isinstance(primary, (int, float)):
        raise RuntimeError(f"{path} completed result must include numeric score.primary")
    if not score.get("metric_name"):
        raise RuntimeError(f"{path} completed result must include score.metric_name")
    return result


def load_run_metadata(work_dir: Path) -> dict:
    path = work_dir / "generated" / "run-metadata.json"
    if not path.exists():
        raise RuntimeError(f"missing run metadata: {path}; run init-work first")
    return load_json(path)


def write_node_state_report(work_dir: Path, out_path: Path) -> dict:
    show = run_cmd_json(["taskops", "show", str(work_dir), "--json"])
    queue = run_cmd_json(["taskops", "queue", "list", str(work_dir), "--json"])
    reports = run_cmd_json(["taskops", "queue", "reports", str(work_dir), "--json"])
    tasks = []
    for task_path in sorted(work_dir.glob("task-groups/*/versions/*/tasks/*.md")):
        fm = read_frontmatter(task_path)
        eow_path = task_path.parent.parent / "eow" / f"eow-{fm.get('id')}.md"
        tasks.append({
            "task_id": fm.get("id"),
            "task_group_version_id": fm.get("taskGroupVersionId"),
            "status": fm.get("status"),
            "run_readiness": fm.get("runReadiness"),
            "has_eow": eow_path.exists(),
            "path": str(task_path.relative_to(work_dir))
        })
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "work_dir": str(work_dir),
        "closure": show.get("closure", {}),
        "errors": show.get("errors", []),
        "warnings": show.get("warnings", []),
        "queue_rows": queue.get("rows", []),
        "progress_reports": reports.get("rows", []),
        "tasks": tasks
    }
    write_json(out_path, report)
    return report


def read_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    fm = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fm[key.strip()] = value.strip()
    return fm


def rewrite_task_status(work_dir: Path, task_id: str, *, status: str, readiness: str, reason: str) -> None:
    matches = list(work_dir.glob(f"task-groups/*/versions/*/tasks/{task_id}.md"))
    if not matches:
        raise RuntimeError(f"could not find task markdown for {task_id}")
    path = matches[0]
    lines = path.read_text(encoding="utf-8").splitlines()
    replacements = {
        "status": status,
        "runReadiness": readiness,
        "runReadinessReason": reason.replace("\n", " ")[:500]
    }
    seen = set()
    out = []
    in_fm = False
    for idx, line in enumerate(lines):
        if idx == 0 and line == "---":
            in_fm = True
            out.append(line)
            continue
        if in_fm and line == "---":
            for key, value in replacements.items():
                if key not in seen:
                    out.append(f"{key}: {value}")
            in_fm = False
            out.append(line)
            continue
        if in_fm and ":" in line:
            key = line.split(":", 1)[0].strip()
            if key in replacements:
                out.append(f"{key}: {replacements[key]}")
                seen.add(key)
                continue
        out.append(line)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def run_benchmarks(args: argparse.Namespace) -> None:
    if not taskops_available():
        raise SystemExit("taskops CLI is not on PATH")
    work_dir = Path(args.work_dir).resolve()
    benchmarks = parse_csv(args.benchmarks)
    run_id = args.run_id or f"{args.mode}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    if args.init or not work_dir.exists():
        init_args = argparse.Namespace(
            work_dir=str(work_dir),
            mode=args.mode,
            arms=args.arms,
            benchmarks=args.benchmarks,
            run_id=run_id,
            force=args.force
        )
        init_work(init_args)
    metadata = load_run_metadata(work_dir)
    run_id = metadata["run_id"]
    mode = metadata["mode"]
    arms = metadata["arms"]
    metadata_benchmarks = None if metadata.get("benchmarks") == "all" else metadata.get("benchmarks")
    lookup = item_lookup(mode, arms, benchmarks=metadata_benchmarks)
    results_dir = ROOT / "results" / run_id
    runner_id = args.runner_id or f"taskops-bench-{run_id}"
    allow_stubs = bool(getattr(args, "allow_stubs_for_smoke", False))
    summary = {
        "run_id": run_id,
        "mode": mode,
        "arms": arms,
        "work_dir": str(work_dir),
        "allow_stubs_for_smoke": allow_stubs,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": None,
        "status": "running",
        "steps": [],
        "error_count": 0
    }
    max_steps = args.max_steps if args.max_steps is not None else len(lookup)
    for _ in range(max_steps):
        run_cmd(["taskops", "queue", "sync", str(work_dir), "--json"])
        claim = run_cmd_json([
            "taskops", "queue", "claim", str(work_dir),
            "--runner-id", runner_id,
            "--ttl-seconds", str(args.ttl_seconds),
            "--json"
        ])
        if not claim.get("claimed"):
            summary["status"] = "queue_empty"
            break
        item_row = claim["item"]
        lease = claim["lease"]
        task_id = item_row["task_id"]
        step = {
            "task_id": task_id,
            "queue_item_id": item_row.get("id"),
            "lease_id": lease.get("id"),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
            "release_status": None,
            "result_path": None,
            "result_status": None,
            "native_score": None,
            "error": None
        }
        try:
            if task_id not in lookup:
                raise RuntimeError(f"claimed task is not in this benchmark matrix: {task_id}")
            item = lookup[task_id]
            result_path = Path(item["result_path_template"].format(run_id=run_id))
            step["result_path"] = str(result_path)
            command = render_adapter_command(item, run_id, str(result_path))
            step["command"] = command
            if not item["adapter"].get("configured") and not allow_stubs:
                raise RuntimeError(
                    f"adapter not configured for {item['benchmark_id']}; "
                    "real scoring runs refuse stubs. Use --allow-stubs-for-smoke only for orchestration smoke tests."
                )
            completed = subprocess.run(
                command,
                cwd=str(ROOT),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False
            )
            step["adapter_stdout"] = completed.stdout.strip()
            step["adapter_stderr"] = completed.stderr.strip()
            result = validate_result_contract(
                ROOT / result_path,
                run_id=run_id,
                arm=item["arm"],
                benchmark_id=item["benchmark_id"],
                allow_not_configured=allow_stubs
            )
            step["result_status"] = result.get("status")
            step["native_score"] = result.get("native_score")
            step["score"] = result.get("score")
            if completed.returncode != 0:
                raise RuntimeError(f"adapter exited with status {completed.returncode}: {step['adapter_stderr'] or step['adapter_stdout']}")
            if result.get("status") != "completed" and not (allow_stubs and result.get("status") == "not_configured"):
                raise RuntimeError(f"adapter did not produce a completed score: status={result.get('status')}")
            close = run_cmd_json([
                "taskops", "close", str(work_dir), task_id,
                "--reason", "manual_verified",
                "--json"
            ])
            step["close"] = close
            run_cmd_json(["taskops", "queue", "release", str(work_dir), lease["id"], "--status", "done", "--json"])
            step["release_status"] = "done"
        except Exception as exc:  # noqa: BLE001 - runner must record and release honestly.
            step["error"] = str(exc)
            try:
                if step.get("result_status") in {"blocked", "failed"}:
                    rewrite_task_status(
                        work_dir,
                        task_id,
                        status="blocked",
                        readiness="blocked",
                        reason=f"Adapter result status={step.get('result_status')}: {step.get('error') or 'see result JSON'}"
                    )
                run_cmd_json(["taskops", "queue", "release", str(work_dir), lease["id"], "--status", "failed", "--json"])
                step["release_status"] = "failed"
            except Exception as release_exc:  # noqa: BLE001
                step["release_status"] = "release_failed"
                step["release_error"] = str(release_exc)
            if not args.continue_on_error:
                step["finished_at"] = datetime.now(timezone.utc).isoformat()
                summary["steps"].append(step)
                summary["status"] = "failed"
                break
            summary["error_count"] += 1
        step["finished_at"] = datetime.now(timezone.utc).isoformat()
        summary["steps"].append(step)
        write_json(results_dir / "summary.json", summary)
    else:
        summary["status"] = "max_steps"

    run_cmd(["taskops", "queue", "sync", str(work_dir), "--json"])
    node_state = write_node_state_report(work_dir, results_dir / "taskops-node-state.json")
    summary["finished_at"] = datetime.now(timezone.utc).isoformat()
    if summary.get("error_count", 0) > 0:
        summary["status"] = "failed"
    elif node_state["closure"].get("complete"):
        summary["status"] = "completed"
    elif summary["status"] == "running":
        summary["status"] = "completed" if node_state["closure"].get("complete") else "incomplete"
    summary["closure"] = node_state["closure"]
    summary["result_count"] = len([step for step in summary["steps"] if step.get("result_path")])
    summary["completed_node_count"] = len([task for task in node_state["tasks"] if task.get("has_eow")])
    scores = build_scores(summary)
    write_json(results_dir / "scores.json", scores)
    write_json(results_dir / "summary.json", summary)
    ok = summary["status"] not in {"failed"}
    print(json.dumps({
        "ok": ok,
        "status": summary["status"],
        "run_id": run_id,
        "work_dir": str(work_dir),
        "summary": str(results_dir / "summary.json"),
        "scores": str(results_dir / "scores.json"),
        "node_state": str(results_dir / "taskops-node-state.json"),
        "steps": len(summary["steps"]),
        "closure": summary["closure"]
    }, indent=2))
    if not ok:
        raise SystemExit(1)


def build_scores(summary: dict) -> dict:
    results = []
    for step in summary.get("steps", []):
        score = step.get("score") or {}
        results.append({
            "task_id": step.get("task_id"),
            "status": step.get("result_status") or ("failed" if step.get("error") else None),
            "score": score,
            "native_score": step.get("native_score"),
            "result_path": step.get("result_path"),
            "error": step.get("error")
        })
    completed = [item for item in results if item["status"] == "completed"]
    score_values = [item["score"].get("primary") for item in completed if isinstance(item.get("score"), dict) and isinstance(item["score"].get("primary"), (int, float))]
    return {
        "run_id": summary.get("run_id"),
        "mode": summary.get("mode"),
        "arms": summary.get("arms"),
        "status": summary.get("status"),
        "allow_stubs_for_smoke": summary.get("allow_stubs_for_smoke"),
        "result_count": len(results),
        "completed_score_count": len(score_values),
        "missing_score_count": len(results) - len(score_values),
        "mean_primary_score": (sum(score_values) / len(score_values)) if score_values else None,
        "results": results
    }


def emit_commands(args: argparse.Namespace) -> None:
    run_id = args.run_id or f"{args.mode}-RUN_ID"
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"# Generated command plan for mode={args.mode}, arms={args.arms}, run_id={run_id}",
        ""
    ]
    for item in resolve_mode(args.mode, args.arms, benchmarks=parse_csv(getattr(args, "benchmarks", None))):
        adapter = item["adapter"]
        benchmark_id = item["benchmark_id"]
        arm = item["arm"]
        result_path = item["result_path_template"].format(run_id=run_id)
        command_template = adapter.get("command_template")
        if not command_template:
            lines.append(f"# No adapter command for {benchmark_id} {arm}")
            continue
        command = command_template.format(
            arm=arm,
            run_id=run_id,
            result_path=result_path,
            benchmark_id=benchmark_id,
            task_count=item.get("task_count")
        )
        prefix = "" if adapter.get("configured") else "# UNCONFIGURED: "
        lines.append(f"{prefix}{command}")
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out.chmod(0o755)
    print(json.dumps({"ok": True, "out": str(out)}, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list", help="List resolved benchmark-arm tasks")
    p.add_argument("--mode", choices=["pilot", "core", "full"], default="core")
    p.add_argument("--arms", choices=["both", "direct_agent", "taskops_agent"], default="both")
    p.add_argument("--benchmarks", help="Comma-separated benchmark ids to include")
    p.set_defaults(func=list_items)

    p = sub.add_parser("adapter-status", help="Show adapter configuration status")
    p.add_argument("--mode", choices=["pilot", "core", "full"], default="core")
    p.add_argument("--arms", choices=["both", "direct_agent", "taskops_agent"], default="both")
    p.add_argument("--benchmarks", help="Comma-separated benchmark ids to include")
    p.set_defaults(func=adapter_status)

    p = sub.add_parser("init-work", help="Create a TaskOps work graph for a run matrix")
    p.add_argument("--work-dir", default="taskops-work/core")
    p.add_argument("--mode", choices=["pilot", "core", "full"], default="core")
    p.add_argument("--arms", choices=["both", "direct_agent", "taskops_agent"], default="both")
    p.add_argument("--benchmarks", help="Comma-separated benchmark ids to include")
    p.add_argument("--run-id")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=init_work)

    p = sub.add_parser("smoke", help="Create a temp TaskOps work graph and run dry-run queue steps")
    p.add_argument("--mode", choices=["pilot", "core", "full"], default="pilot")
    p.add_argument("--arms", choices=["both", "direct_agent", "taskops_agent"], default="both")
    p.add_argument("--steps", type=int, default=2)
    p.set_defaults(func=smoke)

    p = sub.add_parser("emit-commands", help="Emit an adapter command plan shell script")
    p.add_argument("--mode", choices=["pilot", "core", "full"], default="core")
    p.add_argument("--arms", choices=["both", "direct_agent", "taskops_agent"], default="both")
    p.add_argument("--benchmarks", help="Comma-separated benchmark ids to include")
    p.add_argument("--run-id")
    p.add_argument("--out", default="generated/run-commands.sh")
    p.set_defaults(func=emit_commands)

    p = sub.add_parser("run", help="Run selected benchmarks through TaskOps queue claims and write normalized JSON results")
    p.add_argument("--work-dir", default="local/taskops-bench-run")
    p.add_argument("--mode", choices=["pilot", "core", "full"], default="pilot")
    p.add_argument("--arms", choices=["both", "direct_agent", "taskops_agent"], default="both")
    p.add_argument("--benchmarks", help="Comma-separated benchmark ids to include")
    p.add_argument("--run-id")
    p.add_argument("--init", action="store_true", help="Initialize the work graph before running")
    p.add_argument("--force", action="store_true", help="Replace the work graph when used with --init")
    p.add_argument("--allow-stubs-for-smoke", action="store_true", help="Allow unconfigured stub adapters; only for orchestration smoke tests")
    p.add_argument("--continue-on-error", action="store_true")
    p.add_argument("--max-steps", type=int)
    p.add_argument("--ttl-seconds", type=int, default=3600)
    p.add_argument("--runner-id")
    p.set_defaults(func=run_benchmarks)

    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        if exc.stdout:
            print(exc.stdout, file=sys.stdout)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        raise SystemExit(exc.returncode)
