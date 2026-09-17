# PE Claim <-> Evidence Ledger

> **Updated 2026-09-14 (follow-on manuscript-rewrite pass).** C5 and C8
> amended with additional precision found while writing
> `sections/08b_closed_loop.tex`, `08c_linkage.tex`, and
> `08e_continuation.tex`; C13-C15 added below. No prior claim was
> weakened without cause; two (C5, C8) were corrected because the
> original entries, while not wrong, were less precise than the
> manuscript prose ended up needing, and one imprecise generalization
> (a claimed "LRU > SIEVE > random > MRU" ranking) was caught and removed
> before it reached the built PDF.

Status: NOT_PRESENT prior to this task (repository-wide search found no
prior claim/evidence ledger for the Performance Evaluation manuscript).
This is a new document built entirely from already-validated, already-frozen
evidence on `experiment/continuation-sensitivity-full-20260914` @
`484417c326f3c1af8bd48eb85168fa5f6ae93801` (the branch this worktree/branch
`manuscript/pe-evidence-restructure-20260914` was created from). No census
data is used anywhere in this ledger.

Every row cites an exact artifact path and, where the artifact is large, an
exact key/column inside it. Prose in the manuscript should trace back to a
row here rather than restating numbers from memory.

## Legend

- **SUPPORTED**: directly backed by a validated, gate-passed artifact.
- **PARTIALLY_SUPPORTED**: backed, but only under a stated scope (n small,
  exploratory, one workload, etc.) that must be carried into the claim.
- **LIMITATION**: not a positive claim; a boundary condition to disclose.
- **NOT_SUPPORTED**: no current evidence; do not write this claim.
- **Census-dependent**: whether `experiment/continuation-mru-population-census-20260914`
  and its validated evidence branch `analysis/continuation-mru-census-validation-20260915`
  strengthen, weaken, or extend this claim. As of commit `95e3a41`, the
  MRU population census is valid and usable; population random remains
  untested.

---

### C1. The target is not uniformly discriminative; aggregate degeneracy is substantial

- Status: SUPPORTED
- Evidence: `analysis/sigmod_target_discriminativeness_20260913/`
- Source: frozen REPORT (see also `docs/CURRENT_PROJECT_STATUS_AND_HANDOFF.md` Section 6, values re-verified unchanged in this branch)
- Values: candidate rows `277,995,072`; decisions `2,363,286`; decision-weighted random-optimal probability `0.9912418754543462`; decision-weighted random mean regret `0.008826200441884731`; all-tied fraction `0.676601985540472`; unique-winner fraction `0.0`; classification `B = CONDITIONALLY DISCRIMINATIVE`.
- Scope: all 5 families, all capacities {32,64,128,256}, all horizons {4,8,16}, aggregated.
- Caveats: aggregate all-tied fraction of ~68% must not be read as "the labels are useless" — see C2/C3 for the per-family breakdown that shows where the remaining ~32% carries real signal.
- Census-dependent: NO (this is the full canonical SIGMOD-scale target audit, already population-scale; the census concerns continuation-policy sensitivity, not target discriminativeness).

### C2. Discriminativeness varies strongly by workload/capacity/horizon

- Status: SUPPORTED
- Evidence: `analysis/sigmod_target_discriminativeness_20260913/` (per-family breakdown) and `analysis/closed_loop_mechanistic_analysis_20260914/SCIENTIFIC_SUMMARY.md` (trace-characteristic cross-check)
- Values: all-tied fraction by family/capacity at H=16 — cloudphysics 0.87 (cap32) / 0.66 (cap128); metakv 0.87 / 0.86; twemcache 0.24 (cap32) / 0.10 (cap128); metacdn 0.012 / 0.0085; wiki2018 1.0 / 1.0.
- Source: `analysis/closed_loop_offline_linkage_20260914/SCIENTIFIC_SUMMARY.md`, RQ-CL3 table.
- Scope: 5 families x 2 capacities (32, 128) x H=16; Tier-1 scope only (64/256 not covered by closed-loop linkage).
- Census-dependent: NO for the discriminativeness numbers themselves (already population-scale); the census could eventually extend the *continuation-sensitivity* dimension of this table to capacities 64/256, not discriminativeness itself.

