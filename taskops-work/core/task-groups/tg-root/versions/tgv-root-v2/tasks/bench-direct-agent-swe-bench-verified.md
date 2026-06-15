---
taskOpsVersion: v1
entityType: task
id: bench-direct-agent-swe-bench-verified
taskGroupId: tg-root
taskGroupVersionId: tgv-root-v2
title: Run SWE-bench Verified (direct_agent)
objective: Run benchmark `swe_bench_verified` for arm `direct_agent` using Qwen/Qwen3.6-27B. Task count target: 20. Write benchmark-native outputs and the normalized result contract to `results/core-qwen3_6_27b-001/direct_agent/swe_bench_verified/result.json`.
responsibility: Own adapter setup, execution, native benchmark scoring, normalized result writing, and TaskOps orchestration metric capture for this benchmark arm.
completionCriteria: `results/core-qwen3_6_27b-001/direct_agent/swe_bench_verified/result.json` exists and contains run_id, arm, benchmark_id, status, native_score, taskops_metrics, and artifacts; failures must be explicit rather than silently marked complete.
order: 1
createdAt: 2026-06-15T17:03:39.100Z
status: pending
runReadiness: runnable
runReadinessReason: Benchmark arm has a fixed manifest entry and an adapter contract. Configured=False; command=python3 scripts/adapters/swe_bench.py --subset verified --arm direct_agent --run-id core-qwen3_6_27b-001 --out results/core-qwen3_6_27b-001/direct_agent/swe_bench_verified/result.json
understandingLevel: known
---
# Run SWE-bench Verified (direct_agent)
