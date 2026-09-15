from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd

from .io import ensure_clean_output_dir, ensure_parent, iter_files, sha256_file
from .publication import TOKEN_LIKE_PATTERNS, render_hf_dataset_card_metadata

PREVIEW_VERSION = "v0.2"
PREVIEW_RELEASE_TYPE = "real_data_preview"
PREVIEW_DATASET_REPO = "SoroushVahidi/lafc-evict"
PREVIEW_RELEASE_NAME = "lafc-evict-v0.2-preview"
PREVIEW_SEED = "lafc-evict-sample-v0.2-preview-seed-20260811"
PSEUDONYM_SALT = "lafc-evict-v0.2-public-preview-object-id-v1"
PSEUDONYM_SALT_ID = "v0.2-public-preview-object-id-v1"
SAFE_FAMILY = "wiki2018"
DEFAULT_CAPACITIES = (32, 64, 128)
DEFAULT_OBJECTIVE_ROOT = Path(
    "/home/soroush/Augmented-caching-objective-ablation/data/derived/supervision_objective_ablation_v1"
)
DEFAULT_CROSS_FAMILY_ROOT = Path(
    "/home/soroush/Augmented-caching-fairness/data/derived/evict_value_v1_cross_family_v1"
)
DEFAULT_OBJECTIVE_FOLD = "brightkite"
DEFAULT_CROSS_FAMILY_FOLD = "brightkite"
DEFAULT_OBJECTIVE_ROWS_PER_CAPACITY = 700_000
DEFAULT_CROSS_FAMILY_ROWS_PER_CAPACITY = 900_000
DEFAULT_SHARDS_PER_CAPACITY = 4
EXCLUDED_FAMILIES = ("brightkite", "citibike", "cloudphysics", "metacdn", "metakv", "twemcache")
PREVIEW_CONFIGS = ("cross_family_evict_value_v1", "objective_ablation_scalar")
WIKI2018_ATTRIBUTION_TEXT = (
    "LAFC-Evict v0.2 preview includes derived cache-eviction supervision examples generated from "
    "Wikimedia public pageview data. Wikimedia pageview data is made available by the Wikimedia "
    "Foundation at `https://dumps.wikimedia.org/other/pageviews/` under the Creative Commons CC0 "
    "1.0 public domain dedication. This LAFC-Evict preview does not redistribute raw pageview dump "
    "rows or raw page titles; object identifiers are deterministic public pseudonyms. Wikimedia and "
    "the Wikimedia Foundation do not endorse this derived dataset."
)
FORBIDDEN_LITERAL_PATTERNS = (
    "/home/soroush",
    "sv96",
    "wulver",
    "/scratch",
    "/tmp/",
    "HF_TOKEN",
    "GITHUB_TOKEN",
)
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PUBLIC_ID_PATTERN = re.compile(r"^obj_[0-9a-f]{24}$")


@dataclass(frozen=True)
class SourceSelection:
    dataset_key: str
    source_root: Path
    root_label: str
    fold: str
    rel_paths: tuple[str, ...]
    rows_per_capacity: int


@dataclass(frozen=True)
class PreviewBuildConfig:
    output_dir: Path
    repo_root: Path
    objective_root: Path = DEFAULT_OBJECTIVE_ROOT
    cross_family_root: Path = DEFAULT_CROSS_FAMILY_ROOT
    objective_fold: str = DEFAULT_OBJECTIVE_FOLD
    cross_family_fold: str = DEFAULT_CROSS_FAMILY_FOLD
    capacities: tuple[int, ...] = DEFAULT_CAPACITIES
    objective_rows_per_capacity: int = DEFAULT_OBJECTIVE_ROWS_PER_CAPACITY
    cross_family_rows_per_capacity: int = DEFAULT_CROSS_FAMILY_ROWS_PER_CAPACITY
    shards_per_capacity: int = DEFAULT_SHARDS_PER_CAPACITY
    dataset_repo: str = PREVIEW_DATASET_REPO
    overwrite: bool = False


@dataclass(frozen=True)
class PreviewBuildResult:
    release_root: Path
    manifest_path: Path
    total_rows: int
    parquet_bytes: int
    data_files: tuple[Path, ...]
    validation_errors: tuple[str, ...]
    security_scan: dict[str, object]


class _Utf8ByteCounter:
    def __init__(self) -> None:
        self.bytes_written = 0

    def write(self, text: str) -> int:
        self.bytes_written += len(text.encode("utf-8"))
        return len(text)


