from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import pyarrow.parquet as pq

from .real_release_migration import PAIRWISE_SAMPLE_COLUMNS
from .schema import CANONICAL_COLUMNS, SCHEMA_VERSION
from .views import DECISION_VIEW_COLUMNS

DEFAULT_CANDIDATE_SAMPLE_SIZE: Final[int] = 4


@dataclass(frozen=True)
class SchemaAssessment:
    path: str
    compatible: bool
    columns: tuple[str, ...]
    missing_columns: tuple[str, ...]
    extra_columns: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "compatible": self.compatible,
            "columns": list(self.columns),
            "missing_columns": list(self.missing_columns),
            "extra_columns": list(self.extra_columns),
        }


@dataclass(frozen=True)
class CandidateSampleAssessment:
    total_partition_files: int
    sampled_file_count: int
    sampled_paths: tuple[str, ...]
    compatible: bool
    columns: tuple[str, ...]
    missing_columns: tuple[str, ...]
    extra_columns: tuple[str, ...]
    inconsistent_sample_paths: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_partition_files": self.total_partition_files,
            "sampled_file_count": self.sampled_file_count,
            "sampled_paths": list(self.sampled_paths),
            "compatible": self.compatible,
            "columns": list(self.columns),
            "missing_columns": list(self.missing_columns),
            "extra_columns": list(self.extra_columns),
            "inconsistent_sample_paths": list(self.inconsistent_sample_paths),
        }


@dataclass(frozen=True)
class ReleaseTreeSummary:
    total_files: int
    total_dirs: int
    total_size_bytes: int
    sections: dict[str, dict[str, int]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_files": self.total_files,
            "total_dirs": self.total_dirs,
            "total_size_bytes": self.total_size_bytes,
            "sections": self.sections,
        }


@dataclass(frozen=True)
class ManifestMigrationAssessment:
    source_has_dataset_name: bool
    source_has_row_counts: bool
    source_has_candidate_partitions: bool
    source_has_file_inventory: bool
    source_has_pairwise_sample_config: bool
    candidate_partition_count_matches_manifest: bool
    file_inventory_count_matches_manifest: bool
    planned_current_manifest_shape: dict[str, Any]
    updates_required: tuple[str, ...]
    cheap_to_migrate: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_has_dataset_name": self.source_has_dataset_name,
            "source_has_row_counts": self.source_has_row_counts,
            "source_has_candidate_partitions": self.source_has_candidate_partitions,
            "source_has_file_inventory": self.source_has_file_inventory,
            "source_has_pairwise_sample_config": self.source_has_pairwise_sample_config,
            "candidate_partition_count_matches_manifest": self.candidate_partition_count_matches_manifest,
            "file_inventory_count_matches_manifest": self.file_inventory_count_matches_manifest,
            "planned_current_manifest_shape": self.planned_current_manifest_shape,
            "updates_required": list(self.updates_required),
            "cheap_to_migrate": self.cheap_to_migrate,
        }


