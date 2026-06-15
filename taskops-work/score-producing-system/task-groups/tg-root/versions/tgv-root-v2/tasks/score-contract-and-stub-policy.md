---
taskOpsVersion: v1
entityType: task
id: score-contract-and-stub-policy
taskGroupId: tg-root
taskGroupVersionId: tgv-root-v2
title: Define score-producing result contract and stub policy
objective: Make the runner and docs require actual score data for real benchmark runs, while allowing stubs only through an explicit smoke-test opt-in.
responsibility: Own result schema, adapter validation rules, scores.json aggregation, and the policy that not_configured results cannot count as completed benchmark scores.
completionCriteria: Default run fails for unconfigured adapters; --allow-stubs-for-smoke is required for stub adapters; completed results require numeric score.primary; docs describe score JSON outputs and smoke-only stubs.
order: 1
createdAt: 2026-06-15T17:53:27.068Z
status: done
runReadiness: runnable
runReadinessReason: Closed by taskops close --reason manual_verified at 2026-06-15T17:54:36.471Z.
understandingLevel: known
---
# Define score-producing result contract and stub policy
