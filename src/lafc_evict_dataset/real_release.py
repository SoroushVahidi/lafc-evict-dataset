from __future__ import annotations

import csv
import json
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pandas as pd

from .io import resolve_candidate_files

DEFAULT_BLOCKED_FAMILIES: Final[tuple[str, ...]] = ("citibike", "brightkite")


@dataclass(frozen=True)
class CandidateSourceSummary:
    source_path: Path
    manifest_path: Path | None
    split_summary_path: Path | None
    columns: tuple[str, ...]
    discovered_families: tuple[str, ...]
    selected_families: tuple[str, ...]
    excluded_families: tuple[str, ...]
    missing_selected_families: tuple[str, ...]
    blocked_families_present: tuple[str, ...]
    shard_count_total: int
    shard_count_selected: int
    total_bytes_total: int
    total_bytes_selected: int
    estimated_rows_total: int | None
    estimated_rows_selected: int | None
    estimated_decisions_total: int | None
    estimated_decisions_selected: int | None
    splits: tuple[str, ...]
    capacities: tuple[int, ...]
    horizons: tuple[int, ...]
    ready_to_proceed: bool
    warnings: tuple[str, ...]


def load_family_selection(path: str | Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    selected = tuple(sorted({str(name) for name in payload.get("selected_families", [])}))
    excluded = tuple(
        sorted(
            {
                str(entry.get("family"))
                for entry in payload.get("excluded_families", [])
                if isinstance(entry, dict) and entry.get("family")
            }
        )
    )
    return selected, excluded


def filter_candidate_dataframe_by_family(
    df: pd.DataFrame,
    *,
    include_families: set[str] | None = None,
    exclude_families: set[str] | None = None,
) -> pd.DataFrame:
    include_families = include_families or set()
    exclude_families = exclude_families or set()
    _validate_family_filters(include_families=include_families, exclude_families=exclude_families)
    filtered = df.copy()
    if include_families:
        filtered = filtered[filtered["trace_family"].astype(str).isin(sorted(include_families))]
    if exclude_families:
        filtered = filtered[~filtered["trace_family"].astype(str).isin(sorted(exclude_families))]
    return filtered.reset_index(drop=True)


def infer_trace_family_from_path(path: Path, *, known_families: set[str]) -> str | None:
    for part in path.parts:
        if part.startswith("trace_family="):
            family = part.split("=", 1)[1]
            if family:
                return family
    for family in sorted(known_families, key=len, reverse=True):
        if path.name.startswith(f"{family}_"):
            return family
    return None


def summarize_candidate_source(
    input_path: str | Path,
    *,
    include_families: set[str] | None = None,
    exclude_families: set[str] | None = None,
    blocked_families: set[str] | None = None,
) -> CandidateSourceSummary:
    source_path = Path(input_path).expanduser().resolve()
    include_families = include_families or set()
    exclude_families = exclude_families or set()
    blocked_families = blocked_families or set(DEFAULT_BLOCKED_FAMILIES)
    _validate_family_filters(include_families=include_families, exclude_families=exclude_families)

    manifest_path = source_path if source_path.is_file() and source_path.suffix.lower() == ".json" else None
    split_summary_path = None
    if manifest_path is not None:
        sibling_summary = manifest_path.parent / "split_summary.csv"
        if sibling_summary.exists():
            split_summary_path = sibling_summary

    files = resolve_candidate_files(source_path)
    known_families = include_families | exclude_families | blocked_families

    shard_count_total = len(files)
    total_bytes_total = 0
    shard_count_selected = 0
    total_bytes_selected = 0
    discovered_families: set[str] = set()

    for file_path in files:
        total_bytes_total += file_path.stat().st_size
        family = infer_trace_family_from_path(file_path, known_families=known_families)
        if family:
            discovered_families.add(family)
        is_selected = True
        if include_families and family not in include_families:
            is_selected = False
        if family in exclude_families:
            is_selected = False
        if is_selected:
            shard_count_selected += 1
            total_bytes_selected += file_path.stat().st_size

    columns = _read_candidate_columns(files[0]) if files else tuple()
    splits: set[str] = set()
    capacities: set[int] = set()
    horizons: set[int] = set()
    estimated_rows_total: int | None = None
    estimated_rows_selected: int | None = None
    estimated_decisions_total: int | None = None
    estimated_decisions_selected: int | None = None

    if split_summary_path is not None:
        summary_rows = list(csv.DictReader(split_summary_path.open(encoding="utf-8")))
        splits = {str(row["split"]) for row in summary_rows}
        capacities = {int(row["capacity"]) for row in summary_rows}
        horizons = {int(row["horizon"]) for row in summary_rows}
        discovered_families.update(str(row["trace_family"]) for row in summary_rows)
        estimated_rows_total = sum(int(row["row_count"]) for row in summary_rows)
        estimated_decisions_total = sum(int(row["decision_count"]) for row in summary_rows)
        selected_rows = [
            row
            for row in summary_rows
            if (not include_families or str(row["trace_family"]) in include_families)
            and str(row["trace_family"]) not in exclude_families
        ]
        estimated_rows_selected = sum(int(row["row_count"]) for row in selected_rows)
        estimated_decisions_selected = sum(int(row["decision_count"]) for row in selected_rows)
    elif manifest_path is not None:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries = payload.get("files", payload.get("shards", []))
        estimated_rows_total = sum(int(entry.get("row_count", 0)) for entry in entries if isinstance(entry, dict))
        selected_rows = 0
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            raw_path = entry.get("path", "")
            candidate = Path(raw_path)
            family = infer_trace_family_from_path(candidate, known_families=known_families)
            if include_families and family not in include_families:
                continue
            if family in exclude_families:
                continue
            selected_rows += int(entry.get("row_count", 0))
        estimated_rows_selected = selected_rows

    discovered_families_tuple = tuple(sorted(discovered_families))
    selected_families_tuple = tuple(sorted(include_families)) if include_families else discovered_families_tuple
    excluded_families_tuple = tuple(sorted(exclude_families))
    missing_selected = tuple(sorted(include_families - discovered_families)) if include_families else tuple()
    blocked_present = tuple(sorted(discovered_families & blocked_families))

    warnings: list[str] = []
    if blocked_present and not blocked_families.issubset(exclude_families):
        warnings.append("Blocked families are present in the source candidate rows and must be excluded explicitly.")
    if missing_selected:
        warnings.append("One or more selected families are missing from the source candidate rows.")
    warnings.append(
        "The repository does not yet have a single end-to-end real-release builder that emits candidate rows, "
        "decision view, pairwise view, and release checksum/report artifacts in one safe pass."
    )
    warnings.append(
        "Current release/export and downstream view scripts materialize full candidate dataframes in memory. "
        "That is not yet a safe execution path for the full real release."
    )

    ready_to_proceed = not blocked_present and not missing_selected
    return CandidateSourceSummary(
        source_path=source_path,
        manifest_path=manifest_path,
        split_summary_path=split_summary_path,
        columns=columns,
        discovered_families=discovered_families_tuple,
        selected_families=selected_families_tuple,
        excluded_families=excluded_families_tuple,
        missing_selected_families=missing_selected,
        blocked_families_present=blocked_present,
        shard_count_total=shard_count_total,
        shard_count_selected=shard_count_selected,
        total_bytes_total=total_bytes_total,
        total_bytes_selected=total_bytes_selected,
        estimated_rows_total=estimated_rows_total,
        estimated_rows_selected=estimated_rows_selected,
        estimated_decisions_total=estimated_decisions_total,
        estimated_decisions_selected=estimated_decisions_selected,
        splits=tuple(sorted(splits)),
        capacities=tuple(sorted(capacities)),
        horizons=tuple(sorted(horizons)),
        ready_to_proceed=ready_to_proceed,
        warnings=tuple(warnings),
    )


def build_real_release_command(
    *,
    input_path: str | Path,
    output_dir: str | Path,
    dataset_id: str,
    include_families: tuple[str, ...],
    exclude_families: tuple[str, ...],
) -> str:
    parts = [
        "python",
        "scripts/export_lafc_evict_parquet.py",
        "--input-path",
        str(Path(input_path)),
        "--output-dir",
        str(Path(output_dir)),
        "--dataset-id",
        dataset_id,
    ]
    for family in include_families:
        parts.extend(["--include-family", family])
    for family in exclude_families:
        parts.extend(["--exclude-family", family])
    parts.append("--overwrite")
    return " \\\n  ".join(shlex.quote(part) for part in parts)


def render_real_release_report(
    summary: CandidateSourceSummary,
    *,
    release_name: str,
    build_command: str,
) -> str:
    lines = [
        f"# {release_name} Readiness Audit",
        "",
        f"- Source manifest: `{summary.manifest_path or summary.source_path}`",
        f"- Split summary: `{summary.split_summary_path}`" if summary.split_summary_path else "- Split summary: not found",
        f"- Selected families: `{', '.join(summary.selected_families)}`",
        f"- Excluded families: `{', '.join(summary.excluded_families)}`" if summary.excluded_families else "- Excluded families: none",
        f"- Discovered families: `{', '.join(summary.discovered_families)}`",
        f"- Blocked families present in source: `{', '.join(summary.blocked_families_present)}`" if summary.blocked_families_present else "- Blocked families present in source: none",
        f"- Missing selected families: `{', '.join(summary.missing_selected_families)}`" if summary.missing_selected_families else "- Missing selected families: none",
        f"- Candidate shards discovered: `{summary.shard_count_total}` total / `{summary.shard_count_selected}` selected",
        f"- Estimated total bytes: `{format_bytes(summary.total_bytes_total)}` total / `{format_bytes(summary.total_bytes_selected)}` selected",
        f"- Estimated candidate rows: `{summary.estimated_rows_total}` total / `{summary.estimated_rows_selected}` selected",
        f"- Estimated decision rows: `{summary.estimated_decisions_total}` total / `{summary.estimated_decisions_selected}` selected",
        f"- Splits: `{', '.join(summary.splits)}`" if summary.splits else "- Splits: unavailable",
        f"- Capacities: `{', '.join(str(value) for value in summary.capacities)}`" if summary.capacities else "- Capacities: unavailable",
        f"- Horizons: `{', '.join(str(value) for value in summary.horizons)}`" if summary.horizons else "- Horizons: unavailable",
        f"- Candidate columns available: `{', '.join(summary.columns)}`" if summary.columns else "- Candidate columns available: unavailable",
        f"- Release construction safe to proceed: `{'yes' if summary.ready_to_proceed else 'no'}`",
        "",
        "## Proposed Build Command",
        "",
        "```bash",
        build_command,
        "```",
        "",
        "## Warnings / TODOs",
        "",
        *[f"- {warning}" for warning in summary.warnings],
    ]
    return "\n".join(lines) + "\n"


def dry_run_export_plan(
    input_path: str | Path,
    *,
    include_families: set[str] | None = None,
    exclude_families: set[str] | None = None,
) -> dict[str, object]:
    summary = summarize_candidate_source(
        input_path,
        include_families=include_families,
        exclude_families=exclude_families,
    )
    return {
        "mode": "dry_run",
        "input_path": str(summary.source_path),
        "manifest_path": str(summary.manifest_path) if summary.manifest_path else None,
        "split_summary_path": str(summary.split_summary_path) if summary.split_summary_path else None,
        "selected_families": list(summary.selected_families),
        "excluded_families": list(summary.excluded_families),
        "discovered_families": list(summary.discovered_families),
        "blocked_families_present": list(summary.blocked_families_present),
        "missing_selected_families": list(summary.missing_selected_families),
        "candidate_columns": list(summary.columns),
        "shard_count_total": summary.shard_count_total,
        "shard_count_selected": summary.shard_count_selected,
        "estimated_total_bytes": summary.total_bytes_total,
        "estimated_selected_bytes": summary.total_bytes_selected,
        "estimated_total_rows": summary.estimated_rows_total,
        "estimated_selected_rows": summary.estimated_rows_selected,
        "estimated_total_decisions": summary.estimated_decisions_total,
        "estimated_selected_decisions": summary.estimated_decisions_selected,
        "splits": list(summary.splits),
        "capacities": list(summary.capacities),
        "horizons": list(summary.horizons),
        "ready_to_proceed": summary.ready_to_proceed,
        "warnings": list(summary.warnings),
    }


def format_bytes(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024.0 or unit == "TiB":
            return f"{value:.2f} {unit}"
        value /= 1024.0
    return f"{num_bytes} B"


def _validate_family_filters(*, include_families: set[str], exclude_families: set[str]) -> None:
    overlap = include_families & exclude_families
    if overlap:
        raise ValueError("Family filters overlap between include and exclude: " + ", ".join(sorted(overlap)))


def _read_candidate_columns(path: Path) -> tuple[str, ...]:
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8") as handle:
            header = handle.readline().strip()
        return tuple(column.strip() for column in header.split(",") if column.strip())
    if path.suffix.lower() == ".parquet":
        return tuple(pd.read_parquet(path).columns.tolist())
    return tuple()
