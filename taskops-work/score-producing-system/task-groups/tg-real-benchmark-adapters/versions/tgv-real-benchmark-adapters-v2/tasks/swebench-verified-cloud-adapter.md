---
taskOpsVersion: v1
entityType: task
id: swebench-verified-cloud-adapter
taskGroupId: tg-real-benchmark-adapters
taskGroupVersionId: tgv-real-benchmark-adapters-v2
title: Implement SWE-bench Verified cloud scoring adapter
objective: Replace the SWE-bench Verified stub with a real sb-cli based score-producing path that submits prediction files and parses resolved_percent.
responsibility: Own scripts/adapters/swe_bench.py, the shared SWE-bench cloud adapter, and failure evidence when predictions/API key are missing.
completionCriteria: swe_bench_verified adapter is configured true, writes completed score JSON when predictions/API key are supplied, and writes blocked/failed evidence otherwise without fabricating scores.
order: 1
createdAt: 2026-06-15T18:10:45.460Z
status: done
runReadiness: runnable
runReadinessReason: Closed by taskops close --reason manual_verified at 2026-06-15T18:11:18.593Z.
understandingLevel: known
---
# Implement SWE-bench Verified cloud scoring adapter
