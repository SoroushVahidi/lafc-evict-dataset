from __future__ import annotations

import csv
import datetime as dt
import json
import math
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from lafc_evict_dataset.schema import (  # noqa: E402
    BASE_REQUIRED_COLUMNS,
    DECISION_METADATA_COLUMNS,
    FEATURE_COLUMNS,
)

DEFAULT_BATCH_SIZE = 65_536
DEFAULT_GROUP_BY = ("split", "trace_family", "capacity", "horizon")
DEFAULT_QUANTILES = (0.05, 0.25, 0.5, 0.75, 0.95)
DEFAULT_RESERVOIR_SIZE = 16_384
GROUP_KEY_SEPARATOR = "\u241f"
MASK_64 = (1 << 64) - 1


def load_manifest(release_root: Path) -> dict[str, object]:
    return json.loads((release_root / "metadata" / "release_manifest.json").read_text(encoding="utf-8"))


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def parquet_schema_names(path: Path) -> list[str]:
    return pq.ParquetFile(path).schema_arrow.names


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(path.name + ".tmp")
    temp_path.write_text(text, encoding="utf-8")
    os.replace(temp_path, path)


def write_json(path: Path, payload: dict[str, object]) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: Sequence[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    temp_path = path.with_name(path.name + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _jsonable(value) for key, value in row.items()})
    os.replace(temp_path, path)


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


def release_identity(manifest: dict[str, object]) -> dict[str, object]:
    return {
        "dataset_name": manifest.get("dataset_name"),
        "version": manifest.get("version"),
        "release_type": manifest.get("release_type"),
        "schema_version": manifest.get("schema_version"),
    }


def detected_validation_status(release_root: Path) -> str:
    report_path = release_root / "metadata" / "validation_report.md"
    if not report_path.exists():
        return "unknown"
    text = report_path.read_text(encoding="utf-8", errors="replace")
    if "Validation result: passed" in text:
        return "passed"
    if "Validation result: failed" in text:
        return "failed"
    return "unknown"


def candidate_partition_entries(manifest: dict[str, object]) -> list[dict[str, object]]:
    partitions = manifest.get("candidate_partitions", [])
    if not isinstance(partitions, list) or not partitions:
        raise ValueError("release manifest does not list candidate partitions")
    entries: list[dict[str, object]] = []
    for entry in partitions:
        if not isinstance(entry, dict) or "path" not in entry:
            raise ValueError("candidate partition entry is malformed")
        entries.append(entry)
    return entries


def candidate_partition_paths(release_root: Path, manifest: dict[str, object]) -> list[Path]:
    return [release_root / str(entry["path"]) for entry in candidate_partition_entries(manifest)]


def first_candidate_partition_path(release_root: Path, manifest: dict[str, object]) -> Path:
    return candidate_partition_paths(release_root, manifest)[0]


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


def candidate_file_inventory(release_root: Path, manifest: dict[str, object]) -> list[dict[str, object]]:
    entries = candidate_partition_entries(manifest)
    inventory: list[dict[str, object]] = []
    for entry in entries:
        relative_path = str(entry["path"])
        inventory.append(
            {
                "relative_path": relative_path,
                "path": release_root / relative_path,
                "row_count": entry.get("row_count"),
                "split": entry.get("split"),
                "trace_family": entry.get("trace_family"),
                "capacity": entry.get("capacity"),
                "horizon": entry.get("horizon"),
            }
        )
    return inventory


def duplicate_partition_keys(inventory: Sequence[dict[str, object]]) -> list[tuple[object, object, object, object]]:
    seen: set[tuple[object, object, object, object]] = set()
    duplicates: set[tuple[object, object, object, object]] = set()
    for item in inventory:
        key = (
            item.get("split"),
            item.get("trace_family"),
            item.get("capacity"),
            item.get("horizon"),
        )
        if key in seen:
            duplicates.add(key)
        seen.add(key)
    return sorted(duplicates)


