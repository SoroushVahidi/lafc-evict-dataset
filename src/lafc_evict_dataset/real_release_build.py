from __future__ import annotations

import json
import shlex
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

from .io import ensure_clean_output_dir, ensure_parent, fail_if_output_exists, iter_files, sha256_file
from .real_release import (
    DEFAULT_BLOCKED_FAMILIES,
    infer_trace_family_from_path,
    load_family_selection,
    summarize_candidate_source,
)
from .schema import CANONICAL_COLUMNS, SCHEMA_VERSION

DISK_SPACE_MULTIPLIER: Final[float] = 2.0
DECISION_GROUP_COLUMNS: Final[tuple[str, ...]] = (
    "decision_id",
    "capacity",
    "horizon",
    "split",
    "trace_family",
    "trace_name",
)


@dataclass(frozen=True)
class RealReleaseBuildResult:
    release_root: Path
    dry_run: bool
    dataset_id: str
    selected_families: tuple[str, ...]
    excluded_families: tuple[str, ...]
    candidate_row_count: int | None
    decision_row_count: int | None
    pairwise_sample_row_count: int | None
    total_bytes: int | None
    disk_space_check_passed: bool | None
    disk_space_free_bytes: int | None
    disk_space_required_bytes: int | None
    build_command: str
    manifest_path: Path | None
    warnings: tuple[str, ...]


def build_real_release_cli_command(
    *,
    input_manifest: str | Path,
    family_selection: str | Path,
    output_dir: str | Path,
    dataset_id: str,
    dry_run: bool = True,
    overwrite: bool = False,
    skip_disk_space_check: bool = False,
    pairwise_sample: bool = False,
    max_pairwise_rows: int = 1_000_000,
    max_pairs_per_decision: int = 8,
    pairwise_seed: int = 7,
) -> str:
    parts = [
        "python",
        "scripts/build_real_release.py",
        "--input-manifest",
        str(Path(input_manifest)),
        "--family-selection",
        str(Path(family_selection)),
        "--output-dir",
        str(Path(output_dir)),
        "--dataset-id",
        dataset_id,
    ]
    if dry_run:
        parts.append("--dry-run")
    if overwrite:
        parts.append("--overwrite")
    if skip_disk_space_check:
        parts.append("--skip-disk-space-check")
    if pairwise_sample:
        parts.append("--pairwise-sample")
        parts.extend(
            [
                "--max-pairwise-rows",
                str(max_pairwise_rows),
                "--max-pairs-per-decision",
                str(max_pairs_per_decision),
                "--pairwise-seed",
                str(pairwise_seed),
            ]
        )
    return " \\\n  ".join(shlex.quote(part) for part in parts)


def _require_duckdb():
    try:
        import duckdb
    except ImportError as exc:
        raise ImportError(
            "duckdb is required for memory-safe real-release builds. Install with: pip install duckdb"
        ) from exc
    return duckdb


def _validate_family_governance(
    *,
    selected_families: set[str],
    excluded_families: set[str],
    blocked_families: set[str],
) -> None:
    overlap = selected_families & excluded_families
    if overlap:
        raise ValueError("Family filters overlap between selected and excluded: " + ", ".join(sorted(overlap)))

    blocked_in_selected = selected_families & blocked_families
    if blocked_in_selected:
        raise ValueError(
            "Blocked families cannot be selected for a public release: " + ", ".join(sorted(blocked_in_selected))
        )

    if blocked_families - excluded_families:
        raise ValueError(
            "Blocked families must be explicitly excluded: "
            + ", ".join(sorted(blocked_families - excluded_families))
        )


def _selected_shard_paths(
    manifest_path: Path,
    *,
    selected_families: set[str],
    excluded_families: set[str],
    blocked_families: set[str],
) -> list[Path]:
    from .io import resolve_candidate_files

    all_paths = resolve_candidate_files(manifest_path)
    known_families = selected_families | excluded_families | blocked_families
    selected: list[Path] = []
    for path in all_paths:
        family = infer_trace_family_from_path(path, known_families=known_families)
        if family is None:
            raise ValueError(f"Could not infer trace family for shard: {path}")
        if family in blocked_families or family in excluded_families:
            continue
        if selected_families and family not in selected_families:
            continue
        selected.append(path)
    if not selected:
        raise ValueError("Family filters excluded every candidate shard.")
    return selected