def stable_score(*parts: object) -> int:
    text = "|".join(str(part) for part in parts)
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)


def pseudonymize_object_id(value: object) -> str:
    digest = hashlib.sha256(f"{PSEUDONYM_SALT}|{value}".encode("utf-8")).hexdigest()
    return "obj_" + digest[:24]


def selected_rel_paths(
    root: Path,
    fold: str,
    dataset_key: str,
    capacity: int,
    *,
    shards_per_capacity: int = DEFAULT_SHARDS_PER_CAPACITY,
) -> tuple[str, ...]:
    if shards_per_capacity < 1:
        raise ValueError("shards_per_capacity must be positive")
    if dataset_key == "cross_family_evict_value_v1":
        shard_dir = root / fold / "shards"
    elif dataset_key == "objective_ablation_scalar":
        shard_dir = root / fold / "scalar" / "shards"
    else:
        raise ValueError(f"Unknown preview dataset key: {dataset_key}")

    matches = sorted(shard_dir.glob(f"wiki2018_pageviews_en_50k__cap{capacity}.part*.csv"))
    if not matches:
        raise FileNotFoundError(f"No wiki2018 cap={capacity} shards found for {dataset_key} under {shard_dir}")
    if len(matches) <= shards_per_capacity:
        chosen = matches
    elif shards_per_capacity == 1:
        chosen = [matches[0]]
    else:
        indexes = sorted(
            {
                round(i * (len(matches) - 1) / (shards_per_capacity - 1))
                for i in range(shards_per_capacity)
            }
        )
        chosen = [matches[index] for index in indexes]
    return tuple(path.relative_to(root).as_posix() for path in chosen)


def build_source_selections(config: PreviewBuildConfig) -> tuple[SourceSelection, ...]:
    objective_paths: list[str] = []
    cross_paths: list[str] = []
    for capacity in config.capacities:
        objective_paths.extend(
            selected_rel_paths(
                config.objective_root,
                config.objective_fold,
                "objective_ablation_scalar",
                capacity,
                shards_per_capacity=config.shards_per_capacity,
            )
        )
        cross_paths.extend(
            selected_rel_paths(
                config.cross_family_root,
                config.cross_family_fold,
                "cross_family_evict_value_v1",
                capacity,
                shards_per_capacity=config.shards_per_capacity,
            )
        )
    return (
        SourceSelection(
            dataset_key="cross_family_evict_value_v1",
            source_root=config.cross_family_root,
            root_label="evict_value_v1_cross_family_v1",
            fold=config.cross_family_fold,
            rel_paths=tuple(cross_paths),
            rows_per_capacity=config.cross_family_rows_per_capacity,
        ),
        SourceSelection(
            dataset_key="objective_ablation_scalar",
            source_root=config.objective_root,
            root_label="supervision_objective_ablation_v1",
            fold=config.objective_fold,
            rel_paths=tuple(objective_paths),
            rows_per_capacity=config.objective_rows_per_capacity,
        ),
    )


def read_selection(selection: SourceSelection) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    frames: list[pd.DataFrame] = []
    source_entries: list[dict[str, object]] = []
    for rel_path in selection.rel_paths:
        path = selection.source_root / rel_path
        source_entries.append(
            {
                "dataset_key": selection.dataset_key,
                "source_root_label": selection.root_label,
                "source_fold": selection.fold,
                "source_relpath": rel_path,
                "source_csv_bytes": path.stat().st_size,
                "source_sha256": sha256_file(path),
            }
        )
        frame = pd.read_csv(path)
        frame["source_root_label"] = selection.root_label
        frame["source_fold"] = selection.fold
        frame["source_relpath"] = rel_path
        frame["source_row_number"] = range(len(frame))
        frames.append(frame)
    if not frames:
        raise ValueError(f"No source shards selected for {selection.dataset_key}")
    return pd.concat(frames, ignore_index=True), source_entries


def deterministic_sample(df: pd.DataFrame, *, dataset_key: str, rows_per_capacity: int) -> pd.DataFrame:
    samples: list[pd.DataFrame] = []
    for _, group in df.groupby("capacity", sort=True):
        group = group.copy()
        group["_sample_score"] = [
            stable_score(PREVIEW_SEED, dataset_key, row.source_relpath, row.source_row_number)
            for row in group[["source_relpath", "source_row_number"]].itertuples(index=False)
        ]
        samples.append(group.nsmallest(min(rows_per_capacity, len(group)), "_sample_score"))
    result = pd.concat(samples, ignore_index=True)
    return result.sort_values(["capacity", "_sample_score"]).reset_index(drop=True)