@dataclass(frozen=True)
class RealReleaseMigrationPlan:
    source_release_dir: Path
    dataset_id: str
    schema_version: str
    source_manifest_path: Path
    source_candidate_manifest_path: Path | None
    family_selection_manifest_path: Path | None
    source_candidate_manifest_exists: bool
    family_selection_manifest_exists: bool
    release_tree_summary: ReleaseTreeSummary
    manifest_assessment: ManifestMigrationAssessment
    decision_view: SchemaAssessment
    pairwise_sample: SchemaAssessment | None
    candidate_rows: CandidateSampleAssessment
    candidate_rows_can_likely_be_reused: bool
    pairwise_sample_can_likely_be_reused: bool
    decision_view_regeneration_required: bool
    only_heavy_missing_piece_is_decision_view: bool
    recommended_heavy_command: str
    heavy_steps_later: tuple[str, ...]
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_release_dir": str(self.source_release_dir),
            "dataset_id": self.dataset_id,
            "schema_version": self.schema_version,
            "source_manifest_path": str(self.source_manifest_path),
            "source_candidate_manifest_path": (
                str(self.source_candidate_manifest_path) if self.source_candidate_manifest_path else None
            ),
            "family_selection_manifest_path": (
                str(self.family_selection_manifest_path) if self.family_selection_manifest_path else None
            ),
            "source_candidate_manifest_exists": self.source_candidate_manifest_exists,
            "family_selection_manifest_exists": self.family_selection_manifest_exists,
            "release_tree_summary": self.release_tree_summary.to_dict(),
            "manifest_assessment": self.manifest_assessment.to_dict(),
            "decision_view": self.decision_view.to_dict(),
            "pairwise_sample": self.pairwise_sample.to_dict() if self.pairwise_sample else None,
            "candidate_rows": self.candidate_rows.to_dict(),
            "candidate_rows_can_likely_be_reused": self.candidate_rows_can_likely_be_reused,
            "pairwise_sample_can_likely_be_reused": self.pairwise_sample_can_likely_be_reused,
            "decision_view_regeneration_required": self.decision_view_regeneration_required,
            "only_heavy_missing_piece_is_decision_view": self.only_heavy_missing_piece_is_decision_view,
            "recommended_heavy_command": self.recommended_heavy_command,
            "heavy_steps_later": list(self.heavy_steps_later),
            "notes": list(self.notes),
        }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_assessment(path: Path, *, required_columns: tuple[str, ...] | list[str], release_root: Path) -> SchemaAssessment:
    columns = tuple(pq.ParquetFile(path).schema_arrow.names)
    required = tuple(required_columns)
    missing = tuple(column for column in required if column not in columns)
    extra = tuple(column for column in columns if column not in required)
    return SchemaAssessment(
        path=path.relative_to(release_root).as_posix(),
        compatible=not missing,
        columns=columns,
        missing_columns=missing,
        extra_columns=extra,
    )


def _sample_indices(total: int, sample_size: int) -> list[int]:
    if total <= 0:
        return []
    sample_size = max(1, min(sample_size, total))
    if sample_size == 1:
        return [0]
    return sorted({round(index * (total - 1) / (sample_size - 1)) for index in range(sample_size)})


def _candidate_sample_assessment(candidate_root: Path, *, sample_size: int, release_root: Path) -> CandidateSampleAssessment:
    candidate_paths = sorted(candidate_root.rglob("candidate_rows.parquet"))
    if not candidate_paths:
        raise FileNotFoundError(f"No candidate_rows.parquet partitions found under {candidate_root}")

    sampled_paths = [candidate_paths[index] for index in _sample_indices(len(candidate_paths), sample_size)]
    sampled_columns = [tuple(pq.ParquetFile(path).schema_arrow.names) for path in sampled_paths]
    reference = sampled_columns[0]
    missing = tuple(column for column in CANONICAL_COLUMNS if column not in reference)
    extra = tuple(column for column in reference if column not in CANONICAL_COLUMNS)
    inconsistent = tuple(
        path.relative_to(release_root).as_posix()
        for path, columns in zip(sampled_paths, sampled_columns, strict=True)
        if columns != reference
    )
    return CandidateSampleAssessment(
        total_partition_files=len(candidate_paths),
        sampled_file_count=len(sampled_paths),
        sampled_paths=tuple(path.relative_to(release_root).as_posix() for path in sampled_paths),
        compatible=not missing and not inconsistent,
        columns=reference,
        missing_columns=missing,
        extra_columns=extra,
        inconsistent_sample_paths=inconsistent,
    )


def _release_tree_summary(release_root: Path) -> ReleaseTreeSummary:
    files = [path for path in release_root.rglob("*") if path.is_file()]
    dirs = [path for path in release_root.rglob("*") if path.is_dir()]
    sections: dict[str, dict[str, int]] = {}
    for rel_path in (
        Path("data/candidate_rows"),
        Path("data/decision_view"),
        Path("data/pairwise_sample"),
        Path("metadata"),
    ):
        section_root = release_root / rel_path
        section_files = [path for path in section_root.rglob("*") if path.is_file()] if section_root.exists() else []
        sections[rel_path.as_posix()] = {
            "files": len(section_files),
            "size_bytes": sum(path.stat().st_size for path in section_files),
        }
    return ReleaseTreeSummary(
        total_files=len(files),
        total_dirs=len(dirs),
        total_size_bytes=sum(path.stat().st_size for path in files),
        sections=sections,
    )


