# Analysis and Reproducibility Index

This directory contains frozen analysis campaigns used to support the LAFC-Evict manuscript and release validation. Dated and problem-numbered directory names are intentionally retained for provenance. They are not all independent scientific contributions, and the names should not be changed because manuscript text, tables, figures, and audit records may point to them.

Use this index as the public navigation layer. Individual analysis directories may contain local-path provenance or historical workflow notes; those records are retained so results can be audited, not because they are current setup instructions.

## Target Characterization

- Path: [`analysis/sigmod_target_discriminativeness_20260913/`](sigmod_target_discriminativeness_20260913/)
- Purpose: candidate, decision-view, and pairwise target-characterization summaries for the benchmark label surface.
- Supports: manuscript target degeneracy, discriminativeness, row/view sanity checks, and baseline context.
- Key reports/outputs: [`REPORT.md`](sigmod_target_discriminativeness_20260913/REPORT.md), `outputs/candidate_level_report.json`, `outputs/decision_view_report.json`, `outputs/pairwise_report.json`.

## Long-Horizon Sensitivity

- Path: [`analysis/problem4_matched_horizon_20260917/`](problem4_matched_horizon_20260917/)
- Purpose: matched physical-decision analysis for horizons `H={16,32,64,128}`.
- Supports: long-horizon sensitivity claims and the matched-population figure/table material.
- Key reports/outputs: [`DENOMINATOR_AUDIT.md`](problem4_matched_horizon_20260917/DENOMINATOR_AUDIT.md), `artifacts/common_population_manifest.json`, `outputs/validation.json`, `figures/figure_problem4_matched_long_horizon_sensitivity.pdf`.
- Special dependency: contains C++/Python analysis scripts; rerunning is analysis-specific, not part of the base `tests/` smoke suite.

## Closed-Loop Evaluation

- Path: [`analysis/closed_loop_production_tier1_20260913/`](closed_loop_production_tier1_20260913/)
- Purpose: Tier-1 closed-loop policy-evaluation harness and tests.
- Supports: closed-loop validation framing and the policy-comparison evidence later frozen under [`analysis/closed_loop_tier1_evidence_20260914/`](closed_loop_tier1_evidence_20260914/).
- Key reports/outputs: [`README.md`](closed_loop_production_tier1_20260913/README.md), `scripts/run_tier1.py`, `tests/`.

- Path: [`analysis/closed_loop_tier1_evidence_20260914/`](closed_loop_tier1_evidence_20260914/)
- Purpose: compact frozen evidence from the validated Tier-1 closed-loop run.
- Supports: manuscript closed-loop comparison values and validation claims.
- Key reports/outputs: `run/20260914T023445Z_8a4cd32402a1/run_manifest.json`, `run/20260914T023445Z_8a4cd32402a1/run_results.csv`, `run/20260914T023445Z_8a4cd32402a1/run_results.jsonl`.

## Offline / Closed-Loop Linkage

- Path: [`analysis/closed_loop_offline_linkage_20260914/`](closed_loop_offline_linkage_20260914/)
- Purpose: joins offline benchmark metrics to closed-loop replay outcomes and computes rank/gap/workload-dependence analyses.
- Supports: offline-to-online correspondence and linkage robustness claims.
- Key reports/outputs: [`README.md`](closed_loop_offline_linkage_20260914/README.md), [`SCIENTIFIC_SUMMARY.md`](closed_loop_offline_linkage_20260914/SCIENTIFIC_SUMMARY.md), `outputs/rq_cl1_rank_agreement.json`, `outputs/rq_cl2_gap_correspondence.json`, `outputs/rq_cl2_scatter_data.csv`.

## Mechanistic Analysis

- Path: [`analysis/closed_loop_mechanistic_analysis_20260914/`](closed_loop_mechanistic_analysis_20260914/)
- Purpose: trace-locality and mechanism diagnostics explaining workload-specific closed-loop behavior.
- Supports: locality/mechanistic interpretation of closed-loop and linkage exceptions.
- Key reports/outputs: [`README.md`](closed_loop_mechanistic_analysis_20260914/README.md), [`SCIENTIFIC_SUMMARY.md`](closed_loop_mechanistic_analysis_20260914/SCIENTIFIC_SUMMARY.md), [`MECHANISM_CLASSIFICATION.md`](closed_loop_mechanistic_analysis_20260914/MECHANISM_CLASSIFICATION.md), `outputs/reuse_distance_summary.csv`, `outputs/trace_characteristics.csv`.

