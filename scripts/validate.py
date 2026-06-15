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

    metric_ids = [metric.get("id") for metric in suite_doc.get("taskops_metrics", [])]
    require(metric_ids and len(metric_ids) == len(set(metric_ids)), "taskops metric ids missing or duplicated")

    pilot_slices = pilot_doc.get("pilot_slices", [])
    require(isinstance(pilot_slices, list) and pilot_slices, "pilot slices missing")
    for item in pilot_slices:
        benchmark_id = item.get("benchmark_id")
        require(benchmark_id in source_id_set, f"pilot references unknown benchmark {benchmark_id}")
        require(item.get("target_task_count", 0) > 0, f"pilot {benchmark_id} has invalid target count")

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
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