def check_disk_space(
    output_dir: str | Path,
    *,
    required_bytes: int,
    multiplier: float = DISK_SPACE_MULTIPLIER,
) -> tuple[bool, int, int]:
    target = Path(output_dir).expanduser().resolve()
    mount = target if target.exists() else target.parent
    mount.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(mount)
    required = int(required_bytes * multiplier)
    return usage.free >= required, usage.free, required


def _normalize_split_sql(column: str = "split") -> str:
    return (
        f"CASE lower(trim(CAST({column} AS VARCHAR))) "
        f"WHEN 'validation' THEN 'val' "
        f"ELSE lower(trim(CAST({column} AS VARCHAR))) END"
    )


def _duckdb_connect():
    duckdb = _require_duckdb()
    return duckdb.connect()


def _sql_string_list(values: list[str]) -> str:
    return "[" + ", ".join(repr(value) for value in values) + "]"


def _register_candidate_shards(con, shard_paths: list[Path]) -> None:
    paths = [str(path) for path in shard_paths]
    con.execute(
        f"""
        CREATE OR REPLACE TEMP VIEW raw_candidates AS
        SELECT * FROM read_csv(
            {_sql_string_list(paths)},
            header=true,
            auto_detect=true,
            union_by_name=true,
            quote='"'
        )
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TEMP VIEW candidates AS
        SELECT
            * REPLACE ({_normalize_split_sql()} AS split)
        FROM raw_candidates
        """
    )


def _register_candidate_partitions(con, candidate_root: Path) -> None:
    paths = sorted(str(path) for path in candidate_root.rglob("candidate_rows.parquet"))
    if not paths:
        raise FileNotFoundError(f"No candidate_rows.parquet partitions under {candidate_root}")
    con.execute(
        f"""
        CREATE OR REPLACE TEMP VIEW candidates AS
        SELECT * FROM read_parquet({_sql_string_list(paths)})
        """
    )


def _consolidate_partition_parquet_files(con, candidate_root: Path) -> None:
    for partition_dir in sorted(candidate_root.rglob("*")):
        if not partition_dir.is_dir():
            continue
        parquet_files = sorted(partition_dir.glob("*.parquet"))
        if not parquet_files:
            continue
        target = partition_dir / "candidate_rows.parquet"
        if len(parquet_files) == 1 and parquet_files[0].name == "candidate_rows.parquet":
            continue

        path_list = _sql_string_list([str(path) for path in parquet_files])
        merged_path = partition_dir / "_candidate_rows_merged.parquet"
        con.execute(
            f"""
            COPY (SELECT * FROM read_parquet({path_list}))
            TO {merged_path.as_posix()!r} (FORMAT PARQUET)
            """
        )
        for parquet_file in parquet_files:
            parquet_file.unlink()
        merged_path.rename(target)


def _export_partitioned_candidates(con, *, candidate_root: Path, overwrite: bool) -> None:
    if candidate_root.exists() and overwrite:
        shutil.rmtree(candidate_root)
    candidate_root.mkdir(parents=True, exist_ok=True)
    columns_sql = ", ".join(CANONICAL_COLUMNS)
    con.execute(
        f"""
        COPY (
            SELECT {columns_sql}
            FROM candidates
            ORDER BY split, trace_family, capacity, horizon, decision_id, candidate_page_id
        )
        TO {candidate_root.as_posix()!r}
        (
            FORMAT PARQUET,
            PARTITION_BY (split, trace_family, capacity, horizon),
            WRITE_PARTITION_COLUMNS true,
            OVERWRITE_OR_IGNORE
        )
        """
    )
    _consolidate_partition_parquet_files(con, candidate_root)


