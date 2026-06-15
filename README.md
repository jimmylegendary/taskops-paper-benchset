# TaskOps Paper Benchmark Set

This repository defines a representative benchmark set for evaluating TaskOps as a
long-running agent execution control plane.

The intended first model under test is `Qwen/Qwen3.6-27B`. The benchmark design is
not a model leaderboard. It is meant to show where TaskOps changes outcomes when
the same worker model is run directly versus through TaskOps.

## Core Question

TaskOps should be evaluated on tasks where execution structure matters:

- decomposition
- queue admission
- dependency handling
- progress reporting
- restart and stale-work recovery
- evidence and artifact traceability
- honest completion instead of premature "done"

For each benchmark task, compare:

```text
direct-agent(Qwen3.6-27B) vs taskops-agent(Qwen3.6-27B)
```

The external benchmark score measures task quality. The TaskOps score measures
whether the work was managed honestly and recoverably.

## Representative Task Types

| Type | Representative benchmark | Why it matters |
| --- | --- | --- |
| Simple coding baseline | SWE-bench Verified | Should show little TaskOps lift; useful as a control. |
| Hard repo issue repair | SWE-bench Pro | Long-horizon codebase work where planning and recovery matter. |
| Terminal/system work | Terminal-Bench 2.0 | Multi-step shell, build, debug, security, and systems tasks. |
| Skill/procedure workflows | SkillsBench | Tests whether procedural knowledge and tool-specific instructions are followed. |
| Repo-from-scratch generation | NL2Repo | Tests architecture, multi-file implementation, packaging, and installability. |
| Human-calibrated autonomy | HCAST public subset | Calibrated by human time horizons; useful for 1h to 8h+ claims. |
| AI R&D long work | RE-Bench | 8-hour expert-attempt ML research engineering tasks. |
| Broad real-work, free/easy tools | ALE free/easy subset | ALE tasks filtered to avoid licensed commercial tools and emphasize LLM/data/code/image work. |
| Broad real-work oracle | Agents' Last Exam | Diverse economically valuable tasks with hidden-reference grading. |
| Workplace/multi-app tasks | TheAgentCompany | Simulated software-company workflows across apps and communication. |
| Long-term coherence | Vending-Bench | Multi-turn business operation over long horizons. |

## Files

- `data/benchmark_sources.json` - source registry and reproducibility notes.
- `data/qwen3_6_27b_reported_results.json` - reported Qwen3.6-27B benchmark scores.
- `data/taskops_paper_suite.json` - selected paper suite, hypotheses, and metrics.
- `data/pilot_plan.json` - cost-controlled first experiment plan.
- `data/ale_free_easy_subset.json` - curated Agents' Last Exam subset metadata.
- `docs/experimental-design.md` - paper-facing experiment plan.
- `docs/research-notes.md` - source notes and caveats.
- `scripts/validate.py` - manifest validation.

## Initial Paper Position

Use Qwen3.6-27B as the single worker model to control cost. Report improvements
by task type rather than by model:

```text
TaskOps lift = taskops-agent score - direct-agent score
```

Report both:

- external benchmark metrics, such as pass rate or task score
- TaskOps orchestration metrics, such as recovery rate, false completion rate,
  evidence completeness, and master-session reporting coverage

The expected result is not uniform improvement. TaskOps should show little benefit
on short single-patch tasks and larger benefit on complex, long, interruptible,
multi-artifact, and procedure-heavy tasks.

## Validation

```bash
python3 scripts/validate.py
```
