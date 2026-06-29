from __future__ import annotations

import errno
import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

import pyarrow.parquet as pq

from .io import ensure_parent
from .real_release import DEFAULT_BLOCKED_FAMILIES
from .real_release_build import build_real_release
from .real_release_validation import _validate_checksums
from .schema import CANONICAL_COLUMNS

PAIRWISE_SAMPLE_COLUMNS: Final[tuple[str, ...]] = (
    "decision_id",
    "capacity",
    "horizon",
    "split",
    "trace_family",
    "trace_name",
    "candidate_a_page_id",
    "candidate_b_page_id",
    "y_loss_a",
    "y_loss_b",
    "y_loss_diff_a_minus_b",
    "label_a_better",
    "label_b_better",
    "is_tie",
)


@dataclass(frozen=True)
class RealReleaseMigrationResult:
    release_root: Path
    dataset_id: str
    source_release_root: Path
    candidate_row_count: int | None
    decision_row_count: int | None
    pairwise_sample_row_count: int | None
    candidate_rows_reused: bool
    candidate_rows_staging_mode: str
    pairwise_sample_reused: bool
    pairwise_sample_regenerated: bool
    pairwise_sample_staging_mode: str | None
    manifest_path: Path


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest_dataset_id(manifest: dict[str, object], *, release_root: Path) -> str:
    value = manifest.get("dataset_name") or manifest.get("dataset_id") or release_root.name
    return str(value)


def _pairwise_config(manifest: dict[str, object]) -> tuple[bool, int, int, int]:
    config = manifest.get("pairwise_sample", {})
    if not isinstance(config, dict):
        config = {}
    enabled = bool(config.get("enabled", (manifest.get("pairwise_sample_row_count") or 0) > 0))
    max_pairwise_rows = int(config.get("max_pairwise_rows") or 1_000_000)
    max_pairs_per_decision = int(config.get("max_pairs_per_decision") or 8)
    pairwise_seed = int(config.get("pairwise_seed") or 7)
    return enabled, max_pairwise_rows, max_pairs_per_decision, pairwise_seed


def _require_empty_output_dir(path: Path) -> None:
    if path.exists():
        if any(path.iterdir()):
            raise FileExistsError(f"Output directory already exists and is not empty: {path}")
    else:
        path.mkdir(parents=True, exist_ok=True)


def _candidate_partition_paths(candidate_root: Path) -> list[Path]:
    parquet_paths = sorted(candidate_root.rglob("candidate_rows.parquet"))
    if not parquet_paths:
        raise FileNotFoundError(f"No candidate_rows.parquet partitions found under {candidate_root}")
    return parquet_paths


def candidate_rows_are_canonical(candidate_root: str | Path) -> tuple[bool, list[str]]:
    root = Path(candidate_root).expanduser().resolve()
    errors: list[str] = []
    for parquet_path in _candidate_partition_paths(root):
        schema_names = pq.ParquetFile(parquet_path).schema_arrow.names
        missing = [column for column in CANONICAL_COLUMNS if column not in schema_names]
        if missing:
            errors.append(f"{parquet_path}: missing {', '.join(missing)}")
    return not errors, errors


def _pairwise_sample_is_compatible(pairwise_path: Path) -> bool:
    if not pairwise_path.exists():
        return False
    schema_names = pq.ParquetFile(pairwise_path).schema_arrow.names
    return all(column in schema_names for column in PAIRWISE_SAMPLE_COLUMNS)


def _stage_file(source_path: Path, target_path: Path, *, mode: str) -> str:
    ensure_parent(target_path)
    if mode == "copy":
        shutil.copy2(source_path, target_path)
        return "copy"
    if mode == "hardlink":
        os.link(source_path, target_path)
        return "hardlink"
    if mode != "auto":
        raise ValueError(f"Unsupported staging mode: {mode}")

    try:
        os.link(source_path, target_path)
        return "hardlink"
    except OSError as exc:
        if exc.errno not in {errno.EXDEV, errno.EPERM, errno.EMLINK, errno.ENOTSUP}:
            raise
    shutil.copy2(source_path, target_path)
    return "copy"


def _stage_tree(source_root: Path, target_root: Path, *, mode: str) -> str:
    methods_used: set[str] = set()
    for file_path in sorted(path for path in source_root.rglob("*") if path.is_file()):
        relative = file_path.relative_to(source_root)
        target_path = target_root / relative
        methods_used.add(_stage_file(file_path, target_path, mode=mode))
    if not methods_used:
        raise FileNotFoundError(f"No files found under {source_root}")
    return "+".join(sorted(methods_used))


