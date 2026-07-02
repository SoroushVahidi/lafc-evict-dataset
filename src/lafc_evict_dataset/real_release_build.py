from __future__ import annotations

import json
import shlex
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

from .io import ensure_parent, fail_if_output_exists, iter_files, sha256_file
from .real_release import (
    DEFAULT_BLOCKED_FAMILIES,
    infer_trace_family_from_path,
    load_family_selection,
    summarize_candidate_source,
)
from .release_metadata import collect_release_file_inventory
from .schema import CANONICAL_COLUMNS, DECISION_METADATA_COLUMNS, SCHEMA_VERSION

DISK_SPACE_MULTIPLIER: Final[float] = 2.0
DECISION_GROUP_COLUMNS: Final[tuple[str, ...]] = tuple(DECISION_METADATA_COLUMNS)
# Version tag mixed into the pairwise A/B orientation hash below. Bump this
# (and the string) if the orientation algorithm ever changes, so that old and
# new pairwise samples are distinguishable by their "orientation_method".
PAIRWISE_ORIENTATION_METHOD: Final[str] = "deterministic_hash_v1"
DEFAULT_DUCKDB_THREADS: Final[int] = 2
DEFAULT_DUCKDB_MEMORY_LIMIT: Final[str] = "8GB"
DEFAULT_DUCKDB_TEMP_DIR: Final[str] = ".duckdb_tmp"
REAL_RELEASE_STAGE_ORDER: Final[tuple[str, ...]] = (
    "candidate_rows",
    "decision_view",
    "pairwise_sample",
    "metadata",
    "checksums",
    "validate",
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
    duckdb_threads: int = DEFAULT_DUCKDB_THREADS,
    duckdb_memory_limit: str = DEFAULT_DUCKDB_MEMORY_LIMIT,
    duckdb_temp_dir: str | Path = DEFAULT_DUCKDB_TEMP_DIR,
    stages: tuple[str, ...] | None = None,
    resume: bool = False,
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
        "--duckdb-threads",
        str(duckdb_threads),
        "--duckdb-memory-limit",
        str(duckdb_memory_limit),
        "--duckdb-temp-dir",
        str(Path(duckdb_temp_dir)),
    ]
    if dry_run:
        parts.append("--dry-run")
    if overwrite:
        parts.append("--overwrite")
    if resume:
        parts.append("--resume")
    if skip_disk_space_check:
        parts.append("--skip-disk-space-check")
    if stages:
        for stage in stages:
            parts.extend(["--stage", stage])
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


def _log_progress(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


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


def _apply_duckdb_resource_limits(
    con,
    *,
    duckdb_threads: int,
    duckdb_memory_limit: str,
    duckdb_temp_dir: str | Path,
) -> Path:
    temp_dir = Path(duckdb_temp_dir).expanduser().resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)
    con.execute(f"PRAGMA threads={int(duckdb_threads)}")
    con.execute(f"PRAGMA memory_limit={duckdb_memory_limit!r}")
    con.execute(f"PRAGMA temp_directory={temp_dir.as_posix()!r}")
    # Final release outputs are explicitly ordered, so preserving insertion order only adds memory pressure.
    con.execute("SET preserve_insertion_order=false")
    return temp_dir


def _duckdb_connect(
    *,
    duckdb_threads: int = DEFAULT_DUCKDB_THREADS,
    duckdb_memory_limit: str = DEFAULT_DUCKDB_MEMORY_LIMIT,
    duckdb_temp_dir: str | Path = DEFAULT_DUCKDB_TEMP_DIR,
):
    duckdb = _require_duckdb()
    con = duckdb.connect()
    _apply_duckdb_resource_limits(
        con,
        duckdb_threads=duckdb_threads,
        duckdb_memory_limit=duckdb_memory_limit,
        duckdb_temp_dir=duckdb_temp_dir,
    )
    return con


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


