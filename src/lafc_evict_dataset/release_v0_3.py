"""Builder for the local, unpublished LAFC-Evict v0.3 wiki2018-only candidate release.

This module deliberately reuses the already-validated pseudonymization,
security-scan, checksum, and schema-writing helpers from ``preview.py``
(the v0.2 real-data preview builder) rather than reimplementing them, and
follows the same "read full CSV shard(s) into one DataFrame per config,
write one Parquet file per config" pattern v0.2 already used successfully.

Source selection differs deliberately from ``lafc-evict-v0.1-open`` /
``lafc-evict-v0.1-open-current-contract-preserved``: those releases were
built from ``evict_value_v1_wulver_heavy_r1``, whose manifest records
``split_mode: "trace_chunk"`` (a same-family, within-trace chunk split),
not a leave-one-family-out cross-family split. Building a config literally
named ``cross_family_evict_value_v1`` from that source would misrepresent
its split semantics. This module instead sources both v0.3 configs from
the same trees v0.2 already used (``evict_value_v1_cross_family_v1`` and
``supervision_objective_ablation_v1``), simply without v0.2's small-preview
row/shard caps.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd

from .io import coerce_candidate_dataframe, ensure_clean_output_dir, ensure_parent, iter_files, sha256_file
from .preview import (
    DEFAULT_CROSS_FAMILY_ROOT,
    DEFAULT_OBJECTIVE_ROOT,
    EMAIL_PATTERN,
    FORBIDDEN_LITERAL_PATTERNS,
    PSEUDONYM_SALT_ID,
    PUBLIC_ID_PATTERN,
    SAFE_FAMILY,
    WIKI2018_ATTRIBUTION_TEXT,
    pseudonymize_object_id,
)
from .publication import TOKEN_LIKE_PATTERNS, render_hf_dataset_card_metadata

V0_3_VERSION = "v0.3-candidate"
V0_3_RELEASE_TYPE = "real_data_expanded_candidate"
V0_3_RELEASE_NAME = "lafc-evict-v0.3-candidate"
V0_3_SCHEMA_VERSION = "lafc-evict-preview-v0.3"
V0_3_SEED = "lafc-evict-v0.3-candidate-full-inclusion-20260811"
DEFAULT_V0_3_CAPACITIES = (32, 64, 128)
DEFAULT_V0_3_CROSS_FAMILY_FOLD = "brightkite"
DEFAULT_V0_3_OBJECTIVE_FOLD = "brightkite"
V0_3_EXCLUDED_FAMILIES = ("brightkite", "citibike", "cloudphysics", "metacdn", "metakv", "twemcache")
V0_3_CONFIGS = ("cross_family_evict_value_v1", "objective_ablation_scalar")


@dataclass(frozen=True)
class V03SourceSelection:
    dataset_key: str
    source_root: Path
    root_label: str
    fold: str
    rel_paths: tuple[str, ...]


@dataclass(frozen=True)
class V03BuildConfig:
    output_dir: Path
    repo_root: Path
    objective_root: Path = DEFAULT_OBJECTIVE_ROOT
    cross_family_root: Path = DEFAULT_CROSS_FAMILY_ROOT
    objective_fold: str = DEFAULT_V0_3_OBJECTIVE_FOLD
    cross_family_fold: str = DEFAULT_V0_3_CROSS_FAMILY_FOLD
    capacities: tuple[int, ...] = DEFAULT_V0_3_CAPACITIES
    dataset_repo: str = "SoroushVahidi/lafc-evict"
    overwrite: bool = False


@dataclass(frozen=True)
class V03BuildResult:
    release_root: Path
    manifest_path: Path
    total_rows: int
    parquet_bytes: int
    data_files: tuple[Path, ...]
    validation_errors: tuple[str, ...]
    security_scan: dict[str, object]
    leakage_scan: dict[str, object]


def all_wiki2018_rel_paths(root: Path, fold: str, shard_dir_parts: tuple[str, ...], capacity: int) -> tuple[str, ...]:
    """Return every wiki2018 CSV shard for one (fold, capacity), with no artificial cap."""
    shard_dir = root.joinpath(fold, *shard_dir_parts)
    matches = sorted(shard_dir.glob(f"wiki2018_pageviews_en_50k__cap{capacity}.part*.csv"))
    if not matches:
        raise FileNotFoundError(f"No wiki2018 cap={capacity} shards found under {shard_dir}")
    return tuple(path.relative_to(root).as_posix() for path in matches)


def build_source_selections(config: V03BuildConfig) -> tuple[V03SourceSelection, V03SourceSelection]:
    cross_paths: list[str] = []
    objective_paths: list[str] = []
    for capacity in config.capacities:
        cross_paths.extend(
            all_wiki2018_rel_paths(config.cross_family_root, config.cross_family_fold, ("shards",), capacity)
        )
        objective_paths.extend(
            all_wiki2018_rel_paths(config.objective_root, config.objective_fold, ("scalar", "shards"), capacity)
        )
    return (
        V03SourceSelection(
            dataset_key="cross_family_evict_value_v1",
            source_root=config.cross_family_root,
            root_label="evict_value_v1_cross_family_v1",
            fold=config.cross_family_fold,
            rel_paths=tuple(cross_paths),
        ),
        V03SourceSelection(
            dataset_key="objective_ablation_scalar",
            source_root=config.objective_root,
            root_label="supervision_objective_ablation_v1",
            fold=config.objective_fold,
            rel_paths=tuple(objective_paths),
        ),
    )


def read_selection(selection: V03SourceSelection) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    """Read every shard for one config, one file at a time (bounded memory), asserting wiki2018-only."""
    frames: list[pd.DataFrame] = []
    source_entries: list[dict[str, object]] = []
    for rel_path in selection.rel_paths:
        path = selection.source_root / rel_path
        frame = pd.read_csv(path)
        if "trace_family" in frame.columns:
            off_family = sorted(set(frame["trace_family"].astype(str).unique()) - {SAFE_FAMILY})
            if off_family:
                raise ValueError(
                    f"Refusing to include shard {rel_path}: contains non-{SAFE_FAMILY} "
                    f"trace_family values {off_family} (fold-naming leakage guard)"
                )
        source_entries.append(
            {
                "dataset_key": selection.dataset_key,
                "source_root_label": selection.root_label,
                "source_fold": selection.fold,
                "source_relpath": rel_path,
                "source_csv_bytes": path.stat().st_size,
                "source_row_count": int(len(frame)),
                "source_sha256": sha256_file(path),
            }
        )
        frame["source_root_label"] = selection.root_label
        frame["source_fold"] = selection.fold
        frame["source_relpath"] = rel_path
        frame["source_row_number"] = range(len(frame))
        frames.append(frame)
        del frame
    if not frames:
        raise ValueError(f"No source shards selected for {selection.dataset_key}")
    combined = pd.concat(frames, ignore_index=True)
    del frames
    return combined, source_entries


def normalize_v0_3_dataframe(df: pd.DataFrame, *, dataset_key: str) -> pd.DataFrame:
    out = df.copy()
    if "trace_family" in out.columns:
        out = out[out["trace_family"].astype(str) == SAFE_FAMILY].copy()
    out.insert(0, "release_dataset", dataset_key)
    out.insert(1, "release_version", V0_3_VERSION)
    out.insert(2, "schema_version", V0_3_SCHEMA_VERSION)
    out["object_id_public"] = [pseudonymize_object_id(value) for value in out["candidate_page_id"]]
    out["candidate_page_id_original_present"] = False
    out["candidate_page_id_raw"] = out["candidate_page_id"]  # kept in-memory only for the leakage check; dropped before write
    out["candidate_page_id"] = out["object_id_public"]
    if "example_id" in out.columns:
        out["example_id"] = out["decision_id"].astype(str) + "|" + out["candidate_page_id"].astype(str)
    # Fix the split-column dtype inconsistency found in lafc-evict-v0.1-open*
    # (some partitions stored plain string, others dictionary<string>) by
    # explicitly coercing through the shared candidate-schema string dtype
    # before writing a single Parquet file per config.
    if "split" in out.columns:
        out["split"] = out["split"].astype("string").astype(object)
    return out


def csv_equivalent_bytes(df: pd.DataFrame) -> int:
    class _Counter:
        def __init__(self) -> None:
            self.bytes_written = 0

        def write(self, text: str) -> int:
            self.bytes_written += len(text.encode("utf-8"))
            return len(text)

    counter = _Counter()
    df.to_csv(counter, index=False)
    return counter.bytes_written


def raw_title_leakage_scan(df_with_raw: pd.DataFrame, output_df: pd.DataFrame) -> dict[str, object]:
    """Prove none of the raw candidate_page_id values survive into the public columns."""
    raw_values = set(df_with_raw["candidate_page_id_raw"].astype(str).unique())
    leaked_columns: list[str] = []
    leaked_count = 0
    string_cols = [
        c
        for c in output_df.columns
        if pd.api.types.is_object_dtype(output_df[c]) or pd.api.types.is_string_dtype(output_df[c])
    ]
    for col in string_cols:
        col_values = set(output_df[col].dropna().astype(str).unique())
        overlap = raw_values & col_values
        if overlap:
            leaked_columns.append(col)
            leaked_count += len(overlap)
    return {
        "raw_value_population": len(raw_values),
        "leaked_columns": leaked_columns,
        "leaked_value_count": leaked_count,
        "passed": leaked_count == 0,
    }


def pseudonym_collision_scan(df_with_raw: pd.DataFrame) -> dict[str, object]:
    mapping = df_with_raw[["candidate_page_id_raw", "object_id_public"]].drop_duplicates()
    by_pseudonym = mapping.groupby("object_id_public")["candidate_page_id_raw"].nunique()
    colliding = by_pseudonym[by_pseudonym > 1]
    return {
        "unique_raw_ids": int(mapping["candidate_page_id_raw"].nunique()),
        "unique_pseudonyms": int(mapping["object_id_public"].nunique()),
        "colliding_pseudonym_count": int(len(colliding)),
        "passed": len(colliding) == 0,
    }


def write_schema(output_path: Path, data_files: Iterable[Path]) -> dict[str, object]:
    schema: dict[str, object] = {}
    for path in data_files:
        df = pd.read_parquet(path)
        schema[path.name] = [{"name": str(name), "dtype": str(dtype)} for name, dtype in zip(df.columns, df.dtypes)]
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
    token_patterns = tuple(p for p in TOKEN_LIKE_PATTERNS if p.pattern != r"\b[A-Za-z0-9]{32,}\b") + (EMAIL_PATTERN,)
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
            string_cols = [c for c in df.columns if pd.api.types.is_object_dtype(df[c]) or pd.api.types.is_string_dtype(df[c])]
            for col in string_cols:
                values = df[col].dropna().astype(str)
                joined_sample = "\n".join(values.head(50_000).tolist())
                for pattern in FORBIDDEN_LITERAL_PATTERNS:
                    if pattern.lower() in joined_sample.lower():
                        findings.append({"path": rel, "column": col, "pattern": pattern})
                for regex in token_patterns:
                    if regex.search(joined_sample):
                        findings.append({"path": rel, "column": col, "pattern": regex.pattern})
    return {"passed": not findings, "findings": findings}


def provenance_rows() -> list[dict[str, str]]:
    rows = [
        {
            "family": "wiki2018",
            "source_name": "Wikimedia public pageviews derived proxy trace",
            "source_url": "https://dumps.wikimedia.org/other/pageviews/",
            "redistribution_status": "APPROVED_WITH_ATTRIBUTION_AND_CAVEAT",
            "included": "yes",
            "reason": "reviewed 2026-08-11 (docs/WIKI2018_PROVENANCE_REVIEW.md); Wikimedia Analytics pageview data is documented CC0; preview/candidate object identifiers are pseudonymized and no raw page titles are exposed",
        }
    ]
    unclear = [
        ("twemcache", "Twitter cache trace / Twemcache open trace collection", "https://github.com/twitter/cache-trace"),
        ("metakv", "MetaKV trace family via open cache trace collection", "https://github.com/cacheMon/cache_dataset"),
        ("metacdn", "MetaCDN trace family via open cache trace collection", "https://github.com/cacheMon/cache_dataset"),
        ("cloudphysics", "CloudPhysics / open cache trace collection block I/O family", "https://github.com/cacheMon/cache_dataset"),
    ]
    for family, name, url in unclear:
        rows.append(
            {
                "family": family,
                "source_name": name,
                "source_url": url,
                "redistribution_status": "LICENSE_UNCLEAR",
                "included": "no",
                "reason": "final upstream redistribution/attribution review not yet completed and recorded",
            }
        )
    for family, name, url in (
        ("citibike", "Citi Bike trip-data derived trace family", "https://citibikenyc.com/system-data"),
        ("brightkite", "Brightkite / SNAP-derived trace family", "https://snap.stanford.edu/data/loc-brightkite.html"),
    ):
        rows.append(
            {
                "family": family,
                "source_name": name,
                "source_url": url,
                "redistribution_status": "DO_NOT_RELEASE",
                "included": "no",
                "reason": "blocked pending combined license and privacy review",
            }
        )
    return rows


def write_provenance_summary(output_path: Path) -> None:
    import csv

    fieldnames = ["family", "source_name", "source_url", "redistribution_status", "included", "reason"]
    ensure_parent(output_path)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(provenance_rows())


def render_readme(*, stats: dict[str, object], dataset_repo: str) -> str:
    metadata = render_hf_dataset_card_metadata(
        dataset_name="lafc-evict",
        release_type=V0_3_RELEASE_TYPE,
        candidate_row_count=int(stats["totals"]["row_count"]),
        license_id="cc0-1.0",
        pretty_name="LAFC-Evict v0.3 Wiki2018 Expanded Candidate Release (unpublished, local only)",
        extra_tags=("parquet", "v0.3-candidate", "wiki2018-only"),
        configs=(
            ("cross_family_evict_value_v1", (("train", "data/cross_family_evict_value_v1.parquet"),)),
            ("objective_ablation_scalar", (("train", "data/objective_ablation_scalar.parquet"),)),
        ),
    )
    body = f"""
