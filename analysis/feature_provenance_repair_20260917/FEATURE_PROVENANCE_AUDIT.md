# Feature Provenance Audit — 26 Candidate-Level Features

Date: 2026-09-17. Scope: forensic audit and repair design only for Problem 2
(candidate-level feature quality). Read-only against canonical data; no
candidate row values were altered; no public release touched.

## 1. Scope

The 26 `FEATURE_COLUMNS` in `src/lafc_evict_dataset/schema.py` (identical set
and order to `Augmented-caching`'s `EVICT_VALUE_V1_FEATURE_COLUMNS` in
`src/lafc/evict_value_features_v1.py`, and to the `feature_columns` list
stored inside every frozen model pickle inspected — see section 5). This is
the same 26-column set fed to the manuscript's `linear_score` regression
baseline (`scripts/sigmod2027/run_value_regression_baseline.py`) and to the
pairwise feature-difference logistic model.

## 2. Ground-truth profiling (independently measured, not inferred)

Profiled directly against
`release/lafc-evict-v0.1-open-current-contract-preserved/data/candidate_rows/**/*.parquet`
(the exact 277,995,072-row corpus underlying the manuscript's evaluated
benchmark; same source used for Problem 1's `v1.0` release) via DuckDB,
`COUNT(DISTINCT ...)`/`MIN`/`MAX`/null-count per column
(`scripts/profile_features.py`, 5.9s wall time). Raw output:
`artifacts/feature_profile_raw.json`. Full per-feature table:
`artifacts/feature_inventory.csv`.

**Result: exactly 18 of 26 features are globally constant (`COUNT(DISTINCT)=1`)
across all 277,995,072 rows, no nulls anywhere.**

| # | Feature | Distinct | Constant value |
|---|---|---:|---|
| 1 | `request_bucket` | 1 | 0.0 |
| 2 | `request_confidence` | 1 | 0.5 |
| 3 | `candidate_bucket` | 1 | 0.0 |
| 4 | `candidate_confidence` | 1 | 0.5 |
| 5 | `candidate_predictor_score` | 1 | 0.5 |
| 6 | `score_gap_to_predictor_best` | 1 | 0.0 |
| 7 | `bucket_gap_to_predictor_best` | 1 | 0.0 |
| 8 | `bucket_gap_to_lru_victim` | 1 | 0.0 |
| 9 | `confidence_gap_to_predictor_best` | 1 | 0.0 |
| 10 | `confidence_gap_to_lru_victim` | 1 | 0.0 |
| 11 | `cache_bucket_mean` | 1 | 0.0 |
| 12 | `cache_bucket_std` | 1 | 0.0 |
| 13 | `cache_bucket_min` | 1 | 0.0 |
| 14 | `cache_bucket_max` | 1 | 0.0 |
| 15 | `cache_unique_bucket_count` | 1 | 1.0 |
| 16 | `cache_confidence_mean` | 1 | 0.5 |
| 17 | `cache_confidence_std` | 1 | 0.0 |
| 18 | `predictor_lru_disagree` | 1 | 0.0 |

**One additional feature is a proven exact alias, not a constant:**
`candidate_is_predictor_victim` has 2 distinct values (0/1, matching
`candidate_is_lru_victim`'s own distribution) but is **bit-identical** to
`candidate_is_lru_victim` — a direct row-level equality scan found **0
mismatches out of 277,995,072 rows** (`artifacts/alias_leakage_checks.json`,
`predictor_victim_neq_lru_victim_count: 0`).

**The remaining 7 features are genuinely non-constant and independent:**
`candidate_recency_rank`, `candidate_age_norm`, `candidate_lru_score`,
`candidate_is_lru_victim`, `score_gap_to_lru_victim`,
`recent_candidate_request_rate`, `recent_candidate_hit_rate`.

18 + 1 + 7 = 26. This exactly matches the manuscript's stated 18/19/7
breakdown, now independently reproduced from the released data rather than
taken on faith.

`score_gap_to_lru_victim` was additionally verified to be an **exact
deterministic transform** of `candidate_lru_score`
(`score_gap_to_lru_victim = candidate_lru_score − MAX(candidate_lru_score)`
within the same `(trace_name, capacity, horizon, decision_id)` group; 0
mismatches / 277,995,072 rows). This is legitimate, standard within-decision
normalization (comparing a candidate's LRU recency against the best
candidate in the *same* decision, which is fully available at decision
time — not leakage), so it is kept as a valid feature, not deprecated.

## 3. Leakage check

None of the 7 valid features requires information unavailable at eviction
time: `candidate_recency_rank`/`candidate_age_norm`/`candidate_lru_score`/
`candidate_is_lru_victim`/`score_gap_to_lru_victim` are pure functions of
past-request recency order within the resident cache; `recent_candidate_*`
are rolling windows over already-elapsed request/hit history. `y_loss`/
`y_value` are confirmed absent from `FEATURE_COLUMNS` (not fed to any model
as input). A coarse equality scan against `y_loss` for six representative
features found only small, non-systematic overlap counts (order
10^4–10^6 out of 2.78×10^8 rows) consistent with incidental small-integer
collisions, not a copying relationship — expected, since `y_loss` is a
finite-horizon simulated miss count computed by rolling the trace *forward*
after eviction, structurally independent of any candidate-level feature
computed from *past* state. No split-identity or optimal-set-membership
leakage was found in any of the 26 columns' generator code (none of them
read `split`, `decision_id`, or the horizon rollout).

## 4. Root cause (code-proven, not inferred)

Traced into `Augmented-caching`
(`/home/soroush/projects/augmented-caching/repo`, branch
`chore/repository-polish`, commit `ceb3670` at time of audit) — the actual
codebase that generated this release's candidate rows (per
`release_manifest.json`'s `source_manifest` field pointing at
`evict_value_v1_wulver_heavy_r1`).