def _build_decision_view(con, *, candidate_root: Path, decision_view_path: Path) -> int:
    group_cols = ", ".join(DECISION_GROUP_COLUMNS)
    join_cols = " AND ".join(f"c.{column} = m.{column}" for column in DECISION_GROUP_COLUMNS)
    partition_paths = sorted(candidate_root.rglob("candidate_rows.parquet"))
    if not partition_paths:
        raise FileNotFoundError(f"No candidate_rows.parquet partitions under {candidate_root}")
    ensure_parent(decision_view_path)
    temp_dir = decision_view_path.parent / "_decision_view_parts"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    try:
        for index, partition_path in enumerate(partition_paths):
            part_path = temp_dir / f"part-{index:05d}.parquet"
            con.execute(
                f"""
                COPY (
                    WITH partition_candidates AS (
                        SELECT * FROM read_parquet({partition_path.as_posix()!r})
                    ),
                    minima AS (
                        SELECT
                            {group_cols},
                            COUNT(*)::BIGINT AS candidate_count,
                            MIN(y_loss) AS min_y_loss,
                            MAX(y_value) AS max_y_value
                        FROM partition_candidates
                        GROUP BY {group_cols}
                    ),
                    summarized AS (
                        SELECT
                            {", ".join(f"m.{column}" for column in DECISION_GROUP_COLUMNS)},
                            m.candidate_count,
                            m.min_y_loss,
                            m.max_y_value,
                            string_agg(
                                CAST(c.candidate_page_id AS VARCHAR),
                                '|'
                                ORDER BY CAST(c.candidate_page_id AS VARCHAR)
                            ) FILTER (WHERE c.y_loss = m.min_y_loss) AS optimal_candidate_page_ids,
                            COUNT(*) FILTER (WHERE c.y_loss = m.min_y_loss)::BIGINT AS optimal_candidate_count,
                            COUNT(*) FILTER (WHERE c.y_loss = m.min_y_loss)::BIGINT AS tie_count,
                            AVG(c.y_loss - m.min_y_loss) AS regret_mean,
                            STDDEV_POP(c.y_loss - m.min_y_loss) AS regret_std,
                            MAX(c.y_loss - m.min_y_loss) AS regret_max,
                            SUM(c.y_loss - m.min_y_loss) AS regret_sum
                        FROM partition_candidates c
                        INNER JOIN minima m
                            ON {join_cols}
                        GROUP BY
                            {", ".join(f"m.{column}" for column in DECISION_GROUP_COLUMNS)},
                            m.candidate_count,
                            m.min_y_loss,
                            m.max_y_value
                    )
                    SELECT
                        {group_cols},
                        candidate_count,
                        min_y_loss,
                        max_y_value,
                        optimal_candidate_page_ids,
                        optimal_candidate_count,
                        tie_count,
                        regret_mean,
                        regret_std,
                        regret_max,
                        regret_sum
                    FROM summarized
                    ORDER BY {group_cols}
                )
                TO {part_path.as_posix()!r} (FORMAT PARQUET)
                """
            )

        con.execute(
            f"""
            COPY (
                SELECT *
                FROM read_parquet({_sql_string_list([str(path) for path in sorted(temp_dir.glob('*.parquet'))])})
                ORDER BY {group_cols}
            )
            TO {decision_view_path.as_posix()!r} (FORMAT PARQUET)
            """
        )
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    return int(
        con.execute(f"SELECT COUNT(*) FROM read_parquet({decision_view_path.as_posix()!r})").fetchone()[0]
    )


def _build_row_counts(
    *,
    candidate_row_count: int,
    decision_row_count: int,
    pairwise_sample_row_count: int | None,
) -> dict[str, int]:
    row_counts = {
        "candidate_rows": candidate_row_count,
        "decision_view": decision_row_count,
    }
    if pairwise_sample_row_count is not None:
        row_counts["pairwise_sample"] = pairwise_sample_row_count
    return row_counts


