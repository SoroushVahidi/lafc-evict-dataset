from __future__ import annotations

from typing import Final

BASE_REQUIRED_COLUMNS: Final[list[str]] = [
    "trace_name",
    "trace_family",
    "dataset_source",
    "capacity",
    "horizon",
    "decision_id",
    "decision_t",
    "decision_chunk_id",
    "candidate_page_id",
    "split",
    "y_loss",
    "y_value",
]

FEATURE_COLUMNS: Final[list[str]] = [
    "request_bucket",
    "request_confidence",
    "candidate_bucket",
    "candidate_confidence",
    "candidate_recency_rank",
    "candidate_age_norm",
    "candidate_predictor_score",
    "candidate_lru_score",
    "candidate_is_predictor_victim",
    "candidate_is_lru_victim",
    "score_gap_to_predictor_best",
    "score_gap_to_lru_victim",
    "bucket_gap_to_predictor_best",
    "bucket_gap_to_lru_victim",
    "confidence_gap_to_predictor_best",
    "confidence_gap_to_lru_victim",
    "cache_bucket_mean",
    "cache_bucket_std",
    "cache_bucket_min",
    "cache_bucket_max",
    "cache_unique_bucket_count",
    "cache_confidence_mean",
    "cache_confidence_std",
    "predictor_lru_disagree",
    "recent_candidate_request_rate",
    "recent_candidate_hit_rate",
]

CANONICAL_COLUMNS: Final[list[str]] = [*BASE_REQUIRED_COLUMNS, *FEATURE_COLUMNS]

STRING_COLUMNS: Final[list[str]] = [
    "trace_name",
    "trace_family",
    "dataset_source",
    "decision_id",
    "candidate_page_id",
    "split",
]

INTEGER_COLUMNS: Final[list[str]] = [
    "capacity",
    "horizon",
    "decision_t",
    "decision_chunk_id",
]

FLOAT_COLUMNS: Final[list[str]] = [
    "y_loss",
    "y_value",
    *FEATURE_COLUMNS,
]

DECISION_METADATA_COLUMNS: Final[list[str]] = [
    "trace_name",
    "trace_family",
    "dataset_source",
    "capacity",
    "horizon",
    "decision_id",
    "decision_t",
    "decision_chunk_id",
    "split",
]

PAIRWISE_SHARED_COLUMNS: Final[list[str]] = DECISION_METADATA_COLUMNS

SPLIT_NORMALIZATION: Final[dict[str, str]] = {
    "train": "train",
    "val": "val",
    "validation": "val",
    "test": "test",
}

ALLOWED_SPLIT_SETS: Final[list[set[str]]] = [
    {"train", "val", "test"},
    {"train", "validation", "test"},
]


def normalize_split_value(value: object) -> str:
    text = str(value).strip().lower()
    if text not in SPLIT_NORMALIZATION:
        raise ValueError(f"Unsupported split value: {value!r}")
    return SPLIT_NORMALIZATION[text]
