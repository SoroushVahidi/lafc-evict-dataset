from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SUMMARY_FIELDNAMES = ["split", "trace_family", "capacity", "horizon", "row_count", "decision_count"]


@dataclass(frozen=True)
class CompletedShard:
    trace_family: str
    capacity: int
    path: Path
    expected_row_count: int | None


@dataclass(frozen=True)
class RebuildResult:
    source_root: Path
    split_summary_path: Path
    progress_path: Path
    shard_count: int
    row_count: int
    decision_count: int


def _summary_key(*, split: str, trace_family: str, capacity: int, horizon: int) -> str:
    return f"split={split}|family={trace_family}|capacity={capacity}|horizon={horizon}"


def _materialize_summary_rows(summary_by_key: dict[str, dict[str, int]]) -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    for key in sorted(summary_by_key):
        tokens = dict(token.split("=", 1) for token in key.split("|"))
        counts = summary_by_key[key]
        rows.append(
            {
                "split": tokens["split"],
                "trace_family": tokens["family"],
                "capacity": int(tokens["capacity"]),
                "horizon": int(tokens["horizon"]),
                "row_count": int(counts["row_count"]),
                "decision_count": int(counts["decision_count"]),
            }
        )
    return rows


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    _atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def load_completed_shards(source_root: Path) -> list[CompletedShard]:
    markers = sorted((source_root / "logs").glob("*.done.json"))
    shards: list[CompletedShard] = []
    for marker in markers:
        payload = json.loads(marker.read_text(encoding="utf-8"))
        trace_family = str(payload["trace_family"])
        capacity = int(payload["capacity"])
        for shard in payload.get("shards", []):
            shard_path = Path(str(shard["path"]))
            if not shard_path.is_absolute():
                shard_path = source_root / shard_path
            shards.append(
                CompletedShard(
                    trace_family=trace_family,
                    capacity=capacity,
                    path=shard_path,
                    expected_row_count=int(shard["row_count"]) if shard.get("row_count") is not None else None,
                )
            )
    shards.sort(key=lambda shard: str(shard.path))
    return shards


def _load_progress(progress_path: Path, *, shard_paths: set[str]) -> tuple[set[str], dict[str, dict[str, int]], dict[str, str]]:
    if not progress_path.exists():
        return set(), {}, {}

    payload = json.loads(progress_path.read_text(encoding="utf-8"))
    completed = {str(path) for path in payload.get("completed_shards", []) if str(path) in shard_paths}
    summary_by_key: dict[str, dict[str, int]] = {}
    for key, counts in payload.get("summary_by_key", {}).items():
        if not isinstance(counts, dict):
            continue
        summary_by_key[str(key)] = {
            "row_count": int(counts.get("row_count", 0)),
            "decision_count": int(counts.get("decision_count", 0)),
        }
    last_decision_by_key = {str(key): str(value) for key, value in payload.get("last_decision_by_key", {}).items()}
    return completed, summary_by_key, last_decision_by_key


def _write_progress(
    progress_path: Path,
    *,
    source_root: Path,
    completed: set[str],
    summary_by_key: dict[str, dict[str, int]],
    last_decision_by_key: dict[str, str],
    shard_count: int,
) -> None:
    payload = {
        "source_root": str(source_root),
        "completed_shards": sorted(completed),
        "summary_by_key": summary_by_key,
        "last_decision_by_key": last_decision_by_key,
        "shard_count": shard_count,
        "state": "running" if len(completed) < shard_count else "complete",
    }
    _atomic_write_json(progress_path, payload)