def normalize_preview_dataframe(df: pd.DataFrame, *, dataset_key: str) -> pd.DataFrame:
    out = df.copy()
    if "trace_family" in out.columns:
        out = out[out["trace_family"].astype(str) == SAFE_FAMILY].copy()
    out.insert(0, "preview_dataset", dataset_key)
    out.insert(1, "preview_version", PREVIEW_VERSION)
    out.insert(2, "sampling_seed", PREVIEW_SEED)
    out["object_id_public"] = [pseudonymize_object_id(value) for value in out["candidate_page_id"]]
    out["candidate_page_id_original_present"] = False
    out["candidate_page_id"] = out["object_id_public"]
    if "example_id" in out.columns:
        out["example_id"] = out["decision_id"].astype(str) + "|" + out["candidate_page_id"].astype(str)
    return out.drop(columns=["_sample_score"], errors="ignore")


def csv_equivalent_bytes(df: pd.DataFrame) -> int:
    counter = _Utf8ByteCounter()
    df.to_csv(counter, index=False)
    return counter.bytes_written


def write_schema(output_path: Path, data_files: Iterable[Path]) -> dict[str, object]:
    schema: dict[str, object] = {}
    for path in data_files:
        df = pd.read_parquet(path)
        schema[path.name] = [
            {"name": str(name), "dtype": str(dtype)}
            for name, dtype in zip(df.columns, df.dtypes)
        ]
    ensure_parent(output_path).write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    return schema


def write_checksums(release_root: Path, checksum_path: Path) -> None:
    lines = []
    for path in iter_files(release_root):
        if path.resolve() == checksum_path.resolve():
            continue
        rel = path.resolve().relative_to(release_root.resolve())
        lines.append(f"{sha256_file(path)}  {rel.as_posix()}")
    ensure_parent(checksum_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def security_scan(release_root: Path) -> dict[str, object]:
    findings: list[dict[str, str]] = []
    token_patterns = tuple(
        pattern
        for pattern in TOKEN_LIKE_PATTERNS
        if pattern.pattern != r"\b[A-Za-z0-9]{32,}\b"
    ) + (EMAIL_PATTERN,)
    for path in sorted(p for p in release_root.rglob("*") if p.is_file()):
        rel = path.relative_to(release_root).as_posix()
        if path.suffix.lower() in {".md", ".json", ".csv", ".sha256", ".yaml", ".yml"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            for pattern in FORBIDDEN_LITERAL_PATTERNS:
                if pattern.lower() in text.lower():
                    findings.append({"path": rel, "pattern": pattern})
            for regex in token_patterns:
                if regex.search(text):
                    findings.append({"path": rel, "pattern": regex.pattern})
        if path.suffix.lower() == ".parquet":
            df = pd.read_parquet(path)
            string_cols = [
                col
                for col in df.columns
                if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col])
            ]
            for col in string_cols:
                values = df[col].dropna().astype(str)
                joined_sample = "\n".join(values.head(50_000).tolist())
                for pattern in FORBIDDEN_LITERAL_PATTERNS:
                    if pattern.lower() in joined_sample.lower():
                        findings.append({"path": rel, "column": col, "pattern": pattern})
                for regex in token_patterns:
                    if regex.search(joined_sample):
                        findings.append({"path": rel, "column": col, "pattern": regex.pattern})
    result = {"passed": not findings, "findings": findings}
    return result