### C3. wiki2018 is a genuine negative/control regime, not a benchmark failure

- Status: SUPPORTED
- Evidence: `analysis/closed_loop_mechanistic_analysis_20260914/SCIENTIFIC_SUMMARY.md`, Q9; `analysis/closed_loop_tier1_evidence_20260914/run/*/summary.csv` (wiki2018 rows)
- Values: `n_reuse_events = 0` over 4096 scored-window requests (`unique_over_request_ratio = 1.0`); Tier-1 closed-loop miss_ratio = 1.0 for every policy (LRU/MRU/SIEVE/random, 20 seeds) at both capacities 32 and 128, std = 0 exactly.
- Interpretation: zero reuse events makes miss_ratio=1.0 a mathematical certainty, not a statistical tendency — classified `CAUSALLY_ESTABLISHED` in the mechanistic analysis (deductive, not correlational).
- Census-dependent: NO.

### C4. Stronger capacity-scale locality corresponds to stronger target discriminativeness and larger closed-loop policy separation

- Status: PARTIALLY_SUPPORTED (exploratory, small-n)
- Evidence: `analysis/closed_loop_mechanistic_analysis_20260914/SCIENTIFIC_SUMMARY.md`, Q10; `analysis/closed_loop_offline_linkage_20260914/SCIENTIFIC_SUMMARY.md`, RQ-CL3 exploratory correlation
- Values: trace-derived LRU hit rate vs. offline discriminativeness (1 - all-tied fraction): r = -0.83 (pooled n=10; -0.83/-0.83 per-capacity n=5). Trace-derived LRU hit rate vs. closed-loop |MRU-LRU| separation: r = 0.90 (pooled), 0.91/0.89 per-capacity. Offline discriminativeness vs. closed-loop |MRU-LRU| separation directly: r = 0.968, Spearman rho = 0.915, Kendall tau-b = 0.773 (n=10, H=16).
- Scope: n=10 (5 families x 2 capacities), H=16 only for the discriminativeness-vs-separation correlation; trace metrics do not vary by horizon.
- Caveats: exploratory, not pre-registered; small n; explicitly not a "large-sample-validated law" per the source report.
- Census-dependent: NO (would require capacity 64/256 trace-locality analysis, out of current census scope, which is continuation-policy sensitivity not trace locality).

### C5. Offline policy ordering generally tracks closed-loop ordering in informative regimes

- Status: PARTIALLY_SUPPORTED
- Evidence: `analysis/closed_loop_offline_linkage_20260914/SCIENTIFIC_SUMMARY.md`, RQ-CL1
- Values: pairwise concordance (offline regret-gap sign vs. closed-loop miss-ratio-gap sign), MRU-vs-LRU and random-vs-LRU pairs, SIEVE excluded (no offline counterpart): combined 13/20 concordant, 3/20 discordant, 4/20 both-tied (wiki2018), identical at H=4/H=8/H=16. **Per-pair split (added 2026-09-14, used in `sections/08c_linkage.tex`)**: MRU-vs-LRU alone = 7/10 concordant, 1/10 discordant (cloudphysics/cap32 only), 2/10 tied (wiki2018); random-vs-LRU alone = 6/10 concordant, 2/10 discordant (cloudphysics/cap32 AND metakv/cap128), 2/10 tied. Without wiki2018: 13/16 (81%) at H=16. Per-cell 3-item Kendall tau-b: 6/8 non-degenerate cells at exactly +1.0, cloudphysics/cap32 at -1.0, metakv/cap128 at +0.33.
- Scope: 2 comparable pairs (MRU-vs-LRU, random-vs-LRU) x 5 families x 2 capacities = 20 comparisons at each of H={4,8,16}; SIEVE has no offline counterpart and is excluded from this specific claim.
- Caveats: the two discordant cells (C7, C8 below) must always be named, not glossed over.
- Census-dependent: NO (Tier-1/linkage already complete and validated at capacities 32/128).

### C6. Offline regret-gap strength predicts closed-loop miss-gap magnitude (RQ-CL2)