# LAFC-Evict v0.3 Wiki2018 Expanded Candidate Release (LOCAL, UNPUBLISHED)

This is a local build-and-validate candidate for a possible future v0.3
update to the `{dataset_repo}` Hugging Face dataset repository. It has
**not** been uploaded or published anywhere.

Version history:

- v0.1 synthetic sample / v0.1-open (unpublished, `trace_chunk`-split, all
  five license-reviewed families): historical local artifacts, not the
  source for this build.
- v0.2 preview (published): small real derived-data preview, wiki2018 only.
- v0.3 candidate (this release, unpublished): substantially expanded
  wiki2018-only candidate-level supervision, same two configs as v0.2,
  built from the full available wiki2018 shard population in the
  leave-one-family-out `evict_value_v1_cross_family_v1` and
  `supervision_objective_ablation_v1` source trees (no v0.2-style
  down-sampling cap).

The release contains derived candidate-row features and counterfactual
labels only. It does not include raw trace rows, raw Wikimedia page
titles, machine-local paths, model files, or experiment logs. Object
identifiers are deterministic release pseudonyms (same method as v0.2).

## Wiki2018 Provenance and Attribution

{WIKI2018_ATTRIBUTION_TEXT}

License/terms statement: the upstream Wikimedia Analytics pageview data is
CC0. This derived LAFC-Evict release is released under CC0 1.0 as a
dataset. Attribution is included as scholarly provenance, not because CC0
imposes an attribution requirement.

