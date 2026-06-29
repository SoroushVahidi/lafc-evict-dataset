from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from lafc_evict_dataset.schema import BASE_REQUIRED_COLUMNS, FEATURE_COLUMNS  # noqa: E402


def load_manifest(release_root: Path) -> dict[str, object]:
    return json.loads((release_root / "metadata" / "release_manifest.json").read_text())


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def parquet_schema_names(path: Path) -> list[str]:
    return pq.ParquetFile(path).schema_arrow.names


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def require_columns(available: Iterable[str], required: Iterable[str]) -> list[str]:
    available_set = set(available)
    return [column for column in required if column not in available_set]


def release_summary(manifest: dict[str, object]) -> dict[str, object]:
    row_counts = manifest.get("row_counts", {})
    return {
        "candidate_rows": row_counts.get("candidate_rows"),
        "decision_rows": row_counts.get("decision_view"),
        "pairwise_sample_rows": row_counts.get("pairwise_sample"),
        "selected_families": manifest.get("selected_families", []),
        "excluded_families": manifest.get("excluded_families", []),
        "candidate_partitions": len(manifest.get("candidate_partitions", [])),
    }


def first_candidate_partition_path(release_root: Path, manifest: dict[str, object]) -> Path:
    partitions = manifest.get("candidate_partitions", [])
    if not partitions:
        raise ValueError("release manifest does not list candidate partitions")
    first = partitions[0]
    if not isinstance(first, dict) or "path" not in first:
        raise ValueError("candidate partition entry is malformed")
    return release_root / str(first["path"])


def candidate_schema_summary(release_root: Path, manifest: dict[str, object]) -> dict[str, object]:
    sample_path = first_candidate_partition_path(release_root, manifest)
    available = parquet_schema_names(sample_path)
    return {
        "sample_partition_path": repo_relative(sample_path),
        "required_columns": BASE_REQUIRED_COLUMNS,
        "feature_columns": FEATURE_COLUMNS,
        "available_columns": available,
        "missing_required_columns": require_columns(available, BASE_REQUIRED_COLUMNS),
        "missing_feature_columns": require_columns(available, FEATURE_COLUMNS),
    }
