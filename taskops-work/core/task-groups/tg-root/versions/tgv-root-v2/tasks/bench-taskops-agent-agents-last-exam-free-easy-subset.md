---
taskOpsVersion: v1
entityType: task
id: bench-taskops-agent-agents-last-exam-free-easy-subset
taskGroupId: tg-root
taskGroupVersionId: tgv-root-v2
title: Run Agents' Last Exam free/easy TaskOps subset (taskops_agent)
objective: Run benchmark `agents_last_exam_free_easy_subset` for arm `taskops_agent` using Qwen/Qwen3.6-27B. Task count target: 12. Write benchmark-native outputs and the normalized result contract to `results/core-qwen3_6_27b-001/taskops_agent/agents_last_exam_free_easy_subset/result.json`.
responsibility: Own adapter setup, execution, native benchmark scoring, normalized result writing, and TaskOps orchestration metric capture for this benchmark arm.
completionCriteria: `results/core-qwen3_6_27b-001/taskops_agent/agents_last_exam_free_easy_subset/result.json` exists and contains run_id, arm, benchmark_id, status, native_score, taskops_metrics, and artifacts; failures must be explicit rather than silently marked complete.
order: 12
createdAt: 2026-06-15T17:03:39.100Z
status: pending
runReadiness: runnable
runReadinessReason: Benchmark arm has a fixed manifest entry and an adapter contract. Configured=False; command=python3 scripts/adapters/ale.py --subset free_easy --arm taskops_agent --run-id core-qwen3_6_27b-001 --out results/core-qwen3_6_27b-001/taskops_agent/agents_last_exam_free_easy_subset/result.json
understandingLevel: known
---
# Run Agents' Last Exam free/easy TaskOps subset (taskops_agent)
