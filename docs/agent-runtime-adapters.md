# Agent Runtime Adapters

Benchmark adapters must not hardcode a single agent app. They should call
`scripts/agent_runtime.py` and consume its normalized invocation JSON.

## Runtime Config

Runtime definitions live in `config/runtimes.json`.

Current runtimes:

- `noop`: local smoke runtime. It never counts as score-eligible.
- `command`: generic command template runtime for Claude Code, Codex, OpenCode,
  Hermes, or another CLI.
- `openclaw_cli`: same-host OpenClaw invocation through `openclaw agent --json`.

## Invocation

```bash
python3 scripts/agent_runtime.py invoke \
  --runtime noop \
  --run-id smoke \
  --benchmark-id swe_bench_verified \
  --arm direct_agent \
  --task-id demo \
  --prompt "Solve the task" \
  --out results/smoke/runtime/noop.json
```

Output shape:

```json
{
  "schema_version": "0.1.0",
  "runtime_id": "noop",
  "benchmark_id": "swe_bench_verified",
  "arm": "direct_agent",
  "run_id": "smoke",
  "task_id": "demo",
  "status": "completed",
  "score_eligible": false,
  "prompt_chars": 14,
  "response_text": "...",
  "raw": {},
  "artifacts": []
}
```

## Generic Command Runtime

Set `TASKOPS_BENCH_AGENT_COMMAND` to a command template. The template receives:

- `{prompt_file}`
- `{output_file}`
- `{artifact_dir}`
- `{run_id}`
- `{benchmark_id}`
- `{arm}`
- `{task_id}`

The command runtime captures stdout as `response_text`. If a CLI writes richer
JSON, benchmark adapters can read that file from `{artifact_dir}` and include it
in their benchmark artifacts.

## OpenClaw Runtime

`openclaw_cli` runs:

```text
openclaw agent --agent <agent> --session-key <key> --message <prompt> --json
```

Environment overrides:

- `TASKOPS_BENCH_OPENCLAW_AGENT_ID`
- `TASKOPS_BENCH_MODEL`
- `TASKOPS_BENCH_OPENCLAW_SESSION_PREFIX`

The default model is recorded as `Qwen/Qwen3.6-27B`, matching the paper plan.
Whether that model is actually routable depends on the local OpenClaw/Gateway
configuration.

## Adapter Rule

Benchmark adapters may use `noop` only for smoke tests. Real benchmark scoring
must use a score-eligible runtime and must still pass the benchmark's own
official evaluator before writing `status: completed`.
