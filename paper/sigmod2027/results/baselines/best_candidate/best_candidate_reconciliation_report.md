# Best-Candidate Evaluator Reconciliation Report

## Summary

| Metric | Old (buggy) | New (fixed) |
| --- | --- | --- |
| Evaluator `decision_count` | 2,366,413 | **2,363,286** |
| True 9-column decision count (`decision_view` rows) | 2,363,286 | 2,363,286 |
| Match | No (mismatch of 3,127) | **Yes, exact** |

## Root cause

The best-candidate evaluator grouped candidate rows by a **6-column key**
(`split, trace_family, trace_name, capacity, horizon, decision_id`) instead of
the true **9-column canonical decision key**
(`trace_name, trace_family, dataset_source, capacity, horizon, decision_id, decision_t, decision_chunk_id, split`),
and streamed candidate partitions in fixed-size batches with a carryover
mechanism that assumed each decision's rows were contiguous within a
partition file. When a decision's rows were not contiguous, the carryover
logic could flush the same physical decision across two separate "complete"
chunks, each independently grouped and counted — double-counting exactly
3,127 decisions, with zero compensating undercounts. (An exact replica of the
old batching/carryover logic reproduced 2,366,413 bit-for-bit, and a direct
`decision_view` query confirmed zero 6-column keys ever collapse two distinct
9-column decisions, ruling out any offsetting undercount.)

## Fix

- `decision_key_columns()` in `scripts/sigmod2027/_baseline_common.py` now
  returns the canonical 9-column `DECISION_METADATA_COLUMNS` (imported from
  `lafc_evict_dataset.schema`) instead of a hardcoded 6-column subset.
- `run_best_candidate_baseline.py` no longer streams in fixed-size batches
  with cross-batch/cross-file carryover. Each manifest-listed candidate
  partition file is now read in full and grouped once by the canonical
  9-column key. This is correct regardless of row order because every
  decision's rows live entirely within a single partition file (each file
  covers exactly one `(split, trace_family, capacity, horizon)` combination,
  enforced by the existing `duplicate_partition_keys()` check).

## Tests added

- `test_decision_key_columns_is_canonical_nine_column_key`
- `test_best_candidate_runner_distinguishes_decisions_sharing_old_six_column_key`
  (synthetic decisions sharing the old 6-column key but differing in
  `dataset_source`, with non-contiguous rows — the old key would collapse
  them into one group; the fixed key keeps them separate)
- `test_best_candidate_runner_decision_count_matches_decision_view_row_count`
  (release/fixture-level smoke test asserting evaluator `decision_count`
  equals `decision_view` row count)

## Regeneration

Full rerun of `run_best_candidate_baseline.py` (`linear_score` mode) against
all 168 manifest-listed candidate partitions on the preserved open release
(the cluster's `general` partition; the run required more than 8 hours of wall
clock and was resumed once via its built-in checkpoint/`--resume` support —
this matches the wall-clock profile of the original, pre-fix evaluator run
on the same hardware, so it is not a performance regression from this fix).

- `files_total` / `files_processed`: 168 / 168
- `decision_count`: **2,363,286**
- `optimal_selection_rate`: 0.8753
- `mean_regret`: 0.1251
- `median_regret`: 0.0
- `max_regret`: 3.0

## Decision-level floors (cheap, grounded in existing `decision_view` fields)

Computed via a single DuckDB aggregation over `decision_view.parquet`
(2,363,286 rows) — no additional full `candidate_rows` scan required.

- Mean optimal-set size: 116.97 (std 85.12, min 16, max 256)
- Mean candidate-pool size: 117.63
- Random-selector expected optimal-selection rate: **0.9912**
- Random-selector expected regret: **0.0088**

**Observation:** the dataset is heavily tied at the decision level — `y_loss`
is a small bounded integer range (`0..horizon`), so on average ~99.4% of a
decision's candidates already share the minimum `y_loss`. A uniform-random
selector's expected optimal-selection rate (0.9912) and expected regret
(0.0088) are therefore both very favorable purely from tie density, and are
notably better than the `linear_score` selector's observed
`optimal_selection_rate` (0.8753) and `mean_regret` (0.1251). This is a real
characteristic of the corrected data, not a scoring bug — headline
`optimal_selection_rate`/`mean_regret` numbers should be read alongside this
random floor rather than in isolation.

## LRU / continuation-rank floor

**Omitted.** No LRU/continuation-rank best-candidate baseline result already
exists in this release, and computing one would require another full
168-file, multi-hour evaluator run (the same architecture, just invoked with
`--score-column candidate_is_lru_victim`), which is not cheap. Omitted per
instructions rather than invented or approximated.
