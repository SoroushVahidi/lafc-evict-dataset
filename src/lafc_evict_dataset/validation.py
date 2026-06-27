from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .io import read_candidate_dataframe
from .schema import (
    ALLOWED_SPLIT_SETS,
    CANONICAL_COLUMNS,
    DECISION_KEY_COLUMNS,
    DECISION_METADATA_COLUMNS,
    normalize_split_value,
)


def validate_candidate_dataframe(
    df: pd.DataFrame,
    *,
    allow_cross_split_duplicate_decision_ids: bool = False,
) -> list[str]:
    errors: list[str] = []
    missing = [column for column in CANONICAL_COLUMNS if column not in df.columns]
    if missing:
        return [f"Missing required columns: {', '.join(missing)}"]

    split_values = {str(value).strip().lower() for value in df["split"].dropna().tolist()}
    if split_values not in ALLOWED_SPLIT_SETS:
        errors.append(
            "Split values must be exactly one of "
            "{train,val,test} or {train,validation,test}; "
            f"found {sorted(split_values)}"
        )

    y_loss_numeric = pd.to_numeric(df["y_loss"], errors="coerce")
    y_value_numeric = pd.to_numeric(df["y_value"], errors="coerce")
    if y_loss_numeric.isna().any() or y_value_numeric.isna().any():
        errors.append("Labels y_loss and y_value must be present and numeric")

    if df["y_loss"].isna().any() or df["y_value"].isna().any():
        errors.append("Missing labels detected in y_loss or y_value")

    if not y_loss_numeric.isna().any() and not y_value_numeric.isna().any() and not np.allclose(
        y_value_numeric.to_numpy(dtype=float),
        -y_loss_numeric.to_numpy(dtype=float),
    ):
        errors.append("y_value must equal -y_loss for all rows")

    normalized = df.copy()
    try:
        normalized["split_norm"] = normalized["split"].map(normalize_split_value)
    except ValueError as exc:
        errors.append(str(exc))
        return errors

    decision_group = normalized.groupby(DECISION_KEY_COLUMNS, dropna=False, sort=False)
    for key, group in decision_group:
        for column in DECISION_METADATA_COLUMNS:
            if group[column].nunique(dropna=False) != 1:
                errors.append(f"Inconsistent {column} within decision group {key}")
        if group["candidate_page_id"].duplicated().any():
            errors.append(f"Duplicate candidate_page_id within decision group {key}")
        if group["candidate_page_id"].nunique(dropna=False) < 1:
            errors.append(f"Empty decision group detected for {key}")

    if not allow_cross_split_duplicate_decision_ids:
        split_count = normalized.groupby("decision_id", dropna=False)["split_norm"].nunique(dropna=False)
        offenders = split_count[split_count > 1]
        if not offenders.empty:
            errors.append(
                "Found decision_id values spanning multiple splits without override: "
                + ", ".join(offenders.index.astype(str).tolist()[:10])
            )

    return errors


def validate_candidate_file(
    input_path: str | Path,
    *,
    allow_cross_split_duplicate_decision_ids: bool = False,
) -> list[str]:
    try:
        df = read_candidate_dataframe(input_path)
    except Exception as exc:
        return [f"Failed to read candidate rows from {input_path}: {exc}"]
    return validate_candidate_dataframe(
        df,
        allow_cross_split_duplicate_decision_ids=allow_cross_split_duplicate_decision_ids,
    )