**The chain, each link independently verified by reading code, not by
inference from statistics:**

1. `src/lafc/evict_value_features_v1.py::compute_candidate_features_v1` takes
   `bucket_by_page`/`confidence_by_page` dicts as parameters and reads
   `.get(page, default)` (`default=0` for bucket, `default=0.5` for
   confidence) for every candidate/request/cache-aggregate feature.
2. `src/lafc/evict_value_wulver_v1.py` (the actual Wulver-scale generator;
   `src/lafc/evict_value_dataset_v1.py` has an equivalent smaller-scale
   sibling) populates these dicts with exactly one guard each:
   `if req.metadata.get("bucket") is not None: bucket_by_page[pid] = ...`
   (and the analogous line for confidence).
3. **`grep -rn "metadata\['bucket'\]\s*=\|metadata\['confidence'\]\s*=" src/lafc/`
   returns zero matches anywhere in the codebase.** Nothing ever writes
   these two metadata keys onto a `Request` object in the code path that
   produced this release. `req.metadata.get("bucket")` is therefore always
   `None`, `bucket_by_page`/`confidence_by_page` are permanently empty
   dicts, and every `.get(page, default)` call returns its hardcoded
   default for every row of every trace.
4. `src/lafc/learned_gate/features.py::compute_predictor_scores` has an
   explicit branch for this exact situation: `if len(uniq) == 1: return
   {p: 0.5 for p in candidates}` — fires on literally every decision, since
   every candidate's bucket is the same default `0`.
