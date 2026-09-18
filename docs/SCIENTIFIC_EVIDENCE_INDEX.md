# LAFC-Evict Scientific Evidence Index

> **Updated 2026-09-18** for the public v1.0 repository state. Prefer
> `analysis/README.md` for the public analysis navigation layer and
> `docs/PE_CLAIM_EVIDENCE_LEDGER.md` for exact manuscript-ready values.

This index maps each current scientific question to the repository artifact that
supports it. It is a navigation aid; the frozen reports remain the source of
exact numbers.

| Question / area | Evidence artifact | Branch / commit | Status | Key conclusion | Next action |
|---|---|---|---|---|---|
| Target discriminativeness | `analysis/sigmod_target_discriminativeness_20260913/` | `analysis/sigmod-target-discriminativeness-20260913` / `76d562f` | Frozen evidence | `B = CONDITIONALLY DISCRIMINATIVE`; labels are highly tie-dominated overall, but MetaCDN/Twemcache cap32 H16 are substantially more discriminative; wiki2018 is fully degenerate. | Integrate honestly into the journal manuscript and reviewer response. |
| Pairwise provenance | `analysis/pairwise_provenance_repair_20260913/` and `analysis/pairwise_provenance_repair_20260913/artifacts/pairwise_sample_regenerated_canonical.parquet` | `analysis/sigmod-target-discriminativeness-20260913` / `76d562f`, durable artifact added on `polish/final-handoff-20260914` | Frozen / durable | Historical shipped pairwise sample is noncanonical; regenerated canonical sample has balanced direction counts and SHA256 `1d770c6999ac999673b46805a6ca173e24b116793b35405d2d211cae7b9eda02`; storage mode `TRACKED_IN_GIT`. | Keep the historical-vs-canonical distinction explicit; do not promote the analysis sample into a public release without a separate release decision. |
| Predictor feature issue | Target audit and pairwise repair reports | `76d562f` | Documented unresolved issue | `candidate_is_predictor_victim == candidate_is_lru_victim` across audited canonical data; related predictor fields include constants/placeholders. | Avoid unsupported predictor-field claims; fix upstream generation only in a separate authorized task. |
| Closed-loop pilot | `analysis/closed_loop_pilot_20260913/` | `experiment/closed-loop-pilot-20260913` / `983d7d0` | Frozen evidence | `B = MIXED`; LRU/random/MRU offline H=16 ordering agrees with closed-loop ordering on MetaCDN and Twemcache cap32; learned policy beats random/SIEVE but loses to LRU on Twemcache; MetaCDN learned policy blocked. | Use as feasibility evidence and retain exact split caveats. |
| Production closed-loop design | `analysis/closed_loop_production_design_20260913/` | `experiment/closed-loop-production-design-20260913` / `adc7c64` | Designed, not run | Tier 1 covers five families, capacities 32 and 128, LRU/MRU/random/SIEVE, random seeds 0..19; Tier 2 is narrow and approval-gated. | Run and validate Tier 1 only after design review. |
| Performance Evaluation manuscript | `paper/performance_evaluation/` and `paper/performance_evaluation/LAFC-Evict-Performance-Evaluation.pdf` | `master` / `d569ed7` | Integrated final submission package | Canonical 53-page manuscript PDF is tracked; submission state is recorded in `docs/PERFORMANCE_EVALUATION_FINAL_SUBMISSION_STATE.md`. | Do not modify manuscript science during repository-polish work. |
| Public release state | `dataset_card/`, `publication/`, `docs/LAFC_EVICT_PUBLICATION_STATE.md` | `master` / `d569ed7` | Current public status | v1.0 is the full five-family Hugging Face release; v0.3 remains the older Wiki2018-only HF-main/AWS release; Zenodo remains v0.2 DOI-backed only. | Keep v1.0/v0.3/v0.2 host distinctions prominent in all public docs. |
| Continuation-policy sensitivity | `analysis/continuation_policy_sensitivity_full_20260914/`; `analysis/continuation_policy_mru_population_census_20260914/validated/20260914T042528Z_1a29e773a113/` | `experiment/continuation-sensitivity-full-20260914` / `484417c`; `analysis/continuation-mru-census-validation-20260915` / `95e3a41` | Validated | Sampled MRU/random at capacities 32/128 and full-population MRU at capacities 32/64/128/256 classify ROBUST under the pre-registered Set-C criterion. | Integrate with exact scope; do not imply population random or arbitrary-policy validation. |
| Related-work/citation state | `paper/sigmod2027/latex/refs.bib`, related-work notes, manuscript branches | Multiple historical branches | Incomplete | Several references are present but need metadata checks; Cache-Coliseum, Learning Caching Policies with Subsampling, DAgger, Park, and QD-LP are high-priority gaps. | Verify against authoritative sources before editing bibliography metadata. |

