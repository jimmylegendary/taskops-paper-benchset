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
status: done
runReadiness: needs_exploration
runReadinessReason: Closed by taskops close --reason manual_verified at 2026-06-15T17:59:03.516Z.
understandingLevel: partial
---
# Audit real runnable harness paths for all benchmark ids