def _write_migration_metadata(
    *,
    manifest_path: Path,
    source_release_root: Path,
    candidate_rows_staging_mode: str,
    pairwise_sample_reused: bool,
    pairwise_sample_regenerated: bool,
    pairwise_sample_staging_mode: str | None,
) -> None:
    manifest = _read_json(manifest_path)
    manifest["migration"] = {
        "source_release_directory": str(source_release_root),
        "decision_view_regenerated": True,
        "candidate_rows_reused": True,
        "candidate_rows_staging_mode": candidate_rows_staging_mode,
        "pairwise_sample_reused": pairwise_sample_reused,
        "pairwise_sample_regenerated": pairwise_sample_regenerated,
        "pairwise_sample_staging_mode": pairwise_sample_staging_mode,
        "migrated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def migrate_real_release_contract(
    *,
    source_release_dir: str | Path,
    output_dir: str | Path,
    repo_root: str | Path | None = None,
    staging_mode: str = "auto",
    reuse_existing_pairwise_sample: bool = True,
    duckdb_threads: int = 2,
    duckdb_memory_limit: str = "8GB",
    duckdb_temp_dir: str | Path = ".duckdb_tmp",
) -> RealReleaseMigrationResult:
    source_release_root = Path(source_release_dir).expanduser().resolve()
    release_manifest_path = source_release_root / "metadata" / "release_manifest.json"
    if not release_manifest_path.exists():
        raise FileNotFoundError(f"Missing source release manifest: {release_manifest_path}")

    source_checksum_errors = _validate_checksums(source_release_root)
    if source_checksum_errors:
        raise ValueError("Source release checksum validation failed:\n" + "\n".join(source_checksum_errors))

    source_manifest = _read_json(release_manifest_path)
    dataset_id = _manifest_dataset_id(source_manifest, release_root=source_release_root)
    source_input_manifest = Path(str(source_manifest["source_manifest"])).expanduser().resolve()
    family_selection_path = Path(str(source_manifest["family_selection_manifest"])).expanduser().resolve()
    if not source_input_manifest.exists():
        raise FileNotFoundError(f"Missing source candidate manifest referenced by release: {source_input_manifest}")
    if not family_selection_path.exists():
        raise FileNotFoundError(f"Missing family selection manifest referenced by release: {family_selection_path}")

    source_candidate_root = source_release_root / "data" / "candidate_rows"
    canonical_ok, canonical_errors = candidate_rows_are_canonical(source_candidate_root)
    if not canonical_ok:
        raise ValueError("Source candidate rows are not compatible with the canonical schema:\n" + "\n".join(canonical_errors))

    output_root = Path(output_dir).expanduser().resolve()
    _require_empty_output_dir(output_root)

    target_candidate_root = output_root / "data" / "candidate_rows"
    candidate_rows_staging_mode = _stage_tree(source_candidate_root, target_candidate_root, mode=staging_mode)

    source_pairwise_path = source_release_root / "data" / "pairwise_sample" / "pairwise_sample.parquet"
    target_pairwise_path = output_root / "data" / "pairwise_sample" / "pairwise_sample.parquet"
    pairwise_enabled, max_pairwise_rows, max_pairs_per_decision, pairwise_seed = _pairwise_config(source_manifest)
    pairwise_sample_reused = False
    pairwise_sample_regenerated = False
    pairwise_sample_staging_mode: str | None = None
    stages = ["decision_view", "metadata", "checksums", "validate"]

    if pairwise_enabled:
        can_reuse_pairwise = reuse_existing_pairwise_sample and _pairwise_sample_is_compatible(source_pairwise_path)
        if can_reuse_pairwise:
            pairwise_sample_staging_mode = _stage_file(source_pairwise_path, target_pairwise_path, mode=staging_mode)
            pairwise_sample_reused = True
        else:
            stages = ["decision_view", "pairwise_sample", "metadata", "checksums", "validate"]
            pairwise_sample_regenerated = True

    build_real_release(
        input_manifest=source_input_manifest,
        family_selection=family_selection_path,
        output_dir=output_root,
        dataset_id=dataset_id,
        repo_root=repo_root,
        dry_run=False,
        overwrite=False,
        skip_disk_space_check=True,
        pairwise_sample=pairwise_enabled,
        max_pairwise_rows=max_pairwise_rows,
        max_pairs_per_decision=max_pairs_per_decision,
        pairwise_seed=pairwise_seed,
        duckdb_threads=duckdb_threads,
        duckdb_memory_limit=duckdb_memory_limit,
        duckdb_temp_dir=duckdb_temp_dir,
        stages=stages,
        blocked_families=set(DEFAULT_BLOCKED_FAMILIES),
    )

    manifest_path = output_root / "metadata" / "release_manifest.json"
    _write_migration_metadata(
        manifest_path=manifest_path,
        source_release_root=source_release_root,
        candidate_rows_staging_mode=candidate_rows_staging_mode,
        pairwise_sample_reused=pairwise_sample_reused,
        pairwise_sample_regenerated=pairwise_sample_regenerated,
        pairwise_sample_staging_mode=pairwise_sample_staging_mode,
    )

    result = build_real_release(
        input_manifest=source_input_manifest,
        family_selection=family_selection_path,
        output_dir=output_root,
        dataset_id=dataset_id,
        repo_root=repo_root,
        dry_run=False,
        overwrite=True,
        skip_disk_space_check=True,
        pairwise_sample=pairwise_enabled,
        max_pairwise_rows=max_pairwise_rows,
        max_pairs_per_decision=max_pairs_per_decision,
        pairwise_seed=pairwise_seed,
        duckdb_threads=duckdb_threads,
        duckdb_memory_limit=duckdb_memory_limit,
        duckdb_temp_dir=duckdb_temp_dir,
        stages=["checksums", "validate"],
        blocked_families=set(DEFAULT_BLOCKED_FAMILIES),
    )

    return RealReleaseMigrationResult(
        release_root=output_root,
        dataset_id=dataset_id,
        source_release_root=source_release_root,
        candidate_row_count=result.candidate_row_count,
        decision_row_count=result.decision_row_count,
        pairwise_sample_row_count=result.pairwise_sample_row_count,
        candidate_rows_reused=True,
        candidate_rows_staging_mode=candidate_rows_staging_mode,
        pairwise_sample_reused=pairwise_sample_reused,
        pairwise_sample_regenerated=pairwise_sample_regenerated,
        pairwise_sample_staging_mode=pairwise_sample_staging_mode,
        manifest_path=manifest_path,
    )