def _build_decision_view(con, *, decision_view_path: Path) -> int:
    group_cols = ", ".join(DECISION_GROUP_COLUMNS)
    join_predicates = " AND ".join(f"a.{col} = o.{col}" for col in DECISION_GROUP_COLUMNS)
    ensure_parent(decision_view_path)
    con.execute(
        f"""
        COPY (
            WITH agg AS (
                SELECT
                    {group_cols},
                    COUNT(*)::BIGINT AS candidate_count,
                    MIN(y_loss) AS min_y_loss,
                    MAX(y_loss) AS max_y_loss,
                    AVG(y_loss) AS mean_y_loss
                FROM candidates
                GROUP BY {group_cols}
            ),
            optimal AS (
                SELECT
                    {", ".join(f"c.{col}" for col in DECISION_GROUP_COLUMNS)},
                    COUNT(*)::BIGINT AS tie_count,
                    MIN(CAST(c.candidate_page_id AS VARCHAR)) AS best_candidate_page_id
                FROM candidates c
                INNER JOIN agg a
                    ON {" AND ".join(f"c.{col} = a.{col}" for col in DECISION_GROUP_COLUMNS)}
                    AND c.y_loss = a.min_y_loss
                GROUP BY {", ".join(f"c.{col}" for col in DECISION_GROUP_COLUMNS)}
            )
            SELECT
                {", ".join(f"a.{col}" for col in DECISION_GROUP_COLUMNS)},
                a.candidate_count,
                a.min_y_loss,
                a.max_y_loss,
                a.mean_y_loss,
                o.tie_count,
                o.best_candidate_page_id
            FROM agg a
            INNER JOIN optimal o
                ON {join_predicates}
            ORDER BY {group_cols}
        )
        TO {decision_view_path.as_posix()!r} (FORMAT PARQUET)
        """
    )
    return int(
        con.execute(f"SELECT COUNT(*) FROM read_parquet({decision_view_path.as_posix()!r})").fetchone()[0]
    )


def _build_pairwise_sample(
    con,
    *,
    pairwise_sample_path: Path,
    max_pairwise_rows: int,
    max_pairs_per_decision: int,
    pairwise_seed: int,
) -> int:
    ensure_parent(pairwise_sample_path)
    group_cols = DECISION_GROUP_COLUMNS
    group_list = ", ".join(group_cols)
    join_same_decision = " AND ".join(f"a.{col} = b.{col}" for col in group_cols)
    con.execute(
        f"""
        COPY (
            WITH decision_keys AS (
                SELECT DISTINCT {group_list}
                FROM candidates
            ),
            sampled_decisions AS (
                SELECT *
                FROM decision_keys
                ORDER BY hash(concat_ws('|', {group_list}, {str(pairwise_seed)!r}))
                LIMIT (
                    SELECT GREATEST(
                        1,
                        CAST(CEIL({max_pairwise_rows}::DOUBLE / GREATEST({max_pairs_per_decision}, 1)) AS BIGINT)
                    )
                )
            ),
            pairs AS (
                SELECT
                    {", ".join(f"a.{col}" for col in group_cols)},
                    CAST(a.candidate_page_id AS VARCHAR) AS candidate_a_page_id,
                    CAST(b.candidate_page_id AS VARCHAR) AS candidate_b_page_id,
                    a.y_loss AS y_loss_a,
                    b.y_loss AS y_loss_b,
                    (a.y_loss - b.y_loss) AS y_loss_diff_a_minus_b,
                    CASE WHEN a.y_loss < b.y_loss THEN 1 ELSE 0 END AS label_a_better,
                    CASE WHEN b.y_loss < a.y_loss THEN 1 ELSE 0 END AS label_b_better,
                    CASE WHEN a.y_loss = b.y_loss THEN 1 ELSE 0 END AS is_tie,
                    row_number() OVER (
                        PARTITION BY {", ".join(f"a.{col}" for col in group_cols)}
                        ORDER BY CAST(a.candidate_page_id AS VARCHAR), CAST(b.candidate_page_id AS VARCHAR)
                    ) AS pair_rank_in_decision
                FROM candidates a
                INNER JOIN candidates b
                    ON {join_same_decision}
                    AND CAST(a.candidate_page_id AS VARCHAR) < CAST(b.candidate_page_id AS VARCHAR)
                INNER JOIN sampled_decisions d
                    ON {" AND ".join(f"a.{col} = d.{col}" for col in group_cols)}
            )
            SELECT
                {group_list},
                candidate_a_page_id,
                candidate_b_page_id,
                y_loss_a,
                y_loss_b,
                y_loss_diff_a_minus_b,
                label_a_better,
                label_b_better,
                is_tie
            FROM pairs
            WHERE pair_rank_in_decision <= {max_pairs_per_decision}
            ORDER BY {group_list}, candidate_a_page_id, candidate_b_page_id
            LIMIT {max_pairwise_rows}
        )
        TO {pairwise_sample_path.as_posix()!r} (FORMAT PARQUET)
        """
    )
    count = con.execute(f"SELECT COUNT(*) FROM read_parquet({pairwise_sample_path.as_posix()!r})").fetchone()[0]
    return int(count)