def _process_shard(
    shard: CompletedShard,
    *,
    summary_by_key: dict[str, dict[str, int]],
    last_decision_by_key: dict[str, str],
) -> int:
    with shard.path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        if header is None:
            raise ValueError(f"Shard is empty: {shard.path}")
        indices = {name: idx for idx, name in enumerate(header)}
        required = {"split", "horizon", "decision_id"}
        missing = sorted(required - indices.keys())
        if missing:
            raise ValueError(f"Shard {shard.path} is missing required columns: {missing}")

        row_count = 0
        for row in reader:
            row_count += 1
            split = row[indices["split"]]
            horizon = int(row[indices["horizon"]])
            decision_id = row[indices["decision_id"]]
            key = _summary_key(
                split=split,
                trace_family=shard.trace_family,
                capacity=shard.capacity,
                horizon=horizon,
            )
            counts = summary_by_key.setdefault(key, {"row_count": 0, "decision_count": 0})
            counts["row_count"] += 1
            if last_decision_by_key.get(key) != decision_id:
                counts["decision_count"] += 1
                last_decision_by_key[key] = decision_id

    if shard.expected_row_count is not None and row_count != shard.expected_row_count:
        raise ValueError(
            f"Shard row-count mismatch for {shard.path}: expected {shard.expected_row_count}, observed {row_count}"
        )
    return row_count


def _write_split_summary(path: Path, rows: list[dict[str, int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=SUMMARY_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def rebuild_split_summary_from_completed_units(
    *,
    source_root: Path,
    split_summary_path: Path | None = None,
    progress_path: Path | None = None,
) -> RebuildResult:
    source_root = source_root.resolve()
    split_summary_path = (split_summary_path or (source_root / "split_summary.csv")).resolve()
    progress_path = (progress_path or (source_root / "status" / "split_summary_rebuild_progress.json")).resolve()

    shards = load_completed_shards(source_root)
    if not shards:
        raise ValueError(f"No completed-unit markers found under {source_root / 'logs'}")

    shard_paths = {str(shard.path) for shard in shards}
    completed, summary_by_key, last_decision_by_key = _load_progress(progress_path, shard_paths=shard_paths)
    total_rows = sum(int(counts["row_count"]) for counts in summary_by_key.values())

    for shard in shards:
        shard_id = str(shard.path)
        if shard_id in completed:
            continue
        total_rows += _process_shard(
            shard,
            summary_by_key=summary_by_key,
            last_decision_by_key=last_decision_by_key,
        )
        completed.add(shard_id)
        _write_progress(
            progress_path,
            source_root=source_root,
            completed=completed,
            summary_by_key=summary_by_key,
            last_decision_by_key=last_decision_by_key,
            shard_count=len(shards),
        )

    rows = _materialize_summary_rows(summary_by_key)
    _write_split_summary(split_summary_path, rows)
    _write_progress(
        progress_path,
        source_root=source_root,
        completed=completed,
        summary_by_key=summary_by_key,
        last_decision_by_key=last_decision_by_key,
        shard_count=len(shards),
    )
    return RebuildResult(
        source_root=source_root,
        split_summary_path=split_summary_path,
        progress_path=progress_path,
        shard_count=len(shards),
        row_count=sum(int(row["row_count"]) for row in rows),
        decision_count=sum(int(row["decision_count"]) for row in rows),
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Rebuild Wulver split_summary.csv from completed-unit markers and shard CSVs. "
            "The progress file makes the shard scan resumable."
        )
    )
    ap.add_argument("--source-root", type=Path, required=True)
    ap.add_argument("--out-split-summary", type=Path, default=None)
    ap.add_argument("--progress-file", type=Path, default=None)
    args = ap.parse_args()

    result = rebuild_split_summary_from_completed_units(
        source_root=args.source_root,
        split_summary_path=args.out_split_summary,
        progress_path=args.progress_file,
    )
    print(
        "Rebuilt split summary",
        f"source_root={result.source_root}",
        f"shards={result.shard_count}",
        f"rows={result.row_count}",
        f"decisions={result.decision_count}",
        f"split_summary={result.split_summary_path}",
        f"progress={result.progress_path}",
    )


if __name__ == "__main__":
    main()
