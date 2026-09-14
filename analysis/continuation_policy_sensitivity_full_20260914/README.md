# Continuation-Policy Sensitivity: Full Pre-Registered Experiment

The definitive execution of the design frozen in
`analysis/continuation_policy_sensitivity_design_20260914/` and validated
by the 80-decision pilot in
`analysis/continuation_policy_sensitivity_pilot_20260914/`.

## Duplication audit

A fresh search (git grep across every branch of both repositories, plus
inspection of on-disk untracked artifacts) found no full-scale (5,000+
decision) continuation-sensitivity run anywhere -- only the design
documents themselves mention "5,000 decisions", as a plan, never an
executed run. **Classification: NOT_PREVIOUSLY_RUN.**

## Implementation

This directory imports `pilot_lib.py` and `metrics.py` **unchanged** from
the already-validated pilot
(`experiment/continuation-sensitivity-pilot-20260914` @ `3b3b6d7`, primary
repo) rather than reimplementing them -- the same code that passed
52,480/52,480 LRU-equivalence comparisons and 23/23 pilot validity gates.
The secondary repository's implementation
(`experiment/continuation-sensitivity-pilot-20260914` @ `9537afa`) required
**no additional modification** -- MRU/random continuation support was
already complete and validated by the pilot.

## Sampling (frozen before any alternative-continuation result)

- **Primary sample**: 5,000 decisions = 500 per (family, capacity) stratum
  across all 5 families x 2 capacities, stratified proportionally by
  baseline-LRU all-tied/discriminative status at H=16 (the design's primary
  stratification horizon), drawn from a 1,000-decision-per-stratum random
  subsample pool (a documented, pragmatic population-approximation choice,
  same rationale as the pilot's 500-pool -- see `PRIMARY_MANIFEST.json`).
- **Diagnostic oversample**: 500 decisions = 100 per family, drawn from the
  highest-regret-magnitude decile (pooled across both capacities' subsample
  pools), per family -- reported **only** separately, never pooled into
  primary population statements.
- Both manifests record the exact decision IDs, sampling seed (`20260914`),
  baseline-LRU information used for selection, and their own content SHA256
  -- committed and pushed **before** any MRU/random continuation value was
  computed.
- Any overlap between the two samples is identified and recorded explicitly
  in both manifests (`overlap_with_diagnostic_sample` /
  `overlap_with_primary_sample`).

## Execution

`scripts/run_full_experiment.py` computes LRU (baseline), MRU
(deterministic), and random (10 CRN-seeded) continuation losses for every
candidate at every one of the 5,500 frozen decisions, at all 3 horizons
{4,8,16}. Raw candidate-level rows are appended to
`outputs/<RUN_ID>/candidate_results.jsonl` (large, ~1GB, **never committed
to git** -- referenced by exact path/size/SHA256 instead). Compact
decision-level tie-aware metrics are written to
`outputs/<RUN_ID>/decision_metrics.csv` (small, committed).

## Validity

Before launch: a pre-launch duplication recheck, and a blocking
candidate-by-candidate LRU-equivalence recheck covering **every** frozen
decision at **every** horizon actually used (not a subsample) --
`LRU_EQUIVALENCE_MISMATCHES` must be exactly 0 or the run does not proceed.
After completion: 20+ programmatic validity gates (`validate_full.py`),
never marking `FULL_EXPERIMENT_VALID: true` unless every one passes.

## Analysis

`scripts/analyze_full.py` computes the four mandatory stratified sets
(A: all decisions; B: excluding both-tied; C: discriminative under LRU;
D: discriminative under either), by-family/capacity/horizon breakdowns
(on Set C), a decision-level cluster bootstrap (never candidate-row or
seed-level), and applies the pre-registered ROBUST/CONDITIONALLY_ROBUST/
SENSITIVE/INCONCLUSIVE classification verbatim from `DESIGN.md` Section 3
-- not re-derived or adjusted after seeing results.
`scripts/independent_recheck.py` recomputes the headline median-Jaccard and
mean-cross-continuation-regret numbers via a fully separate pandas-based
code path reading the raw JSONL directly, and requires exact numerical
agreement (tolerance 1e-9) with `analyze_full.py`'s own output.

## What is committed vs. kept local-only

Committed: both frozen manifests, all scripts/tests, `decision_metrics.csv`
(compact), `scientific_analysis.json`, `validity_gates.json`,
`provenance.json`, `summary.json`, `run_manifest.json`, this README.
**Not committed**: `candidate_results.jsonl` (~1GB raw output) -- kept
immutable in the local run directory, referenced by exact path, byte size,
and SHA256 in `provenance.json`/`run_manifest.json`.
