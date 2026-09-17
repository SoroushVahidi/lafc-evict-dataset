from __future__ import annotations

"""Validate that the OFFICIAL model-feature set (metadata/model_feature_schema_v2.json)
has not silently regressed: no advertised predictive feature may be globally
constant, an exact duplicate of another advertised feature, a prohibited
leakage column, or contain unexpected nulls.

This does not re-validate release schema/checksums (see validate_real_release.py
for that); it validates the MODELING feature surface specifically, which is
the subject of Problem 2.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_official_feature_set(schema: dict) -> list[str]:
    errors: list[str] = []
    official = set(schema["rules"]["official_model_feature_set"])
    valid_names = {f["name"] for f in schema["valid_model_features"]}
    deprecated_names = {f["name"] for f in schema["deprecated_legacy_features"]}
    prohibited = set(schema["prohibited_leakage_columns"])

    unknown = official - valid_names
    if unknown:
        errors.append(f"official_model_feature_set references names not in valid_model_features: {sorted(unknown)}")

    leaked_in = official & prohibited
    if leaked_in:
        errors.append(f"official_model_feature_set includes prohibited leakage columns: {sorted(leaked_in)}")

    deprecated_in_official = official & deprecated_names
    if deprecated_in_official:
        errors.append(f"official_model_feature_set includes deprecated legacy features: {sorted(deprecated_in_official)}")

    labels_in_official = official & set(schema["label_columns"])
    if labels_in_official:
        errors.append(f"official_model_feature_set includes label columns: {sorted(labels_in_official)}")

    split_in_official = official & set(schema["split_column"])
    if split_in_official:
        errors.append(f"official_model_feature_set includes the split identifier column: {sorted(split_in_official)}")

    return errors


def validate_data_against_schema(
    parquet_glob: str,
    schema: dict,
    *,
    allow_missing_columns: bool = False,
) -> list[str]:
    import duckdb

    errors: list[str] = []
    official = list(schema["rules"]["official_model_feature_set"])
    deprecated = {f["name"] for f in schema["deprecated_legacy_features"]}

    con = duckdb.connect()
    con.execute("SET threads TO 8")
    source = f"read_parquet('{parquet_glob}', hive_partitioning=1)"

    try:
        columns = {row[0] for row in con.execute(f"DESCRIBE SELECT * FROM {source} LIMIT 0").fetchall()}
    except Exception as exc:
        return [f"Could not read {parquet_glob}: {exc}"]

    missing = [c for c in official if c not in columns]
    if missing and not allow_missing_columns:
        errors.append(f"Official model features missing from data: {missing}")
    official = [c for c in official if c in columns]

    if not official:
        return errors

    agg = ", ".join(f"COUNT(DISTINCT {c}) AS distinct_{c}, SUM(CASE WHEN {c} IS NULL THEN 1 ELSE 0 END) AS nulls_{c}" for c in official)
    row = con.execute(f"SELECT {agg} FROM {source}").fetchone()
    cols = [d[0] for d in con.description]
    stats = dict(zip(cols, row))

    for c in official:
        if stats[f"distinct_{c}"] == 1:
            errors.append(f"Official model feature '{c}' is globally constant in this data (regression: was expected non-constant)")
        if stats[f"nulls_{c}"] > 0:
            errors.append(f"Official model feature '{c}' has {stats[f'nulls_{c}']} unexpected nulls")

    # pairwise exact-duplicate check among official features only (cheap: len(official) is small)
    for i in range(len(official)):
        for j in range(i + 1, len(official)):
            a, b = official[i], official[j]
            mismatch = con.execute(f"SELECT COUNT(*) FROM {source} WHERE {a} IS DISTINCT FROM {b}").fetchone()[0]
            if mismatch == 0:
                errors.append(f"Official model features '{a}' and '{b}' are exact duplicates (0 mismatches)")

    # deprecated features must not have silently become part of the declared official set
    overlap = set(official) & deprecated
    if overlap:
        errors.append(f"Deprecated legacy features present in official set at validation time: {sorted(overlap)}")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", default=str(ROOT / "metadata" / "model_feature_schema_v2.json"))
    parser.add_argument(
        "--candidate-rows-glob",
        default=None,
        help="Optional glob of candidate_rows parquet files to validate against (skips data checks if omitted)",
    )
    args = parser.parse_args()

    schema = load_schema(Path(args.schema))
    errors = validate_official_feature_set(schema)

    if args.candidate_rows_glob:
        errors.extend(validate_data_against_schema(args.candidate_rows_glob, schema))

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        raise SystemExit(1)
    print("Model feature schema validation passed.")


if __name__ == "__main__":
    main()
