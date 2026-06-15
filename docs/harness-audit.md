# Harness Audit

This audit exists to keep the benchmark suite honest. The final artifact for a
benchmark run is score data. A benchmark is not runnable just because a row
exists in the run matrix.

Machine-readable status lives in `data/harness_audit.json`.

## Current Classification

| Benchmark | Status | Real score path |
| --- | --- | --- |
| SWE-bench Verified | `runnable_after_setup` | Official SWE-bench Docker/cloud evaluation, resolved percent. |
| SWE-bench Pro | `runnable_after_setup` | Public SWE-bench Pro harness, with exact public subset pinned. |
| Terminal-Bench 2.0 | `runnable_after_setup` | Harbor official harness for Terminal-Bench 2.x, task success rate. |
| SkillsBench | `runnable_after_setup` | BenchFlow runtime, selected self-contained tasks, average success. |
| NL2Repo | `runnable_after_setup` | NL2RepoBench task tests/evaluator against generated repos. |
| ALE-FreeEasy | `blocked_operationally` | ALE task cards/evaluators, but local free-tool environments must be pinned. |
| HCAST public | `blocked_until_pinned` | Public source subset exists; runnable graders/subset need inspection. |
| RE-Bench | `blocked_operationally` | Public tasks exist, but compute/runtime cost must be pinned. |
| Full ALE | `blocked_operationally` | Full set includes heavier/licensed/professional environments. |
| TheAgentCompany | `blocked_operationally` | Self-hosted workplace services and checkpoint scoring needed. |
| Vending-Bench | `blocked_until_pinned` | Public paper is available; evaluator/scenario code is not pinned here. |
| SWE-bench Multilingual | `reported_only` | Qwen reports the score, but this repo has no public harness/task set pinned. |

## Policy

- `scripts/taskops_bench.py run` is a score-producing command by default.
- Unconfigured adapters fail by default.
- `--allow-stubs-for-smoke` is only for checking TaskOps queue/closure behavior.
- `status: not_configured` does not count as a benchmark score.
- Completed results must include numeric `score.primary`.

## Sources Checked

- SWE-bench official repository and evaluation guide:
  <https://github.com/swe-bench/SWE-bench>
- SWE-bench `sb-cli` cloud submission path:
  <https://github.com/swe-bench/sb-cli>
- Terminal-Bench / Harbor running guide:
  <https://www.harborframework.com/docs/tutorials/running-terminal-bench>
- Terminal-Bench public site:
  <https://www.tbench.ai/>
- SkillsBench getting started:
  <https://www.skillsbench.ai/docs/getting-started>
- SkillsBench repository:
  <https://github.com/benchflow-ai/skillsbench>
- BenchFlow repository:
  <https://github.com/benchflow-ai/benchflow>
- NL2RepoBench repository:
  <https://github.com/multimodal-art-projection/NL2RepoBench>
- Agents' Last Exam repository:
  <https://github.com/rdi-berkeley/agents-last-exam>
- HCAST public repository:
  <https://github.com/METR/hcast-public>
- RE-Bench repository:
  <https://github.com/METR/RE-Bench>
- TheAgentCompany repository:
  <https://github.com/TheAgentCompany/TheAgentCompany>
- TheAgentCompany evaluation guide:
  <https://github.com/TheAgentCompany/TheAgentCompany/blob/main/docs/EVALUATION.md>
- Vending-Bench paper:
  <https://arxiv.org/html/2502.15840v1>

## Next Adapter Priority

1. SWE-bench Verified: best first control adapter.
2. Terminal-Bench 2.0: best terminal/evidence-heavy TaskOps adapter.
3. SkillsBench: best procedure/skill-following adapter.
4. ALE-FreeEasy: best TaskOps-paper fit after environment setup is pinned.

