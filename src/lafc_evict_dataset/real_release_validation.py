from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .io import sha256_file
from .real_release import DEFAULT_BLOCKED_FAMILIES
from .real_release_build import DECISION_GROUP_COLUMNS
from .schema import ALLOWED_SPLIT_SETS, CANONICAL_COLUMNS

DECISION_VIEW_COLUMNS = [
    *DECISION_GROUP_COLUMNS,
    "candidate_count",
    "min_y_loss",
    "max_y_loss",
    "mean_y_loss",
    "tie_count",
    "best_candidate_page_id",
]


def _sql_string_list(values: list[str]) -> str:
    return "[" + ", ".join(repr(value) for value in values) + "]"


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

    total_rows = 0
    families_seen: set[str] = set()
    splits_seen: set[str] = set()
    for parquet_path in parquet_paths:
        work = pd.read_parquet(parquet_path)
        missing = [column for column in CANONICAL_COLUMNS if column not in work.columns]
        if missing:
            errors.append(
                f"Partition {parquet_path.relative_to(release_root)} missing columns: {', '.join(missing)}"
            )
            continue

        y_loss = pd.to_numeric(work["y_loss"], errors="coerce")
        y_value = pd.to_numeric(work["y_value"], errors="coerce")
        if y_loss.isna().any() or y_value.isna().any():
            errors.append(f"Non-numeric labels in {parquet_path.relative_to(release_root)}")

        families = {str(value) for value in work["trace_family"].dropna().tolist()}
        families_seen.update(families)
        splits = {str(value).strip().lower() for value in work["split"].dropna().tolist()}
        splits_seen.update(splits)
        blocked = families & blocked_families
        if blocked:
            errors.append(
                f"Blocked families present in {parquet_path.relative_to(release_root)}: {', '.join(sorted(blocked))}"
            )
        total_rows += len(work)

    if splits_seen not in ALLOWED_SPLIT_SETS:
        errors.append(f"Invalid split values found: {sorted(splits_seen)}")

    missing_selected = selected_families - families_seen
    if missing_selected:
        errors.append("Selected families missing from candidate rows: " + ", ".join(sorted(missing_selected)))

    return errors, total_rows, {"trace_family": {family: 0 for family in families_seen}}, {"split": {split: 0 for split in splits_seen}}


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

    for column in ("candidate_count", "min_y_loss", "max_y_loss", "mean_y_loss", "tie_count"):
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

    manifest_candidate_rows = expected_candidate_rows
    if actual_candidate_rows != manifest_candidate_rows:
        errors.append(
            "Candidate row count mismatch between partitions and manifest: "
            f"{actual_candidate_rows} vs {manifest_candidate_rows}"
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

    manifest_candidate_rows = int(manifest.get("candidate_row_count", candidate_rows)) if manifest else candidate_rows
    decision_errors, decision_rows = _validate_decision_view(
        release_root,
        expected_candidate_rows=manifest_candidate_rows,
    )
    errors.extend(decision_errors)

    if manifest:
        manifest_decision_rows = int(manifest.get("decision_row_count", decision_rows))
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