## Continuation-Policy Sensitivity

- Path: [`analysis/continuation_policy_sensitivity_pilot_20260914/`](continuation_policy_sensitivity_pilot_20260914/)
- Purpose: pilot continuation-policy sensitivity checks.
- Supports: scoped robustness discussion before full sensitivity analysis.
- Key reports/outputs: [`README.md`](continuation_policy_sensitivity_pilot_20260914/README.md), `outputs/20260914T034205Z_79e601be06ae/run_manifest.json`.

- Path: [`analysis/continuation_policy_sensitivity_full_20260914/`](continuation_policy_sensitivity_full_20260914/)
- Purpose: sampled continuation-policy sensitivity study across the documented configurations.
- Supports: continuation-policy robustness claims and limitations.
- Key reports/outputs: [`README.md`](continuation_policy_sensitivity_full_20260914/README.md), `PRIMARY_MANIFEST.json`, `DIAGNOSTIC_MANIFEST.json`, `outputs/20260914T040333Z_1f66342be435/run_manifest.json`.
- Special dependency: tests import shared campaign scripts and are not part of the base install contract.

- Path: [`analysis/continuation_policy_mru_population_census_20260914/`](continuation_policy_mru_population_census_20260914/)
- Purpose: compact validated full-population MRU continuation census.
- Supports: full-population MRU robustness evidence.
- Key reports/outputs: `validated/20260914T042528Z_1a29e773a113/summary_by_family_capacity_horizon.csv`, `validated/20260914T042528Z_1a29e773a113/RAW_EVIDENCE_MANIFEST.json`, `validated/20260914T042528Z_1a29e773a113/RAW_EVIDENCE_MANIFEST_POST_VALIDATION.json`.

## Expanded Comparator Robustness

- Path: [`analysis/problem5_expanded_closed_loop_20260917/`](problem5_expanded_closed_loop_20260917/)
- Purpose: expanded closed-loop comparator study and robustness evidence.
- Supports: expanded comparator table/figure material and closed-loop robustness discussion.
- Key reports/outputs: [`COMPARATOR_PROTOCOL.md`](problem5_expanded_closed_loop_20260917/COMPARATOR_PROTOCOL.md), [`IMPLEMENTATION_INVENTORY.md`](problem5_expanded_closed_loop_20260917/IMPLEMENTATION_INVENTORY.md), `outputs/problem5_primary_table.csv`, `outputs/problem5_scientific_answers.json`, `figures/figure_problem5_policy_spread_vs_discriminativeness.pdf`.
- Special dependency: optional analysis tests may require dependencies listed in [`requirements-problem5-expanded-baselines.txt`](problem5_expanded_closed_loop_20260917/requirements-problem5-expanded-baselines.txt), including simulator/policy support not installed by the base package.

## Feature / Schema Integrity

- Path: [`analysis/feature_provenance_repair_20260917/`](feature_provenance_repair_20260917/)
- Purpose: feature provenance audit, clean feature interface checks, and repaired modeling evidence.
- Supports: model-feature-schema guidance and feature-integrity claims.
- Key reports/outputs: [`FEATURE_PROVENANCE_AUDIT.md`](feature_provenance_repair_20260917/FEATURE_PROVENANCE_AUDIT.md), [`LEGACY_VS_CLEAN_RESULTS.md`](feature_provenance_repair_20260917/LEGACY_VS_CLEAN_RESULTS.md), `RUN_STATUS.json`, `artifacts/feature_inventory.csv`.

- Path: [`analysis/pairwise_provenance_repair_20260913/`](pairwise_provenance_repair_20260913/)
- Purpose: canonical pairwise-sample regeneration and provenance repair.
- Supports: pairwise-view orientation and canonical pairwise sample evidence.
- Key reports/outputs: [`README.md`](pairwise_provenance_repair_20260913/README.md), [`REPORT.md`](pairwise_provenance_repair_20260913/REPORT.md), [`ARTIFACT_MANIFEST.md`](pairwise_provenance_repair_20260913/ARTIFACT_MANIFEST.md), `artifacts/pairwise_sample_regenerated_canonical.parquet`.

## Historical / Audit Directories

Other directories under `analysis/` include feasibility studies, pilot runs, design notes, micro-closure analyses, and audit records retained for reproducibility and decision provenance. They should generally be left unchanged unless a future task explicitly updates the evidence map. In particular, "Problem N" labels reflect development provenance and should not be interpreted as public-facing problem statements.
