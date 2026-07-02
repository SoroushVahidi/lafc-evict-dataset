from __future__ import annotations

import hashlib
from itertools import combinations

import pandas as pd

from .schema import CANONICAL_COLUMNS, DECISION_METADATA_COLUMNS

# Version tag mixed into the pairwise A/B orientation hash below (see
# real_release_build.PAIRWISE_ORIENTATION_METHOD for the DuckDB-side
# counterpart -- same method name, independent per-engine implementation).
PAIRWISE_ORIENTATION_METHOD = "deterministic_hash_v1"

DECISION_VIEW_VALUE_COLUMNS = [
    "candidate_count",
    "min_y_loss",
    "max_y_value",
    "optimal_candidate_page_ids",
    "optimal_candidate_count",
    "tie_count",
    "regret_mean",
    "regret_std",
    "regret_max",
    "regret_sum",
]

DECISION_VIEW_COLUMNS = [*DECISION_METADATA_COLUMNS, *DECISION_VIEW_VALUE_COLUMNS]


def _candidate_specific_columns() -> list[str]:
    shared = set(DECISION_METADATA_COLUMNS)
    return [column for column in CANONICAL_COLUMNS if column not in shared]


def _with_regret(df: pd.DataFrame) -> pd.DataFrame:
    # Must group by the full canonical decision key (DECISION_METADATA_COLUMNS),
    # not a narrower key: grouping by fewer columns can silently pool y_loss
    # across two distinct decisions that happen to share e.g. decision_id but
    # differ in dataset_source/decision_t/decision_chunk_id, understating regret.
    out = df.copy()
    out["best_y_loss"] = out.groupby(DECISION_METADATA_COLUMNS)["y_loss"].transform("min")
    out["regret"] = out["y_loss"] - out["best_y_loss"]
    return out


def _orientation_swap(parts: list[object]) -> bool:
    """Deterministic pseudo-random A/B swap decision (PAIRWISE_ORIENTATION_METHOD).

    Uses a stable cryptographic hash (not Python's salted built-in hash())
    over the decision key plus the two candidate ids, so the result is
    reproducible across runs/machines and is not correlated with
    candidate_page_id ordering.
    """
    key = "|".join(str(part) for part in parts) + f"|{PAIRWISE_ORIENTATION_METHOD}"
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return (digest[-1] % 2) == 1


def build_decision_view(df: pd.DataFrame) -> pd.DataFrame:
    rows = _with_regret(df)
    group_cols = DECISION_METADATA_COLUMNS

    def _summarize(group: pd.DataFrame) -> pd.Series:
        optimal = group[group["regret"] == 0].sort_values("candidate_page_id")
        return pd.Series(
            {
                "candidate_count": int(group["candidate_page_id"].nunique()),
                "min_y_loss": float(group["y_loss"].min()),
                "max_y_value": float(group["y_value"].max()),
                "optimal_candidate_page_ids": "|".join(optimal["candidate_page_id"].astype(str).tolist()),
                "optimal_candidate_count": int(len(optimal)),
                "tie_count": int(len(optimal)),
                "regret_mean": float(group["regret"].mean()),
                "regret_std": float(group["regret"].std(ddof=0)),
                "regret_max": float(group["regret"].max()),
                "regret_sum": float(group["regret"].sum()),
            }
        )

    decision_view = rows.groupby(group_cols, dropna=False, sort=True).apply(_summarize).reset_index()
    return decision_view.sort_values(group_cols).reset_index(drop=True)


def build_pairwise_view(df: pd.DataFrame, *, include_ties: bool = False) -> pd.DataFrame:
    rows = _with_regret(df)
    group_cols = DECISION_METADATA_COLUMNS
    candidate_cols = _candidate_specific_columns()
    pairwise_rows: list[dict[str, object]] = []

    for group_key, group in rows.groupby(group_cols, dropna=False, sort=True):
        shared = dict(zip(group_cols, group_key))
        records = group.sort_values("candidate_page_id").to_dict(orient="records")
        for low, high in combinations(records, 2):
            # `low`/`high` are ordered by candidate_page_id purely to enumerate
            # each unordered pair exactly once. The actual A/B slot assignment
            # is decided separately below by a deterministic hash, so which
            # candidate lands in "a" is not systematically tied to id ordering.
            swap = _orientation_swap(
                [*group_key, low["candidate_page_id"], high["candidate_page_id"]]
            )
            left, right = (high, low) if swap else (low, high)
            left_regret = float(left["regret"])
            right_regret = float(right["regret"])
            is_tie = left_regret == right_regret
            if is_tie and not include_ties:
                continue

            pair = dict(shared)
            pair["candidate_a_page_id"] = str(left["candidate_page_id"])
            pair["candidate_b_page_id"] = str(right["candidate_page_id"])
            for column in candidate_cols:
                pair[f"{column}_a"] = left[column]
                pair[f"{column}_b"] = right[column]
            pair["regret_a"] = left_regret
            pair["regret_b"] = right_regret
            pair["regret_diff_a_minus_b"] = left_regret - right_regret
            pair["label_a_better"] = int(left_regret < right_regret)
            pair["label_b_better"] = int(right_regret < left_regret)
            pair["is_tie"] = int(is_tie)
            pairwise_rows.append(pair)

    if not pairwise_rows:
        return pd.DataFrame(columns=[*group_cols, "candidate_a_page_id", "candidate_b_page_id"])
    return pd.DataFrame(pairwise_rows).sort_values(
        [*group_cols, "candidate_a_page_id", "candidate_b_page_id"]
    ).reset_index(drop=True)
