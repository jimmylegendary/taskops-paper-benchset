#!/usr/bin/env python3
"""TaskOps-backed benchmark-suite orchestration helper."""

from __future__ import annotations

import argparse
import json
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


def taskops_available() -> bool:
    return shutil.which("taskops") is not None


def benchmark_sources() -> dict[str, dict]:
    return {item["id"]: item for item in load_json(DATA / "benchmark_sources.json")["sources"]}


def run_matrix() -> dict:
    return load_json(DATA / "run_matrix.json")


def adapter_config() -> dict:
    return load_json(CONFIG / "adapters.json")["adapters"]


def resolve_mode(mode: str, arms: str) -> list[dict]:
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
    for benchmark in matrix["suite_modes"][mode]["benchmarks"]:
        benchmark_id = benchmark["benchmark_id"]
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
    return items


def task_id_for(item: dict) -> str:
    safe_benchmark = item["benchmark_id"].replace("_", "-")
    return f"bench-{item['arm'].replace('_', '-')}-{safe_benchmark}"


def build_task_spec(mode: str, arms: str, run_id: str) -> dict:
    tasks = []
    for item in resolve_mode(mode, arms):
        source = item["source"]
        adapter = item["adapter"]
        benchmark_id = item["benchmark_id"]
        arm = item["arm"]
        result_path = item["result_path_template"].format(run_id=run_id)
        command = adapter.get("command_template", "UNCONFIGURED").format(
            arm=arm,
            run_id=run_id,
            result_path=result_path
        )
        task_count = item["task_count"]
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
    spec = build_task_spec(args.mode, args.arms, run_id)
    generated_dir = work_dir / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    spec_path = generated_dir / "root-benchmark-matrix.spec.json"
    write_json(spec_path, spec)
    write_json(generated_dir / "run-metadata.json", {
        "run_id": run_id,
        "mode": args.mode,
        "arms": args.arms,
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
        "task_count": len(spec["tasks"])
    }, indent=2))


def list_items(args: argparse.Namespace) -> None:
    items = resolve_mode(args.mode, args.arms)
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
    items = resolve_mode(args.mode, args.arms)
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


def emit_commands(args: argparse.Namespace) -> None:
    run_id = args.run_id or f"{args.mode}-RUN_ID"
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"# Generated command plan for mode={args.mode}, arms={args.arms}, run_id={run_id}",
        ""
    ]
    for item in resolve_mode(args.mode, args.arms):
        adapter = item["adapter"]
        benchmark_id = item["benchmark_id"]
        arm = item["arm"]
        result_path = item["result_path_template"].format(run_id=run_id)
        command_template = adapter.get("command_template")
        if not command_template:
            lines.append(f"# No adapter command for {benchmark_id} {arm}")
            continue
        command = command_template.format(arm=arm, run_id=run_id, result_path=result_path)
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
    p.set_defaults(func=list_items)

    p = sub.add_parser("adapter-status", help="Show adapter configuration status")
    p.add_argument("--mode", choices=["pilot", "core", "full"], default="core")
    p.add_argument("--arms", choices=["both", "direct_agent", "taskops_agent"], default="both")
    p.set_defaults(func=adapter_status)

    p = sub.add_parser("init-work", help="Create a TaskOps work graph for a run matrix")
    p.add_argument("--work-dir", default="taskops-work/core")
    p.add_argument("--mode", choices=["pilot", "core", "full"], default="core")
    p.add_argument("--arms", choices=["both", "direct_agent", "taskops_agent"], default="both")
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
    p.add_argument("--run-id")
    p.add_argument("--out", default="generated/run-commands.sh")
    p.set_defaults(func=emit_commands)

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