def _count_candidate_rows(con) -> int:
    return int(con.execute("SELECT COUNT(*) FROM candidates").fetchone()[0])


def _count_rows_by_column(con, column: str) -> dict[str, int]:
    rows = con.execute(
        f"""
        SELECT CAST({column} AS VARCHAR) AS key, COUNT(*)::BIGINT AS row_count
        FROM candidates
        GROUP BY 1
        ORDER BY 1
        """
    ).fetchall()
    return {str(key): int(count) for key, count in rows}


def _collect_candidate_inventory(candidate_root: Path, *, release_root: Path) -> list[dict[str, object]]:
    inventory: list[dict[str, object]] = []
    for parquet_path in sorted(candidate_root.rglob("candidate_rows.parquet")):
        relative = parquet_path.resolve().relative_to(release_root.resolve())
        parts = {segment.split("=", 1)[0]: segment.split("=", 1)[1] for segment in relative.parts if "=" in segment}
        row_count = int(
            _require_duckdb()
            .connect()
            .execute(f"SELECT COUNT(*) FROM read_parquet({parquet_path.as_posix()!r})")
            .fetchone()[0]
        )
        inventory.append(
            {
                "path": relative.as_posix(),
                "row_count": row_count,
                "sha256": sha256_file(parquet_path),
                "split": parts.get("split"),
                "trace_family": parts.get("trace_family"),
                "capacity": int(parts["capacity"]) if "capacity" in parts else None,
                "horizon": int(parts["horizon"]) if "horizon" in parts else None,
            }
        )
    return inventory


def _checksum_lines(root: Path, checksum_output_path: Path) -> list[str]:
    lines: list[str] = []
    for file_path in iter_files(root):
        if file_path.resolve() == checksum_output_path.resolve():
            continue
        rel = file_path.resolve().relative_to(root.resolve())
        lines.append(f"{sha256_file(file_path)}  {rel.as_posix()}")
    return lines


def _copy_governance_artifacts(
    *,
    repo_root: Path,
    metadata_dir: Path,
    family_selection_path: Path,
) -> list[str]:
    copied: list[str] = []
    registry_src = repo_root / "manifests" / "source_family_registry.yaml"
    selection_dst = metadata_dir / Path(family_selection_path).name
    registry_dst = metadata_dir / "source_family_registry.yaml"
    shutil.copy2(family_selection_path, selection_dst)
    copied.append(str(selection_dst.relative_to(metadata_dir.parent)))
    if registry_src.exists():
        shutil.copy2(registry_src, registry_dst)
        copied.append(str(registry_dst.relative_to(metadata_dir.parent)))
    return copied


def _write_release_readme(
    *,
    output_path: Path,
    dataset_id: str,
    selected_families: tuple[str, ...],
    excluded_families: tuple[str, ...],
    pairwise_sample_enabled: bool,
) -> None:
    pairwise_note = (
        "A capped pairwise sample is included under `data/pairwise_sample/`."
        if pairwise_sample_enabled
        else "Full pairwise materialization is intentionally omitted from the default real release."
    )
    text = "\n".join(
        [
            f"# {dataset_id}",
            "",
            "Real public LAFC-Evict release built from generated candidate rows.",
            "",
            f"- Dataset ID: `{dataset_id}`",
            "- Version: `0.1`",
            "- Release type: `real_public`",
            f"- Selected families: `{', '.join(selected_families)}`",
            f"- Excluded families: `{', '.join(excluded_families)}`",
            "",
            "This release contains generated counterfactual supervision labels and benchmark views only.",
            "Upstream raw traces are external source artifacts and are not redistributed here.",
            "",
            pairwise_note,
            "Pairwise tasks can also be derived on demand from candidate rows.",
            "Full pairwise materialization is intentionally not part of the default real release because it can grow quadratically with decision size.",
        ]
    )
    ensure_parent(output_path).write_text(text + "\n", encoding="utf-8")


