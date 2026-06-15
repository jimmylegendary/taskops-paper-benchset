# Runbook

This repository is structured so a clone can run selected or full benchmark
matrices through TaskOps and write score JSON. A real scoring run fails if any
selected benchmark adapter is still a stub.

## Prerequisites

- Python 3.10+
- Node 22+
- `taskops` CLI 0.5.1+

Install TaskOps:

```bash
npm install -g taskops@0.5.1
```

Validate the repository manifests:

```bash
python3 scripts/validate.py
```

## Inspect the Matrix

```bash
python3 scripts/taskops_bench.py list --mode core --arms both
python3 scripts/taskops_bench.py adapter-status --mode core --arms both
python3 scripts/agent_runtime.py list
```

Modes:

- `pilot` - smaller cost-controlled run
- `core` - main paper suite
- `full` - includes extension benchmarks

Arms:

- `direct_agent`
- `taskops_agent`
- `both`

## Generate a TaskOps Work Graph

```bash
python3 scripts/taskops_bench.py init-work \
  --work-dir taskops-work/core \
  --mode core \
  --arms both \
  --run-id core-qwen3_6_27b-001 \
  --force
```

This creates:

```text
taskops-work/core/
  index.md
  task-groups/
  snapshots/
  runs/
  generated/root-benchmark-matrix.spec.json
  generated/run-metadata.json
  .taskops/queue.sqlite
```

Then inspect:

```bash
taskops validate taskops-work/core
taskops summary taskops-work/core
taskops queue list taskops-work/core --json
```

## Smoke the TaskOps Queue

This does not run external benchmarks. It verifies that the generated TaskOps
work graph can be queued and advanced by the TaskOps runner primitive.

```bash
python3 scripts/taskops_bench.py smoke --mode pilot --arms both --steps 2
```

Equivalent manual command after `init-work`:

```bash
taskops runner once taskops-work/core \
  --runtime dry-run \
  --runner-id local-smoke \
  --report-sink ledger \
  --json
```

## Emit Adapter Commands

```bash
python3 scripts/taskops_bench.py emit-commands \
  --mode core \
  --arms both \
  --run-id core-qwen3_6_27b-001 \
  --out generated/run-core.sh
```

The generated shell script is deliberately conservative. Commands whose
benchmark adapters are not configured are commented with `UNCONFIGURED`.

To make a benchmark actually runnable:

1. Install or clone its upstream harness.
2. Replace the stub adapter script named in `config/adapters.json`.
3. Change that adapter's `configured` field to `true`.
4. Re-run `python3 scripts/validate.py`.
5. Generate a fresh TaskOps work graph and run it.

The adapter files already exist as stubs under `scripts/adapters/`. Stubs are
only valid for explicit orchestration smoke tests. They must not count as
benchmark scores.

## Run Through TaskOps

`run` is the end-to-end harness command. It creates or reuses a TaskOps work
graph, syncs the SQLite queue projection, claims queue items, executes each
benchmark adapter, validates the normalized score JSON, closes the TaskOps task
with an EoW node, releases the lease, and writes aggregate reports.

Run a small selected set:

```bash
python3 scripts/taskops_bench.py run \
  --init --force \
  --work-dir local/pilot-swe \
  --mode pilot \
  --arms both \
  --benchmarks swe_bench_verified \
  --run-id pilot-swe-001
```

Run the full matrix:

```bash
python3 scripts/taskops_bench.py run \
  --init --force \
  --work-dir local/full-run \
  --mode full \
  --arms both \
  --run-id full-qwen3_6_27b-001
```

Outputs:

```text
results/<run_id>/summary.json
results/<run_id>/scores.json
results/<run_id>/taskops-node-state.json
results/<run_id>/<arm>/<benchmark_id>/result.json
```

By default, unconfigured adapters fail. This is intentional: the final artifact
of a benchmark run is score data, not a queue smoke result.

For an orchestration-only smoke test, opt into stubs explicitly:

```bash
python3 scripts/taskops_bench.py run \
  --init --force \
  --work-dir local/smoke-core \
  --mode pilot \
  --arms both \
  --benchmarks swe_bench_verified \
  --run-id smoke-pilot-001 \
  --allow-stubs-for-smoke
```

Smoke results write `status: not_configured` and `score.available: false`. They
are useful for checking TaskOps queue/closure behavior, not for paper scores.

## Agent Runtime Adapter

Benchmark adapters call `scripts/agent_runtime.py` instead of hardcoding one
agent application.

```bash
python3 scripts/agent_runtime.py invoke \
  --runtime noop \
  --run-id smoke \
  --benchmark-id swe_bench_verified \
  --arm direct_agent \
  --task-id demo \
  --prompt "Solve this benchmark task" \
  --out results/smoke/runtime/noop.json
```

See `docs/agent-runtime-adapters.md`.

## SWE-bench Verified Adapter

`swe_bench_verified` uses the SWE-bench cloud CLI path through `sb-cli`. It is
configured as a real adapter, but it needs a predictions file and API key before
it can produce a score.

```bash
export SWEBENCH_API_KEY=...
export TASKOPS_BENCH_SWEBENCH_PREDICTIONS=/path/to/predictions.jsonl

python3 scripts/taskops_bench.py run \
  --init --force \
  --work-dir local/swebench-verified \
  --mode pilot \
  --arms direct_agent \
  --benchmarks swe_bench_verified \
  --run-id swebench-verified-001
```

If the predictions file or API key is missing, the adapter writes
`status: blocked` with `score.available: false` and the TaskOps runner exits
non-zero. That is expected; it is evidence that the benchmark was not scored,
not a score.

## Result Contract

Each adapter must write:

```text
results/<run_id>/<arm>/<benchmark_id>/result.json
```

with at least:

```json
{
  "run_id": "core-qwen3_6_27b-001",
  "arm": "taskops_agent",
  "benchmark_id": "agents_last_exam_free_easy_subset",
  "status": "completed",
  "score": {
    "primary": 0.75,
    "metric_name": "pass_rate",
    "higher_is_better": true,
    "available": true
  },
  "raw_scores": {},
  "task_count": 20,
  "passed": 15,
  "failed": 5,
  "native_score": 0.75,
  "taskops_metrics": {},
  "artifacts": []
}
```

Completed results must include a numeric `score.primary`. `status:
not_configured` is rejected unless `--allow-stubs-for-smoke` is passed.

External benchmark metrics and TaskOps orchestration metrics should stay
separate. TaskOps lift is not only a pass-rate delta; it also includes false
completion reduction, evidence completeness, queue integrity, restart recovery,
and progress-report coverage.
