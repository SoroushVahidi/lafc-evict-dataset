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

**Modeling status (2026-09-17):** of these 26 columns, an independent
full-corpus audit
(`analysis/feature_provenance_repair_20260917/FEATURE_PROVENANCE_AUDIT.md`)
found that 18 are globally constant across all 277,995,072 candidate rows
and 1 (`candidate_is_predictor_victim`) is bit-identical to
`candidate_is_lru_victim`. Root cause: the upstream generator
(`Augmented-caching`'s `evict_value_wulver_v1.py`) never wires a
bucket/confidence-annotation step into the trace-replay loop that produced
this release, so every predictor/bucket/confidence-derived field silently
falls back to its hardcoded default. Only **7 of the 26 columns are
currently non-degenerate**: `candidate_recency_rank`, `candidate_age_norm`,
`candidate_lru_score`, `candidate_is_lru_victim`, `score_gap_to_lru_victim`,
`recent_candidate_request_rate`, `recent_candidate_hit_rate`. These 7 are the
**official model feature set** for new baselines/models
(`metadata/model_feature_schema_v2.json`); the other 19 remain in the
released data for provenance/reproducibility but are marked
**DEPRECATED — DO NOT USE AS A MODEL INPUT** below. See the audit for full
per-column evidence, why reconstruction was rejected (the only available
annotation function derives buckets from perfect future information, which
would fabricate a predictor and leak future data), and a legacy-vs-clean
baseline comparison showing this deprecation does not change any previously
reported model-quality numbers
(`analysis/feature_provenance_repair_20260917/LEGACY_VS_CLEAN_RESULTS.md`).

| Column | Type | Description | Status |
| --- | --- | --- | --- |
| `request_bucket` | float | Bucket assigned to the incoming miss request by the upstream predictor or preprocessing stage. | DEPRECATED — constant (0.0) |
| `request_confidence` | float | Confidence associated with the incoming miss request bucket or score. | DEPRECATED — constant (0.5) |
| `candidate_bucket` | float | Bucket attached to the candidate victim. | DEPRECATED — constant (0.0) |
| `candidate_confidence` | float | Confidence attached to the candidate victim. | DEPRECATED — constant (0.5) |
| `candidate_recency_rank` | float | Candidate position in recency order within the resident cache state. | OK — official feature |
| `candidate_age_norm` | float | Normalized recency rank. | OK — official feature |
| `candidate_predictor_score` | float | Predictor-side score for the candidate victim. | DEPRECATED — constant (0.5) |
| `candidate_lru_score` | float | LRU-side score for the candidate victim. | OK — official feature |
| `candidate_is_predictor_victim` | float | Indicator that the predictor would choose this victim. | DEPRECATED — bit-identical alias of `candidate_is_lru_victim` |
| `candidate_is_lru_victim` | float | Indicator that LRU would choose this victim. | OK — official feature |
| `score_gap_to_predictor_best` | float | Candidate predictor-score gap to the predictor-selected victim. | DEPRECATED — constant (0.0) |
| `score_gap_to_lru_victim` | float | Candidate LRU-score gap to the LRU victim. | OK — official feature |
| `bucket_gap_to_predictor_best` | float | Bucket gap to the predictor-selected victim. | DEPRECATED — constant (0.0) |
| `bucket_gap_to_lru_victim` | float | Bucket gap to the LRU victim. | DEPRECATED — constant (0.0) |
| `confidence_gap_to_predictor_best` | float | Confidence gap to the predictor-selected victim. | DEPRECATED — constant (0.0) |
| `confidence_gap_to_lru_victim` | float | Confidence gap to the LRU victim. | DEPRECATED — constant (0.0) |
| `cache_bucket_mean` | float | Mean bucket value across the current cache residents. | DEPRECATED — constant (0.0) |
| `cache_bucket_std` | float | Standard deviation of cache bucket values. | DEPRECATED — constant (0.0) |
| `cache_bucket_min` | float | Minimum bucket value in the current cache. | DEPRECATED — constant (0.0) |
| `cache_bucket_max` | float | Maximum bucket value in the current cache. | DEPRECATED — constant (0.0) |
| `cache_unique_bucket_count` | float | Number of unique bucket values in the current cache. | DEPRECATED — constant (1.0) |
| `cache_confidence_mean` | float | Mean candidate confidence across the current cache. | DEPRECATED — constant (0.5) |
| `cache_confidence_std` | float | Standard deviation of candidate confidence across the current cache. | DEPRECATED — constant (0.0) |
| `predictor_lru_disagree` | float | Indicator that predictor and LRU would evict different candidates. | DEPRECATED — constant (0.0) |
| `recent_candidate_request_rate` | float | Recent request frequency for the candidate over the configured history window. | OK — official feature |
| `recent_candidate_hit_rate` | float | Recent hit frequency for the candidate over the configured history window. | OK — official feature |

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