Caveat: this statement is based on Wikimedia's public documentation and is
not legal advice.

Read `dataset_card.md`, `RELEASE_NOTES_v0_3.md`,
`metadata/release_manifest.json`, `metadata/transformation_manifest.json`,
and `metadata/provenance_summary.csv` for release details.
"""
    return metadata + "\n" + body.strip() + "\n"


def render_dataset_card(*, dataset_repo: str) -> str:
    return f"""# LAFC-Evict v0.3 Wiki2018 Expanded Candidate Release (LOCAL, UNPUBLISHED)

This is a local, unpublished candidate build for a possible future v0.3
update to `{dataset_repo}`. Includes only Wikimedia pageview-derived rows.
Upstream pageviews are public Wikimedia Analytics datasets available under
the Creative Commons CC0 1.0 public domain dedication. The rows here are
derived cache-eviction supervision examples, not raw pageview logs. Object
identifiers are pseudonymized using the same deterministic method as the
published v0.2 preview.

## Configs

- `cross_family_evict_value_v1`: finite-horizon eviction-loss candidate
  rows from the corrected leave-one-family-out cross-family dataset
  (`evict_value_v1_cross_family_v1`), wiki2018-only, full available shard
  population (no down-sampling cap).
- `objective_ablation_scalar`: scalar multi-target objective-ablation
  candidate rows (`supervision_objective_ablation_v1`), wiki2018-only,
  full available shard population (no down-sampling cap).

