---
taskOpsVersion: v1
entityType: task
id: benchmark-harness-audit
taskGroupId: tg-root
taskGroupVersionId: tgv-root-v2
title: Audit real runnable harness paths for all benchmark ids
objective: For every benchmark in pilot/core/full, determine the exact install, execution, evaluator, scoring metric, cost/runtime, and blockers needed to produce real score JSON.
responsibility: Map each configured benchmark id to an upstream harness or mark it blocked with evidence; no benchmark may remain a vague adapter placeholder.
completionCriteria: A machine-readable harness audit exists and classifies every selected benchmark as runnable_now, runnable_after_setup, blocked, or reported_only with concrete reasons.
order: 2
createdAt: 2026-06-15T17:53:27.068Z
status: pending
runReadiness: needs_exploration
runReadinessReason: Requires checking upstream benchmark repositories, install paths, evaluator commands, and local prerequisites.
understandingLevel: partial
---
# Audit real runnable harness paths for all benchmark ids
