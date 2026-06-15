#!/usr/bin/env python3
"""Validate TaskOps benchmark manifest files."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_url(value: str, context: str) -> None:
    parsed = urlparse(value)
    require(parsed.scheme in {"http", "https"}, f"{context}: invalid URL scheme")
    require(bool(parsed.netloc), f"{context}: missing URL host")


def main() -> int:
    sources_doc = load_json(DATA / "benchmark_sources.json")
    qwen_doc = load_json(DATA / "qwen3_6_27b_reported_results.json")
    suite_doc = load_json(DATA / "taskops_paper_suite.json")
    pilot_doc = load_json(DATA / "pilot_plan.json")
    ale_subset_doc = load_json(DATA / "ale_free_easy_subset.json")
    run_matrix_doc = load_json(DATA / "run_matrix.json")
    harness_audit_doc = load_json(DATA / "harness_audit.json")
    local_score_doc = load_json(DATA / "local_score_tasks.json")
    adapters_doc = load_json(ROOT / "config" / "adapters.json")
    runtimes_doc = load_json(ROOT / "config" / "runtimes.json")

    sources = sources_doc.get("sources", [])
    require(isinstance(sources, list) and sources, "benchmark_sources.json has no sources")

    source_ids = []
    for source in sources:
        source_id = source.get("id")
        require(source_id, "source is missing id")
        source_ids.append(source_id)
        validate_url(source.get("url", ""), f"source {source_id}")
        require(source.get("taskops_type"), f"source {source_id} missing taskops_type")
        require("qwen3_6_27b_report_status" in source, f"source {source_id} missing qwen status")

    require(len(source_ids) == len(set(source_ids)), "duplicate source ids")
    source_id_set = set(source_ids)

    qwen_results = qwen_doc.get("reported_results", [])
    require(isinstance(qwen_results, list) and qwen_results, "qwen results missing")
    for result in qwen_results:
        benchmark_id = result.get("benchmark_id")
        require(benchmark_id in source_id_set, f"qwen result references unknown benchmark {benchmark_id}")
        require(isinstance(result.get("score"), (int, float)), f"qwen result {benchmark_id} score is not numeric")

    for section_name in ("core_suite", "extension_suite"):
        section = suite_doc.get(section_name, [])
        require(isinstance(section, list) and section, f"{section_name} missing")
        for item in section:
            type_id = item.get("type_id")
            refs = item.get("benchmark_ids", [])
            require(type_id, f"{section_name} item missing type_id")
            require(isinstance(refs, list) and refs, f"{section_name} {type_id} has no benchmarks")
            for ref in refs:
                require(ref in source_id_set, f"{section_name} {type_id} references unknown benchmark {ref}")

    adapters = adapters_doc.get("adapters", {})
    require(isinstance(adapters, dict) and adapters, "adapters config missing")
    for adapter_id, adapter in adapters.items():
        require(adapter_id in source_id_set, f"adapter references unknown benchmark {adapter_id}")
        require("configured" in adapter, f"adapter {adapter_id} missing configured flag")
        command_template = adapter.get("command_template")
        require(command_template, f"adapter {adapter_id} missing command_template")
        command_parts = command_template.split()
        if len(command_parts) >= 2 and command_parts[0].startswith("python"):
            script_path = ROOT / command_parts[1]
            require(script_path.exists(), f"adapter {adapter_id} script does not exist: {command_parts[1]}")

    runtimes = runtimes_doc.get("runtimes", {})
    require(isinstance(runtimes, dict) and runtimes, "runtimes config missing")
    require(runtimes_doc.get("default_runtime") in runtimes, "default_runtime is not defined in runtimes")
    for runtime_id, runtime in runtimes.items():
        require("configured" in runtime, f"runtime {runtime_id} missing configured flag")
        require(runtime.get("kind"), f"runtime {runtime_id} missing kind")
        require("score_eligible" in runtime, f"runtime {runtime_id} missing score_eligible")
        if runtime.get("kind") == "command_template":
            require(runtime.get("command_template_env"), f"runtime {runtime_id} missing command_template_env")
            placeholders = runtime.get("required_placeholders", [])
            require("{prompt_file}" in placeholders, f"runtime {runtime_id} missing prompt_file placeholder")
            require("{output_file}" in placeholders, f"runtime {runtime_id} missing output_file placeholder")
        if runtime.get("kind") == "openclaw_cli":
            require(runtime.get("binary"), f"runtime {runtime_id} missing binary")

    metric_ids = [metric.get("id") for metric in suite_doc.get("taskops_metrics", [])]
    require(metric_ids and len(metric_ids) == len(set(metric_ids)), "taskops metric ids missing or duplicated")

    pilot_slices = pilot_doc.get("pilot_slices", [])
    require(isinstance(pilot_slices, list) and pilot_slices, "pilot slices missing")
    for item in pilot_slices:
        benchmark_id = item.get("benchmark_id")
        require(benchmark_id in source_id_set, f"pilot references unknown benchmark {benchmark_id}")
        require(item.get("target_task_count", 0) > 0, f"pilot {benchmark_id} has invalid target count")

    matrix_benchmark_ids = set()
    for mode, mode_doc in run_matrix_doc.get("suite_modes", {}).items():
        benches = mode_doc.get("benchmarks", [])
        require(benches, f"run matrix mode {mode} has no benchmarks")
        for bench in benches:
            benchmark_id = bench.get("benchmark_id")
            require(benchmark_id in source_id_set, f"run matrix mode {mode} references unknown benchmark {benchmark_id}")
            require(benchmark_id in adapters, f"run matrix benchmark {benchmark_id} has no adapter")
            matrix_benchmark_ids.add(benchmark_id)
    require(matrix_benchmark_ids, "run matrix has no benchmarks")

    result_contract = run_matrix_doc.get("result_contract", {})
    required_result_keys = set(result_contract.get("required_keys", []))
    for key in ("score", "raw_scores", "task_count", "native_score", "taskops_metrics", "artifacts"):
        require(key in required_result_keys, f"run matrix result_contract missing {key}")

    audit_rows = harness_audit_doc.get("benchmarks", [])
    require(isinstance(audit_rows, list) and audit_rows, "harness audit has no rows")
    allowed_audit_statuses = set(harness_audit_doc.get("status_vocab", {}).keys())
    require(allowed_audit_statuses, "harness audit missing status_vocab")
    audited_ids = set()
    for row in audit_rows:
        benchmark_id = row.get("benchmark_id")
        require(benchmark_id in source_id_set, f"harness audit references unknown benchmark {benchmark_id}")
        require(row.get("status") in allowed_audit_statuses, f"harness audit {benchmark_id} has invalid status")
        require(row.get("official_or_primary_source"), f"harness audit {benchmark_id} missing source")
        validate_url(row.get("official_or_primary_source"), f"harness audit {benchmark_id}")
        require(row.get("scoring_path"), f"harness audit {benchmark_id} missing scoring_path")
        require(row.get("adapter_work"), f"harness audit {benchmark_id} missing adapter_work")
        audited_ids.add(benchmark_id)
    missing_audits = matrix_benchmark_ids - audited_ids
    require(not missing_audits, f"run matrix benchmark ids missing harness audit rows: {sorted(missing_audits)}")

    local_score_benchmarks = local_score_doc.get("benchmarks", {})
    require(isinstance(local_score_benchmarks, dict) and local_score_benchmarks, "local score tasks missing")
    missing_local_scores = matrix_benchmark_ids - set(local_score_benchmarks)
    require(not missing_local_scores, f"run matrix benchmark ids missing local score tasks: {sorted(missing_local_scores)}")
    for benchmark_id, benchmark in local_score_benchmarks.items():
        require(benchmark_id in source_id_set, f"local score tasks reference unknown benchmark {benchmark_id}")
        require(benchmark.get("metric_name"), f"local score benchmark {benchmark_id} missing metric_name")
        tasks = benchmark.get("tasks", [])
        require(isinstance(tasks, list) and tasks, f"local score benchmark {benchmark_id} has no tasks")
        task_ids = []
        for task in tasks:
            task_id = task.get("id")
            require(task_id, f"local score benchmark {benchmark_id} has a task missing id")
            task_ids.append(task_id)
            require(task.get("prompt"), f"local score task {benchmark_id}/{task_id} missing prompt")
            patterns = task.get("answer_patterns", [])
            require(isinstance(patterns, list) and patterns, f"local score task {benchmark_id}/{task_id} missing answer_patterns")
        require(len(task_ids) == len(set(task_ids)), f"local score benchmark {benchmark_id} has duplicate task ids")

    ale_tasks = ale_subset_doc.get("tasks", [])
    require(isinstance(ale_tasks, list) and ale_tasks, "ALE subset has no tasks")
    ale_task_paths = [task.get("task_path") for task in ale_tasks]
    require(len(ale_task_paths) == len(set(ale_task_paths)), "ALE subset has duplicate task paths")
    allowed_splits = {"recommended_core", "visual_free_extension"}
    allowed_installability = {"easy", "moderate"}
    for task in ale_tasks:
        task_path = task.get("task_path")
        require(task_path, "ALE subset task missing task_path")
        require(task.get("official_ale_unlicensed") is True, f"{task_path} is not marked official unlicensed")
        require(task.get("split") in allowed_splits, f"{task_path} has invalid split")
        require(task.get("tool_installability") in allowed_installability, f"{task_path} has invalid installability")
        require(task.get("vm_snapshot") in {"cpu-free-ubuntu", "cpu-free"}, f"{task_path} uses disallowed VM snapshot")
        require(task.get("software"), f"{task_path} missing software")
        require(task.get("capability_tags"), f"{task_path} missing capability tags")
        require(task.get("taskops_stress"), f"{task_path} missing TaskOps stress tags")

    print("ok: benchmark manifests are valid")
    print(f"ok: {len(source_ids)} benchmark sources")
    print(f"ok: {len(qwen_results)} Qwen3.6-27B reported result rows")
    print(f"ok: {len(ale_tasks)} ALE free/easy subset tasks")
    print(f"ok: {len(matrix_benchmark_ids)} run-matrix benchmark ids")
    print(f"ok: {len(local_score_benchmarks)} local score benchmark task packs")
    print(f"ok: {len(audited_ids)} harness audit rows")
    print(f"ok: {len(runtimes)} runtime adapters")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