## Wiki2018 Provenance and Attribution

{WIKI2018_ATTRIBUTION_TEXT}

License/terms statement: the upstream Wikimedia Analytics pageview data is
CC0. This derived LAFC-Evict release is released under CC0 1.0 as a
dataset. Attribution is included as scholarly provenance, not because CC0
imposes an attribution requirement.

Caveat: this statement is based on Wikimedia's public documentation and is
not legal advice.

## Limitations

- Only `wiki2018` is included; Brightkite, CitiBike, CloudPhysics, MetaCDN,
  MetaKV, and Twemcache are excluded pending redistribution review.
- `decision_view` and `objective_ablation_pairwise` are not included in
  this candidate; deferred to a future v1.0 build.
- This is a local build-and-validate candidate, not the published dataset.
  It has not been uploaded anywhere.
"""


def render_release_notes(*, comparison: dict[str, object]) -> str:
    return f"""# v0.3 Candidate Release Notes (LOCAL, UNPUBLISHED)

This is a local build-and-validate candidate. It has not been published.

Changes relative to the published v0.2 preview:

- Same two configs (`cross_family_evict_value_v1`, `objective_ablation_scalar`),
  same source trees, same pseudonymization method -- no breaking schema
  change.
- Removes v0.2's per-capacity row-count cap and 4-shards-per-capacity cap;
  includes every available wiki2018 shard in both source trees instead.
