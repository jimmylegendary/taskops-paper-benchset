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
runReadinessReason: Blocked until at least one real benchmark adapter and runtime adapter are configured; full run blocked until all selected adapters are implemented or explicitly classified.
understandingLevel: known
blockedBy:
  - agent-runtime-adapter-contract
  - real-benchmark-adapters
---
# Validate selected and full score-producing runs
