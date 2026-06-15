---
taskOpsVersion: v1
entityType: task
id: score-runner-validation
taskGroupId: tg-root
taskGroupVersionId: tgv-root-v2
title: Validate selected and full score-producing runs
objective: Run selected and full benchmark matrices through TaskOps and verify they produce score JSON, aggregate scores, artifacts, logs, queue state, and TaskOps node-state reports.
responsibility: Own end-to-end validation, failure/resume behavior, and final reporting that distinguishes completed scores from blocked or failed benchmarks.
completionCriteria: A selected real benchmark run and the requested full or core run produce results/<run_id>/scores.json, summary.json, taskops-node-state.json, and per-benchmark result.json files with no stub scores counted.
order: 5
createdAt: 2026-06-15T17:53:27.068Z
status: pending
runReadiness: blocked
runReadinessReason: Blocked by external benchmark execution prerequisites, not by incomplete TaskOps code. SWE-bench Verified needs TASKOPS_BENCH_SWEBENCH_PREDICTIONS plus SWEBENCH_API_KEY; other benchmark rows need upstream harness setup, credentials, pinned public tasks, or compute before numeric scores can be produced.
understandingLevel: known
---
# Validate selected and full score-producing runs

Current validation state:

- The runner refuses unconfigured stubs by default.
- The OpenClaw runtime adapter smoke test passes with the local `openclaw agent --json` path.
- The SWE-bench Verified adapter is score-producing when real predictions and `SWEBENCH_API_KEY` are supplied.
- The full benchmark matrix currently writes explicit blocked/failed result JSON for every non-scoreable benchmark instead of fabricating scores.
- `results/full-blocker-collection-v2/scores.json` is the latest full blocker collection run: 24 result files, 0 completed numeric scores, 22 blocked, 2 failed/reported-only.

This task must stay open until at least one selected real benchmark produces numeric score data through the TaskOps runner.