def _planned_row_counts(manifest: dict[str, Any]) -> dict[str, int]:
    row_counts = manifest.get("row_counts")
    if isinstance(row_counts, dict) and row_counts:
        return {str(key): int(value) for key, value in row_counts.items() if value is not None}

    planned: dict[str, int] = {}
    legacy_pairs = (
        ("candidate_rows", "candidate_row_count"),
        ("decision_view", "decision_row_count"),
        ("pairwise_sample", "pairwise_sample_row_count"),
    )
    for nested_key, flat_key in legacy_pairs:
        value = manifest.get(flat_key)
        if value is not None:
            planned[nested_key] = int(value)
    return planned


def _manifest_assessment(
    manifest: dict[str, Any],
    *,
    release_root: Path,
    dataset_id: str,
    tree_summary: ReleaseTreeSummary,
    candidate_partition_count: int,
) -> ManifestMigrationAssessment:
    planned_shape = {
        "dataset_name": dataset_id,
        "dataset_id": dataset_id,
        "version": str(manifest.get("version", "unknown")),
        "release_name": str(manifest.get("release_name", dataset_id)),
        "release_type": str(manifest.get("release_type", "unknown")),
        "schema_version": SCHEMA_VERSION,
        "row_counts": _planned_row_counts(manifest),
    }

    manifest_candidate_partitions = manifest.get("candidate_partitions")
    manifest_file_inventory = manifest.get("file_inventory")
    updates_required: list[str] = []
    if "dataset_name" not in manifest:
        updates_required.append("add dataset_name from dataset_id")
    if "row_counts" not in manifest:
        updates_required.append("derive row_counts from legacy flat row-count fields")
    if "migration" not in manifest:
        updates_required.append("add migration provenance block when materializing the migrated release")

    file_inventory_count = len(manifest_file_inventory) if isinstance(manifest_file_inventory, list) else None
    candidate_partition_inventory_count = (
        len(manifest_candidate_partitions) if isinstance(manifest_candidate_partitions, list) else None
    )
    cheap_to_migrate = bool(
        planned_shape["row_counts"]
        and isinstance(manifest_candidate_partitions, list)
        and isinstance(manifest_file_inventory, list)
        and candidate_partition_inventory_count == candidate_partition_count
        and file_inventory_count == tree_summary.total_files
    )

    return ManifestMigrationAssessment(
        source_has_dataset_name="dataset_name" in manifest,
        source_has_row_counts="row_counts" in manifest,
        source_has_candidate_partitions=isinstance(manifest_candidate_partitions, list),
        source_has_file_inventory=isinstance(manifest_file_inventory, list),
        source_has_pairwise_sample_config=isinstance(manifest.get("pairwise_sample"), dict),
        candidate_partition_count_matches_manifest=candidate_partition_inventory_count == candidate_partition_count,
        file_inventory_count_matches_manifest=file_inventory_count == tree_summary.total_files,
        planned_current_manifest_shape=planned_shape,
        updates_required=tuple(updates_required),
        cheap_to_migrate=cheap_to_migrate,
    )


