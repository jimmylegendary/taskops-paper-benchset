#!/usr/bin/env python3
"""Agent runtime adapter used by benchmark adapters.

The benchmark adapters should not hardcode OpenClaw, Claude, Codex, or any
specific app. They call this helper with a normalized prompt and receive a
normalized invocation JSON artifact.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "runtimes.json"


def load_config() -> dict:
    with CONFIG.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        return Path(args.prompt_file).read_text(encoding="utf-8")
    if args.prompt:
        return args.prompt
    raise SystemExit("Either --prompt or --prompt-file is required")


def base_result(args: argparse.Namespace, runtime_id: str, prompt: str) -> dict:
    return {
        "schema_version": "0.1.0",
        "runtime_id": runtime_id,
        "benchmark_id": args.benchmark_id,
        "arm": args.arm,
        "run_id": args.run_id,
        "task_id": args.task_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "score_eligible": False,
        "prompt_chars": len(prompt),
        "response_text": None,
        "raw": {},
        "artifacts": []
    }


def invoke_noop(args: argparse.Namespace, runtime: dict, prompt: str) -> dict:
    result = base_result(args, "noop", prompt)
    result.update({
        "status": "completed",
        "score_eligible": False,
        "response_text": "NOOP runtime response. This is only valid for orchestration smoke tests.",
        "raw": {"kind": runtime.get("kind")}
    })
    return result


def invoke_command(args: argparse.Namespace, runtime: dict, prompt: str, out_path: Path, artifact_dir: Path) -> dict:
    template_env = runtime.get("command_template_env", "TASKOPS_BENCH_AGENT_COMMAND")
    template = os.environ.get(template_env)
    if not template:
        raise RuntimeError(f"Runtime 'command' requires env {template_env}")
    prompt_file = artifact_dir / "prompt.txt"
    prompt_file.write_text(prompt, encoding="utf-8")
    command = template.format(
        prompt_file=str(prompt_file),
        output_file=str(out_path),
        artifact_dir=str(artifact_dir),
        run_id=args.run_id,
        benchmark_id=args.benchmark_id,
        arm=args.arm,
        task_id=args.task_id or ""
    )
    completed = subprocess.run(
        shlex.split(command),
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=args.timeout_seconds,
        check=False
    )
    result = base_result(args, "command", prompt)
    result.update({
        "status": "completed" if completed.returncode == 0 else "failed",
        "score_eligible": bool(runtime.get("score_eligible")),
        "response_text": completed.stdout.strip(),
        "raw": {
            "command": command,
            "returncode": completed.returncode,
            "stderr": completed.stderr.strip()
        },
        "artifacts": [str(prompt_file)]
    })
    return result


def invoke_openclaw_cli(args: argparse.Namespace, runtime: dict, prompt: str) -> dict:
    binary = runtime.get("binary", "openclaw")
    if shutil.which(binary) is None:
        raise RuntimeError(f"OpenClaw binary not found on PATH: {binary}")
    agent_id = os.environ.get(runtime.get("agent_id_env", ""), runtime.get("default_agent_id", "main"))
    model = os.environ.get(runtime.get("model_env", ""), runtime.get("default_model"))
    prefix = os.environ.get(runtime.get("session_key_prefix_env", ""), "agent:main:taskops-bench")
    session_key = f"{prefix}:{args.run_id}:{args.arm}:{args.benchmark_id}"
    timeout = args.timeout_seconds or int(runtime.get("timeout_seconds", 3600))
    command = [
        binary,
        "agent",
        "--agent",
        agent_id,
        "--session-key",
        session_key,
        "--message",
        prompt,
        "--json",
        "--timeout",
        str(timeout)
    ]
    if model:
        command.extend(["--model", model])
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout + 30,
        check=False
    )
    result = base_result(args, "openclaw_cli", prompt)
    response_text = completed.stdout.strip()
    raw: dict = {
        "command": command[:],
        "returncode": completed.returncode,
        "stderr": completed.stderr.strip(),
        "session_key": session_key
    }
    try:
        raw["json"] = json.loads(response_text) if response_text else None
    except json.JSONDecodeError:
        raw["json_parse_error"] = True
    result.update({
        "status": "completed" if completed.returncode == 0 else "failed",
        "score_eligible": bool(runtime.get("score_eligible")),
        "response_text": response_text,
        "raw": raw
    })
    return result


def cmd_list(_: argparse.Namespace) -> int:
    config = load_config()
    print(json.dumps(config, indent=2, ensure_ascii=False))
    return 0


def cmd_invoke(args: argparse.Namespace) -> int:
    config = load_config()
    runtimes = config.get("runtimes", {})
    runtime_id = args.runtime or config.get("default_runtime")
    if runtime_id not in runtimes:
        raise SystemExit(f"unknown runtime: {runtime_id}")
    runtime = runtimes[runtime_id]
    prompt = read_prompt(args)
    out_path = Path(args.out).resolve()
    artifact_dir = Path(args.artifact_dir).resolve() if args.artifact_dir else out_path.parent / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    try:
        if runtime_id == "noop":
            result = invoke_noop(args, runtime, prompt)
        elif runtime_id == "command":
            result = invoke_command(args, runtime, prompt, out_path, artifact_dir)
        elif runtime_id == "openclaw_cli":
            result = invoke_openclaw_cli(args, runtime, prompt)
        else:
            raise RuntimeError(f"runtime kind is not implemented: {runtime_id}")
    except Exception as exc:  # noqa: BLE001 - write failure artifact for runners.
        result = base_result(args, runtime_id, prompt)
        result.update({
            "status": "failed",
            "score_eligible": bool(runtime.get("score_eligible")),
            "error": str(exc)
        })
        write_json(out_path, result)
        print(json.dumps({"ok": False, "out": str(out_path), "error": str(exc)}, indent=2), file=sys.stderr)
        return 1

    write_json(out_path, result)
    ok = result.get("status") == "completed"
    print(json.dumps({"ok": ok, "out": str(out_path), "status": result.get("status")}, indent=2))
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list", help="List configured runtime adapters")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("invoke", help="Invoke one runtime and write normalized invocation JSON")
    p.add_argument("--runtime")
    p.add_argument("--prompt")
    p.add_argument("--prompt-file")
    p.add_argument("--out", required=True)
    p.add_argument("--artifact-dir")
    p.add_argument("--run-id", required=True)
    p.add_argument("--benchmark-id", required=True)
    p.add_argument("--arm", required=True)
    p.add_argument("--task-id")
    p.add_argument("--timeout-seconds", type=int, default=3600)
    p.set_defaults(func=cmd_invoke)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