def provenance_rows() -> list[dict[str, str]]:
    return [
        {
            "family": "wiki2018",
            "source_name": "Wikimedia public pageviews derived proxy trace",
            "source_url": "https://dumps.wikimedia.org/other/pageviews/",
            "redistribution_status": "ALLOWED_WITH_ATTRIBUTION_LOCALLY_NEEDS_FINAL_WORDING_REVIEW",
            "included": "yes",
            "reason": "local evidence records public Wikimedia pageview source; preview object identifiers are pseudonymized",
        },
        {
            "family": "twemcache",
            "source_name": "Twitter cache trace / Twemcache open trace collection",
            "source_url": "https://github.com/twitter/cache-trace",
            "redistribution_status": "UNCLEAR",
            "included": "no",
            "reason": "local registry does not contain final redistribution and attribution clearance",
        },
        {
            "family": "metakv",
            "source_name": "MetaKV trace family via open cache trace collection",
            "source_url": "https://github.com/cacheMon/cache_dataset",
            "redistribution_status": "UNCLEAR",
            "included": "no",
            "reason": "local registry does not contain final redistribution and attribution clearance",
        },
        {
            "family": "metacdn",
            "source_name": "MetaCDN trace family via open cache trace collection",
            "source_url": "https://github.com/cacheMon/cache_dataset",
            "redistribution_status": "UNCLEAR",
            "included": "no",
            "reason": "local registry does not contain final redistribution and attribution clearance",
        },
        {
            "family": "cloudphysics",
            "source_name": (
                "Alibaba Cloud EBS block-storage trace (historical/internal "
                "family key 'cloudphysics'; this is NOT VMware/CloudPhysics data)"
            ),
            "source_url": "https://github.com/alibaba/block-traces",
            "redistribution_status": "cleared_for_public_release",
            "included": "no",
            "reason": "cleared under CC BY 4.0 for public release (see THIRD_PARTY_DATA.md); not yet packaged into the v0.2/v0.3 real-data preview build",
        },
        {
            "family": "citibike",
            "source_name": "Citi Bike trip-data derived trace family",
            "source_url": "https://citibikenyc.com/system-data",
            "redistribution_status": "UNCLEAR",
            "included": "no",
            "reason": "local governance marks blocked pending review with privacy review required",
        },
        {
            "family": "brightkite",
            "source_name": "Brightkite / SNAP-derived trace family",
            "source_url": "https://snap.stanford.edu/data/loc-brightkite.html",
            "redistribution_status": "UNCLEAR",
            "included": "no",
            "reason": "local governance marks blocked pending review with license and privacy review required",
        },
    ]


def write_provenance_summary(output_path: Path) -> None:
    fieldnames = [
        "family",
        "source_name",
        "source_url",
        "redistribution_status",
        "included",
        "reason",
    ]
    ensure_parent(output_path)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(provenance_rows())


def render_preview_readme(*, stats: dict[str, object], dataset_repo: str) -> str:
    metadata = render_hf_dataset_card_metadata(
        dataset_name="lafc-evict",
        release_type=PREVIEW_RELEASE_TYPE,
        candidate_row_count=int(stats["totals"]["row_count"]),
        license_id="cc0-1.0",
        pretty_name="LAFC-Evict v0.2 Real-Data Preview",
        extra_tags=("parquet", "preview", "real-data-preview"),
        configs=(
            ("cross_family_evict_value_v1", (("train", "data/cross_family_evict_value_v1.parquet"),)),
            ("objective_ablation_scalar", (("train", "data/objective_ablation_scalar.parquet"),)),
        ),
    )
    body = f"""
# LAFC-Evict v0.2 Real-Data Preview

This is the first public real-data preview for the `{dataset_repo}` Hugging Face dataset repository.

Version history:

- `SoroushVahidi/lafc-evict-sample` v0.1 synthetic sample: publication workflow dry run built from `examples/tiny_candidate_rows.csv`.
- v0.1-open / current-contract preserved: historical real release artifacts retained under local `release/` namespaces.
- v0.2 preview: small real derived-data preview using Wikimedia pageview-derived rows only.
- Future v1.0/full release: broader curated dataset after storage, licensing, and provenance review.

The preview contains derived candidate-row features and counterfactual labels. It does not include raw trace rows, raw Wikimedia page titles, machine-local paths, model files, or experiment logs. Object identifiers are deterministic release pseudonyms.

## Wiki2018 Provenance and Attribution

{WIKI2018_ATTRIBUTION_TEXT}

License/terms statement: the upstream Wikimedia Analytics pageview data is CC0. This derived LAFC-Evict preview is released under CC0 1.0 as a dataset. Attribution is included as scholarly provenance and to avoid user confusion, not because CC0 imposes an attribution requirement.

Caveat: this statement is based on Wikimedia's public documentation and is not legal advice.

Read `dataset_card.md`, `RELEASE_NOTES_v0_2.md`, `metadata/release_manifest.json`, `metadata/sampling_manifest.json`, and `metadata/provenance_summary.csv` for release details.
"""
    return metadata + "\n" + body.strip() + "\n"


