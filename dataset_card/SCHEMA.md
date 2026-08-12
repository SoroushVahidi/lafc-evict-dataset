# Schema

This document defines stable column semantics. Release-specific fields, dtypes,
and file inventories are authoritative in each release's
`metadata/schema.json` and `metadata/release_manifest.json`; the v0.2
published preview is the current public schema instance.

The canonical base row represents one candidate victim at one full-cache miss eviction decision, for one capacity and one finite horizon.

## Base columns

| Column | Type | Description |
| --- | --- | --- |
| `trace_name` | string | Release-facing trace identifier. |
| `trace_family` | string | Coarser trace-family label used for grouping and release filtering. |
| `dataset_source` | string | Source dataset label for provenance. |
| `capacity` | int | Cache capacity used when generating this decision. |
| `horizon` | int | Finite rollout horizon used for the label. |
| `decision_id` | string | Identifier for the eviction decision. |
| `decision_t` | int | Request index of the decision in the processed trace. |
| `decision_chunk_id` | int | Chunk identifier used for split bookkeeping or chunk-aware analyses. |
| `candidate_page_id` | string | Candidate victim page identifier. |
| `split` | string | Dataset split, expected as `train`, `val`, `test` or `train`, `validation`, `test`. |
| `y_loss` | float | Finite-horizon counterfactual LRU-continuation miss count after forcing this eviction. |
| `y_value` | float | Convenience target equal to `-y_loss`. |

## Feature columns

| Column | Type | Description |
| --- | --- | --- |
| `request_bucket` | float | Bucket assigned to the incoming miss request by the upstream predictor or preprocessing stage. |
| `request_confidence` | float | Confidence associated with the incoming miss request bucket or score. |
| `candidate_bucket` | float | Bucket attached to the candidate victim. |
| `candidate_confidence` | float | Confidence attached to the candidate victim. |
| `candidate_recency_rank` | float | Candidate position in recency order within the resident cache state. |
| `candidate_age_norm` | float | Normalized recency rank. |
| `candidate_predictor_score` | float | Predictor-side score for the candidate victim. |
| `candidate_lru_score` | float | LRU-side score for the candidate victim. |
| `candidate_is_predictor_victim` | float | Indicator that the predictor would choose this victim. |
| `candidate_is_lru_victim` | float | Indicator that LRU would choose this victim. |
| `score_gap_to_predictor_best` | float | Candidate predictor-score gap to the predictor-selected victim. |
| `score_gap_to_lru_victim` | float | Candidate LRU-score gap to the LRU victim. |
| `bucket_gap_to_predictor_best` | float | Bucket gap to the predictor-selected victim. |
| `bucket_gap_to_lru_victim` | float | Bucket gap to the LRU victim. |
| `confidence_gap_to_predictor_best` | float | Confidence gap to the predictor-selected victim. |
| `confidence_gap_to_lru_victim` | float | Confidence gap to the LRU victim. |
| `cache_bucket_mean` | float | Mean bucket value across the current cache residents. |
| `cache_bucket_std` | float | Standard deviation of cache bucket values. |
| `cache_bucket_min` | float | Minimum bucket value in the current cache. |
| `cache_bucket_max` | float | Maximum bucket value in the current cache. |
| `cache_unique_bucket_count` | float | Number of unique bucket values in the current cache. |
| `cache_confidence_mean` | float | Mean candidate confidence across the current cache. |
| `cache_confidence_std` | float | Standard deviation of candidate confidence across the current cache. |
| `predictor_lru_disagree` | float | Indicator that predictor and LRU would evict different candidates. |
| `recent_candidate_request_rate` | float | Recent request frequency for the candidate over the configured history window. |
| `recent_candidate_hit_rate` | float | Recent hit frequency for the candidate over the configured history window. |

## Derived views

### Decision view

One row per unique decision/capacity/horizon/split, with:

- candidate count,
- minimum `y_loss`,
- optimal candidate IDs,
- tie count,
- regret summary statistics.

### Pairwise view

One row per candidate pair from the same decision/capacity/horizon/split, with:

- shared decision metadata,
- `_a` and `_b` suffixed candidate fields,
- regret difference,
- pairwise preference labels.
