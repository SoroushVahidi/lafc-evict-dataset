from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from .io import sha256_file
from .real_release import DEFAULT_BLOCKED_FAMILIES
from .real_release_build import DECISION_GROUP_COLUMNS
from .schema import ALLOWED_SPLIT_SETS, CANONICAL_COLUMNS, DECISION_KEY_COLUMNS, DECISION_METADATA_COLUMNS
from .views import DECISION_VIEW_COLUMNS


def _sql_string_list(values: list[str]) -> str:
    return "[" + ", ".join(repr(value) for value in values) + "]"


def _normalized_split_sql(column: str = "split") -> str:
    return (
        f"CASE lower(trim(CAST({column} AS VARCHAR))) "
        f"WHEN 'validation' THEN 'val' "
        f"ELSE lower(trim(CAST({column} AS VARCHAR))) END"
    )


def _require_duckdb():
    try:
        import duckdb
    except ImportError as exc:
        raise ImportError("duckdb is required for real-release validation") from exc
    return duckdb


def _read_manifest(release_root: Path) -> dict[str, object]:
    manifest_path = release_root / "metadata" / "release_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _validate_checksums(release_root: Path) -> list[str]:
    errors: list[str] = []
    checksums_path = release_root / "metadata" / "checksums.sha256"
    if not checksums_path.exists():
        return ["Missing checksum manifest: metadata/checksums.sha256"]

    lines = [
        line.strip()
        for line in checksums_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    for line in lines:
        digest, rel_path = line.split(maxsplit=1)
        rel_path = rel_path.strip()
        file_path = release_root / rel_path
        if not file_path.exists():
            errors.append(f"Checksum entry references missing file: {rel_path}")
            continue
        if sha256_file(file_path) != digest:
            errors.append(f"Checksum mismatch for {rel_path}")
    return errors


def _validate_candidate_partitions(
    release_root: Path,
    *,
    selected_families: set[str],
    blocked_families: set[str],
) -> tuple[list[str], int, dict[str, int], dict[str, int]]:
    errors: list[str] = []
    candidate_root = release_root / "data" / "candidate_rows"
    if not candidate_root.exists():
        return ["Missing candidate rows directory: data/candidate_rows"], 0, {}, {}

    parquet_paths = sorted(candidate_root.rglob("candidate_rows.parquet"))
    if not parquet_paths:
        return ["No candidate_rows.parquet partitions found"], 0, {}, {}

    for parquet_path in parquet_paths:
        schema_names = pq.ParquetFile(parquet_path).schema.names
        missing = [column for column in CANONICAL_COLUMNS if column not in schema_names]
        if missing:
            errors.append(
                f"Partition {parquet_path.relative_to(release_root)} missing columns: {', '.join(missing)}"
            )
    con = _require_duckdb().connect()
    try:
        path_list = _sql_string_list([str(p) for p in parquet_paths])
        source_sql = f"read_parquet({path_list})"

        total_rows = int(con.execute(f"SELECT COUNT(*) FROM {source_sql}").fetchone()[0])
        families_seen = {
            str(value)
            for (value,) in con.execute(
                f"SELECT DISTINCT CAST(trace_family AS VARCHAR) FROM {source_sql}"
            ).fetchall()
        }
        splits_seen = {
            str(value)
            for (value,) in con.execute(
                f"SELECT DISTINCT lower(trim(CAST(split AS VARCHAR))) FROM {source_sql}"
            ).fetchall()
        }

        typed_cte = (
            f"WITH typed AS ("
            f"SELECT *, TRY_CAST(y_loss AS DOUBLE) AS y_loss_num, TRY_CAST(y_value AS DOUBLE) AS y_value_num "
            f"FROM {source_sql}"
            f") "
        )
        invalid_label_rows = int(
            con.execute(
                typed_cte
                + """
                SELECT COUNT(*)
                FROM typed
                WHERE y_loss_num IS NULL
                    OR y_value_num IS NULL
                    OR NOT isfinite(y_loss_num)
                    OR NOT isfinite(y_value_num)
                """
            ).fetchone()[0]
        )
        if invalid_label_rows:
            errors.append("Labels y_loss and y_value must be present and numeric")
            errors.append("Missing labels detected in y_loss or y_value")

        y_value_mismatch_rows = int(
            con.execute(
                typed_cte
                + """
                SELECT COUNT(*)
                FROM typed
                WHERE y_loss_num IS NOT NULL
                    AND y_value_num IS NOT NULL
                    AND isfinite(y_loss_num)
                    AND isfinite(y_value_num)
                    AND abs(y_value_num + y_loss_num) > 1e-8
                """
            ).fetchone()[0]
        )
        if y_value_mismatch_rows:
            errors.append("y_value must equal -y_loss for all rows")

        if splits_seen not in ALLOWED_SPLIT_SETS:
            errors.append(f"Invalid split values found: {sorted(splits_seen)}")

        blocked_present = families_seen & blocked_families
        if blocked_present:
            errors.append("Blocked families present in candidate rows: " + ", ".join(sorted(blocked_present)))

        missing_selected = selected_families - families_seen
        if missing_selected:
            errors.append("Selected families missing from candidate rows: " + ", ".join(sorted(missing_selected)))

        duplicate_query = f"""
            SELECT
                {", ".join(DECISION_KEY_COLUMNS)},
                CAST(candidate_page_id AS VARCHAR) AS candidate_page_id
            FROM {source_sql}
            GROUP BY {", ".join(DECISION_KEY_COLUMNS)}, CAST(candidate_page_id AS VARCHAR)
            HAVING COUNT(*) > 1
            LIMIT 5
        """
        duplicate_rows = con.execute(duplicate_query).fetchall()
        if duplicate_rows:
            errors.append(
                "Duplicate candidate_page_id within decision group: "
                + "; ".join(str(row) for row in duplicate_rows)
            )

        metadata_columns_to_check = [
            column for column in DECISION_METADATA_COLUMNS if column not in DECISION_KEY_COLUMNS
        ]
        for column in metadata_columns_to_check:
            inconsistent_rows = con.execute(
                f"""
                SELECT {", ".join(DECISION_KEY_COLUMNS)}
                FROM {source_sql}
                GROUP BY {", ".join(DECISION_KEY_COLUMNS)}
                HAVING COUNT(DISTINCT COALESCE(CAST({column} AS VARCHAR), '__NULL__')) > 1
                LIMIT 5
                """
            ).fetchall()
            if inconsistent_rows:
                errors.append(
                    f"Inconsistent {column} within decision group(s): "
                    + "; ".join(str(row) for row in inconsistent_rows)
                )

        cross_split_rows = con.execute(
            f"""
            SELECT CAST(decision_id AS VARCHAR)
            FROM {source_sql}
            GROUP BY CAST(decision_id AS VARCHAR)
            HAVING COUNT(DISTINCT {_normalized_split_sql()}) > 1
            LIMIT 10
            """
        ).fetchall()
        if cross_split_rows:
            errors.append(
                "Found decision_id values spanning multiple splits without override: "
                + ", ".join(str(row[0]) for row in cross_split_rows)
            )

        family_counts = {
            str(key): int(count)
            for key, count in con.execute(
                f"""
                SELECT CAST(trace_family AS VARCHAR), COUNT(*)::BIGINT
                FROM {source_sql}
                GROUP BY 1
                ORDER BY 1
                """
            ).fetchall()
        }
        split_counts = {
            str(key): int(count)
            for key, count in con.execute(
                f"""
                SELECT CAST(split AS VARCHAR), COUNT(*)::BIGINT
                FROM {source_sql}
                GROUP BY 1
                ORDER BY 1
                """
            ).fetchall()
        }
    finally:
        con.close()

    return errors, total_rows, {"trace_family": family_counts}, {"split": split_counts}


def _manifest_row_count(manifest: dict[str, object], *, nested_key: str, flat_key: str) -> int | None:
    row_counts = manifest.get("row_counts", {})
    if isinstance(row_counts, dict) and row_counts.get(nested_key) is not None:
        return int(row_counts[nested_key])
    if manifest.get(flat_key) is not None:
        return int(manifest[flat_key])
    return None


def _validate_decision_view(
    release_root: Path,
    *,
    expected_candidate_rows: int,
) -> tuple[list[str], int]:
    errors: list[str] = []
    decision_path = release_root / "data" / "decision_view" / "decision_view.parquet"
    if not decision_path.exists():
        return ["Missing decision view: data/decision_view/decision_view.parquet"], 0

    decision_view = pd.read_parquet(decision_path)
    missing = [column for column in DECISION_VIEW_COLUMNS if column not in decision_view.columns]
    if missing:
        errors.append("Decision view missing columns: " + ", ".join(missing))

    for column in ("candidate_count", "min_y_loss", "max_y_value", "optimal_candidate_count", "tie_count"):
        if column in decision_view.columns and pd.to_numeric(decision_view[column], errors="coerce").isna().any():
            errors.append(f"Decision view column {column} is not numeric")
    for column in ("regret_mean", "regret_std", "regret_max", "regret_sum"):
        if column in decision_view.columns and pd.to_numeric(decision_view[column], errors="coerce").isna().any():
            errors.append(f"Decision view column {column} is not numeric")

    candidate_root = release_root / "data" / "candidate_rows"
    parquet_paths = sorted(candidate_root.rglob("candidate_rows.parquet"))
    con = _require_duckdb().connect()
    try:
        if parquet_paths:
            path_list = _sql_string_list([str(p) for p in parquet_paths])
            actual_candidate_rows = int(
                con.execute(f"SELECT COUNT(*) FROM read_parquet({path_list})").fetchone()[0]
            )
            actual_decisions = int(
                con.execute(
                    f"""
                    SELECT COUNT(*) FROM (
                        SELECT DISTINCT {", ".join(DECISION_GROUP_COLUMNS)}
                        FROM read_parquet({path_list})
                    )
                    """
                ).fetchone()[0]
            )
        else:
            actual_candidate_rows = expected_candidate_rows
            actual_decisions = len(decision_view)
    finally:
        con.close()

    if actual_candidate_rows != expected_candidate_rows:
        errors.append(
            "Candidate row count mismatch between partitions and manifest: "
            f"{actual_candidate_rows} vs {expected_candidate_rows}"
        )
    if len(decision_view) != actual_decisions:
        errors.append(
            "Decision view row count does not match distinct decision groups in candidate rows: "
            f"{len(decision_view)} vs {actual_decisions}"
        )

    return errors, len(decision_view)


def validate_real_release(
    release_root: str | Path,
    *,
    blocked_families: set[str] | None = None,
    require_manifest: bool = True,
    selected_families: set[str] | None = None,
) -> list[str]:
    release_root = Path(release_root).expanduser().resolve()
    blocked = blocked_families or set(DEFAULT_BLOCKED_FAMILIES)
    errors: list[str] = []

    required_paths = [
        release_root / "README.md",
        release_root / "data" / "candidate_rows",
        release_root / "data" / "decision_view" / "decision_view.parquet",
    ]
    if require_manifest:
        required_paths.extend(
            [
                release_root / "metadata" / "release_manifest.json",
                release_root / "metadata" / "validation_report.md",
                release_root / "metadata" / "checksums.sha256",
            ]
        )
    for path in required_paths:
        if not path.exists():
            errors.append(f"Missing required release artifact: {path.relative_to(release_root)}")

    manifest: dict[str, object] = {}
    manifest_path = release_root / "metadata" / "release_manifest.json"
    if manifest_path.exists():
        manifest = _read_manifest(release_root)
    elif require_manifest:
        return [*errors, f"Missing release manifest: {manifest_path.relative_to(release_root)}"]

    selected_families = selected_families or {str(name) for name in manifest.get("selected_families", [])}
    excluded_families = {str(name) for name in manifest.get("excluded_families", [])}
    if manifest:
        if blocked & selected_families:
            errors.append("Manifest selects blocked families: " + ", ".join(sorted(blocked & selected_families)))
        if blocked - excluded_families:
            errors.append("Manifest does not exclude all blocked families")

    candidate_errors, candidate_rows, _, _ = _validate_candidate_partitions(
        release_root,
        selected_families=selected_families or set(),
        blocked_families=blocked,
    )
    errors.extend(candidate_errors)

    manifest_candidate_rows = (
        _manifest_row_count(manifest, nested_key="candidate_rows", flat_key="candidate_row_count")
        if manifest
        else candidate_rows
    ) or candidate_rows
    decision_errors, decision_rows = _validate_decision_view(
        release_root,
        expected_candidate_rows=manifest_candidate_rows,
    )
    errors.extend(decision_errors)

    if manifest:
        manifest_decision_rows = (
            _manifest_row_count(manifest, nested_key="decision_view", flat_key="decision_row_count")
            or decision_rows
        )
        if decision_rows and manifest_decision_rows != decision_rows:
            errors.append(
                f"Manifest decision_row_count mismatch: {manifest_decision_rows} vs {decision_rows}"
            )

        inventory = manifest.get("file_inventory", [])
        if isinstance(inventory, list):
            for rel_path in inventory:
                if not (release_root / str(rel_path)).exists():
                    errors.append(f"Manifest file_inventory references missing file: {rel_path}")

    if require_manifest and (release_root / "metadata" / "checksums.sha256").exists():
        errors.extend(_validate_checksums(release_root))

    return errors