def render_dataset_card(*, dataset_repo: str) -> str:
    return f"""# LAFC-Evict v0.2 Real-Data Preview

This is a small real-data preview for the proposed `{dataset_repo}` Hugging Face dataset repository.

The preview includes only Wikimedia pageview-derived rows. Upstream pageviews are public Wikimedia Analytics datasets available under the Creative Commons CC0 1.0 public domain dedication. The rows here are derived cache-eviction supervision examples, not raw pageview logs. Object identifiers are pseudonymized.

The existing `SoroushVahidi/lafc-evict-sample` v0.1 repository remains a synthetic workflow dry run and is not suitable for scientific benchmarking. This v0.2 preview is intended to demonstrate the real derived schema at small scale. It is not the full benchmark release.

## Configs

- `cross_family_evict_value_v1`: finite-horizon eviction-loss candidate rows from the corrected cross-family dataset.
- `objective_ablation_scalar`: scalar multi-target objective-ablation candidate rows.

## Wiki2018 Provenance and Attribution

Known factual provenance: this preview uses derived rows generated from the `wiki2018` family, described locally as a Wikimedia public pageviews derived proxy trace with upstream source `https://dumps.wikimedia.org/other/pageviews/`. Wikimedia's pageviews readme states that pageview statistics are compiled using the current pageview definition and that all Analytics datasets are available under the Creative Commons CC0 dedication. The preview is not a redistribution of raw pageview dumps and does not expose raw page titles.

Attribution wording: {WIKI2018_ATTRIBUTION_TEXT}

License/terms statement: the upstream Wikimedia Analytics pageview data is CC0. This derived LAFC-Evict preview is released under CC0 1.0 as a dataset. Attribution is included as scholarly provenance and to avoid user confusion, not because CC0 imposes an attribution requirement.

Caveat: this statement is based on Wikimedia's public documentation and is not legal advice.

## Limitations

- Only `wiki2018` is included.
- Brightkite, CitiBike, CloudPhysics, MetaCDN, MetaKV, and Twemcache are excluded pending redistribution review.
- This package is a preview, not the full LAFC-Evict release.
- Dataset metadata uses `license: cc0-1.0`; code in the canonical publication repository remains separately licensed.
"""


def render_release_notes() -> str:
    return """# v0.2 Preview Release Notes

This proposed update introduces the first real-data preview in the `SoroushVahidi/lafc-evict` Hugging Face dataset repository while preserving the existing synthetic-only `SoroushVahidi/lafc-evict-sample` repository as historical publication workflow evidence.

Changes:

- Adds real Wikimedia pageview-derived candidate-row examples.
- Preserves v0.1 synthetic sample history in the separate sample repository.
- Preserves v0.1-open / current-contract preserved real release artifacts in the canonical local repository.
- Uses two Parquet configs: `cross_family_evict_value_v1` and `objective_ablation_scalar`.
- Pseudonymizes object identifiers.
- Excludes Brightkite, CitiBike, Twemcache, MetaKV, MetaCDN, and CloudPhysics until final redistribution review.

The preview uses Wikimedia Analytics pageview data documented as CC0. Attribution and non-endorsement wording are included in the dataset card and provenance metadata.
"""


def write_text_artifacts(release_root: Path, *, stats: dict[str, object], dataset_repo: str) -> None:
    (release_root / "README.md").write_text(
        render_preview_readme(stats=stats, dataset_repo=dataset_repo),
        encoding="utf-8",
    )
    (release_root / "dataset_card.md").write_text(render_dataset_card(dataset_repo=dataset_repo), encoding="utf-8")
    (release_root / "RELEASE_NOTES_v0_2.md").write_text(render_release_notes(), encoding="utf-8")


def copy_governance_artifacts(repo_root: Path, metadata_dir: Path) -> list[str]:
    copied: list[str] = []
    for source in (
        repo_root / "manifests" / "source_family_registry.yaml",
        repo_root / "manifests" / "lafc_evict_v0_2_preview_families.json",
    ):
        if source.exists():
            target = metadata_dir / source.name
            shutil.copy2(source, target)
            copied.append(target.relative_to(metadata_dir.parent).as_posix())
    return copied


def _file_inventory(release_root: Path, *, include_checksums: bool = True) -> list[str]:
    paths = []
    for path in iter_files(release_root):
        rel = path.relative_to(release_root).as_posix()
        if not include_checksums and rel == "metadata/checksums.sha256":
            continue
        paths.append(rel)
    return sorted(paths)


