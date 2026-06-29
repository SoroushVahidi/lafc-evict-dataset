from __future__ import annotations

import csv
import json
from pathlib import Path

from lafc_evict_dataset.wulver_source_summary import rebuild_split_summary_from_completed_units


FIELDNAMES = [
    "trace_name",
    "trace_family",
    "dataset_source",
    "capacity",
    "horizon",
    "decision_id",
    "decision_t",
    "decision_chunk_id",
    "candidate_page_id",
    "split",
    "y_loss",
    "y_value",
]


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def _row(*, decision_id: str, candidate_page_id: str, split: str, horizon: int) -> dict[str, object]:
    return {
        "trace_name": "cloudphysics_demo",
        "trace_family": "cloudphysics",
        "dataset_source": "cloudphysics",
        "capacity": 32,
        "horizon": horizon,
        "decision_id": decision_id,
        "decision_t": 1,
        "decision_chunk_id": 0,
        "candidate_page_id": candidate_page_id,
        "split": split,
        "y_loss": 1.0,
        "y_value": -1.0,
    }


def test_rebuild_split_summary_from_completed_units(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    logs_dir = source_root / "logs"
    shard_dir = source_root / "shards"
    logs_dir.mkdir(parents=True)
    shard_dir.mkdir(parents=True)

    shard0 = shard_dir / "cloudphysics_demo__cap32.part0000.csv"
    shard1 = shard_dir / "cloudphysics_demo__cap32.part0001.csv"
    _write_rows(
        shard0,
        [
            _row(decision_id="d1", candidate_page_id="A", split="train", horizon=4),
            _row(decision_id="d1", candidate_page_id="A", split="train", horizon=8),
            _row(decision_id="d1", candidate_page_id="B", split="train", horizon=4),
            _row(decision_id="d1", candidate_page_id="B", split="train", horizon=8),
            _row(decision_id="d2", candidate_page_id="C", split="val", horizon=4),
        ],
    )
    _write_rows(
        shard1,
        [
            _row(decision_id="d2", candidate_page_id="D", split="val", horizon=4),
            _row(decision_id="d3", candidate_page_id="E", split="test", horizon=4),
            _row(decision_id="d3", candidate_page_id="F", split="test", horizon=4),
        ],
    )

    done_marker = logs_dir / "cloudphysics_demo__cap32.done.json"
    done_marker.write_text(
        json.dumps(
            {
                "trace_path": "data/processed/cloudphysics/trace.jsonl",
                "trace_name": "cloudphysics_demo",
                "dataset_source": "cloudphysics",
                "trace_family": "cloudphysics",
                "capacity": 32,
                "shards": [
                    {"path": str(shard0), "row_count": 5},
                    {"path": str(shard1), "row_count": 3},
                ],
            }
        ),
        encoding="utf-8",
    )

    result = rebuild_split_summary_from_completed_units(source_root=source_root)

    rows = list(csv.DictReader((source_root / "split_summary.csv").open(encoding="utf-8")))
    assert result.row_count == 8
    assert result.decision_count == 4
    assert rows == [
        {
            "split": "test",
            "trace_family": "cloudphysics",
            "capacity": "32",
            "horizon": "4",
            "row_count": "2",
            "decision_count": "1",
        },
        {
            "split": "train",
            "trace_family": "cloudphysics",
            "capacity": "32",
            "horizon": "4",
            "row_count": "2",
            "decision_count": "1",
        },
        {
            "split": "train",
            "trace_family": "cloudphysics",
            "capacity": "32",
            "horizon": "8",
            "row_count": "2",
            "decision_count": "1",
        },
        {
            "split": "val",
            "trace_family": "cloudphysics",
            "capacity": "32",
            "horizon": "4",
            "row_count": "2",
            "decision_count": "1",
        },
    ]

    progress_payload = json.loads((source_root / "status" / "split_summary_rebuild_progress.json").read_text())
    assert progress_payload["state"] == "complete"
    assert len(progress_payload["completed_shards"]) == 2