def _write_validation_report(
    *,
    output_path: Path,
    release_root: Path,
    source_manifest: Path,
    candidate_row_count: int,
    decision_row_count: int,
    pairwise_sample_row_count: int | None,
    validation_errors: list[str],
) -> None:
    status = "passed" if not validation_errors else "failed"
    lines = [
        "# Validation Report",
        "",
        f"- Release root: `{release_root}`",
        f"- Source manifest: `{source_manifest}`",
        f"- Validation result: {status}",
        f"- Candidate row count: {candidate_row_count}",
        f"- Decision row count: {decision_row_count}",
        f"- Pairwise sample row count: {pairwise_sample_row_count if pairwise_sample_row_count is not None else 'n/a'}",
        "",
    ]
    if validation_errors:
        lines.extend(["## Validation errors", "", *[f"- {error}" for error in validation_errors], ""])
    ensure_parent(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_real_release(
    *,
    input_manifest: str | Path,
    family_selection: str | Path,
    output_dir: str | Path,
    dataset_id: str,
    repo_root: str | Path | None = None,
    dry_run: bool = True,
    overwrite: bool = False,
    skip_disk_space_check: bool = False,
    pairwise_sample: bool = False,
    max_pairwise_rows: int = 1_000_000,
    max_pairs_per_decision: int = 8,
    pairwise_seed: int = 7,
    blocked_families: set[str] | None = None,
) -> RealReleaseBuildResult:
    manifest_path = Path(input_manifest).expanduser().resolve()
    family_selection_path = Path(family_selection).expanduser().resolve()
    release_root = Path(output_dir).expanduser().resolve()
    repo_root_path = Path(repo_root).expanduser().resolve() if repo_root else Path(__file__).resolve().parents[2]
    blocked = blocked_families or set(DEFAULT_BLOCKED_FAMILIES)

    selected_families, excluded_families = load_family_selection(family_selection_path)
    selected_set = set(selected_families)
    excluded_set = set(excluded_families)
    _validate_family_governance(
        selected_families=selected_set,
        excluded_families=excluded_set,
        blocked_families=blocked,
    )

    summary = summarize_candidate_source(
        manifest_path,
        include_families=selected_set,
        exclude_families=excluded_set,
        blocked_families=blocked,
    )
    if summary.missing_selected_families:
        raise ValueError(
            "Missing selected families in source manifest: "
            + ", ".join(summary.missing_selected_families)
        )

    build_command = build_real_release_cli_command(
        input_manifest=manifest_path,
        family_selection=family_selection_path,
        output_dir=release_root,
        dataset_id=dataset_id,
        dry_run=False,
        overwrite=True,
        skip_disk_space_check=skip_disk_space_check,
        pairwise_sample=pairwise_sample,
        max_pairwise_rows=max_pairwise_rows,
        max_pairs_per_decision=max_pairs_per_decision,
        pairwise_seed=pairwise_seed,
    )

    disk_passed: bool | None = None
    disk_free: int | None = None
    disk_required: int | None = None
    if not dry_run:
        disk_passed, disk_free, disk_required = check_disk_space(
            release_root,
            required_bytes=summary.total_bytes_selected,
        )
        if not skip_disk_space_check and not disk_passed:
            raise OSError(
                "Insufficient disk space for real release build. "
                f"Free bytes: {disk_free}, required bytes (>{DISK_SPACE_MULTIPLIER}x input): {disk_required}. "
                "Pass --skip-disk-space-check to override."
            )

    if dry_run:
        return RealReleaseBuildResult(
            release_root=release_root,
            dry_run=True,
            dataset_id=dataset_id,
            selected_families=selected_families,
            excluded_families=excluded_families,
            candidate_row_count=summary.estimated_rows_selected,
            decision_row_count=summary.estimated_decisions_selected,
            pairwise_sample_row_count=0 if pairwise_sample else None,
            total_bytes=summary.total_bytes_selected,
            disk_space_check_passed=disk_passed,
            disk_space_free_bytes=disk_free,
            disk_space_required_bytes=disk_required,
            build_command=build_command,
            manifest_path=None,
            warnings=summary.warnings,
        )

    shard_paths = _selected_shard_paths(
        manifest_path,
        selected_families=selected_set,
        excluded_families=excluded_set,
        blocked_families=blocked,
    )

    release_root = ensure_clean_output_dir(release_root, overwrite=overwrite, kind="Real release output directory")
    data_dir = release_root / "data"
    metadata_dir = release_root / "metadata"
    candidate_root = data_dir / "candidate_rows"
    decision_view_path = data_dir / "decision_view" / "decision_view.parquet"
    pairwise_sample_path = data_dir / "pairwise_sample" / "pairwise_sample.parquet"
    manifest_path_out = metadata_dir / "release_manifest.json"
    checksums_path = metadata_dir / "checksums.sha256"
    validation_report_path = metadata_dir / "validation_report.md"
    readme_path = release_root / "README.md"

    for output_path, kind in [
        (manifest_path_out, "Release manifest"),
        (checksums_path, "Checksum output"),
        (validation_report_path, "Validation report"),
        (readme_path, "Release README"),
    ]:
        fail_if_output_exists(output_path, overwrite=overwrite, kind=kind)

    metadata_dir.mkdir(parents=True, exist_ok=True)
    governance_files = _copy_governance_artifacts(
        repo_root=repo_root_path,
        metadata_dir=metadata_dir,
        family_selection_path=family_selection_path,
    )

    con = _duckdb_connect()
    try:
        _register_candidate_shards(con, shard_paths)
        present_families = {
            str(row[0])
            for row in con.execute("SELECT DISTINCT trace_family FROM candidates").fetchall()
        }
        blocked_in_output = present_families & blocked
        if blocked_in_output:
            raise ValueError(
                "Blocked families would be included in release output: "
                + ", ".join(sorted(blocked_in_output))
            )
        unexpected = present_families - selected_set
        if unexpected:
            raise ValueError(
                "Unexpected trace families in filtered candidate rows: " + ", ".join(sorted(unexpected))
            )

        _export_partitioned_candidates(con, candidate_root=candidate_root, overwrite=overwrite)
        _register_candidate_partitions(con, candidate_root)
        candidate_row_count = _count_candidate_rows(con)
        decision_row_count = _build_decision_view(con, decision_view_path=decision_view_path)
        pairwise_sample_row_count: int | None = None
        if pairwise_sample:
            pairwise_sample_row_count = _build_pairwise_sample(
                con,
                pairwise_sample_path=pairwise_sample_path,
                max_pairwise_rows=max_pairwise_rows,
                max_pairs_per_decision=max_pairs_per_decision,
                pairwise_seed=pairwise_seed,
            )

        row_counts_by_split = _count_rows_by_column(con, "split")
        row_counts_by_trace_family = _count_rows_by_column(con, "trace_family")
        row_counts_by_capacity = _count_rows_by_column(con, "capacity")
        row_counts_by_horizon = _count_rows_by_column(con, "horizon")
    finally:
        con.close()

    candidate_inventory = _collect_candidate_inventory(candidate_root, release_root=release_root)

    _write_release_readme(
        output_path=readme_path,
        dataset_id=dataset_id,
        selected_families=selected_families,
        excluded_families=excluded_families,
        pairwise_sample_enabled=pairwise_sample,
    )

    from .real_release_validation import validate_real_release

    validation_errors = validate_real_release(
        release_root,
        require_manifest=False,
        selected_families=selected_set,
    )
    _write_validation_report(
        output_path=validation_report_path,
        release_root=release_root,
        source_manifest=manifest_path,
        candidate_row_count=candidate_row_count,
        decision_row_count=decision_row_count,
        pairwise_sample_row_count=pairwise_sample_row_count,
        validation_errors=validation_errors,
    )
    if validation_errors:
        raise ValueError("Real release validation failed:\n" + "\n".join(validation_errors))

    generated_files = sorted(
        str(path.relative_to(release_root))
        for path in iter_files(release_root)
        if path.is_file()
    )
    total_bytes = sum(path.stat().st_size for path in iter_files(release_root) if path.is_file())

    build_timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    manifest = {
        "dataset_id": dataset_id,
        "version": "0.1",
        "release_name": dataset_id,
        "release_type": "real_public",
        "schema_version": SCHEMA_VERSION,
        "source_manifest": str(manifest_path),
        "family_selection_manifest": str(family_selection_path),
        "selected_families": list(selected_families),
        "excluded_families": list(excluded_families),
        "blocked_families_absent": True,
        "candidate_row_count": candidate_row_count,
        "decision_row_count": decision_row_count,
        "pairwise_sample_row_count": pairwise_sample_row_count,
        "row_counts_by_split": row_counts_by_split,
        "row_counts_by_trace_family": row_counts_by_trace_family,
        "row_counts_by_capacity": row_counts_by_capacity,
        "row_counts_by_horizon": row_counts_by_horizon,
        "file_inventory": generated_files,
        "candidate_partitions": candidate_inventory,
        "governance_files": governance_files,
        "total_bytes": total_bytes,
        "build_command": build_command,
        "build_timestamp": build_timestamp,
        "pairwise_sample": {
            "enabled": pairwise_sample,
            "max_pairwise_rows": max_pairwise_rows if pairwise_sample else None,
            "max_pairs_per_decision": max_pairs_per_decision if pairwise_sample else None,
            "pairwise_seed": pairwise_seed if pairwise_sample else None,
            "note": (
                "Full pairwise materialization is intentionally omitted from the default real release "
                "because it can grow quadratically with decision size."
            ),
        },
    }
    ensure_parent(manifest_path_out).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    checksum_lines = _checksum_lines(release_root, checksums_path)
    ensure_parent(checksums_path).write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")

    final_errors = validate_real_release(release_root, require_manifest=True)
    if final_errors:
        raise ValueError("Real release validation failed after manifest write:\n" + "\n".join(final_errors))

    return RealReleaseBuildResult(
        release_root=release_root,
        dry_run=False,
        dataset_id=dataset_id,
        selected_families=selected_families,
        excluded_families=excluded_families,
        candidate_row_count=candidate_row_count,
        decision_row_count=decision_row_count,
        pairwise_sample_row_count=pairwise_sample_row_count,
        total_bytes=total_bytes,
        disk_space_check_passed=disk_passed,
        disk_space_free_bytes=disk_free,
        disk_space_required_bytes=disk_required,
        build_command=build_command,
        manifest_path=manifest_path_out,
        warnings=summary.warnings,
    )


def dry_run_real_release(
    *,
    input_manifest: str | Path,
    family_selection: str | Path,
    output_dir: str | Path,
    dataset_id: str,
    skip_disk_space_check: bool = False,
    pairwise_sample: bool = False,
) -> dict[str, object]:
    result = build_real_release(
        input_manifest=input_manifest,
        family_selection=family_selection,
        output_dir=output_dir,
        dataset_id=dataset_id,
        dry_run=True,
        skip_disk_space_check=skip_disk_space_check,
        pairwise_sample=pairwise_sample,
    )
    disk_passed, disk_free, disk_required = check_disk_space(
        result.release_root,
        required_bytes=result.total_bytes or 0,
    )
    return {
        "mode": "dry_run",
        "dataset_id": result.dataset_id,
        "input_manifest": str(Path(input_manifest).expanduser().resolve()),
        "family_selection": str(Path(family_selection).expanduser().resolve()),
        "output_dir": str(result.release_root),
        "selected_families": list(result.selected_families),
        "excluded_families": list(result.excluded_families),
        "estimated_candidate_rows": result.candidate_row_count,
        "estimated_decision_rows": result.decision_row_count,
        "estimated_input_bytes": result.total_bytes,
        "pairwise_sample_enabled": pairwise_sample,
        "disk_space_check_passed": disk_passed if not skip_disk_space_check else None,
        "disk_space_free_bytes": disk_free,
        "disk_space_required_bytes": disk_required,
        "build_command": result.build_command,
        "warnings": list(result.warnings),
    }