- Row count: {comparison.get('v0_2_rows')} (v0.2) -> {comparison.get('v0_3_rows')} (v0.3 candidate).
- Adds an explicit `schema_version` field in the row data itself
  (`{V0_3_SCHEMA_VERSION}`), not just in the release manifest.
- Adds a `transformation_manifest.json` documenting every applied
  transformation explicitly.
- Fixes (by construction -- single-DataFrame-per-config write, coerced
  through the shared candidate-schema string dtype) the `split`-column
  dtype inconsistency found during the prior data-inventory audit in the
  unrelated, unpublished `lafc-evict-v0.1-open*` trees. That inconsistency
  never affected the published v0.2 files (verified: both already use a
  single consistent `large_string` dtype) and does not require a v0.2
  erratum.
- Still wiki2018-only; still excludes Brightkite, CitiBike, CloudPhysics,
  MetaCDN, MetaKV, and Twemcache pending redistribution review.

This release notes file documents a **local, unpublished** candidate.
"""


def write_text_artifacts(release_root: Path, *, stats: dict[str, object], dataset_repo: str, comparison: dict[str, object]) -> None:
    (release_root / "README.md").write_text(render_readme(stats=stats, dataset_repo=dataset_repo), encoding="utf-8")
    (release_root / "dataset_card.md").write_text(render_dataset_card(dataset_repo=dataset_repo), encoding="utf-8")
    (release_root / "RELEASE_NOTES_v0_3.md").write_text(render_release_notes(comparison=comparison), encoding="utf-8")


def _file_inventory(release_root: Path, *, include_checksums: bool = True) -> list[str]:
    paths = []
    for path in iter_files(release_root):
        rel = path.relative_to(release_root).as_posix()
        if not include_checksums and rel == "metadata/checksums.sha256":
            continue
        paths.append(rel)
    return sorted(paths)


def write_transformation_manifest(
    output_path: Path,
    *,
    source_entries: list[dict[str, object]],
    leakage_scans: dict[str, dict[str, object]],
    collision_scans: dict[str, dict[str, object]],
) -> None:
    manifest = {
        "transformations_applied": [
            "family_filter:trace_family==wiki2018",
            "object_id_pseudonymization:candidate_page_id replaced with obj_<first24_sha256(salt|original)>",
            f"pseudonym_salt_id:{PSEUDONYM_SALT_ID}",
            "split_dtype_normalization:split cast through shared candidate-schema string dtype before write",
            "schema_version_field_added_in_row_data",
            "no_row_downsampling:every row of every selected wiki2018 shard is included",
        ],
        "not_applied": [
            "no_column_rename (candidate_page_id/object_id_public names kept identical to v0.2 for backward compatibility; a rename to candidate_object_pseudonym is proposed for v1.0, not applied here)",
            "no_dtype_narrowing (float32 narrowing evaluated but not applied in this candidate; proposed for v1.0)",
        ],
        "raw_title_leakage_scans": leakage_scans,
        "pseudonym_collision_scans": collision_scans,
        "source_entries_count": len(source_entries),
        "source_files_read_bytes": int(sum(int(e["source_csv_bytes"]) for e in source_entries)),
        "source_rows_read": int(sum(int(e["source_row_count"]) for e in source_entries)),
    }
    ensure_parent(output_path).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_release_manifest(
    release_root: Path,
    *,
    dataset_repo: str,
    stats: dict[str, object],
    source_entries: list[dict[str, object]],
    data_files: list[Path],
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
        "version": V0_3_VERSION,
        "release_type": V0_3_RELEASE_TYPE,
        "release_title": "LAFC-Evict v0.3 Wiki2018 Expanded Candidate Release",
        "schema_version": V0_3_SCHEMA_VERSION,
        "supersedes": "v0.2-preview",
        "upload_status": "NOT_UPLOADED",
        "readiness": "LOCAL_BUILD_VALIDATED_NOT_YET_APPROVED_FOR_PUBLISH",
        "row_counts": {
            "total_rows": int(stats["totals"]["row_count"]),
            **{key: int(value["row_count"]) for key, value in stats["datasets"].items() if isinstance(value, dict)},
        },
        "included_families": [SAFE_FAMILY],
        "excluded_families": list(V0_3_EXCLUDED_FAMILIES),
        "data_files": [path.relative_to(release_root).as_posix() for path in data_files],
        "no_raw_trace_rows": True,
        "object_ids_pseudonymized": True,
        "machine_paths_in_metadata": False,
        "sampling": {
            "method": "full inclusion of every available wiki2018 shard in the selected source fold; no row down-sampling",
            "seed": V0_3_SEED,
            "object_id_pseudonymization": "candidate_page_id replaced with obj_<first24_sha256(salt|original)>",
            "pseudonym_salt_id": PSEUDONYM_SALT_ID,
            "source_file_count": len(source_entries),
            "source_files_read_bytes": int(sum(int(entry["source_csv_bytes"]) for entry in source_entries)),
        },
        "license_provenance_status": {
            "wiki2018": "APPROVED_WITH_ATTRIBUTION_AND_CAVEAT",
            "basis": "Wikimedia pageviews and Analytics API documentation identify Analytics datasets/pageview data as CC0.",
        },
        "file_inventory": file_inventory,
    }
    path = release_root / "metadata" / "release_manifest.json"
    ensure_parent(path).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def build_v0_3_candidate_release(config: V03BuildConfig, *, v0_2_rows: int | None = None) -> V03BuildResult:
    release_root = ensure_clean_output_dir(config.output_dir, overwrite=config.overwrite, kind="v0.3 candidate release")
    data_dir = release_root / "data"
    metadata_dir = release_root / "metadata"
    data_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    all_source_entries: list[dict[str, object]] = []
    data_files: list[Path] = []
    leakage_scans: dict[str, dict[str, object]] = {}
    collision_scans: dict[str, dict[str, object]] = {}
    stats: dict[str, object] = {
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "release_version": V0_3_VERSION,
        "seed": V0_3_SEED,
        "included_families": [SAFE_FAMILY],
        "excluded_families": list(V0_3_EXCLUDED_FAMILIES),
        "datasets": {},
    }

    # Sequential, one config at a time, to bound peak memory.
    for selection in build_source_selections(config):
        raw_df, entries = read_selection(selection)
        all_source_entries.extend(entries)
        normalized = normalize_v0_3_dataframe(raw_df, dataset_key=selection.dataset_key)

        leakage_scans[selection.dataset_key] = raw_title_leakage_scan(normalized, normalized.drop(columns=["candidate_page_id_raw"]))
        collision_scans[selection.dataset_key] = pseudonym_collision_scan(normalized)

        public = normalized.drop(columns=["candidate_page_id_raw"]).pipe(coerce_candidate_dataframe)
        parquet_path = data_dir / f"{selection.dataset_key}.parquet"
        csv_bytes = csv_equivalent_bytes(public)
        public.to_parquet(parquet_path, index=False, compression="zstd")
        parquet_bytes = parquet_path.stat().st_size
        data_files.append(parquet_path)
        stats["datasets"][selection.dataset_key] = {
            "row_count": int(len(public)),
            "decision_count": int(public["decision_id"].nunique()),
            "capacities": sorted(int(v) for v in public["capacity"].unique()),
            "splits": sorted(str(v) for v in public["split"].unique()),
            "shard_count": len(selection.rel_paths),
            "source_csv_equivalent_bytes": int(csv_bytes),
            "parquet_bytes": int(parquet_bytes),
            "csv_to_parquet_ratio": float(csv_bytes / parquet_bytes) if parquet_bytes else math.nan,
            "columns": list(public.columns),
        }
        del raw_df, normalized, public

    total_csv = sum(int(d["source_csv_equivalent_bytes"]) for d in stats["datasets"].values())
    total_parquet = sum(path.stat().st_size for path in data_files)
    ratio = float(total_csv / total_parquet) if total_parquet else math.nan
    stats["totals"] = {
        "row_count": int(sum(int(d["row_count"]) for d in stats["datasets"].values())),
        "source_csv_equivalent_bytes": int(total_csv),
        "parquet_bytes": int(total_parquet),
        "csv_to_parquet_ratio": ratio,
        "source_files_read": len(all_source_entries),
        "source_files_read_bytes": int(sum(int(e["source_csv_bytes"]) for e in all_source_entries)),
        "staging_total_bytes_before_checksums": int(sum(p.stat().st_size for p in release_root.rglob("*") if p.is_file())),
    }

    comparison = {"v0_2_rows": v0_2_rows, "v0_3_rows": stats["totals"]["row_count"]}

    (metadata_dir / "sampling_manifest.json").write_text(
        json.dumps(
            {
                "method": "full inclusion of every available wiki2018 shard; no row down-sampling",
                "seed": V0_3_SEED,
                "source_entries": all_source_entries,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (metadata_dir / "statistics.json").write_text(json.dumps(stats, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_schema(metadata_dir / "schema.json", data_files)
    write_provenance_summary(metadata_dir / "provenance_summary.csv")
    write_transformation_manifest(
        metadata_dir / "transformation_manifest.json",
        source_entries=all_source_entries,
        leakage_scans=leakage_scans,
        collision_scans=collision_scans,
    )
    write_text_artifacts(release_root, stats=stats, dataset_repo=config.dataset_repo, comparison=comparison)
    scan = security_scan(release_root)
    (metadata_dir / "security_scan.json").write_text(json.dumps(scan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = write_release_manifest(
        release_root,
        dataset_repo=config.dataset_repo,
        stats=stats,
        source_entries=all_source_entries,
        data_files=data_files,
    )
    initial_errors = validate_v0_3_release(release_root, require_checksums=False)
    write_validation_report(metadata_dir / "validation_report.md", release_root=release_root, errors=initial_errors)
    write_checksums(release_root, metadata_dir / "checksums.sha256")
    final_errors = validate_v0_3_release(release_root, require_checksums=True)
    if final_errors != initial_errors:
        write_validation_report(metadata_dir / "validation_report.md", release_root=release_root, errors=final_errors)
        write_checksums(release_root, metadata_dir / "checksums.sha256")
        final_errors = validate_v0_3_release(release_root, require_checksums=True)

    return V03BuildResult(
        release_root=release_root,
        manifest_path=release_root / "metadata" / "release_manifest.json",
        total_rows=int(stats["totals"]["row_count"]),
        parquet_bytes=int(stats["totals"]["parquet_bytes"]),
        data_files=tuple(data_files),
        validation_errors=tuple(final_errors),
        security_scan=scan,
        leakage_scan=leakage_scans,
    )


def write_validation_report(output_path: Path, *, release_root: Path, errors: list[str]) -> None:
    status = "passed" if not errors else "failed"
    lines = [
        "# Validation Report",
        "",
        f"- Release root: `{release_root.name}`",
        f"- Validation result: {status}",
        "- Validator: `lafc_evict_dataset.release_v0_3.validate_v0_3_release`",
        "",
    ]
    if errors:
        lines.extend(["## Validation errors", "", *[f"- {e}" for e in errors], ""])
    ensure_parent(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


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
        target = release_root / rel_path.strip()
        if not target.exists():
            errors.append(f"Checksum references missing file: {rel_path}")
            continue
        if sha256_file(target) != expected:
            errors.append(f"Checksum mismatch for {rel_path}")
    return errors


def _validate_data_file(release_root: Path, rel_path: str, *, expected_rows: int) -> list[str]:
    errors: list[str] = []
    path = release_root / rel_path
    if not path.exists():
        return [f"Missing v0.3 data file: {rel_path}"]
    df = pd.read_parquet(path)
    if len(df) != expected_rows:
        errors.append(f"{rel_path} row count mismatch: {len(df)} vs {expected_rows}")
    if set(df["trace_family"].astype(str).unique()) != {SAFE_FAMILY}:
        errors.append(f"{rel_path} contains non-{SAFE_FAMILY} trace_family values")
    if set(df["schema_version"].astype(str).unique()) != {V0_3_SCHEMA_VERSION}:
        errors.append(f"{rel_path} contains unexpected schema_version values")
    if "candidate_page_id_original_present" not in df.columns or bool(df["candidate_page_id_original_present"].any()):
        errors.append(f"{rel_path} does not mark original candidate_page_id as absent")
    if not df["candidate_page_id"].astype(str).map(lambda v: bool(PUBLIC_ID_PATTERN.match(v))).all():
        errors.append(f"{rel_path} has candidate_page_id values outside public pseudonym format")
    if "object_id_public" not in df.columns or not (
        df["candidate_page_id"].astype(str) == df["object_id_public"].astype(str)
    ).all():
        errors.append(f"{rel_path} candidate_page_id and object_id_public differ")
    if df["source_relpath"].astype(str).str.startswith("/").any():
        errors.append(f"{rel_path} contains absolute source_relpath values")
    if df["split"].isna().any():
        errors.append(f"{rel_path} has null split values")
    if str(df["split"].dtype) not in ("object", "string"):
        errors.append(f"{rel_path} split column has unexpected dtype {df['split'].dtype}")
    if "y_loss" in df.columns and "y_value" in df.columns:
        if (df["y_loss"] < 0).any():
            errors.append(f"{rel_path} has negative y_loss values")
        if not (df["y_value"] == -df["y_loss"]).all():
            errors.append(f"{rel_path} y_value does not equal -y_loss for all rows")
        if df["y_loss"].isna().any() or df["y_value"].isna().any():
            errors.append(f"{rel_path} has NaN in y_loss/y_value")
    elif "eviction_loss_label" in df.columns:
        if (df["eviction_loss_label"] < 0).any():
            errors.append(f"{rel_path} has negative eviction_loss_label values")
        if df["eviction_loss_label"].isna().any():
            errors.append(f"{rel_path} has NaN in eviction_loss_label")
    dup_keys = df.duplicated(subset=["decision_id", "candidate_page_id"]).sum()
    if dup_keys:
        errors.append(f"{rel_path} has {dup_keys} duplicate (decision_id, candidate_page_id) keys")
    return errors


def validate_v0_3_release(release_root: str | Path, *, require_checksums: bool = True) -> list[str]:
    root = Path(release_root).expanduser().resolve()
    errors: list[str] = []
    required_files = [
        "README.md",
        "dataset_card.md",
        "RELEASE_NOTES_v0_3.md",
        "metadata/release_manifest.json",
        "metadata/sampling_manifest.json",
        "metadata/provenance_summary.csv",
        "metadata/schema.json",
        "metadata/statistics.json",
        "metadata/security_scan.json",
        "metadata/validation_report.md",
        "metadata/transformation_manifest.json",
    ]
    if require_checksums:
        required_files.append("metadata/checksums.sha256")
    for rel_path in required_files:
        if not (root / rel_path).exists():
            errors.append(f"Missing required v0.3 artifact: {rel_path}")
    if errors:
        return errors

    manifest = _read_json(root / "metadata" / "release_manifest.json")
    stats = _read_json(root / "metadata" / "statistics.json")
    scan = _read_json(root / "metadata" / "security_scan.json")
    if manifest.get("included_families") != [SAFE_FAMILY]:
        errors.append("Release manifest must include only wiki2018")
    if sorted(str(v) for v in manifest.get("excluded_families", [])) != sorted(V0_3_EXCLUDED_FAMILIES):
        errors.append("Release manifest excluded_families does not match the conservative v0.3 scope")
    if not manifest.get("object_ids_pseudonymized"):
        errors.append("Release manifest does not mark object identifiers as pseudonymized")
    if not scan.get("passed"):
        errors.append("Security scan did not pass")

    data_files = [str(p) for p in manifest.get("data_files", [])]
    if sorted(data_files) != [f"data/{name}.parquet" for name in sorted(V0_3_CONFIGS)]:
        errors.append("Release manifest data_files does not contain the expected two v0.3 configs")
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