def _build_pairwise_sample(
    con,
    *,
    pairwise_sample_path: Path,
    max_pairwise_rows: int,
    max_pairs_per_decision: int,
    pairwise_seed: int,
) -> int:
    """Build the capped pairwise sample.

    Candidate pairs within a decision are first enumerated as an unordered
    pair via a lexicographic join (candidate_id_low < candidate_id_high) --
    this is only used to enumerate each unordered pair exactly once and to
    rank/cap pairs per decision deterministically. The final A/B orientation
    exposed in candidate_a_page_id/candidate_b_page_id is decided separately
    by a deterministic hash over stable decision + pair-identity fields
    (PAIRWISE_ORIENTATION_METHOD), so which candidate lands in slot A is not
    systematically correlated with candidate_page_id ordering.
    """
    ensure_parent(pairwise_sample_path)
    group_cols = DECISION_GROUP_COLUMNS
    group_list = ", ".join(group_cols)
    join_same_decision = " AND ".join(f"a.{col} = b.{col}" for col in group_cols)
    # NOTE: this expression is evaluated against the `pairs` CTE (aliased as
    # `oriented`), whose columns are plain names (trace_name, capacity, ...),
    # not table-qualified -- unlike join_same_decision above, which runs
    # against the raw `candidates a`/`candidates b` join.
    orientation_hash_expr = (
        "hash(concat_ws('|', "
        + ", ".join(f"CAST({col} AS VARCHAR)" for col in group_cols)
        + ", candidate_id_low, candidate_id_high, "
        + f"{PAIRWISE_ORIENTATION_METHOD!r}))"
    )
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
                    CAST(a.candidate_page_id AS VARCHAR) AS candidate_id_low,
                    CAST(b.candidate_page_id AS VARCHAR) AS candidate_id_high,
                    a.y_loss AS y_loss_low,
                    b.y_loss AS y_loss_high,
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
            ),
            oriented AS (
                SELECT
                    *,
                    ({orientation_hash_expr} % 2 = 1) AS swap_orientation
                FROM pairs
            )
            SELECT
                {group_list},
                CASE WHEN swap_orientation THEN candidate_id_high ELSE candidate_id_low END AS candidate_a_page_id,
                CASE WHEN swap_orientation THEN candidate_id_low ELSE candidate_id_high END AS candidate_b_page_id,
                CASE WHEN swap_orientation THEN y_loss_high ELSE y_loss_low END AS y_loss_a,
                CASE WHEN swap_orientation THEN y_loss_low ELSE y_loss_high END AS y_loss_b,
                (
                    CASE WHEN swap_orientation THEN y_loss_high ELSE y_loss_low END
                    - CASE WHEN swap_orientation THEN y_loss_low ELSE y_loss_high END
                ) AS y_loss_diff_a_minus_b,
                CASE
                    WHEN swap_orientation THEN CASE WHEN y_loss_high < y_loss_low THEN 1 ELSE 0 END
                    ELSE CASE WHEN y_loss_low < y_loss_high THEN 1 ELSE 0 END
                END AS label_a_better,
                CASE
                    WHEN swap_orientation THEN CASE WHEN y_loss_low < y_loss_high THEN 1 ELSE 0 END
                    ELSE CASE WHEN y_loss_high < y_loss_low THEN 1 ELSE 0 END
                END AS label_b_better,
                CASE WHEN y_loss_low = y_loss_high THEN 1 ELSE 0 END AS is_tie
            FROM oriented
            WHERE pair_rank_in_decision <= {max_pairs_per_decision}
            ORDER BY {group_list}, candidate_id_low, candidate_id_high
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


def _count_parquet_rows(parquet_path: Path) -> int:
    return int(
        _require_duckdb()
        .connect()
        .execute(f"SELECT COUNT(*) FROM read_parquet({parquet_path.as_posix()!r})")
        .fetchone()[0]
    )


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


def _governance_output_paths(
    *,
    repo_root: Path,
    metadata_dir: Path,
    family_selection_path: Path,
) -> list[Path]:
    paths = [metadata_dir / Path(family_selection_path).name]
    if (repo_root / "manifests" / "source_family_registry.yaml").exists():
        paths.append(metadata_dir / "source_family_registry.yaml")
    return paths


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


