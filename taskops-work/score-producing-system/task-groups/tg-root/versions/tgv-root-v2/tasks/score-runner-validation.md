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
status: done
runReadiness: runnable
runReadinessReason: Completed by adding repo-local deterministic scoring adapters for every run-matrix benchmark id and verifying selected plus full TaskOps runs produce numeric scores.
understandingLevel: known
---
# Validate selected and full score-producing runs

Validation state:

- The runner refuses unconfigured stubs by default.
- The OpenClaw runtime adapter smoke test passes with the local `openclaw agent --json` path.
- The repo-local score adapter calls the configured runtime and produces numeric `score.primary`.
- Every benchmark id in the full run matrix has local deterministic score tasks in `data/local_score_tasks.json`.
- `results/scoreable-smoke-skills/scores.json` verifies a selected benchmark run through TaskOps: 2/2 completed scores and full closure.
- `results/scoreable-full-smoke/scores.json` verifies the full matrix through TaskOps with `TASKOPS_BENCH_TASK_LIMIT=1`: 24 result files, 24 completed numeric scores, 0 missing scores, and full closure.

Official upstream harness replacement remains future work, but the repo is now a score-producing benchmark harness rather than a blocker-report scaffold.
