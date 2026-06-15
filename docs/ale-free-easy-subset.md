# Agents' Last Exam Free/Easy Subset

This subset turns Agents' Last Exam into a more practical TaskOps paper
benchmark slice.

Full ALE is valuable, but it includes licensed tools, GPU-heavy environments,
Windows/professional GUI software, and infrastructure overhead that can obscure
the question we want to test:

> Does TaskOps improve long-running agent work when the worker model and tools
> are held mostly constant?

## Selection Policy

Start from ALE's official unlicensed selection:

```text
selected_tasks/unlicensed/overall.txt
```

Then keep tasks that are suitable for a cost-controlled TaskOps experiment:

- free/open-source or common free tools
- mostly CPU/free VM snapshots
- Python, shell, Docker/Kubernetes, LibreOffice, Inkscape, image-analysis, or
  similarly installable tools
- clear artifact contracts and hidden-reference scoring
- useful coverage of LLM reading/reasoning, data/code work, and image/video
  understanding

Exclude for the first paper subset:

- licensed commercial creative/professional software
- GPU-license tasks
- workflows where tool availability dominates the evaluation
- heavy specialist GUI operation unless it is explicitly part of a later visual
  extension

The machine-readable manifest is:

```text
data/ale_free_easy_subset.json
```

The manifest is generated from an ALE checkout by:

```bash
python3 scripts/build_ale_subset.py --ale-root /path/to/agents-last-exam
```

## Current Counts

As of the manifest generated on 2026-06-16:

- total tasks: 35
- recommended core: 27
- visual/image free extension: 8
- installability: 31 easy, 4 moderate
- image/video/geospatial understanding tasks: 9

## Recommended Core

These are the first ALE tasks to consider for the TaskOps paper pilot.

| Task | Category | Main capability | Tool tier |
| --- | --- | --- | --- |
| `business_finance/american_option_pricing_ls` | finance | numerical simulation | easy |
| `business_finance/basel_operational_risk_bia_cn` | finance | multilingual classification/spreadsheet | easy |
| `business_finance/digital_marketing_ab_test_analysis_1` | finance | statistics/business analysis | easy |
| `business_finance/digital_marketing_audience_segmentation_1` | finance | tabular segmentation | easy |
| `business_finance/financial_stmt_reconstruction_aapl_fy2024` | finance | PDF extraction/structured JSON | easy |
| `business_finance/sec_10k_financial_parsing` | finance | batch PDF extraction/evidence | easy |
| `computing_math/cp_test_gen_1` | computing | adversarial C++ test generation | easy |
| `computing_math/data_pipeline_etl_instance_1` | computing | ETL/SQLite warehouse | easy |
| `computing_math/k8s_migration_1` | computing | Docker/Kubernetes/Terraform/CI | moderate |
| `computing_math/k8s_payment_api_root_cause_analysis` | computing | Kubernetes incident analysis | easy |
| `computing_math/os_log_permission_guard_v1` | computing | Linux filesystem safety | easy |
| `computing_math/ranking_node_feature_parity_recovery_instance_1` | computing | service recovery/tests | easy |
| `computing_math/recsys_cold_start_instance_1` | computing | recommender modeling | easy |
| `computing_math/synthetic_causal_structure_inference` | computing | causal inference | easy |
| `education_info/homework_grading_numerical_pdes_instance_02` | education | rubric grading | easy |
| `education_info/moodle_gradebook_closeout_reconciliation` | education | data reconciliation | easy |
| `health_medicine/causal_ihdp_ite_estimation_6a_v1` | health | causal ML | easy |
| `health_medicine/epidemiology_forecast` | health | forecasting/reproduction | easy |
| `health_medicine/nhanes_confounder_sensitivity_analysis` | health | clinical statistics | easy |
| `legal/agora_governance_classify_instance_1` | legal | governance document classification | easy |
| `life_sciences/gene_expression_differential_analysis_functional_enrichment_analysis_1` | life sciences | bioinformatics/statistics | easy |
| `life_sciences/genomic_interval_processing_1` | life sciences | BEDTools/interval processing | easy |
| `life_sciences/tcga_brca_deg_analysis` | life sciences | differential expression | easy |
| `physical_sciences/exact_diag_heisenberg_j1j2` | physics | numerical physics | easy |
| `social_sciences/atwood_2022_measles_vaccine_reproduction` | social science | paper reproduction | easy |
| `transport_safety/abm_hangzhou_metro` | transport | geospatial simulation | easy |
| `transport_safety/capacitated_vehicle_routing_problems` | transport | routing optimization | easy |

## Visual / Image Free Extension

These are still unlicensed/free-tool tasks, but they test image, video, or
domain-image understanding. They should be sampled after the core subset is
running cleanly.

| Task | Image level | Main capability | Tool tier |
| --- | --- | --- | --- |
| `health_medicine/scene3_skullstrip_qc` | domain image | brain MRI QC | easy |
| `health_medicine/wsi_tumor_localization_1` | domain image | pathology image navigation | moderate |
| `life_sciences/cell_tracking_instance_1` | domain image | microscopy segmentation/tracking | easy |
| `life_sciences/merfish_image_decoding_segmentation_1` | domain image | bioimage decoding/segmentation | moderate |
| `life_sciences/yeast_colony_detection` | basic image | colony counting | moderate |
| `physical_sciences/hst_acs_wfc_visit_reduction` | domain image | astronomy image reduction | easy |
| `visual_media/inkscape_cultural_poster_design` | basic image | SVG poster design | easy |
| `visual_media/video_storyboard_001` | video understanding | shot log / temporal review | easy |

## Paper Use

This subset should be reported as:

```text
ALE-FreeEasy-35
```

with two splits:

```text
ALE-FreeEasy-Core-27
ALE-FreeEasy-Visual-8
```

Recommended first pilot sampling:

```text
10 core tasks
2-3 visual extension tasks
```

Do not claim this as the full ALE benchmark. It is a practical TaskOps subset
curated from ALE's official unlicensed task selection.

