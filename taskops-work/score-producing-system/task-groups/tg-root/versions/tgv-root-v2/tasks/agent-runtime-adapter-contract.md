---
taskOpsVersion: v1
entityType: task
id: agent-runtime-adapter-contract
taskGroupId: tg-root
taskGroupVersionId: tgv-root-v2
title: Implement agent runtime adapter contract
objective: Define and implement the common interface used by benchmark adapters to invoke OpenClaw first and other agent CLIs later.
responsibility: Separate benchmark harness execution from agent invocation; support direct_agent and taskops_agent arms without hardcoding one app into the benchmark runner.
completionCriteria: The repo has a documented runtime adapter contract and at least one runnable OpenClaw/Qwen3.6-27B adapter path that benchmark adapters can call.
order: 3
createdAt: 2026-06-15T17:53:27.068Z
status: done
runReadiness: needs_decomposition
runReadinessReason: Decomposed by taskops-runner (dry-run) into tg-agent-runtime-adapter-contract/tgv-agent-runtime-adapter-contract-v1 at 2026-06-15T18:02:26.074Z.
understandingLevel: partial
runRefs:
  - runId: run-main
    runNodeId: run-node-agent-runtime-adapter-contract
    role: primary_decomposition
childTaskGroupId: tg-agent-runtime-adapter-contract
---
# Implement agent runtime adapter contract
