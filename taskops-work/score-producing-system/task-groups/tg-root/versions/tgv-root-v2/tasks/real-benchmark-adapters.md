---
taskOpsVersion: v1
entityType: task
id: real-benchmark-adapters
taskGroupId: tg-root
taskGroupVersionId: tgv-root-v2
title: Replace benchmark stubs with real score-producing adapters
objective: Implement real adapters for all selected benchmark ids so each adapter installs/verifies its harness, runs benchmark tasks, calls official scoring, and writes normalized result JSON.
responsibility: Own benchmark-specific setup and scorer integration for SWE-bench, Terminal-Bench, SkillsBench, NL2Repo, ALE-FreeEasy/ALE, HCAST, RE-Bench, and extension benchmarks as selected.
completionCriteria: Every selected benchmark adapter either produces completed score JSON or records an explicit blocked/failed result before the aggregate run is reported.
order: 4
createdAt: 2026-06-15T17:53:27.068Z
status: done
runReadiness: needs_decomposition
runReadinessReason: Decomposed by taskops-runner (dry-run) into tg-real-benchmark-adapters/tgv-real-benchmark-adapters-v1 at 2026-06-15T18:06:48.483Z.
understandingLevel: partial
runRefs:
  - runId: run-main
    runNodeId: run-node-real-benchmark-adapters
    role: primary_decomposition
childTaskGroupId: tg-real-benchmark-adapters
---
# Replace benchmark stubs with real score-producing adapters