def write_validation_report(output_path: Path, *, release_root: Path, errors: list[str]) -> None:
    status = "passed" if not errors else "failed"
    lines = [
        "# Validation Report",
        "",
        f"- Release root: `{release_root.name}`",
        f"- Validation result: {status}",
        "- Validator: `lafc_evict_dataset.preview.validate_preview_release`",
        "",
    ]
    if errors:
        lines.extend(["## Validation errors", "", *[f"- {error}" for error in errors], ""])
    ensure_parent(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_release_manifest(
    release_root: Path,
    *,
    dataset_repo: str,
    stats: dict[str, object],
    source_entries: list[dict[str, object]],
    data_files: list[Path],
    governance_artifacts: list[str],
) -> dict[str, object]:
    file_inventory = sorted(
        {
            *_file_inventory(release_root),
            "metadata/release_manifest.json",
            "metadata/validation_report.md",
            "metadata/checksums.sha256",
        }
    )
    manifest = {
        "dataset_name": "lafc-evict",
        "dataset_repo": dataset_repo,
        "version": "0.2-preview",
        "release_type": PREVIEW_RELEASE_TYPE,
        "release_title": "LAFC-Evict v0.2 Real-Data Preview",
        "schema_version": "lafc-evict-preview-v0.2",
        "upload_status": "NOT_UPLOADED",
        "readiness": "READY_FOR_PUBLIC_PREVIEW_UPLOAD",
        "row_counts": {
            "total_rows": int(stats["totals"]["row_count"]),
            **{
                key: int(value["row_count"])
                for key, value in stats["datasets"].items()
                if isinstance(value, dict)
            },
        },
        "included_families": [SAFE_FAMILY],
        "excluded_families": list(EXCLUDED_FAMILIES),
        "data_files": [path.relative_to(release_root).as_posix() for path in data_files],
        "no_raw_trace_rows": True,
        "object_ids_pseudonymized": True,
        "machine_paths_in_metadata": False,
        "sampling": {
            "method": "deterministic SHA-256 row sampling by source shard relative path and source row number",
            "seed": PREVIEW_SEED,
            "object_id_pseudonymization": "candidate_page_id replaced with obj_<first24_sha256(salt|original)>",
            "pseudonym_salt_id": PSEUDONYM_SALT_ID,
            "source_file_count": len(source_entries),
            "source_files_read_bytes": int(sum(int(entry["source_csv_bytes"]) for entry in source_entries)),
        },
        "governance_artifacts": governance_artifacts,
        "license_provenance_status": {
            "wiki2018": "APPROVED_WITH_ATTRIBUTION_AND_CAVEAT",
            "basis": "Wikimedia pageviews and Analytics API documentation identify Analytics datasets/pageview data as CC0.",
        },
        "file_inventory": file_inventory,
    }
    path = release_root / "metadata" / "release_manifest.json"
    ensure_parent(path).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def build_preview_release(config: PreviewBuildConfig) -> PreviewBuildResult:
    release_root = ensure_clean_output_dir(config.output_dir, overwrite=config.overwrite, kind="v0.2 preview release")
    data_dir = release_root / "data"
    metadata_dir = release_root / "metadata"
    data_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    source_entries: list[dict[str, object]] = []
    data_files: list[Path] = []
    stats: dict[str, object] = {
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "preview_version": PREVIEW_VERSION,
        "sampling_seed": PREVIEW_SEED,
        "included_families": [SAFE_FAMILY],
        "excluded_families": list(EXCLUDED_FAMILIES),
        "datasets": {},
    }

    for selection in build_source_selections(config):
        df, entries = read_selection(selection)
        source_entries.extend(entries)
        sample = deterministic_sample(df, dataset_key=selection.dataset_key, rows_per_capacity=selection.rows_per_capacity)
        preview = normalize_preview_dataframe(sample, dataset_key=selection.dataset_key)
        parquet_path = data_dir / f"{selection.dataset_key}.parquet"
        csv_bytes = csv_equivalent_bytes(preview)
        preview.to_parquet(parquet_path, index=False, compression="zstd")
        parquet_bytes = parquet_path.stat().st_size
        data_files.append(parquet_path)
        stats["datasets"][selection.dataset_key] = {
            "row_count": int(len(preview)),
            "decision_count": int(preview["decision_id"].nunique()),
            "capacities": sorted(int(value) for value in preview["capacity"].unique()),
            "splits": sorted(str(value) for value in preview["split"].unique()),
            "source_csv_equivalent_bytes": int(csv_bytes),
            "parquet_bytes": int(parquet_bytes),
            "csv_to_parquet_ratio": float(csv_bytes / parquet_bytes) if parquet_bytes else math.nan,
            "columns": list(preview.columns),
        }

    total_csv = sum(int(dataset["source_csv_equivalent_bytes"]) for dataset in stats["datasets"].values())
    total_parquet = sum(path.stat().st_size for path in data_files)
    ratio = float(total_csv / total_parquet) if total_parquet else math.nan
    stats["totals"] = {
        "row_count": int(sum(int(dataset["row_count"]) for dataset in stats["datasets"].values())),
        "source_csv_equivalent_bytes": int(total_csv),
        "parquet_bytes": int(total_parquet),
        "csv_to_parquet_ratio": ratio,
        "source_files_read": len(source_entries),
        "source_files_read_bytes": int(sum(int(entry["source_csv_bytes"]) for entry in source_entries)),
        "staging_total_bytes_before_checksums": int(sum(path.stat().st_size for path in release_root.rglob("*") if path.is_file())),
    }
    stats["full_release_size_estimates"] = {
        "basis": "local du sizes divided by sampled CSV-to-Parquet ratio; rough upper-level estimate",
        "objective_ablation_csv_tree_bytes": 121 * 1024**3,
        "cross_family_csv_tree_bytes": 93 * 1024**3,
        "objective_ablation_parquet_estimate_bytes": int((121 * 1024**3) / ratio) if ratio else None,
        "cross_family_parquet_estimate_bytes": int((93 * 1024**3) / ratio) if ratio else None,
        "combined_parquet_estimate_bytes": int(((121 + 93) * 1024**3) / ratio) if ratio else None,
    }

    sampling_manifest = {
        "method": "deterministic SHA-256 row sampling by source shard relative path and source row number",
        "seed": PREVIEW_SEED,
        "object_id_pseudonymization": "candidate_page_id replaced with obj_<first24_sha256(salt|original)>",
        "pseudonym_salt_id": PSEUDONYM_SALT_ID,
        "source_entries": source_entries,
    }
    (metadata_dir / "sampling_manifest.json").write_text(
        json.dumps(sampling_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (metadata_dir / "statistics.json").write_text(json.dumps(stats, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_schema(metadata_dir / "schema.json", data_files)
    write_provenance_summary(metadata_dir / "provenance_summary.csv")
    governance_artifacts = copy_governance_artifacts(config.repo_root, metadata_dir)
    write_text_artifacts(release_root, stats=stats, dataset_repo=config.dataset_repo)
    scan = security_scan(release_root)
    (metadata_dir / "security_scan.json").write_text(json.dumps(scan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_release_manifest(
        release_root,
        dataset_repo=config.dataset_repo,
        stats=stats,
        source_entries=source_entries,
        data_files=data_files,
        governance_artifacts=governance_artifacts,
    )
    initial_errors = validate_preview_release(release_root, require_checksums=False)
    write_validation_report(metadata_dir / "validation_report.md", release_root=release_root, errors=initial_errors)
    write_checksums(release_root, metadata_dir / "checksums.sha256")
    final_errors = validate_preview_release(release_root, require_checksums=True)
    if final_errors != initial_errors:
        write_validation_report(metadata_dir / "validation_report.md", release_root=release_root, errors=final_errors)
        write_checksums(release_root, metadata_dir / "checksums.sha256")
        final_errors = validate_preview_release(release_root, require_checksums=True)

    return PreviewBuildResult(
        release_root=release_root,
        manifest_path=release_root / "metadata" / "release_manifest.json",
        total_rows=int(stats["totals"]["row_count"]),
        parquet_bytes=int(stats["totals"]["parquet_bytes"]),
        data_files=tuple(data_files),
        validation_errors=tuple(final_errors),
        security_scan=scan,
    )


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_checksums(release_root: Path) -> list[str]:
    errors: list[str] = []
    checksum_path = release_root / "metadata" / "checksums.sha256"
    for line_no, line in enumerate(checksum_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            errors.append(f"Malformed checksum line {line_no}")
            continue
        expected, rel_path = parts
        rel_path = rel_path.strip()
        target = release_root / rel_path
        if not target.exists():
            errors.append(f"Checksum references missing file: {rel_path}")
            continue
        actual = sha256_file(target)
        if actual != expected:
            errors.append(f"Checksum mismatch for {rel_path}")
    return errors


def _validate_data_file(release_root: Path, rel_path: str, *, expected_rows: int) -> list[str]:
    errors: list[str] = []
    path = release_root / rel_path
    if not path.exists():
        return [f"Missing preview data file: {rel_path}"]
    df = pd.read_parquet(path)
    if len(df) != expected_rows:
        errors.append(f"{rel_path} row count mismatch: {len(df)} vs {expected_rows}")
    if set(df["trace_family"].astype(str).unique()) != {SAFE_FAMILY}:
        errors.append(f"{rel_path} contains non-{SAFE_FAMILY} trace_family values")
    if set(df["preview_version"].astype(str).unique()) != {PREVIEW_VERSION}:
        errors.append(f"{rel_path} contains unexpected preview_version values")
    if set(df["sampling_seed"].astype(str).unique()) != {PREVIEW_SEED}:
        errors.append(f"{rel_path} contains unexpected sampling_seed values")
    if "candidate_page_id_original_present" not in df.columns or bool(df["candidate_page_id_original_present"].any()):
        errors.append(f"{rel_path} does not mark original candidate_page_id as absent")
    if not df["candidate_page_id"].astype(str).map(lambda value: bool(PUBLIC_ID_PATTERN.match(value))).all():
        errors.append(f"{rel_path} has candidate_page_id values outside public pseudonym format")
    if "object_id_public" not in df.columns or not df["candidate_page_id"].equals(df["object_id_public"]):
        errors.append(f"{rel_path} candidate_page_id and object_id_public differ")
    if df["source_relpath"].astype(str).str.startswith("/").any():
        errors.append(f"{rel_path} contains absolute source_relpath values")
    return errors


def validate_preview_release(release_root: str | Path, *, require_checksums: bool = True) -> list[str]:
    root = Path(release_root).expanduser().resolve()
    errors: list[str] = []
    required_files = [
        "README.md",
        "dataset_card.md",
        "RELEASE_NOTES_v0_2.md",
        "metadata/release_manifest.json",
        "metadata/sampling_manifest.json",
        "metadata/provenance_summary.csv",
        "metadata/schema.json",
        "metadata/statistics.json",
        "metadata/security_scan.json",
        "metadata/validation_report.md",
    ]
    if require_checksums:
        required_files.append("metadata/checksums.sha256")
    for rel_path in required_files:
        if not (root / rel_path).exists():
            errors.append(f"Missing required preview artifact: {rel_path}")
    if errors:
        return errors

    manifest = _read_json(root / "metadata" / "release_manifest.json")
    stats = _read_json(root / "metadata" / "statistics.json")
    scan = _read_json(root / "metadata" / "security_scan.json")
    if manifest.get("release_type") != PREVIEW_RELEASE_TYPE:
        errors.append("Release manifest is not a v0.2 real-data preview")
    if manifest.get("included_families") != [SAFE_FAMILY]:
        errors.append("Release manifest must include only wiki2018")
    if sorted(str(value) for value in manifest.get("excluded_families", [])) != sorted(EXCLUDED_FAMILIES):
        errors.append("Release manifest excluded_families does not match conservative v0.2 scope")
    if not manifest.get("object_ids_pseudonymized"):
        errors.append("Release manifest does not mark object identifiers as pseudonymized")
    if not scan.get("passed"):
        errors.append("Security scan did not pass")

    data_files = [str(path) for path in manifest.get("data_files", [])]
    if sorted(data_files) != [f"data/{name}.parquet" for name in sorted(PREVIEW_CONFIGS)]:
        errors.append("Release manifest data_files does not contain the expected two preview configs")
    stats_datasets = stats.get("datasets", {})
    if isinstance(stats_datasets, dict):
        for rel_path in data_files:
            key = Path(rel_path).stem
            dataset_stats = stats_datasets.get(key, {})
            if isinstance(dataset_stats, dict):
                errors.extend(_validate_data_file(root, rel_path, expected_rows=int(dataset_stats["row_count"])))
            else:
                errors.append(f"Missing statistics for {key}")
    else:
        errors.append("statistics.json does not contain a datasets object")

    if require_checksums:
        errors.extend(_validate_checksums(root))
    return errors
