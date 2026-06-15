---
taskOpsVersion: v1
entityType: task
id: runtime-config-schema
taskGroupId: tg-agent-runtime-adapter-contract
taskGroupVersionId: tgv-agent-runtime-adapter-contract-v2
title: Define runtime configuration schema
objective: Create a machine-readable runtime configuration that describes supported agent invocation backends and required fields.
responsibility: Own config/runtimes.json and validation coverage so benchmark adapters can discover supported runtimes without hardcoding OpenClaw.
completionCriteria: config/runtimes.json exists, includes command and openclaw_cli runtimes, and scripts/validate.py verifies required runtime fields.
order: 1
createdAt: 2026-06-15T18:03:29.302Z
status: done
runReadiness: runnable
runReadinessReason: Closed by taskops close --reason manual_verified at 2026-06-15T18:06:17.967Z.
understandingLevel: known
---
# Define runtime configuration schema