5. A working bucket-annotation function, `attach_perfect_buckets()` (`src/
   lafc/predictors/buckets.py`), **does exist** in the same codebase, but
   git history shows it predates `evict_value_wulver_v1.py`
   (`buckets.py`'s earliest commit is `7c7e45e`, "Add first-pass
   cross-policy comparison study outputs" — built for a *different*
   experiment, `atlas_v1` policy comparisons) and was **never imported or
   called** by either `evict_value_wulver_v1.py` or
   `evict_value_dataset_v1.py` (confirmed by reading both files' full
   import lists). `evict_value_wulver_v1.py` was introduced complete, in a
   single commit (`58f4530`, "Wulver evict-value v1: dataset pipeline,
   training, policy comparison, Slurm"), without this wiring — i.e. this is
   a missing integration between two pieces of code that both already
   existed, not a later regression.

**Conclusion: this is a provable, code-level wiring gap — a "recoverable
generation bug" in the sense that its cause is fully understood and, in
principle, fixable in the generator code — but the fix (`attach_perfect_
buckets`) is NOT a scientifically valid reconstruction for this release's
purposes**, because it is documented explicitly as deriving buckets from
`req.actual_next` — perfect, ground-truth future information. Using it now
would (a) inject genuine future-information leakage into features that the
rest of this benchmark carefully keeps online-computable, and (b) fabricate
a "perfect oracle predictor" and present its output as if it were an
authentic historical (necessarily fallible) predictor's score — both
explicitly forbidden by this repair's hard rules ("never fabricate
plausible predictor values," "never substitute a new predictor/model and
call its values historical"). No other candidate source of a genuine,
non-oracle, non-fabricated bucket/confidence signal exists for these five
traces: `Request.predicted_next` defaults to `math.inf` and is only ever
populated either by trace files that already embed real external
predictions (not true of any of this release's five raw traces, confirmed
by inspecting `data/raw/*`) or by `src/lafc/predictors/noisy.py`'s synthetic
noise-injection wrapper (itself explicitly a perturbation of `actual_next`,
i.e. also future-information-derived, and an experimental construct with
arbitrary noise parameters — not a historical value).

**Therefore the correct repair for all 18 constant features plus the one
alias is DEPRECATE_FROM_MODEL_FEATURES, not RECONSTRUCT.** See section 6.

## 5. Frozen learned-policy artifacts (Phase 6 input)

The manuscript's current committed text (`paper/performance_evaluation/`)
does not yet contain any section describing a HistGradientBoostingRegressor
or `evict_value_v1` result — grepped directly, zero matches. The closest
real artifacts are the frozen model pickles in `Augmented-caching`:

| Pickle | `model_name` | Estimator |
|---|---|---|
| `models/evict_value_wulver_v1_best.pkl` | `wulver_h4_random_forest` | `RandomForestRegressor` |
| `models/evict_value_wulver_v1_best_heavy_r1.pkl` | `wulver_h4_random_forest` | `RandomForestRegressor` |
| `models/evict_value_wulver_v1_h16_hist_gb.pkl` | `wulver_h16_hist_gb` | `HistGradientBoostingRegressor` |
| (siblings) `*_h4_hist_gb.pkl`, `*_h8_hist_gb.pkl`, `*_h4/h8/h16_ridge.pkl`, `*_h4/h8/h16_random_forest.pkl` | — | — |

Each inspected pickle stores its own `feature_columns` list (not just the
fitted estimator) — confirmed identical, same order, to `schema.py`'s
26-column `FEATURE_COLUMNS`.

**Empirical confirmation (`evict_value_wulver_v1_h16_hist_gb.pkl`,
HistGradientBoostingRegressor, 150 boosting iterations):** enumerated every
non-leaf split node's `feature_idx` across every tree. Only feature indices
`{4, 5, 7, 8, 24, 25}` — `candidate_recency_rank`, `candidate_age_norm`,
`candidate_lru_score`, `candidate_is_predictor_victim`,
`recent_candidate_request_rate`, `recent_candidate_hit_rate` — were ever
used in a split. **None of the 18 globally-constant feature indices were
ever split on** (mathematically guaranteed: a decision tree splitter cannot
produce a valid non-trivial threshold on a zero-variance column). The tree
did split on `candidate_is_predictor_victim` (index 8) rather than its
identical twin `candidate_is_lru_victim` (index 9) — expected, since the two
columns are byte-identical and the splitter's tie-break happened to pick one
of them; using either produces the same partition.

**Conclusion for Phase 6:** Problem 2's repair strategy changes no
candidate-row *values* (see hard rules — only the official modeling-feature
schema is revised; deprecated columns keep their original values in the
data for provenance). Therefore any frozen model already fit on the
original 26-column data is mathematically unaffected: it is a deterministic
function of exactly the same column values it always had, and this repair
does not alter any of them. **Rerunning the frozen learned-policy
experiment is unnecessary**, independent of and in addition to the
empirical split-index confirmation above. See
`artifacts/feature_dependency_map.json`'s `frozen_model_impact` block.

## 6. Repair decisions (Phase 2 output)

| Category | Count | Repair |
|---|---:|---|
| Globally constant (`ACCIDENTAL_PLACEHOLDER`) | 18 | `DEPRECATE_FROM_MODEL_FEATURES` |
| Exact alias (`REDUNDANT_ALIAS`) | 1 | `DEPRECATE_FROM_MODEL_FEATURES` |
| Valid, non-degenerate (`VALID_MODEL_FEATURE`) | 7 | `KEEP` |

No feature was reconstructed. No feature was removed from the schema
entirely (`REMOVE_FROM_NEW_SCHEMA` was not used) — all 26 columns remain in
the released Parquet data for provenance/reproducibility (their original,
already-published values are not touched), but only 7 are admitted to the
official modeling feature set going forward (`metadata/model_feature_schema_v2.json`,
section 7).

Full per-feature detail, including the exact reasoning for each of the 26
rows, is in `artifacts/feature_inventory.csv`.

## 7. What this audit does NOT claim

- It does not claim the historical predictor/bucket pipeline was never
  built with good intentions — `attach_perfect_buckets` and the bucket-based
  `compute_predictor_scores` machinery are real, working code; they were
  simply never connected to this specific dataset-generation path.
- It does not claim `linear_score`'s previously-reported R² is invalidated
  — that number was already near zero and is not changed by this repair
  (see Phase 5 rerun in the companion report for the corrected-feature
  numbers).
- It does not claim the frozen `evict_value_v1` closed-loop pilot findings
  (already reported as "learned model does not beat LRU" in
  `docs/CURRENT_PROJECT_STATUS_AND_HANDOFF.md`) are wrong or need
  retraining — see section 5.
