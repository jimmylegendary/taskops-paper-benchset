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
status: pending
runReadiness: needs_decomposition
runReadinessReason: This is a multi-benchmark implementation branch and should split per benchmark family after the harness audit.
understandingLevel: partial
---
# Replace benchmark stubs with real score-producing adapters