| Tier-1 closed-loop production evaluation (NEW) | `analysis/closed_loop_tier1_evidence_20260914/` | `experiment/closed-loop-tier1-harness-20260913` / `8a4cd32` | Validated (14/14 gates, 230/230 complete) | 5 families x 2 capacities x 4 policies x 20 seeds; LRU best in 9/10 cells, MetaKV/cap128 is the sole SIEVE-beats-LRU exception. | Use `PE_CLAIM_EVIDENCE_LEDGER.md` C1-C9 for exact manuscript values. |
| Offline<->closed-loop linkage (NEW) | `analysis/closed_loop_offline_linkage_20260914/` | `analysis/tier1-offline-closed-loop-linkage-20260914` / `c5c8422` | Validated, dual code-path checked | RQ-CL1-CL4 answered; 8/9 non-degenerate cells concordant at H=16; H=16 best-aligned horizon; two named exceptions. | Integrate into manuscript per restructuring plan. |
| Mechanistic workload analysis (NEW) | `analysis/closed_loop_mechanistic_analysis_20260914/` | `analysis/closed-loop-mechanisms-20260914` / `412c47f` | Validated, trace-only | Explains cloudphysics/cap32 (near-zero-signal) and characterizes but does not fully resolve MetaKV/cap128; wiki2018 degeneracy causally established. | Cite mechanism classifications exactly (DIRECTLY_SUPPORTED vs PLAUSIBLE_BUT_NOT_ESTABLISHED). |
| Continuation-policy sensitivity, full sampled study (NEW) | `analysis/continuation_policy_sensitivity_full_20260914/` | `experiment/continuation-sensitivity-full-20260914` / `484417c` | Validated (`FULL_EXPERIMENT_VALID: true`) | MRU and mean-random continuation both ROBUST at capacities 32/128, Set C n=6597; median Jaccard 1.0 both; see ledger C10 for full nuance. | Extend, do not replace, with population census once validated. |
| Full-population MRU continuation census (NEW) | `analysis/continuation_policy_mru_population_census_20260914/validated/20260914T042528Z_1a29e773a113/` | `analysis/continuation-mru-census-validation-20260915` / `95e3a41`, RUN_ID `20260914T042528Z_1a29e773a113` | Validated (`FULL_CENSUS_VALID: true`; 30/30 gates; independent recheck PASS) | Population MRU is ROBUST: Set-C n=764,282 decision-horizon units, mean Jaccard 0.998459, median 1.0, mean CCR 0.000638, still-optimal fraction 0.999396. | Use as population-MRU evidence only; keep random sampled-only. |

## Current Hypothesis Summary

| Hypothesis | Current state |
|---|---|
| H_TARGET | CONDITIONALLY SUPPORTED |
| H_OFFLINE_CLOSED_LOOP | SUPPORTED IN PILOT ONLY |
| H_LEARNED_POLICY | NOT SUPPORTED AS SUPERIOR TO LRU |
| H_WIKI | NOT SUPPORTED AS A DISCRIMINATIVE SUPERVISED TARGET |
| H_CONTINUATION | ROBUST WITHIN EVALUATED SCOPE |
| H_PRACTICAL_USE | PARTIALLY SUPPORTED AND STRENGTHENED BY PILOT |
| H_PAIRWISE | OLD SHIPPED SAMPLE NOT CANONICAL |