- Status: PARTIALLY_SUPPORTED (real effect size, very small n)
- Evidence: `analysis/closed_loop_offline_linkage_20260914/SCIENTIFIC_SUMMARY.md`, RQ-CL2
- Values (H=16, primary): MRU-vs-LRU r=0.835 / rho=0.915 / tau=0.773; random-vs-LRU r=0.755 / rho=0.829 / tau=0.591. H=4: r=0.746/0.605; H=8: r=0.783/0.671 (MRU/random respectively).
- Scope: n=10 (family x capacity cells) per horizon; explicitly "p-values were computed but are explicitly not treated as evidence of significance."
- Census-dependent: NO.

### C7. CloudPhysics/cap32's apparent discordance is largely a near-zero-signal regime, not a real contradiction

- Status: SUPPORTED
- Evidence: `analysis/closed_loop_mechanistic_analysis_20260914/SCIENTIFIC_SUMMARY.md`, Q1
- Values: only 17.5% of window requests are reuses at all; of those, only 9.4% fall within stack distance 32. Trace-only predicted LRU hit rate `0.175 x 0.094 = 1.6%` at cap32 exactly reproduces the observed Tier-1 LRU hit rate (134/8192 = 1.64%). Offline H=16 regret gaps there: MRU-LRU = -0.00266, random-LRU = -0.00066 (both near zero on an absolute scale where metacdn's MRU-LRU gap is >100x larger).
- Classification: `DIRECTLY_OBSERVED` per the source report.
- Census-dependent: NO.

### C8. MetaKV/cap128 remains a real but bounded exception

- Status: SUPPORTED as a documented exception; NOT_SUPPORTED as an explained mechanism
- Evidence: `analysis/closed_loop_mechanistic_analysis_20260914/SCIENTIFIC_SUMMARY.md`, Q2-Q7; `analysis/closed_loop_offline_linkage_20260914/SCIENTIFIC_SUMMARY.md`, RQ-CL1/RQ-CL3
- Values: MetaKV/cap128 is the only Tier-1 cell (of 10) where a policy other than LRU wins closed-loop outright (SIEVE 0.6982 vs LRU 0.7290, -4.22% relative). **Correction (2026-09-14): random-mean ALSO beats LRU at this cell** (relative gap -2.07%, i.e. random miss ratio ~0.7137), so LRU is actually in *third* place at metakv/cap128 (SIEVE 1st, random 2nd, LRU 3rd, MRU worst) — not merely "one other policy wins," two do. An earlier draft of this entry and of `sections/08b_closed_loop.tex` stated only the SIEVE exception and a universal "LRU > SIEVE > random > MRU" ranking claim; both were corrected before the manuscript build because they were contradicted by this same summary.csv data (SIEVE loses to random at twemcache both capacities and at cloudphysics both capacities, so no fixed SIEVE-vs-random order exists). Offline random-LRU regret gap = +0.00129 (random slightly worse) vs. closed-loop miss-ratio gap = -0.0151 (random better) — a sign disagreement. MetaKV's all-tied fraction (0.856-0.867) is comparable to cloudphysics's, ruling out "weak offline signal" as the sole explanation.
- Caveats: the mechanistic analysis identifies two *plausible* contributing structural properties (cold-start/no-warmup scoring window; a reuse-distance "boundary zone" at 0.574->0.600 fraction between distance 32 and 128) but explicitly classifies causation as `PLAUSIBLE_BUT_NOT_ESTABLISHED` (Q5) and states directly that existing data "cannot isolate which one... caused the reversal" (Q6). Do not claim this is explained; claim it is characterized.
- Census-dependent: NO (structural/trace argument, independent of continuation-policy choice).

### C9. H=16 gives the strongest, though modest, offline<->closed-loop alignment among H={4,8,16}

- Status: SUPPORTED
- Evidence: `analysis/closed_loop_offline_linkage_20260914/SCIENTIFIC_SUMMARY.md`, RQ-CL4
- Values: H=16 wins or ties on every magnitude-sensitive statistic (Pearson/Spearman/Kendall, both pairs) across every sensitivity slice tested; coarse concordant/discordant counts are identical (13/3/4-tied) at every horizon — horizon changes correlation *magnitude*, not which cells agree in *sign*.
- Caveats: differences between horizons are modest in absolute terms (e.g. r=0.746 to 0.835 for MRU-vs-LRU, H=4 to H=16); n=8-10 per horizon.
- Census-dependent: NO.

### C10. Continuation-policy sensitivity: sampled MRU/random at capacities 32/128 and population MRU at capacities 32/64/128/256 classify ROBUST

- Status: SUPPORTED, at the stated scope only
- Sampled-study evidence: `analysis/continuation_policy_sensitivity_full_20260914/outputs/20260914T040333Z_1f66342be435/scientific_analysis.json` (`ROBUSTNESS_CLASSIFICATION`, `PRIMARY_ANALYSIS`), `validity_gates.json`, `provenance.json`
- Validated HEAD: `experiment/continuation-sensitivity-full-20260914` @ `484417c326f3c1af8bd48eb85168fa5f6ae93801` (RUN_ID `20260914T040333Z_1f66342be435`; 16,500 decision-horizon pairs; 0 failed; prelaunch LRU-equivalence gate: 1,271,616 comparisons, 0 mismatches; `FULL_EXPERIMENT_VALID: true`).
- Sample: 5,000 primary decisions (500 per family x capacity stratum, stratified by baseline-LRU discriminative status at H=16) + 500 diagnostic decisions (high-regret oversample, reported separately, never pooled into primary statements).
- Values, Set C (discriminative-under-LRU, n=6597 decisions, primary sample only):
  - **MRU continuation**: cap32 (n=3021) median Jaccard 1.0, mean Jaccard 0.9958, mean cross-continuation regret (CCR) 0.00183, strict reversal fraction 2.74e-05; cap128 (n=3576) median Jaccard 1.0, mean Jaccard 0.99990, mean CCR 6.52e-05, strict reversal fraction 0.0 exactly. Bootstrap (2000 resamples) mean-CCR 95% CI [0.00073, 0.00103].
  - **Mean-random continuation** (10 CRN seeds): cap32 median Jaccard 1.0, mean Jaccard 0.7251 (lower than MRU's mean, though median is unaffected), mean CCR 0.0463, strict reversal fraction 1.03e-03; cap128 median Jaccard 1.0, mean Jaccard 0.8522, mean CCR 0.0197, strict reversal fraction 1.51e-06.
  - Classification: both `mru` and `random_mean` -> `ROBUST` at both capacities per the pre-registered DESIGN.md Section 3 rule, applied verbatim (not re-derived after seeing results).
- Population-census evidence: `analysis/continuation_policy_mru_population_census_20260914/validated/20260914T042528Z_1a29e773a113/VALIDATION_REPORT.json`, `validity_gates.json`, `summary_overall.json`, `summary_by_capacity.csv`, `summary_by_horizon.csv`, `summary_by_family_capacity_horizon.csv`, `sampled_vs_population_mru.csv`, `figure5_mru_continuation_data.csv`, `EVIDENCE_MANIFEST.json`.
- Population validation: `analysis/continuation-mru-census-validation-20260915` @ `95e3a41`; RUN_ID `20260914T042528Z_1a29e773a113`; 60/60 chunks, 2,363,286/2,363,286 records, 0 duplicate/missing/extra keys, 30/30 gates PASS, independent recheck PASS, `FULL_CENSUS_VALID: true`, raw output unmodified.
- Population MRU values:
  - Overall: mean Jaccard 0.9994054593, median 1.0, Jaccard=1 fraction 0.9869262544, strict reversal count 4,646, strict reversal fraction 1.874e-07, mean CCR 0.000304471, median CCR 0.0, p95 CCR 0.0, max CCR 0.193548, nonzero-regret fraction 0.0106635422, still-optimal fraction 0.9997084155, both-tied fraction 0.6730687695.
  - Set C (discriminative under LRU): n=764,282 decision-horizon units; mean Jaccard 0.9984587309, median 1.0, strict reversal fraction 5.378e-07, mean CCR 0.000638213, still-optimal fraction 0.9993955215.
  - Set C by capacity: c32 J=0.9948091745 / CCR=0.002066944; c64 J=0.9988592298 / CCR=0.000529716; c128 J=0.9998063823 / CCR=0.000096333; c256 J=0.9999591646 / CCR=0.000019153.
  - Worst Set-C cell: cloudphysics/c32/H16, mean Jaccard 0.9804326227, median 1.0, mean CCR 0.003899105, strict reversal fraction 3.453e-05.
- Caveats (must appear in every manuscript sentence using this result): (a) sampled MRU and mean-random evidence covers capacities 32 and 128 only; (b) full-population evidence covers MRU only, not random; (c) no result here proves robustness to every possible stateful deployed continuation policy; (d) wiki2018 is a degenerate negative control and must not be used to inflate the robustness story without Set-C/informative-stratum reporting.
- Census-dependent: RESOLVED for population MRU; still not resolved for population random or arbitrary continuation policies.

### C11. LAFC-Evict complements rather than replaces closed-loop evaluation

- Status: SUPPORTED (framing claim, backed by the full evidence chain)
- Evidence: synthesis of C1-C10; explicit statement already present in `docs/CURRENT_PROJECT_STATUS_AND_HANDOFF.md` Section 2 and reaffirmed by every analysis task's own scope boundary (none of Tier-1/linkage/mechanistic/continuation substitute closed-loop replay for the offline labels).
- Census-dependent: NO.

### C12. The abstraction remains unit-object/count-capacity, unconditional admission, finite horizon

- Status: LIMITATION (scope-defining, not a positive claim)
- Evidence: dataset construction as documented across `analysis/sigmod_target_discriminativeness_20260913/`, `analysis/closed_loop_production_design_20260913/`, and the closed-loop harness (`experiment/closed-loop-tier1-harness-20260913`) — all operate on object-count capacity with unconditional admission and unit-sized objects; no byte/latency/dirty-write cost model exists anywhere in the evidence chain.
- Census-dependent: NO.

### C13. MRU is worst in every non-degenerate closed-loop cell; no fixed SIEVE-vs-random order exists

- Status: SUPPORTED (added 2026-09-14, `sections/08b_closed_loop.tex`)
- Evidence: `analysis/closed_loop_tier1_evidence_20260914/run/20260914T023445Z_8a4cd32402a1/summary.csv`, `relative_miss_diff_vs_lru` column, all 8 non-degenerate (family, capacity) cells.
- Values: MRU has the largest positive relative-miss-ratio gap vs. LRU in all 8 non-degenerate cells (range +1.65% to +54.93%). SIEVE beats random-mean at metacdn (both capacities) and metakv/cap32; random-mean beats SIEVE at twemcache (both capacities), cloudphysics (both capacities), and metakv/cap128 — i.e. neither policy is consistently second- or third-best.
- Caveat: this entry exists specifically because an earlier draft claimed a universal "LRU > SIEVE > random > MRU" ordering, which the same source data contradicts; kept here as a record of the correction, not just the finding.
- Census-dependent: NO.

### C14. Continuation-robustness erodes with horizon for random continuation, though it stays above the ROBUST threshold

- Status: SUPPORTED, at the stated scope only
- Evidence: `analysis/continuation_policy_sensitivity_full_20260914/outputs/20260914T040333Z_1f66342be435/scientific_analysis.json`, `PRIMARY_ANALYSIS.{mru,random_mean}.by_horizon_setC`.
- Values (Set C, both capacities pooled, n=2199 decisions per horizon): MRU median Jaccard is 1.000 at H=4, H=8, and H=16 (mean Jaccard 0.9996/0.9987/0.9957). Random-mean median Jaccard is 1.000 at H=4 and H=8 but **drops to 0.881 at H=16** (mean Jaccard 0.9033/0.8047/0.6740); mean cross-continuation regret for random rises from 0.0114 (H=4) to 0.0570 (H=16); strict reversal fraction rises from 0.0 (H=4) to 1.41e-04 (H=16).
- Caveat: 0.881 remains above the pre-registered ROBUST threshold (median Jaccard >= 0.8), so the overall ROBUST classification (C10) is not contradicted — but reporting only the by-capacity pooled numbers (median exactly 1.0 at both capacities) would hide this horizon-dependent erosion. Both breakdowns must be reported together, as done in `tables/table_linkage_continuation_summary.tex`.
- Census-dependent: only insofar as population-scale validation may later confirm or extend this same by-horizon pattern; the sampled-study finding itself is not census-dependent.

### C15. Capacity-scale reuse is a single trace statistic that predicts both offline discriminativeness and closed-loop separation

- Status: PARTIALLY_SUPPORTED (exploratory, n=10) — restates C4 with the exact mechanistic-analysis correlation values used in `sections/08d_mechanistic.tex` and `sections/08f_practical_implications.tex`
- Evidence: `analysis/closed_loop_mechanistic_analysis_20260914/outputs/correlation_summary.csv`, `mechanism_comparison.csv`.
- Values: trace-derived LRU hit rate vs. offline all-tied fraction (H=16): pooled r=-0.832 (n=10), cap32 r=-0.829 (n=5), cap128 r=-0.834 (n=5). vs. closed-loop |MRU-LRU| miss-ratio gap: pooled r=0.899 (n=10), cap32 r=0.909 (n=5), cap128 r=0.893 (n=5).
- Census-dependent: NO.

### C16. A frozen offline-trained learned selector evaluated in true closed-loop is generally not competitive with heuristic baselines

- Status: SUPPORTED (confirmatory, frozen-model evaluation under pre-registered protocol)
- Evidence: `analysis/pe_publication_learned_closed_loop_20260916/PE_LEARNED_CLOSED_LOOP_FINAL_REPORT.md` (campaign `pe_publication_learned_closed_loop_20260916`, 250 tasks total).
- Values:
  - **Overall macro miss ratio**: Learned `0.7629` vs. LRU `0.71175`, SIEVE `0.70965`, Random (seed mean) `0.72285`, LFU `0.78245`, MRU `0.84839` across all 10 cells.
  - **Excluding 2 degenerate wiki2018 cells**: Learned `0.7036` vs. LRU `0.6397`, SIEVE `0.6371`, Random `0.6536` on the remaining 8 cells.
  - **Win/tie/loss counts** (vs. LRU/SIEVE/random): 1 win, 2 ties (the degenerate wiki2018 cells), 7 losses.
  - **Single learned win**: metakv/cap128 (learned `0.76497` vs. LRU `0.76582`, SIEVE `0.76656`, random-mean `0.76685`).
  - **twemcache** shows largest gap: learned worse by ~0.15.
- Interpretation: Good offline predictive structure does not translate automatically to closed-loop improvement. This is likely due to trajectory/state shift, action-underdetermined labels, or continuation-policy mismatch.
- Census-dependent: NO.

## Cross-cutting caveats that apply to nearly every claim above

- Labels are finite-horizon; canonical continuation is LRU (see C10 for the sensitivity result on that assumption).
- The target can be highly tied; unique winners are absent in the audited canonical target (unique-winner fraction 0.0, C1).
- MetaCDN closed-loop evidence throughout Tier-1/linkage/mechanistic analysis is **validation-window** evidence, not a temporally held-out test window (Twemcache is test-window).
- MetaKV has a first-window/cold-start caveat (`evictions = misses - capacity` identity; only family whose scored window starts at request 0) — see C8.
- Continuation validation (C10) covers sampled MRU/random at capacities 32/128 and full-population MRU at capacities 32/64/128/256.
- The historical full-release generator commit provenance remains incomplete/unknown (carried over from prior handoff documentation; not re-investigated in this task since it is orthogonal to the manuscript-evidence questions above).
- Predictor-field issue: `candidate_is_predictor_victim == candidate_is_lru_victim` throughout the audited canonical data; predictor/bucket/confidence fields include constant or placeholder values. Any manuscript claim involving predictor fields must be avoided or explicitly caveated (carried over from the prior handoff, unchanged, not re-investigated in this task).

## Not-yet-claimed items intentionally excluded from this ledger

- Any full-population random-continuation number.
- Any claim of continuation-independence for arbitrary deployed policies.