def _non_empty_file(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def _candidate_rows_stage_complete(candidate_root: Path) -> bool:
    return any(path.stat().st_size > 0 for path in candidate_root.rglob("candidate_rows.parquet"))


def _metadata_stage_complete(
    *,
    manifest_path: Path,
    validation_report_path: Path,
    readme_path: Path,
    governance_paths: list[Path],
) -> bool:
    required_paths = [manifest_path, validation_report_path, readme_path, *governance_paths]
    return all(_non_empty_file(path) for path in required_paths)


def _validate_stage_complete(
    *,
    manifest_path: Path,
    checksums_path: Path,
    validation_report_path: Path,
) -> bool:
    return all(_non_empty_file(path) for path in (manifest_path, checksums_path, validation_report_path))


def _normalize_stage_selection(
    stages: tuple[str, ...] | list[str] | None,
    *,
    pairwise_sample: bool,
) -> tuple[str, ...]:
    if stages:
        ordered = tuple(dict.fromkeys(stages))
    else:
        ordered_list = ["candidate_rows", "decision_view"]
        if pairwise_sample:
            ordered_list.append("pairwise_sample")
        ordered_list.extend(["metadata", "checksums", "validate"])
        ordered = tuple(ordered_list)
    unknown = sorted(set(ordered) - set(REAL_RELEASE_STAGE_ORDER))
    if unknown:
        raise ValueError("Unknown real release stage(s): " + ", ".join(unknown))
    if "pairwise_sample" in ordered and not pairwise_sample:
        raise ValueError("The pairwise_sample stage requires --pairwise-sample.")
    return ordered


def _summarize_release_outputs(
    *,
    release_root: Path,
    candidate_root: Path,
    decision_view_path: Path,
    pairwise_sample_path: Path,
    duckdb_threads: int,
    duckdb_memory_limit: str,
    duckdb_temp_dir: str | Path,
) -> tuple[int | None, int | None, int | None, int | None]:
    candidate_row_count: int | None = None
    if _candidate_rows_stage_complete(candidate_root):
        con = _duckdb_connect(
            duckdb_threads=duckdb_threads,
            duckdb_memory_limit=duckdb_memory_limit,
            duckdb_temp_dir=duckdb_temp_dir,
        )
        try:
            _register_candidate_partitions(con, candidate_root)
            candidate_row_count = _count_candidate_rows(con)
        finally:
            con.close()
    decision_row_count = _count_parquet_rows(decision_view_path) if _non_empty_file(decision_view_path) else None
    pairwise_sample_row_count = (
        _count_parquet_rows(pairwise_sample_path) if _non_empty_file(pairwise_sample_path) else None
    )
    total_bytes = sum(path.stat().st_size for path in iter_files(release_root) if path.is_file()) if release_root.exists() else 0
    return candidate_row_count, decision_row_count, pairwise_sample_row_count, total_bytes


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
    duckdb_threads: int = DEFAULT_DUCKDB_THREADS,
    duckdb_memory_limit: str = DEFAULT_DUCKDB_MEMORY_LIMIT,
    duckdb_temp_dir: str | Path = DEFAULT_DUCKDB_TEMP_DIR,
    stages: tuple[str, ...] | list[str] | None = None,
    resume: bool = False,
    blocked_families: set[str] | None = None,
) -> RealReleaseBuildResult:
    manifest_path = Path(input_manifest).expanduser().resolve()
    family_selection_path = Path(family_selection).expanduser().resolve()
    release_root = Path(output_dir).expanduser().resolve()
    repo_root_path = Path(repo_root).expanduser().resolve() if repo_root else Path(__file__).resolve().parents[2]
    blocked = blocked_families or set(DEFAULT_BLOCKED_FAMILIES)
    selected_stages = _normalize_stage_selection(stages, pairwise_sample=pairwise_sample)

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
        overwrite=overwrite or dry_run,
        skip_disk_space_check=skip_disk_space_check,
        pairwise_sample=pairwise_sample,
        max_pairwise_rows=max_pairwise_rows,
        max_pairs_per_decision=max_pairs_per_decision,
        pairwise_seed=pairwise_seed,
        duckdb_threads=duckdb_threads,
        duckdb_memory_limit=duckdb_memory_limit,
        duckdb_temp_dir=duckdb_temp_dir,
        stages=selected_stages if stages else None,
        resume=resume,
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

    release_root.mkdir(parents=True, exist_ok=True)
    data_dir = release_root / "data"
    metadata_dir = release_root / "metadata"
    candidate_root = data_dir / "candidate_rows"
    decision_view_path = data_dir / "decision_view" / "decision_view.parquet"
    pairwise_sample_path = data_dir / "pairwise_sample" / "pairwise_sample.parquet"
    manifest_path_out = metadata_dir / "release_manifest.json"
    checksums_path = metadata_dir / "checksums.sha256"
    validation_report_path = metadata_dir / "validation_report.md"
    readme_path = release_root / "README.md"
    governance_paths = _governance_output_paths(
        repo_root=repo_root_path,
        metadata_dir=metadata_dir,
        family_selection_path=family_selection_path,
    )

    if "candidate_rows" in selected_stages:
        if resume and not overwrite and _candidate_rows_stage_complete(candidate_root):
            _log_progress("Skipping candidate_rows stage (existing non-empty outputs found)")
        else:
            if candidate_root.exists() and overwrite:
                shutil.rmtree(candidate_root)
            elif candidate_root.exists() and any(candidate_root.iterdir()) and not overwrite:
                raise FileExistsError(
                    f"Candidate rows directory already exists and is not empty: {candidate_root}. "
                    "Pass --overwrite to replace files or --resume to skip."
                )
            _log_progress("Starting candidate_rows stage")
            con = _duckdb_connect(
                duckdb_threads=duckdb_threads,
                duckdb_memory_limit=duckdb_memory_limit,
                duckdb_temp_dir=duckdb_temp_dir,
            )
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
            finally:
                con.close()
            _log_progress("Finished candidate_rows stage")

    if "decision_view" in selected_stages:
        if resume and not overwrite and _non_empty_file(decision_view_path):
            _log_progress("Skipping decision_view stage (existing non-empty outputs found)")
        else:
            if not _candidate_rows_stage_complete(candidate_root):
                raise FileNotFoundError(
                    "The decision_view stage requires emitted candidate_rows parquet partitions under "
                    f"{candidate_root}."
                )
            fail_if_output_exists(
                decision_view_path,
                overwrite=overwrite,
                kind="Decision view parquet",
            )
            if decision_view_path.exists() and overwrite:
                decision_view_path.unlink()
            _log_progress("Starting decision_view stage")
            con = _duckdb_connect(
                duckdb_threads=duckdb_threads,
                duckdb_memory_limit=duckdb_memory_limit,
                duckdb_temp_dir=duckdb_temp_dir,
            )
            try:
                _build_decision_view(con, candidate_root=candidate_root, decision_view_path=decision_view_path)
            finally:
                con.close()
            _log_progress("Finished decision_view stage")

    if "pairwise_sample" in selected_stages:
        if resume and not overwrite and _non_empty_file(pairwise_sample_path):
            _log_progress("Skipping pairwise_sample stage (existing non-empty outputs found)")
        else:
            if not _candidate_rows_stage_complete(candidate_root):
                raise FileNotFoundError(
                    "The pairwise_sample stage requires emitted candidate_rows parquet partitions under "
                    f"{candidate_root}."
                )
            fail_if_output_exists(
                pairwise_sample_path,
                overwrite=overwrite,
                kind="Pairwise sample parquet",
            )
            if pairwise_sample_path.exists() and overwrite:
                pairwise_sample_path.unlink()
            _log_progress("Starting pairwise_sample stage")
            con = _duckdb_connect(
                duckdb_threads=duckdb_threads,
                duckdb_memory_limit=duckdb_memory_limit,
                duckdb_temp_dir=duckdb_temp_dir,
            )
            try:
                _register_candidate_partitions(con, candidate_root)
                _build_pairwise_sample(
                    con,
                    pairwise_sample_path=pairwise_sample_path,
                    max_pairwise_rows=max_pairwise_rows,
                    max_pairs_per_decision=max_pairs_per_decision,
                    pairwise_seed=pairwise_seed,
                )
            finally:
                con.close()
            _log_progress("Finished pairwise_sample stage")

    if "metadata" in selected_stages:
        if resume and not overwrite and _metadata_stage_complete(
            manifest_path=manifest_path_out,
            validation_report_path=validation_report_path,
            readme_path=readme_path,
            governance_paths=governance_paths,
        ):
            _log_progress("Skipping metadata stage (existing non-empty outputs found)")
        else:
            if not _candidate_rows_stage_complete(candidate_root):
                raise FileNotFoundError(
                    f"The metadata stage requires emitted candidate_rows parquet partitions under {candidate_root}."
                )
            if not _non_empty_file(decision_view_path):
                raise FileNotFoundError(
                    "The metadata stage requires an emitted decision view parquet at "
                    f"{decision_view_path}."
                )
            if pairwise_sample and not _non_empty_file(pairwise_sample_path):
                raise FileNotFoundError(
                    "The metadata stage expected an emitted pairwise sample parquet at "
                    f"{pairwise_sample_path} because --pairwise-sample was requested."
                )
            for output_path, kind in [
                (manifest_path_out, "Release manifest"),
                (validation_report_path, "Validation report"),
                (readme_path, "Release README"),
            ]:
                fail_if_output_exists(output_path, overwrite=overwrite, kind=kind)
            for governance_path in governance_paths:
                fail_if_output_exists(governance_path, overwrite=overwrite, kind="Governance metadata")
            metadata_dir.mkdir(parents=True, exist_ok=True)
            _log_progress("Starting metadata stage")
            governance_files = _copy_governance_artifacts(
                repo_root=repo_root_path,
                metadata_dir=metadata_dir,
                family_selection_path=family_selection_path,
            )
            con = _duckdb_connect(
                duckdb_threads=duckdb_threads,
                duckdb_memory_limit=duckdb_memory_limit,
                duckdb_temp_dir=duckdb_temp_dir,
            )
            try:
                _register_candidate_partitions(con, candidate_root)
                candidate_row_count = _count_candidate_rows(con)
                row_counts_by_split = _count_rows_by_column(con, "split")
                row_counts_by_trace_family = _count_rows_by_column(con, "trace_family")
                row_counts_by_capacity = _count_rows_by_column(con, "capacity")
                row_counts_by_horizon = _count_rows_by_column(con, "horizon")
            finally:
                con.close()

            decision_row_count = _count_parquet_rows(decision_view_path)
            pairwise_sample_row_count = (
                _count_parquet_rows(pairwise_sample_path) if _non_empty_file(pairwise_sample_path) else None
            )
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

            generated_files = collect_release_file_inventory(
                release_root,
                include_paths=[manifest_path_out, checksums_path],
            )
            total_bytes = sum(path.stat().st_size for path in iter_files(release_root) if path.is_file())
            build_timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            row_counts = _build_row_counts(
                candidate_row_count=candidate_row_count,
                decision_row_count=decision_row_count,
                pairwise_sample_row_count=pairwise_sample_row_count,
            )
            # These source paths are local build provenance for the release artifact itself.
            # Public-facing bundle metadata intentionally does not copy machine-local absolute paths.
            manifest = {
                "dataset_name": dataset_id,
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
                "row_counts": row_counts,
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
                "duckdb": {
                    "threads": duckdb_threads,
                    "memory_limit": duckdb_memory_limit,
                    "temp_directory": str(Path(duckdb_temp_dir).expanduser().resolve()),
                },
                "pairwise_sample": {
                    "enabled": pairwise_sample,
                    "max_pairwise_rows": max_pairwise_rows if pairwise_sample else None,
                    "max_pairs_per_decision": max_pairs_per_decision if pairwise_sample else None,
                    "pairwise_seed": pairwise_seed if pairwise_sample else None,
                    "orientation_method": PAIRWISE_ORIENTATION_METHOD if pairwise_sample else None,
                    "note": (
                        "Full pairwise materialization is intentionally omitted from the default real release "
                        "because it can grow quadratically with decision size. Candidate A/B orientation within "
                        "each pair is assigned by a deterministic hash over stable decision and pair-identity "
                        "fields (see orientation_method), not by candidate_page_id ordering."
                    ),
                },
            }
            ensure_parent(manifest_path_out).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            _log_progress("Finished metadata stage")

    if "checksums" in selected_stages:
        if resume and not overwrite and _non_empty_file(checksums_path):
            _log_progress("Skipping checksums stage (existing non-empty outputs found)")
        else:
            fail_if_output_exists(checksums_path, overwrite=overwrite, kind="Checksum output")
            if checksums_path.exists() and overwrite:
                checksums_path.unlink()
            _log_progress("Starting checksums stage")
            checksum_lines = _checksum_lines(release_root, checksums_path)
            ensure_parent(checksums_path).write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
            _log_progress("Finished checksums stage")

    if "validate" in selected_stages:
        if resume and not overwrite and _validate_stage_complete(
            manifest_path=manifest_path_out,
            checksums_path=checksums_path,
            validation_report_path=validation_report_path,
        ):
            _log_progress("Skipping validate stage (existing non-empty outputs found)")
        else:
            _log_progress("Starting validate stage")
            from .real_release_validation import validate_real_release

            candidate_row_count, decision_row_count, pairwise_sample_row_count, _ = _summarize_release_outputs(
                release_root=release_root,
                candidate_root=candidate_root,
                decision_view_path=decision_view_path,
                pairwise_sample_path=pairwise_sample_path,
                duckdb_threads=duckdb_threads,
                duckdb_memory_limit=duckdb_memory_limit,
                duckdb_temp_dir=duckdb_temp_dir,
            )
            validation_errors = validate_real_release(
                release_root,
                require_manifest=True,
                selected_families=selected_set,
            )
            _write_validation_report(
                output_path=validation_report_path,
                release_root=release_root,
                source_manifest=manifest_path,
                candidate_row_count=candidate_row_count or 0,
                decision_row_count=decision_row_count or 0,
                pairwise_sample_row_count=pairwise_sample_row_count,
                validation_errors=validation_errors,
            )
            if validation_errors:
                raise ValueError("Real release validation failed:\n" + "\n".join(validation_errors))
            _log_progress("Finished validate stage")

    candidate_row_count, decision_row_count, pairwise_sample_row_count, total_bytes = _summarize_release_outputs(
        release_root=release_root,
        candidate_root=candidate_root,
        decision_view_path=decision_view_path,
        pairwise_sample_path=pairwise_sample_path,
        duckdb_threads=duckdb_threads,
        duckdb_memory_limit=duckdb_memory_limit,
        duckdb_temp_dir=duckdb_temp_dir,
    )

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
        manifest_path=manifest_path_out if manifest_path_out.exists() else None,
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
    duckdb_threads: int = DEFAULT_DUCKDB_THREADS,
    duckdb_memory_limit: str = DEFAULT_DUCKDB_MEMORY_LIMIT,
    duckdb_temp_dir: str | Path = DEFAULT_DUCKDB_TEMP_DIR,
    stages: tuple[str, ...] | list[str] | None = None,
    resume: bool = False,
) -> dict[str, object]:
    result = build_real_release(
        input_manifest=input_manifest,
        family_selection=family_selection,
        output_dir=output_dir,
        dataset_id=dataset_id,
        dry_run=True,
        skip_disk_space_check=skip_disk_space_check,
        pairwise_sample=pairwise_sample,
        duckdb_threads=duckdb_threads,
        duckdb_memory_limit=duckdb_memory_limit,
        duckdb_temp_dir=duckdb_temp_dir,
        stages=stages,
        resume=resume,
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