def manifest_row_count(manifest: dict[str, object], key: str) -> int | None:
    row_counts = manifest.get("row_counts", {})
    value = row_counts.get(key) if isinstance(row_counts, dict) else None
    return int(value) if isinstance(value, (int, float)) else None


def ensure_output_dir_safe(output_dir: Path, release_root: Path) -> Path:
    resolved_output = output_dir.resolve()
    resolved_release = release_root.resolve()
    if _is_relative_to(resolved_output, resolved_release):
        raise ValueError(f"Refusing to write outputs under release root: {resolved_output}")
    resolved_output.mkdir(parents=True, exist_ok=True)
    return resolved_output


def guard_output_path(path: Path, release_root: Path) -> Path:
    resolved = path.resolve()
    resolved_release = release_root.resolve()
    if _is_relative_to(resolved, resolved_release):
        raise ValueError(f"Refusing to write output under release root: {resolved}")
    return resolved


def reset_outputs(
    *,
    output_paths: Sequence[Path],
    checkpoint_paths: Sequence[Path],
    overwrite: bool,
    resume: bool,
) -> None:
    if overwrite and resume:
        raise ValueError("Use either --overwrite or --resume, not both")

    existing_outputs = [path for path in output_paths if path.exists()]
    existing_checkpoints = [path for path in checkpoint_paths if path.exists()]

    if overwrite:
        for path in [*existing_outputs, *existing_checkpoints]:
            if path.is_file():
                path.unlink()
        return

    if resume:
        if existing_outputs and not existing_checkpoints:
            raise ValueError(
                "Refusing to resume because final outputs already exist and no checkpoint remains. "
                "Use --overwrite to replace them."
            )
        return

    if existing_outputs or existing_checkpoints:
        raise ValueError(
            "Output path or checkpoint already exists. Use --overwrite to replace or --resume to continue."
        )


def checkpoint_path(output_dir: Path, stem: str) -> Path:
    return output_dir / f".{stem}.checkpoint.json"


def save_checkpoint(path: Path, payload: dict[str, object]) -> None:
    write_json(path, payload)


def load_checkpoint(path: Path, *, missing_ok: bool = False) -> dict[str, object] | None:
    if not path.exists():
        if missing_ok:
            return None
        raise FileNotFoundError(f"Checkpoint does not exist: {path}")
    try:
        payload = read_json(path)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Checkpoint file is corrupt: {path}. Delete it or rerun with --overwrite to start fresh."
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError(
            f"Checkpoint file must contain a JSON object: {path}. Delete it or rerun with --overwrite to start fresh."
        )
    return payload


def remove_checkpoint(path: Path) -> None:
    if path.exists():
        path.unlink()


