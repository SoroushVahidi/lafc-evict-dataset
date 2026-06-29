# Decision View Contract Note

## Summary

The preserved release at `release/lafc-evict-v0.1-open-current-contract-preserved` contains a `data/decision_view/decision_view.parquet` file that is about `1.6G` because it materializes the current richer decision-view contract, not because of a compression or packaging bug.

This note is based on a local Parquet footer-metadata audit only. It did not run a full row scan, rebuild the release, or rewrite any artifact under `release/`.

## Files Compared

- Smaller local release: `release/lafc-evict-v0.1-open/data/decision_view/decision_view.parquet`
- Preserved release: `release/lafc-evict-v0.1-open-current-contract-preserved/data/decision_view/decision_view.parquet`

## High-Level Comparison

| property | smaller local decision view | preserved decision view |
| --- | --- | --- |
| size | about `15M` | `1,650,386,195` bytes |
| rows | `2,363,286` | `2,363,286` |
| columns | `12` | `19` |
| compression | `SNAPPY` | `SNAPPY` |
| row groups | `20` | `20` |
| contract status | older/slimmer local shape | richer/current preserved-release shape |

The equal row counts and equal row-group counts show that the size difference is not caused by duplicated decisions. The decisive difference is schema and payload.

## Decision-View Contracts

### Older / slimmer 12-column local decision view

`decision_id, capacity, horizon, split, trace_family, trace_name, candidate_count, min_y_loss, max_y_loss, mean_y_loss, tie_count, best_candidate_page_id`

This slimmer file stores one `best_candidate_page_id` per decision plus a few aggregated loss statistics.

### Richer / current 19-column preserved decision view

`trace_name, trace_family, dataset_source, capacity, horizon, decision_id, decision_t, decision_chunk_id, split, candidate_count, min_y_loss, max_y_value, optimal_candidate_page_ids, optimal_candidate_count, tie_count, regret_mean, regret_std, regret_max, regret_sum`

This richer file stores additional decision provenance, regret statistics, and the full `optimal_candidate_page_ids` set for each decision.

## Footer-Metadata Evidence

For the preserved release decision view:

- file path: `release/lafc-evict-v0.1-open-current-contract-preserved/data/decision_view/decision_view.parquet`
- file size: `1,650,386,195` bytes
- row count from footer: `2,363,286`
- column count from footer: `19`
- total compressed size from footer: `1,650,302,962` bytes
- total uncompressed size from footer: `12,466,063,350` bytes
- codec observed across columns: `SNAPPY`

The dominant column by far is `optimal_candidate_page_ids`:

- compressed size across row groups: `1,624,751,927` bytes
- uncompressed size across row groups: `12,321,025,894` bytes
- share of total compressed bytes: `98.4517%`

The footer audit therefore shows that almost the entire file is explained by materializing the full pipe-delimited optimal candidate ID sets per decision.

## Interpretation

The preserved file is large because `optimal_candidate_page_ids` is high-cardinality string payload stored for every decision. That is a semantic contract choice, not a compression failure.

The smaller `15M` local decision view should not be treated as the current contract for publication packaging. It reflects an older/slimmer representation that stores only a single `best_candidate_page_id` rather than the full optimal candidate set.

## Publication Guidance

The preserved release remains the correct publication candidate because:

- it matches the richer/current 19-column decision-view contract
- the June 29, 2026 preserved-release validation and SIGMOD result summaries were recorded against the preserved release
- the `1.6G` size is expected under the current contract

## Warning

Do not cite the smaller local `15M` decision view as if it were the current release contract. It is useful as a local comparison point only.

## Method Note

This note is derived from Parquet footer metadata and local release metadata only. It does not rely on a full candidate-row scan, a full decision-view row scan, or a release rebuild.