def plan_real_release_migration(
    source_release_dir: str | Path,
    *,
    candidate_sample_size: int = DEFAULT_CANDIDATE_SAMPLE_SIZE,
    suggested_output_dir: str | Path | None = None,
) -> RealReleaseMigrationPlan:
    release_root = Path(source_release_dir).expanduser().resolve()
    manifest_path = release_root / "metadata" / "release_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing release manifest: {manifest_path}")

    manifest = _read_json(manifest_path)
    dataset_id = str(manifest.get("dataset_name") or manifest.get("dataset_id") or release_root.name)
    candidate_manifest_path = (
        Path(str(manifest["source_manifest"])).expanduser().resolve() if manifest.get("source_manifest") else None
    )
    family_selection_manifest_path = (
        Path(str(manifest["family_selection_manifest"])).expanduser().resolve()
        if manifest.get("family_selection_manifest")
        else None
    )

    tree_summary = _release_tree_summary(release_root)
    candidate_rows = _candidate_sample_assessment(
        release_root / "data" / "candidate_rows",
        sample_size=candidate_sample_size,
        release_root=release_root,
    )
    decision_view = _schema_assessment(
        release_root / "data" / "decision_view" / "decision_view.parquet",
        required_columns=DECISION_VIEW_COLUMNS,
        release_root=release_root,
    )

    pairwise_path = release_root / "data" / "pairwise_sample" / "pairwise_sample.parquet"
    pairwise_sample = (
        _schema_assessment(pairwise_path, required_columns=PAIRWISE_SAMPLE_COLUMNS, release_root=release_root)
        if pairwise_path.exists()
        else None
    )

    manifest_assessment = _manifest_assessment(
        manifest,
        release_root=release_root,
        dataset_id=dataset_id,
        tree_summary=tree_summary,
        candidate_partition_count=candidate_rows.total_partition_files,
    )
    candidate_rows_can_likely_be_reused = (
        candidate_rows.compatible and manifest_assessment.candidate_partition_count_matches_manifest
    )
    pairwise_sample_can_likely_be_reused = bool(pairwise_sample and pairwise_sample.compatible)
    decision_view_regeneration_required = not decision_view.compatible
    only_heavy_missing_piece_is_decision_view = bool(
        candidate_rows_can_likely_be_reused
        and pairwise_sample_can_likely_be_reused
        and manifest_assessment.cheap_to_migrate
        and decision_view_regeneration_required
    )

    target_output_dir = (
        Path(suggested_output_dir).expanduser().resolve()
        if suggested_output_dir is not None
        else release_root.with_name(f"{release_root.name}-migrated")
    )
    recommended_heavy_command = " ".join(
        [
            "python",
            "scripts/migrate_real_release_contract.py",
            "--source-release-dir",
            str(release_root),
            "--output-dir",
            str(target_output_dir),
            "--staging-mode",
            "hardlink",
            "--duckdb-threads",
            "2",
            "--duckdb-memory-limit",
            "8GB",
            "--duckdb-temp-dir",
            ".duckdb_tmp",
        ]
    )

    heavy_steps_later = (
        "Create a new migrated release directory; do not modify the source release in place.",
        "Reuse candidate_rows by hardlinking or copying the existing partitions into the new release root.",
        "Reuse the existing pairwise_sample parquet if the compatibility check still passes at execution time.",
        "Regenerate data/decision_view/decision_view.parquet from candidate_rows under the current contract.",
        "Rewrite metadata/checksums/validation artifacts against the migrated release after decision-view regeneration.",
    )
    notes = (
        "Candidate-row validation here is schema-sample based only; it intentionally does not scan every partition.",
        "Decision-view compatibility here is footer/schema based only; it intentionally does not read the full parquet body.",
        "The recommended command above is the future heavy workflow and was not executed by this planner.",
    )

    return RealReleaseMigrationPlan(
        source_release_dir=release_root,
        dataset_id=dataset_id,
        schema_version=SCHEMA_VERSION,
        source_manifest_path=manifest_path,
        source_candidate_manifest_path=candidate_manifest_path,
        family_selection_manifest_path=family_selection_manifest_path,
        source_candidate_manifest_exists=bool(candidate_manifest_path and candidate_manifest_path.exists()),
        family_selection_manifest_exists=bool(
            family_selection_manifest_path and family_selection_manifest_path.exists()
        ),
        release_tree_summary=tree_summary,
        manifest_assessment=manifest_assessment,
        decision_view=decision_view,
        pairwise_sample=pairwise_sample,
        candidate_rows=candidate_rows,
        candidate_rows_can_likely_be_reused=candidate_rows_can_likely_be_reused,
        pairwise_sample_can_likely_be_reused=pairwise_sample_can_likely_be_reused,
        decision_view_regeneration_required=decision_view_regeneration_required,
        only_heavy_missing_piece_is_decision_view=only_heavy_missing_piece_is_decision_view,
        recommended_heavy_command=recommended_heavy_command,
        heavy_steps_later=heavy_steps_later,
        notes=notes,
    )