def iter_candidate_batches(
    file_path: Path,
    *,
    columns: Sequence[str],
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> Iterator[pd.DataFrame]:
    parquet = pq.ParquetFile(file_path)
    for batch in parquet.iter_batches(columns=list(columns), batch_size=batch_size):
        yield batch.to_pandas()


def build_file_budget(max_files: int | None) -> int | None:
    if max_files is None:
        return None
    if max_files <= 0:
        raise ValueError("--max-files must be a positive integer")
    return max_files


def consume_budget(budget: int | None) -> int | None:
    if budget is None:
        return None
    return budget - 1


def budget_exhausted(budget: int | None) -> bool:
    return budget is not None and budget <= 0


def encode_group_key(values: Sequence[object]) -> str:
    return GROUP_KEY_SEPARATOR.join("" if value is None else str(value) for value in values)


def decode_group_key(key: str) -> list[str]:
    return key.split(GROUP_KEY_SEPARATOR)


def group_record(group_by: Sequence[str], key: str) -> dict[str, object]:
    values = decode_group_key(key)
    return {column: _coerce_group_value(values[index]) for index, column in enumerate(group_by)}


def available_feature_columns(schema: Sequence[str], requested: Sequence[str] | None = None) -> list[str]:
    if requested:
        requested_list = [column.strip() for column in requested if column.strip()]
        missing = require_columns(schema, requested_list)
        if missing:
            raise ValueError("Requested feature columns missing from candidate schema: " + ", ".join(missing))
        return requested_list
    return [column for column in FEATURE_COLUMNS if column in schema]


def decision_key_columns() -> list[str]:
    """Canonical decision identity: the 9-column DECISION_METADATA_COLUMNS key.

    This must match the key used to build decision_view.parquet
    (see DECISION_METADATA_COLUMNS in lafc_evict_dataset.schema) so that
    streaming evaluators count exactly one decision per true release decision.
    A narrower key (e.g. omitting dataset_source/decision_t/decision_chunk_id)
    can silently double-count a single decision whose rows are not contiguous
    within a partition.
    """
    return list(DECISION_METADATA_COLUMNS)


def sanitize_output_name(name: str) -> str:
    cleaned = []
    for char in name:
        if char.isalnum() or char in {"_", "-"}:
            cleaned.append(char)
        else:
            cleaned.append("_")
    return "".join(cleaned)


def current_timestamp_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def current_git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    return result.stdout.strip() or None


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _jsonable(value: object) -> object:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def _coerce_group_value(value: str) -> object:
    if value == "":
        return ""
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _splitmix64(value: int) -> int:
    result = (value + 0x9E3779B97F4A7C15) & MASK_64
    result = ((result ^ (result >> 30)) * 0xBF58476D1CE4E5B9) & MASK_64
    result = ((result ^ (result >> 27)) * 0x94D049BB133111EB) & MASK_64
    return (result ^ (result >> 31)) & MASK_64


@dataclass
class DeterministicReservoir:
    size: int = DEFAULT_RESERVOIR_SIZE
    seed: int = 7
    seen_count: int = 0
    entries: list[list[float]] = field(default_factory=list)

    def update(self, values: np.ndarray) -> None:
        if self.size <= 0:
            self.seen_count += int(len(values))
            return
        for value in values.tolist():
            self.seen_count += 1
            priority = _splitmix64(self.seed + self.seen_count)
            heap_item = [-float(priority), float(value)]
            if len(self.entries) < self.size:
                import heapq

                heapq.heappush(self.entries, heap_item)
                continue
            current_max_priority = -self.entries[0][0]
            if priority < current_max_priority:
                import heapq

                heapq.heapreplace(self.entries, heap_item)

    def sample_values(self) -> list[float]:
        return [float(item[1]) for item in self.entries]

    def is_approximate(self) -> bool:
        return self.seen_count > self.size

    def to_state(self) -> dict[str, object]:
        return {
            "size": self.size,
            "seed": self.seed,
            "seen_count": self.seen_count,
            "entries": self.entries,
        }

    @classmethod
    def from_state(cls, payload: dict[str, object]) -> "DeterministicReservoir":
        return cls(
            size=int(payload.get("size", DEFAULT_RESERVOIR_SIZE)),
            seed=int(payload.get("seed", 7)),
            seen_count=int(payload.get("seen_count", 0)),
            entries=[[float(item[0]), float(item[1])] for item in payload.get("entries", [])],
        )


@dataclass
class RunningNumericSummary:
    reservoir_size: int = DEFAULT_RESERVOIR_SIZE
    reservoir_seed: int = 7
    count: int = 0
    missing_count: int = 0
    value_sum: float = 0.0
    value_sum_squares: float = 0.0
    minimum: float | None = None
    maximum: float | None = None
    reservoir: DeterministicReservoir = field(default_factory=DeterministicReservoir)

    def __post_init__(self) -> None:
        if self.reservoir.size != self.reservoir_size or self.reservoir.seed != self.reservoir_seed:
            self.reservoir = DeterministicReservoir(size=self.reservoir_size, seed=self.reservoir_seed)

    def update(self, values: np.ndarray) -> None:
        array = np.asarray(values, dtype=float).reshape(-1)
        finite_mask = np.isfinite(array)
        valid = array[finite_mask]
        self.missing_count += int(array.size - valid.size)
        if valid.size == 0:
            return
        self.count += int(valid.size)
        self.value_sum += float(valid.sum())
        self.value_sum_squares += float(np.square(valid).sum())
        current_min = float(valid.min())
        current_max = float(valid.max())
        self.minimum = current_min if self.minimum is None else min(self.minimum, current_min)
        self.maximum = current_max if self.maximum is None else max(self.maximum, current_max)
        self.reservoir.update(valid)

    def merge(self, other: "RunningNumericSummary") -> None:
        self.count += other.count
        self.missing_count += other.missing_count
        self.value_sum += other.value_sum
        self.value_sum_squares += other.value_sum_squares
        if other.minimum is not None:
            self.minimum = other.minimum if self.minimum is None else min(self.minimum, other.minimum)
        if other.maximum is not None:
            self.maximum = other.maximum if self.maximum is None else max(self.maximum, other.maximum)
        self.reservoir.update(np.asarray(other.reservoir.sample_values(), dtype=float))

    def mean(self) -> float | None:
        if self.count == 0:
            return None
        return self.value_sum / self.count

    def variance_population(self) -> float | None:
        if self.count == 0:
            return None
        mean = self.mean()
        if mean is None:
            return None
        variance = (self.value_sum_squares / self.count) - (mean * mean)
        return max(variance, 0.0)

    def std_population(self) -> float | None:
        variance = self.variance_population()
        return math.sqrt(variance) if variance is not None else None

    def quantiles(self, levels: Sequence[float] = DEFAULT_QUANTILES) -> dict[str, float | None]:
        sample = self.reservoir.sample_values()
        if not sample:
            return {f"q{int(level * 100):02d}": None for level in levels}
        sample_array = np.asarray(sorted(sample), dtype=float)
        results: dict[str, float | None] = {}
        for level in levels:
            results[f"q{int(level * 100):02d}"] = float(np.quantile(sample_array, level))
        return results

    def to_summary_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "count": self.count,
            "missing_count": self.missing_count,
            "total_rows_seen": self.count + self.missing_count,
            "min": self.minimum,
            "max": self.maximum,
            "mean": self.mean(),
            "std": self.std_population(),
            "quantiles": self.quantiles(),
            "quantiles_approximate": self.reservoir.is_approximate(),
            "quantile_sample_size": len(self.reservoir.entries),
        }
        return payload

    def to_state(self) -> dict[str, object]:
        return {
            "reservoir_size": self.reservoir_size,
            "reservoir_seed": self.reservoir_seed,
            "count": self.count,
            "missing_count": self.missing_count,
            "value_sum": self.value_sum,
            "value_sum_squares": self.value_sum_squares,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "reservoir": self.reservoir.to_state(),
        }

    @classmethod
    def from_state(cls, payload: dict[str, object]) -> "RunningNumericSummary":
        summary = cls(
            reservoir_size=int(payload.get("reservoir_size", DEFAULT_RESERVOIR_SIZE)),
            reservoir_seed=int(payload.get("reservoir_seed", 7)),
        )
        summary.count = int(payload.get("count", 0))
        summary.missing_count = int(payload.get("missing_count", 0))
        summary.value_sum = float(payload.get("value_sum", 0.0))
        summary.value_sum_squares = float(payload.get("value_sum_squares", 0.0))
        minimum = payload.get("minimum")
        maximum = payload.get("maximum")
        summary.minimum = None if minimum is None else float(minimum)
        summary.maximum = None if maximum is None else float(maximum)
        reservoir_payload = payload.get("reservoir", {})
        if isinstance(reservoir_payload, dict):
            summary.reservoir = DeterministicReservoir.from_state(reservoir_payload)
        return summary
