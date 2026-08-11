from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

from lafc_evict_dataset.preview import (
    PREVIEW_SEED,
    PreviewBuildConfig,
    build_preview_release,
    deterministic_sample,
    pseudonymize_object_id,
    validate_preview_release,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _candidate_rows(capacity: int, *, count: int, prefix: str, objective: bool) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for index in range(count):
        row = {
            "trace_name": "wiki2018_pageviews_en_50k",
            "trace_family": "wiki2018",
            "dataset_source": "fixture",
            "capacity": capacity,
            "horizon": 64,
            "decision_id": f"{prefix}-d{index // 2}",
            "decision_t": index,
            "decision_chunk_id": 0,
            "candidate_page_id": f"page-{capacity}-{prefix}-{index}",
            "split": "train",
            "y_loss": float(index % 5),
            "y_value": float(10 - (index % 5)),
            "request_bucket": 1.0,
            "request_confidence": 0.5,
            "candidate_bucket": 2.0,
            "candidate_confidence": 0.25,
            "candidate_recency_rank": float(index),
            "candidate_age_norm": 0.1,
            "candidate_predictor_score": 0.2,
            "candidate_lru_score": 0.3,
            "candidate_is_predictor_victim": 0.0,
            "candidate_is_lru_victim": 1.0,
            "score_gap_to_predictor_best": 0.0,
            "score_gap_to_lru_victim": 0.0,
            "bucket_gap_to_predictor_best": 0.0,
            "bucket_gap_to_lru_victim": 0.0,
            "confidence_gap_to_predictor_best": 0.0,
            "confidence_gap_to_lru_victim": 0.0,
            "cache_bucket_mean": 1.0,
            "cache_bucket_std": 0.0,
            "cache_bucket_min": 1.0,
            "cache_bucket_max": 2.0,
            "cache_unique_bucket_count": 2.0,
            "cache_confidence_mean": 0.4,
            "cache_confidence_std": 0.1,
            "predictor_lru_disagree": 1.0,
            "recent_candidate_request_rate": 0.01,
            "recent_candidate_hit_rate": 0.02,
        }
        if objective:
            row.update(
                {
                    "example_id": f"raw-{capacity}-{index}",
                    "eviction_loss_label": float(index),
                    "next_arrival_label_raw": float(index + 1),
                    "next_arrival_label_censored": float(index + 1),
                    "next_arrival_censored_flag": 0,
                    "reuse_distance_label_raw": float(index + 2),
                    "reuse_distance_label_censored": float(index + 2),
                    "reuse_distance_censored_flag": 0,
                }
            )
            row.pop("dataset_source")
            row.pop("decision_chunk_id")
            row.pop("y_loss")
            row.pop("y_value")
        rows.append(row)
    return pd.DataFrame(rows)


def _write_fixture_sources(tmp_path: Path) -> tuple[Path, Path]:
    cross_root = tmp_path / "cross"
    objective_root = tmp_path / "objective"
    for capacity in (32, 64):
        for part in range(2):
            cross_dir = cross_root / "brightkite" / "shards"
            cross_dir.mkdir(parents=True, exist_ok=True)
            _candidate_rows(capacity, count=6, prefix=f"c{part}", objective=False).to_csv(
                cross_dir / f"wiki2018_pageviews_en_50k__cap{capacity}.part{part:04d}.csv",
                index=False,
            )
            objective_dir = objective_root / "brightkite" / "scalar" / "shards"
            objective_dir.mkdir(parents=True, exist_ok=True)
            _candidate_rows(capacity, count=6, prefix=f"o{part}", objective=True).to_csv(
                objective_dir / f"wiki2018_pageviews_en_50k__cap{capacity}.part{part:04d}.csv",
                index=False,
            )
    return cross_root, objective_root


def test_deterministic_sample_uses_stable_seed_and_source_position() -> None:
    df = pd.DataFrame(
        {
            "capacity": [32, 32, 32, 64, 64],
            "source_relpath": ["a.csv", "a.csv", "b.csv", "c.csv", "c.csv"],
            "source_row_number": [0, 1, 0, 0, 1],
        }
    )

    first = deterministic_sample(df, dataset_key="cross_family_evict_value_v1", rows_per_capacity=1)
    second = deterministic_sample(df.sample(frac=1, random_state=7), dataset_key="cross_family_evict_value_v1", rows_per_capacity=1)

    assert first[["capacity", "source_relpath", "source_row_number"]].to_dict("records") == second[
        ["capacity", "source_relpath", "source_row_number"]
    ].to_dict("records")
    assert set(first["capacity"]) == {32, 64}


def test_pseudonymize_object_id_is_deterministic_and_public_shaped() -> None:
    value = pseudonymize_object_id("wiki-page-title-or-id")
    assert value == pseudonymize_object_id("wiki-page-title-or-id")
    assert value != pseudonymize_object_id("another-page")
    assert re.fullmatch(r"obj_[0-9a-f]{24}", value)


def test_build_preview_release_and_validator(tmp_path: Path) -> None:
    cross_root, objective_root = _write_fixture_sources(tmp_path)
    release_dir = tmp_path / "release" / "lafc-evict-v0.2-preview"

    result = build_preview_release(
        PreviewBuildConfig(
            output_dir=release_dir,
            repo_root=_repo_root(),
            cross_family_root=cross_root,
            objective_root=objective_root,
            capacities=(32, 64),
            cross_family_rows_per_capacity=3,
            objective_rows_per_capacity=2,
            shards_per_capacity=2,
            overwrite=True,
        )
    )

    assert result.validation_errors == ()
    assert result.total_rows == 10
    assert validate_preview_release(release_dir) == []

    manifest = json.loads((release_dir / "metadata" / "release_manifest.json").read_text(encoding="utf-8"))
    assert manifest["release_type"] == "real_data_preview"
    assert manifest["included_families"] == ["wiki2018"]
    assert sorted(manifest["data_files"]) == [
        "data/cross_family_evict_value_v1.parquet",
        "data/objective_ablation_scalar.parquet",
    ]

    cross = pd.read_parquet(release_dir / "data" / "cross_family_evict_value_v1.parquet")
    assert set(cross["sampling_seed"]) == {PREVIEW_SEED}
    assert cross["candidate_page_id"].str.match(r"^obj_[0-9a-f]{24}$").all()
    assert not cross["candidate_page_id_original_present"].any()
    assert not cross["source_relpath"].str.startswith("/").any()


def test_build_v0_2_preview_cli_and_hf_dry_run(tmp_path: Path) -> None:
    cross_root, objective_root = _write_fixture_sources(tmp_path)
    release_dir = tmp_path / "release" / "lafc-evict-v0.2-preview"

    subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "scripts" / "build_v0_2_preview.py"),
            "--output-dir",
            str(release_dir),
            "--cross-family-root",
            str(cross_root),
            "--objective-root",
            str(objective_root),
            "--capacity",
            "32,64",
            "--cross-family-rows-per-capacity",
            "3",
            "--objective-rows-per-capacity",
            "2",
            "--shards-per-capacity",
            "2",
            "--overwrite",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    validation = subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "scripts" / "validate_v0_2_preview.py"),
            "--release-dir",
            str(release_dir),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(validation.stdout)["passed"] is True

    dry_run = subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "scripts" / "publish_to_huggingface.py"),
            "--release-dir",
            str(release_dir),
            "--repo-id",
            "SoroushVahidi/lafc-evict-sample",
            "--repo-type",
            "dataset",
            "--allow-public",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(dry_run.stdout)
    assert "data/cross_family_evict_value_v1.parquet" in payload["files"]
    assert "data/objective_ablation_scalar.parquet" in payload["files"]
