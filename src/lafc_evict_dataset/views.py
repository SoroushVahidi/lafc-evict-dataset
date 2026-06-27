from __future__ import annotations

from itertools import combinations

import pandas as pd

from .schema import CANONICAL_COLUMNS, DECISION_METADATA_COLUMNS


def _candidate_specific_columns() -> list[str]:
    shared = set(DECISION_METADATA_COLUMNS)
    return [column for column in CANONICAL_COLUMNS if column not in shared]


def _with_regret(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["best_y_loss"] = out.groupby(["trace_name", "capacity", "horizon", "decision_id"])["y_loss"].transform("min")
    out["regret"] = out["y_loss"] - out["best_y_loss"]
    return out


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
        for left, right in combinations(records, 2):
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
    return pd.DataFrame(pairwise_rows)
