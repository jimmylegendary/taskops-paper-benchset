---
taskOpsVersion: v1
entityType: task
id: runtime-invocation-cli
taskGroupId: tg-agent-runtime-adapter-contract
taskGroupVersionId: tgv-agent-runtime-adapter-contract-v2
title: Implement runtime invocation CLI
objective: Add a CLI helper that benchmark adapters can call to invoke an agent runtime and capture response JSON.
responsibility: Own scripts/agent_runtime.py, including noop smoke, command runtime, and OpenClaw CLI runtime.
completionCriteria: scripts/agent_runtime.py can list runtimes and run a noop invocation that writes normalized invocation JSON; OpenClaw and command runtime paths are implemented behind config.
order: 2
createdAt: 2026-06-15T18:03:29.302Z
status: done
runReadiness: runnable
runReadinessReason: Closed by taskops close --reason manual_verified at 2026-06-15T18:06:17.994Z.
understandingLevel: known
---
# Implement runtime invocation CLI
