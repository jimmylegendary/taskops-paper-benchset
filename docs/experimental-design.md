# Experimental Design

## Goal

Show when TaskOps improves a single worker model's ability to complete real work.
The first cost-controlled setup uses only `Qwen/Qwen3.6-27B`.

The paper should not claim that TaskOps makes the model smarter. It should claim
that TaskOps changes the execution substrate:

- tasks are decomposed before execution
- run evidence is durable
- queue claims are explicit
- retries and restarts are visible
- completion requires closure evidence
- master-session reporting is structured

## Main Comparison

Run each task in two modes:

```text
direct-agent:
  Qwen3.6-27B worker receives the original benchmark prompt.

taskops-agent:
  Qwen3.6-27B worker is called through TaskOps.
  TaskOps owns decomposition, queueing, run graph, reporting, and closure.
```

Keep the worker runtime as similar as possible across both modes. If the direct
agent uses a CLI harness, the TaskOps worker adapter should call the same CLI
or an equivalent OpenAI-compatible endpoint.

## Core Suite

1. SWE-bench Verified
   - Role: low-lift control.
   - Expected result: little TaskOps improvement.
   - Paper value: shows TaskOps is not merely improving all scores through extra
     budget or different harness behavior.

2. SWE-bench Pro
   - Role: primary long-horizon codebase repair benchmark.
   - Expected result: medium lift through planning, recovery, and honest closure.

3. Terminal-Bench 2.0
   - Role: terminal/system multi-step work.
   - Expected result: medium-to-high lift because failures and setup states are
     common.

4. SkillsBench
   - Role: procedural skill-following benchmark.
   - Expected result: high lift because TaskOps externalizes workflow state.

5. NL2Repo
   - Role: 0-to-1 repo generation benchmark.
   - Expected result: high lift through decomposition, verification, and artifact
     closure.

6. HCAST public subset + RE-Bench
   - Role: time-horizon and 8-hour-class long-work benchmark.
   - Expected result: lift may appear more in restartability, reporting, and
     false-completion reduction than in raw final score.

7. ALE-FreeEasy-35
   - Role: broad real-work hidden-reference oracle without licensed-tool
     confounds.
   - Expected result: medium-to-high lift on tasks with many artifacts, source
     grounding, visual/domain-image interpretation, and structured output
     contracts.

## Extension Suite

- Agents' Last Exam full set: broad real-work hidden-reference oracle after
  environment and cost issues are solved.
- TheAgentCompany: workplace and multi-app coordination.
- Vending-Bench: long-term coherence over many simulated business turns.
- SWE-bench Multilingual: cross-language issue repair after harness pinning.

## Primary Tables for the Paper

### Table 1: Benchmark Coverage

Columns:

- task type
- benchmark
- public harness
- public tasks
- Qwen3.6-27B reported result available
- TaskOps hypothesis
- expected cost tier

### Table 2: Outcome by Task Type

Columns:

- benchmark
- direct-agent score
- TaskOps-agent score
- absolute delta
- relative delta
- wall-time overhead
- token overhead
- false-completion rate delta

### Table 3: Orchestration Metrics

Columns:

- benchmark
- evidence completeness
- queue integrity
- restart recovery rate
- reporting coverage
- blocked/waiting honesty

## Recommended First Experiment

Start with a small, defensible pilot:

```text
SWE-bench Verified: 20 tasks
SWE-bench Pro: 20 tasks
Terminal-Bench 2.0: 15 tasks
SkillsBench: 15 tasks
NL2Repo: 10 tasks
ALE-FreeEasy-35: 12 tasks
HCAST public / RE-Bench: 3-5 long tasks
```

Use a fixed task list and publish the task IDs in this repository before running.
Do not tune TaskOps against the hidden results.

## Ultra-Long Campaign Layer

Existing public benchmarks rarely provide clean 3-day agent tasks. For the paper,
construct a TaskOps campaign benchmark by chaining public tasks into a durable
work graph:

```text
campaign objective
  -> benchmark task A
  -> benchmark task B
  -> review/debug task
  -> regression check
  -> documentation/report task
  -> restart/recovery injection
```

This campaign should be scored by:

- native benchmark results for the task nodes
- TaskOps orchestration metrics for the campaign
- whether a final answer is delivered only after all required evidence exists
