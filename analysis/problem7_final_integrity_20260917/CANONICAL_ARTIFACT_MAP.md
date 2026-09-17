# Problem 7 Phase 3: canonical artifact map

Each headline manuscript number's preferred single source of truth.

## Problem 1 (public release / dataset scale)
- `analysis/pairwise_provenance_repair_20260913/` -- pairwise sample provenance.
- External: Hugging Face `SoroushVahidi/lafc-evict` v1.0 revision (live-checked
  this pass via `hub_repo_details`) -- 277,995,072 candidate rows, 2,363,286
  decisions, 1,000,000 pairwise-sample rows. This is the release-level
  cross-check; `tables/table_dataset_scale.tex` and
  `tables/table_regret_tie_stats.tex` restate the same numbers in-repo.

## Problem 2 (seven-feature clean schema)
- `analysis/feature_provenance_repair_20260917/` -- feature provenance repair,
  referenced by `sections/07_tasks_baselines.tex`'s feature-degeneracy
  paragraph.

## Problem 3 (informativeness stratification)
- `analysis/problem3_informativeness_20260917/outputs/
  headline_random_optimal_decomposition.csv` -- the A/B/D mechanism-group
  decomposition (zero/large-optimal-set/material-regret-separation) cited in
  `sections/08_characterization.tex`'s "Interpretation" subsection.
- `analysis/problem3_informativeness_20260917/outputs/
  absolute_informativeness_decomposition.csv` -- the five-bin
  (zero/tiny/small/moderate/large) breakdown used for the zero-information
  fraction (67.66%).
- `analysis/sigmod_target_discriminativeness_20260913/` -- the pre-Problem-3
  discriminative/non-discriminative split this stratification refines.

## Problem 4 (matched long-horizon population)
- `analysis/problem4_matched_horizon_20260917/outputs/validation.json` --
  exact match to canonical H16 release + preserved non-twemcache H32/64/128
  values (`PASS`).
- `analysis/problem4_matched_horizon_20260917/outputs/
  matched_monotonicity_micro_summary.csv` -- the
  `adjacent_all_nondecreasing_fraction=1.0` monotonicity claim.
- `tables/table_matched_long_horizon_sensitivity.tex` -- the in-manuscript
  restatement (787,762 at every horizon).

## Problem 5 (expanded closed-loop comparators)
- `analysis/problem5_expanded_closed_loop_20260917/outputs/
  problem5_scientific_answers.json` -- LRU-best-of-4-vs-7 counts, per-cell
  exception list with relative gaps, and both policy-spread correlations
  (old4/all7).
- `analysis/problem5_expanded_closed_loop_20260917/IMPLEMENTATION_INVENTORY.md`
  -- libcachesim provenance/license decision.
- `analysis/closed_loop_tier1_evidence_20260914/` -- the original 4-policy
  Tier-1 evidence (`tables/table_tier1_closed_loop.tex`'s source).

## Continuation robustness (RQ4)
- `analysis/continuation_policy_sensitivity_full_20260914/` -- sampled
  MRU/random study (capacities 32/128).
- `analysis/continuation_policy_mru_population_census_20260914/` -- full-
  population MRU census (all capacities/horizons).

## Mechanistic analysis (RQ3 part 2)
- `analysis/closed_loop_mechanistic_analysis_20260914/outputs/
  mechanism_comparison.csv` -- the n=10 hit-rate/discriminativeness/
  closed-loop-gap correlation triple (`sections/08d_mechanistic.tex`).
  **New this pass:** `analysis/problem7_final_integrity_20260917/outputs/
  correlation_robustness_recheck.json` -- independent LOFO + exact
  family-permutation recomputation from the same CSV, added as the
  canonical source for the new robustness caveat in
  `sections/08d_mechanistic.tex`.

## Problem 6 (narrative rewrite)
- No new numbers; `analysis/problem6_narrative_readability_20260917/`
  documents the prose-only changes. Confirmed no numeric drift during this
  Problem-7 pass.

## Reproducibility / release
- `THIRD_PARTY_DATA.md`, `dataset_card/LICENSE_DATA.md`,
  `manifests/source_family_registry.yaml` -- per-family trace licensing.
- `git remote -v` (this repo) -- GitHub URL cross-check.
- Hugging Face `hub_repo_details` (live, external) -- v1.0 revision existence
  and scale cross-check.
