# Problem 3 Informativeness-Stratified Benchmark Utility Protocol

Date: 2026-09-17.

Source state fixed before model-outcome evaluation:

- Repository: `/home/soroush/projects/lafc-evict-dataset/repo`
- Source branch: `repair/feature-provenance-and-modeling-20260917`
- Source SHA: `a79da7235297eb2be3436a884195025f24df3c68`
- Problem-3 branch: `experiment/problem3-informativeness-stratification-20260917`
- Problem-3 worktree: `/home/soroush/projects/lafc-evict-dataset/worktrees/problem3-informativeness-stratification-20260917`

This protocol is written before evaluating selector/model outcomes by
informativeness stratum. It is intentionally not allowed to change after the
method results are inspected.

## Population

The canonical population is the full LAFC-Evict candidate-row corpus used by
the completed Problem-2 repair:

`/home/soroush/projects/lafc-evict-dataset/repo/release/lafc-evict-v0.1-open-current-contract-preserved/data/candidate_rows/**/*.parquet`

The matching decision view is:

`/home/soroush/projects/lafc-evict-dataset/repo/release/lafc-evict-v0.1-open-current-contract-preserved/data/decision_view/decision_view.parquet`

The public Hugging Face v1.0 release is not modified.

## Primary Informativeness Metric

For each decision `d`, define:

`expected_random_regret(d) = mean_c[y_loss(c)] - min_c[y_loss(c)]`

This is primary regardless of downstream outcome. It is equal to zero if and
only if all candidate losses in the decision are tied; it measures the
expected miss-count penalty of choosing a candidate uniformly at random; and
it combines optimal-set size and non-optimal-choice severity without inventing
new ground truth.

In the existing decision view this equals `regret_mean`.

## Secondary Informativeness Metrics

The robustness metrics are:

- `optimal_set_fraction = optimal_candidate_count / candidate_count`
- `loss_range = max(y_loss) - min(y_loss)`, equal to `regret_max`
- `strict_preference_density = fraction of unordered candidate pairs whose y_loss values differ`
- `random_optimal_probability = optimal_candidate_count / candidate_count`

The primary conclusion must not depend exclusively on a secondary metric.

## Primary Stratification

Stratum `Z` is the zero-information stratum:

`expected_random_regret = 0`

For decisions with `expected_random_regret > 0`, quartile ranks are assigned
within each `(trace_family, capacity, horizon)` cell separately, using
`expected_random_regret` only. The positive-information strata are:

- `Q1`: lowest positive-information quartile
- `Q2`
- `Q3`
- `Q4`: highest positive-information quartile

Corresponding quantile ranks are pooled across cells for summary tables and
figures. This prevents any one family/capacity/horizon scale from defining
the global thresholds.

Fallback for sparse cells: if a `(trace_family, capacity, horizon)` cell has
fewer than four positive-information decisions, all positive decisions in that
cell are assigned to `Q4_sparse` and the cell is reported explicitly. No
positive decision is silently dropped.

Ties at quantile boundaries are handled deterministically by DuckDB's
`ntile(4)` over `(expected_random_regret, trace_name, split, decision_t,
decision_chunk_id, decision_id)`. Equal values can therefore be split across
adjacent quartile ranks for count balance, but the rule is fixed before
method evaluation.

## Absolute Utility Decomposition Bins

Absolute bins are based on miss-count semantics, not method performance:

- `zero`: `expected_random_regret = 0`
- `tiny`: `0 < expected_random_regret <= 1/256`
- `small`: `1/256 < expected_random_regret <= 1/64`
- `moderate`: `1/64 < expected_random_regret <= 1/16`
- `large`: `expected_random_regret > 1/16`

These cut points correspond to expected fractions of one miss and align with
the cache-capacity scale present in the benchmark.

## Methods

Evaluate only the following selectors, subject to artifact availability:

- `uniform_random`: analytical expected regret (`expected_random_regret`).
- `lru`: candidate with `candidate_is_lru_victim = 1`.
- `clean_linear`: Problem-2 clean seven-feature least-squares regressor,
  selecting the lowest predicted `y_loss`.
- `clean_pairwise_logistic`: Problem-2 clean seven-feature pairwise logistic
  model, trained only on strict-preference sampled pairs; equal-loss pairs are
  omitted as ties. Candidate score is the linear utility
  `coef dot features`; higher score is selected.
- `frozen_hgb`: include only if the frozen offline HGB artifacts can be loaded
  and scored against the canonical candidate rows without changing their
  training protocol or feature values.

No additional architecture search is allowed. If the existing pairwise
logistic selector admits decision-level scores, no new tie-aware model is
trained.

## Outcomes

For every evaluated decision and method, compute:

- selected candidate
- selected `y_loss`
- decision minimum `y_loss`
- realized regret: `selected_y_loss - min_y_loss`
- optimal-set selection indicator

Primary outcome: mean realized regret by informativeness stratum.

Also report median, p90/p95 where meaningful, optimal-set selection rate,
improvement vs. uniform random, decision count, and family/capacity/horizon
composition.

The central interpretation is effect-size based: separation should increase
in a structured way from `Z` to `Q4`; enormous-n significance alone is not
used as evidence of benchmark utility.
