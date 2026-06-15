# Runbook

This repository is structured so a clone can generate a TaskOps work graph for
the full benchmark suite.

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

The adapter files already exist as stubs under `scripts/adapters/`. A stub writes
`status: not_configured` using the normal result contract, which lets the
orchestration path be tested before expensive benchmark harness work begins.

## Run Through TaskOps

`run` is the end-to-end harness command. It creates or reuses a TaskOps work
graph, syncs the SQLite queue projection, claims queue items, executes each
benchmark adapter, validates the normalized result JSON, closes the TaskOps task
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
results/<run_id>/taskops-node-state.json
results/<run_id>/<arm>/<benchmark_id>/result.json
```

By default, unconfigured adapters still run their stubs and write
`status: not_configured` with `native_score: null`. This is intentional: it lets
the TaskOps queue, JSON result storage, and node closure path be tested before
benchmark-native harnesses and paid model endpoints are connected.

For a real scoring run, require configured adapters:

```bash
python3 scripts/taskops_bench.py run \
  --init --force \
  --work-dir local/strict-core \
  --mode core \
  --arms both \
  --run-id core-qwen3_6_27b-001 \
  --strict-config
```

`--strict-config` exits non-zero if any selected adapter is still a stub.

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
  "native_score": null,
  "taskops_metrics": {},
  "artifacts": []
}
```

External benchmark metrics and TaskOps orchestration metrics should stay
separate. TaskOps lift is not only a pass-rate delta; it also includes false
completion reduction, evidence completeness, queue integrity, restart recovery,
and progress-report coverage.
