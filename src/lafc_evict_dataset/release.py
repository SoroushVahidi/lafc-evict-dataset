from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .io import ensure_clean_output_dir, ensure_parent, fail_if_output_exists, iter_files, sha256_file
from .publication import render_hf_dataset_card_metadata
from .schema import CANONICAL_COLUMNS, DECISION_KEY_COLUMNS, SCHEMA_VERSION, normalize_split_value
from .validation import validate_candidate_dataframe
from .views import build_decision_view, build_pairwise_view


@dataclass(frozen=True)
class SampleReleaseResult:
    release_root: Path
    candidate_rows_path: Path
    decision_view_path: Path
    pairwise_view_path: Path
    manifest_path: Path
    checksums_path: Path
    validation_report_path: Path
    readme_path: Path
    candidate_row_count: int
    decision_row_count: int
    pairwise_row_count: int
    generated_files: tuple[str, ...]


def _write_partitioned_candidate_rows(df: pd.DataFrame, candidate_root: Path) -> list[dict[str, object]]:
    file_entries: list[dict[str, object]] = []
    partition_cols = ["split", "trace_family", "capacity", "horizon"]

    for values, group in df.groupby(partition_cols, dropna=False, sort=True):
        split, trace_family, capacity, horizon = values
        partition_dir = (
            candidate_root
            / f"split={split}"
            / f"trace_family={trace_family}"
            / f"capacity={int(capacity)}"
            / f"horizon={int(horizon)}"
        )
        partition_dir.mkdir(parents=True, exist_ok=True)
        out_file = partition_dir / "candidate_rows.parquet"
        group.to_parquet(out_file, index=False)
        file_entries.append(
            {
                "path": out_file,
                "row_count": int(len(group)),
                "sha256": sha256_file(out_file),
                "split": split,
                "trace_family": trace_family,
                "capacity": int(capacity),
                "horizon": int(horizon),
            }
        )
    return file_entries


def _checksum_lines(root: Path, checksum_output_path: Path) -> list[str]:
    lines: list[str] = []
    for file_path in iter_files(root):
        if file_path.resolve() == checksum_output_path.resolve():
            continue
        rel = file_path.resolve().relative_to(root.resolve())
        lines.append(f"{sha256_file(file_path)}  {rel.as_posix()}")
    return lines


def _write_validation_report(
    *,
    input_path: Path,
    output_dir: Path,
    candidate_row_count: int,
    decision_row_count: int,
    pairwise_row_count: int,
    generated_files: list[str],
    output_path: Path,
) -> None:
    body = "\n".join(
        [
            "# Validation Report",
            "",
            f"- Input path: `{input_path}`",
            f"- Output directory: `{output_dir}`",
            "- Validation result: passed",
            f"- Candidate row count: {candidate_row_count}",
            f"- Decision row count: {decision_row_count}",
            f"- Pairwise row count: {pairwise_row_count}",
            "",
            "## Generated files",
            "",
            *[f"- `{path}`" for path in generated_files],
            "",
            "This sample release contains synthetic rows only and does not include raw traces or external trace-derived data.",
        ]
    )
    ensure_parent(output_path).write_text(body + "\n", encoding="utf-8")


def _write_release_readme(*, output_path: Path, include_ties: bool, candidate_row_count: int) -> None:
    metadata_block = render_hf_dataset_card_metadata(
        dataset_name="lafc-evict-sample",
        release_type="synthetic_sample",
        candidate_row_count=candidate_row_count,
    )
    text = "\n".join(
        [
            metadata_block,
            "",
            "# LAFC-Evict Sample Release v0.1",
            "",
            "This directory is a fully synthetic LAFC-Evict sample release dry run built from `examples/tiny_candidate_rows.csv`.",
            "",
            "- Dataset name: `lafc-evict-sample`",
            "- Version: `0.1`",
            "- Release type: `synthetic_sample`",
            f"- Pairwise ties included: `{'yes' if include_ties else 'no'}`",
            "",
            "This is a synthetic sample release for testing the publication workflow. It is not suitable for scientific benchmarking.",
            "",
            "This sample release contains synthetic rows only and does not include raw traces or external trace-derived data.",
        ]
    )
    ensure_parent(output_path).write_text(text + "\n", encoding="utf-8")


