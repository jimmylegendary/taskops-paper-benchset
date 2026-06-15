# Research Notes

Research date: 2026-06-16.

## Qwen3.6-27B

The Qwen3.6-27B Hugging Face model card reports the coding-agent benchmark
scores used in this repository:

- SWE-bench Verified: 77.2
- SWE-bench Pro: 53.5
- SWE-bench Multilingual: 71.3
- Terminal-Bench 2.0: 59.3
- SkillsBench Avg5: 48.2
- NL2Repo: 36.2
- Claw-Eval Avg: 72.4
- Claw-Eval Pass^3: 60.6
- QwenClawBench: 53.4

Source: https://huggingface.co/Qwen/Qwen3.6-27B

Important caveats from the same model card:

- SWE-Bench Series used an internal agent scaffold with bash and file-edit tools.
- SWE-bench Pro was corrected/refined before reported evaluation.
- Terminal-Bench 2.0 used Harbor/Terminus-2, 3h timeout, 32 CPU/48 GB RAM, and
  an average of 5 runs.
- SkillsBench used OpenCode on a 78-task self-contained subset.
- QwenClawBench and QwenWebBench appear useful but are not public enough for a
  reproducible core paper suite.

## Benchmark Source Notes

### SWE-bench Verified

Use as a control benchmark. It is recognized and public, but may be too short or
too saturated to expose TaskOps' main value.

Source: https://www.swebench.com/

### SWE-bench Pro

Strong core benchmark for hard codebase issue repair. Public repo includes data
access, Docker evaluation, patch gathering, and reproduction guidance.

Source: https://github.com/scaleapi/SWE-bench_Pro-os

### Terminal-Bench 2.0

Strong core benchmark for terminal agents. The official site describes terminal
mastery and shows task examples such as building a Linux kernel, configuring a
git/web server, cracking archives, and creating TLS certificates.

Source: https://www.tbench.ai/

### SkillsBench

Strong core benchmark for skill/procedure following. It evaluates how agents use
modular skills and workflows, which is directly aligned with TaskOps.

Source: https://github.com/benchflow-ai/skillsbench

### NL2Repo

Strong core benchmark for 0-to-1 repository generation. It tests architecture,
multi-file implementation, package setup, and installability from a natural
language document.

Source: https://github.com/multimodal-art-projection/NL2RepoBench

### HCAST Public

Best fit for time-horizon claims. The public repository contains a subset of
the HCAST tasks and points to the METR Task Standard / Task Bridge path.

Source: https://github.com/METR/hcast-public

### RE-Bench

Strong 8-hour-class AI R&D benchmark. It contains seven ML research engineering
environments and human expert 8-hour attempt data. Use as high-value long-work
slice, not as broad coverage.

Source: https://github.com/METR/RE-Bench

### Agents' Last Exam

Useful as broad external oracle, especially because task cards and graders can
be adapted into TaskOps work graphs. It is infra-heavy, so start with selected
Linux deterministic tasks.

Source: https://github.com/rdi-berkeley/agents-last-exam

### TheAgentCompany

Good extension benchmark for workplace and multi-app coordination. It is more
operationally complex than the core coding benchmarks.

Source: https://github.com/TheAgentCompany/TheAgentCompany

### Vending-Bench

Good long-term coherence benchmark. Less code-centric, but useful for the
ultra-long "does the agent drift over time?" question.

Source: https://arxiv.org/html/2502.15840v1

## Current Decision

Core paper suite:

```text
SWE-bench Verified
SWE-bench Pro
Terminal-Bench 2.0
SkillsBench
NL2Repo
HCAST public subset
RE-Bench
```

Extension suite:

```text
Agents' Last Exam
TheAgentCompany
Vending-Bench
SWE-bench Multilingual
Claw-Eval / QwenClawBench only if definitions become public
```

