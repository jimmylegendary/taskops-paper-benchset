#!/usr/bin/env python3
"""Build the curated ALE free/easy subset manifest from an ALE checkout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


CURATED_TASKS = {
    "business_finance/american_option_pricing_ls": {
        "split": "recommended_core",
        "llm_reasoning_level": "medium",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["numerical_reasoning", "python", "simulation"],
        "taskops_stress": ["multi_artifact", "validation_loop"]
    },
    "business_finance/basel_operational_risk_bia_cn": {
        "split": "recommended_core",
        "llm_reasoning_level": "high",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["llm_reading", "classification", "spreadsheet", "multilingual"],
        "taskops_stress": ["rubric_following", "evidence_traceability"]
    },
    "business_finance/digital_marketing_ab_test_analysis_1": {
        "split": "recommended_core",
        "llm_reasoning_level": "medium",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["statistics", "python", "business_analysis"],
        "taskops_stress": ["analysis_report", "validation_loop"]
    },
    "business_finance/digital_marketing_audience_segmentation_1": {
        "split": "recommended_core",
        "llm_reasoning_level": "medium",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["tabular_data", "python", "segmentation"],
        "taskops_stress": ["data_cleaning", "artifact_contract"]
    },
    "business_finance/financial_stmt_reconstruction_aapl_fy2024": {
        "split": "recommended_core",
        "llm_reasoning_level": "high",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["pdf_extraction", "financial_reasoning", "structured_json"],
        "taskops_stress": ["source_grounding", "artifact_contract"]
    },
    "business_finance/sec_10k_financial_parsing": {
        "split": "recommended_core",
        "llm_reasoning_level": "high",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["pdf_extraction", "batch_processing", "structured_json"],
        "taskops_stress": ["many_artifacts", "deterministic_rerun", "evidence_traceability"]
    },
    "computing_math/cp_test_gen_1": {
        "split": "recommended_core",
        "llm_reasoning_level": "medium",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["c_plus_plus", "adversarial_testing", "algorithmic_reasoning"],
        "taskops_stress": ["test_generation", "validation_loop"]
    },
    "computing_math/data_pipeline_etl_instance_1": {
        "split": "recommended_core",
        "llm_reasoning_level": "medium",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["etl", "sqlite", "python", "tabular_data"],
        "taskops_stress": ["multi_artifact", "truthful_sidecars", "schema_contract"]
    },
    "computing_math/k8s_migration_1": {
        "split": "recommended_core",
        "llm_reasoning_level": "high",
        "image_understanding_level": "none",
        "tool_installability": "moderate",
        "capability_tags": ["docker", "kubernetes", "terraform", "ci_cd"],
        "taskops_stress": ["multi_stage_execution", "external_tool_state", "verification_snapshots"]
    },
    "computing_math/k8s_payment_api_root_cause_analysis": {
        "split": "recommended_core",
        "llm_reasoning_level": "high",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["incident_analysis", "kubernetes", "structured_json"],
        "taskops_stress": ["source_grounding", "honest_diagnosis"]
    },
    "computing_math/os_log_permission_guard_v1": {
        "split": "recommended_core",
        "llm_reasoning_level": "medium",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["linux", "bash", "filesystem_safety"],
        "taskops_stress": ["safety_constraints", "artifact_contract"]
    },
    "computing_math/ranking_node_feature_parity_recovery_instance_1": {
        "split": "recommended_core",
        "llm_reasoning_level": "medium",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["python", "pytest", "service_recovery"],
        "taskops_stress": ["debugging", "safe_cleanup", "regression_tests"]
    },
    "computing_math/recsys_cold_start_instance_1": {
        "split": "recommended_core",
        "llm_reasoning_level": "medium",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["recommender_systems", "python", "machine_learning"],
        "taskops_stress": ["modeling_choices", "evaluation_contract"]
    },
    "computing_math/synthetic_causal_structure_inference": {
        "split": "recommended_core",
        "llm_reasoning_level": "high",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["causal_inference", "python", "tabular_data"],
        "taskops_stress": ["repeated_analysis", "structured_submission"]
    },
    "education_info/homework_grading_numerical_pdes_instance_02": {
        "split": "recommended_core",
        "llm_reasoning_level": "high",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["llm_reading", "grading", "numerical_methods"],
        "taskops_stress": ["rubric_following", "evidence_traceability"]
    },
    "education_info/moodle_gradebook_closeout_reconciliation": {
        "split": "recommended_core",
        "llm_reasoning_level": "medium",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["data_reconciliation", "python", "education_records"],
        "taskops_stress": ["multi_artifact", "consistency_checks"]
    },
    "health_medicine/causal_ihdp_ite_estimation_6a_v1": {
        "split": "recommended_core",
        "llm_reasoning_level": "medium",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["causal_inference", "python", "machine_learning"],
        "taskops_stress": ["hidden_test_script", "modeling_choices"]
    },
    "health_medicine/epidemiology_forecast": {
        "split": "recommended_core",
        "llm_reasoning_level": "medium",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["forecasting", "python", "public_health"],
        "taskops_stress": ["reproduction", "scoring_table"]
    },
    "health_medicine/nhanes_confounder_sensitivity_analysis": {
        "split": "recommended_core",
        "llm_reasoning_level": "high",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["clinical_statistics", "python", "tabular_data"],
        "taskops_stress": ["cohort_construction", "sensitivity_analysis"]
    },
    "legal/agora_governance_classify_instance_1": {
        "split": "recommended_core",
        "llm_reasoning_level": "high",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["llm_reading", "legal_classification", "governance"],
        "taskops_stress": ["rubric_following", "source_grounding"]
    },
    "life_sciences/gene_expression_differential_analysis_functional_enrichment_analysis_1": {
        "split": "recommended_core",
        "llm_reasoning_level": "medium",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["bioinformatics", "python", "statistics"],
        "taskops_stress": ["pipeline_execution", "multi_artifact"]
    },
    "life_sciences/genomic_interval_processing_1": {
        "split": "recommended_core",
        "llm_reasoning_level": "medium",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["bioinformatics", "bedtools", "python"],
        "taskops_stress": ["cli_pipeline", "deterministic_output"]
    },
    "life_sciences/tcga_brca_deg_analysis": {
        "split": "recommended_core",
        "llm_reasoning_level": "medium",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["bioinformatics", "python", "statistics"],
        "taskops_stress": ["analysis_report", "structured_outputs"]
    },
    "physical_sciences/exact_diag_heisenberg_j1j2": {
        "split": "recommended_core",
        "llm_reasoning_level": "high",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["physics", "python", "numerical_linear_algebra"],
        "taskops_stress": ["scientific_computation", "validation_loop"]
    },
    "social_sciences/atwood_2022_measles_vaccine_reproduction": {
        "split": "recommended_core",
        "llm_reasoning_level": "high",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["paper_reproduction", "pdf_reading", "python"],
        "taskops_stress": ["source_grounding", "reproduction"]
    },
    "transport_safety/abm_hangzhou_metro": {
        "split": "recommended_core",
        "llm_reasoning_level": "medium",
        "image_understanding_level": "basic_geospatial",
        "tool_installability": "easy",
        "capability_tags": ["geospatial", "simulation", "python"],
        "taskops_stress": ["simulation_pipeline", "multi_artifact"]
    },
    "transport_safety/capacitated_vehicle_routing_problems": {
        "split": "recommended_core",
        "llm_reasoning_level": "medium",
        "image_understanding_level": "none",
        "tool_installability": "easy",
        "capability_tags": ["optimization", "python", "routing"],
        "taskops_stress": ["optimization_loop", "structured_submission"]
    },
    "health_medicine/scene3_skullstrip_qc": {
        "split": "visual_free_extension",
        "llm_reasoning_level": "medium",
        "image_understanding_level": "domain_image",
        "tool_installability": "easy",
        "capability_tags": ["medical_image_qc", "python", "nifti"],
        "taskops_stress": ["visual_qc", "honest_decision"]
    },
    "health_medicine/wsi_tumor_localization_1": {
        "split": "visual_free_extension",
        "llm_reasoning_level": "medium",
        "image_understanding_level": "domain_image",
        "tool_installability": "moderate",
        "capability_tags": ["pathology_image", "python", "openslide"],
        "taskops_stress": ["large_image_navigation", "structured_output"]
    },
    "life_sciences/cell_tracking_instance_1": {
        "split": "visual_free_extension",
        "llm_reasoning_level": "medium",
        "image_understanding_level": "domain_image",
        "tool_installability": "easy",
        "capability_tags": ["microscopy", "segmentation", "tracking", "python"],
        "taskops_stress": ["image_pipeline", "sequence_artifacts"]
    },
    "life_sciences/merfish_image_decoding_segmentation_1": {
        "split": "visual_free_extension",
        "llm_reasoning_level": "high",
        "image_understanding_level": "domain_image",
        "tool_installability": "moderate",
        "capability_tags": ["microscopy", "segmentation", "bioimage_pipeline", "python"],
        "taskops_stress": ["pipeline_execution", "multi_artifact", "quality_metrics"]
    },
    "life_sciences/yeast_colony_detection": {
        "split": "visual_free_extension",
        "llm_reasoning_level": "low",
        "image_understanding_level": "basic_image",
        "tool_installability": "moderate",
        "capability_tags": ["image_counting", "cellprofiler", "python"],
        "taskops_stress": ["image_pipeline", "measurement_table"]
    },
    "physical_sciences/hst_acs_wfc_visit_reduction": {
        "split": "visual_free_extension",
        "llm_reasoning_level": "high",
        "image_understanding_level": "domain_image",
        "tool_installability": "easy",
        "capability_tags": ["astronomy_image", "python", "astropy"],
        "taskops_stress": ["scientific_pipeline", "qc_report"]
    },
    "visual_media/inkscape_cultural_poster_design": {
        "split": "visual_free_extension",
        "llm_reasoning_level": "medium",
        "image_understanding_level": "basic_image",
        "tool_installability": "easy",
        "capability_tags": ["visual_design", "svg", "image_layout"],
        "taskops_stress": ["creative_artifact", "spec_following"]
    },
    "visual_media/video_storyboard_001": {
        "split": "visual_free_extension",
        "llm_reasoning_level": "high",
        "image_understanding_level": "video_understanding",
        "tool_installability": "easy",
        "capability_tags": ["video_understanding", "docx", "archival_logging"],
        "taskops_stress": ["temporal_review", "structured_report"]
    }
}


def read_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


def normalize_files(files: list[dict]) -> list[dict]:
    normalized = []
    for item in files or []:
        if isinstance(item, str):
            normalized.append({"path": item})
            continue
        normalized.append({
            "name": item.get("name"),
            "format": item.get("format"),
            "path": item.get("path"),
            "description": item.get("description")
        })
    return normalized


def file_extensions(files: list[dict]) -> list[str]:
    exts = set()
    for item in files:
        path = (item.get("path") or item.get("name") or "").lower()
        if "." in path and not path.endswith("/"):
            exts.add(path.rsplit(".", 1)[1].strip("`*{}<>"))
    return sorted(ext for ext in exts if ext)


def build_manifest(ale_root: Path) -> dict:
    unlicensed_path = ale_root / "selected_tasks" / "unlicensed" / "overall.txt"
    official_unlicensed = set(read_lines(unlicensed_path))
    current_sha = None
    head_path = ale_root / ".git" / "HEAD"
    if head_path.exists():
        import subprocess
        current_sha = subprocess.check_output(["git", "-C", str(ale_root), "rev-parse", "HEAD"], text=True).strip()

    tasks = []
    for task_path, meta in CURATED_TASKS.items():
        card_path = ale_root / "tasks" / task_path / "task_card.json"
        card = json.loads(card_path.read_text(encoding="utf-8"))
        inputs = normalize_files(card.get("inputFiles") or [])
        refs = normalize_files(card.get("referenceFiles") or [])
        vm = card.get("vm") or {}
        software = card.get("software") or []
        if isinstance(software, str):
            software = [software]
        tasks.append({
            "task_path": task_path,
            "task_id": card.get("taskId") or task_path,
            "title": card.get("title") or card.get("taskName") or card.get("task_name"),
            "summary": card.get("summary"),
            "category": card.get("category"),
            "official_ale_unlicensed": task_path in official_unlicensed,
            "split": meta["split"],
            "vm_snapshot": vm.get("snapshot"),
            "machine_type": vm.get("machineType"),
            "timeout_seconds": vm.get("timeout"),
            "software": software,
            "input_extensions": file_extensions(inputs),
            "reference_extensions": file_extensions(refs),
            "input_files": inputs,
            "reference_files": refs,
            "agent_must_do_count": len(card.get("agentMustDo") or []),
            "llm_reasoning_level": meta["llm_reasoning_level"],
            "image_understanding_level": meta["image_understanding_level"],
            "tool_installability": meta["tool_installability"],
            "capability_tags": meta["capability_tags"],
            "taskops_stress": meta["taskops_stress"]
        })

    return {
        "schema_version": "0.1.0",
        "updated_at": "2026-06-16",
        "source": {
            "benchmark_id": "agents_last_exam",
            "repo_url": "https://github.com/rdi-berkeley/agents-last-exam",
            "ale_git_sha": current_sha,
            "official_selection_file": "selected_tasks/unlicensed/overall.txt",
            "official_unlicensed_task_count_at_build": len(official_unlicensed)
        },
        "selection_policy": {
            "goal": "A TaskOps-friendly ALE subset emphasizing LLM reading/reasoning and image understanding while avoiding licensed or hard-to-install commercial tools.",
            "include": [
                "Task appears in ALE's official unlicensed overall selection.",
                "Tooling is free/open-source or common free desktop software.",
                "Prefer CPU/free snapshots; no licensed GPU/proprietary creative suites.",
                "Tasks expose structured artifacts suitable for TaskOps run graph and EoW scoring."
            ],
            "exclude": [
                "Licensed commercial software such as Adobe, DaVinci Resolve, PowerMill, or Microsoft PowerPoint.",
                "GPU-license snapshots.",
                "Tasks whose first value is professional GUI operation rather than LLM/tool orchestration.",
                "Very specialized heavy simulators are deferred unless they are already useful as a long-work stressor."
            ]
        },
        "counts": {
            "total": len(tasks),
            "recommended_core": sum(1 for task in tasks if task["split"] == "recommended_core"),
            "visual_free_extension": sum(1 for task in tasks if task["split"] == "visual_free_extension")
        },
        "tasks": tasks
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ale-root", default="/tmp/agents-last-exam", help="Path to an agents-last-exam checkout")
    parser.add_argument("--out", default="data/ale_free_easy_subset.json", help="Output manifest path")
    args = parser.parse_args()

    ale_root = Path(args.ale_root).resolve()
    out = Path(args.out)
    manifest = build_manifest(ale_root)
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out} with {manifest['counts']['total']} tasks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