def build_sample_release(
    *,
    input_path: str | Path,
    output_dir: str | Path,
    overwrite: bool = False,
    include_ties: bool = False,
) -> SampleReleaseResult:
    input_path = Path(input_path).resolve()
    release_root = ensure_clean_output_dir(output_dir, overwrite=overwrite, kind="Sample release output directory").resolve()
    data_dir = release_root / "data"
    metadata_dir = release_root / "metadata"
    candidate_root = data_dir / "candidate_rows"
    decision_view_path = data_dir / "decision_view" / "decision_view.parquet"
    pairwise_view_path = data_dir / "pairwise_view" / "pairwise_view.parquet"
    manifest_path = metadata_dir / "release_manifest.json"
    checksums_path = metadata_dir / "checksums.sha256"
    validation_report_path = metadata_dir / "validation_report.md"
    readme_path = release_root / "README.md"

    for output_path, kind in [
        (manifest_path, "Release manifest"),
        (checksums_path, "Checksum output"),
        (validation_report_path, "Validation report"),
        (readme_path, "Release README"),
    ]:
        fail_if_output_exists(output_path, overwrite=overwrite, kind=kind)

    raw_df = pd.read_csv(input_path)
    df = raw_df[CANONICAL_COLUMNS].copy()
    df["split"] = df["split"].map(normalize_split_value)
    df = df.sort_values([*DECISION_KEY_COLUMNS, "candidate_page_id"]).reset_index(drop=True)

    errors = validate_candidate_dataframe(df)
    if errors:
        raise ValueError("\n".join(errors))

    candidate_entries = _write_partitioned_candidate_rows(df, candidate_root)
    decision_view = build_decision_view(df)
    ensure_parent(decision_view_path)
    decision_view.to_parquet(decision_view_path, index=False)

    pairwise_view = build_pairwise_view(df, include_ties=include_ties)
    ensure_parent(pairwise_view_path)
    pairwise_view.to_parquet(pairwise_view_path, index=False)

    generated_files = sorted(
        [
            str(path.resolve().relative_to(release_root))
            for path in [
                *[Path(entry["path"]) for entry in candidate_entries],
                decision_view_path,
                pairwise_view_path,
                manifest_path,
                checksums_path,
                validation_report_path,
                readme_path,
            ]
        ]
    )

    manifest = {
        "dataset_name": "lafc-evict-sample",
        "version": "0.1",
        "release_type": "synthetic_sample",
        "schema_version": SCHEMA_VERSION,
        "source_input_path": str(input_path),
        "note": "Synthetic sample release only; not suitable for scientific benchmarking.",
        "include_ties": include_ties,
        "created_files": generated_files,
        "row_counts": {
            "candidate_rows": int(len(df)),
            "decision_view": int(len(decision_view)),
            "pairwise_view": int(len(pairwise_view)),
        },
        "candidate_partitions": [
            {
                "path": str(Path(entry["path"]).resolve().relative_to(release_root)),
                "row_count": entry["row_count"],
                "sha256": entry["sha256"],
                "split": entry["split"],
                "trace_family": entry["trace_family"],
                "capacity": entry["capacity"],
                "horizon": entry["horizon"],
            }
            for entry in candidate_entries
        ],
    }
    ensure_parent(manifest_path).write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    _write_release_readme(
        output_path=readme_path,
        include_ties=include_ties,
        candidate_row_count=int(len(df)),
    )

    checksum_lines = _checksum_lines(release_root, checksums_path)
    ensure_parent(checksums_path).write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")

    generated_files = sorted(
        {
            *[str(path.relative_to(release_root)) for path in iter_files(release_root) if path.is_file()],
            str(validation_report_path.relative_to(release_root)),
        }
    )
    _write_validation_report(
        input_path=input_path,
        output_dir=release_root,
        candidate_row_count=int(len(df)),
        decision_row_count=int(len(decision_view)),
        pairwise_row_count=int(len(pairwise_view)),
        generated_files=generated_files,
        output_path=validation_report_path,
    )

    checksum_lines = _checksum_lines(release_root, checksums_path)
    checksums_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")

    generated_files = tuple(
        sorted(
            [
                str(path.relative_to(release_root))
                for path in iter_files(release_root)
                if path.is_file()
            ]
        )
    )
    return SampleReleaseResult(
        release_root=release_root,
        candidate_rows_path=candidate_root,
        decision_view_path=decision_view_path,
        pairwise_view_path=pairwise_view_path,
        manifest_path=manifest_path,
        checksums_path=checksums_path,
        validation_report_path=validation_report_path,
        readme_path=readme_path,
        candidate_row_count=int(len(df)),
        decision_row_count=int(len(decision_view)),
        pairwise_row_count=int(len(pairwise_view)),
        generated_files=generated_files,
    )
