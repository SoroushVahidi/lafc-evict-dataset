from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from lafc_evict_dataset.release_v0_3 import (
    V0_3_EXCLUDED_FAMILIES,
    V0_3_SCHEMA_VERSION,
    V03BuildConfig,
    build_v0_3_candidate_release,
    pseudonym_collision_scan,
    raw_title_leakage_scan,
    validate_v0_3_release,
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
            "candidate_page_id": f"en:Raw_Page_Title_{capacity}_{prefix}_{index}",
            "split": "train",
            "y_loss": float(index % 5),
            "y_value": float(-(index % 5)),
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


def _write_fixture_sources(tmp_path: Path, *, include_off_family: bool = False) -> tuple[Path, Path]:
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
    if include_off_family:
        contaminated = _candidate_rows(32, count=2, prefix="leak", objective=False)
        contaminated["trace_family"] = "brightkite"
        contaminated.to_csv(
            cross_root / "brightkite" / "shards" / "wiki2018_pageviews_en_50k__cap32.part9999.csv",
            index=False,
        )
    return cross_root, objective_root


def test_pseudonymize_object_id_is_deterministic_and_public_shaped() -> None:
    from lafc_evict_dataset.preview import pseudonymize_object_id

    value = pseudonymize_object_id("en:Some_Raw_Wiki_Title")
    assert value == pseudonymize_object_id("en:Some_Raw_Wiki_Title")
    assert value != pseudonymize_object_id("en:Another_Title")
    assert re.fullmatch(r"obj_[0-9a-f]{24}", value)


def test_build_v0_3_release_wiki2018_only_and_expanded(tmp_path: Path) -> None:
    cross_root, objective_root = _write_fixture_sources(tmp_path)
    release_dir = tmp_path / "release" / "lafc-evict-v0.3-candidate"

    result = build_v0_3_candidate_release(
        V03BuildConfig(
            output_dir=release_dir,
            repo_root=_repo_root(),
            cross_family_root=cross_root,
            objective_root=objective_root,
            capacities=(32, 64),
            overwrite=True,
        ),
        v0_2_rows=4_800_000,
    )

    assert result.validation_errors == ()
    # full inclusion: 2 shards x 2 capacities x 6 rows = 24 rows per config
    assert result.total_rows == 48
    assert result.security_scan["passed"] is True
    assert all(scan["passed"] for scan in result.leakage_scan.values())
    assert validate_v0_3_release(release_dir) == []

    manifest = json.loads((release_dir / "metadata" / "release_manifest.json").read_text(encoding="utf-8"))
    assert manifest["included_families"] == ["wiki2018"]
    assert sorted(manifest["excluded_families"]) == sorted(V0_3_EXCLUDED_FAMILIES)
    assert manifest["schema_version"] == V0_3_SCHEMA_VERSION
    assert manifest["object_ids_pseudonymized"] is True
    assert manifest["supersedes"] == "v0.2-preview"

    cross = pd.read_parquet(release_dir / "data" / "cross_family_evict_value_v1.parquet")
    assert set(cross["trace_family"]) == {"wiki2018"}
    assert set(cross["schema_version"]) == {V0_3_SCHEMA_VERSION}
    assert cross["candidate_page_id"].str.match(r"^obj_[0-9a-f]{24}$").all()
    assert not cross["candidate_page_id_original_present"].any()
    assert not cross["source_relpath"].str.startswith("/").any()
    # split-dtype regression guard: single-file write must yield one consistent dtype
    assert str(cross["split"].dtype) in ("object", "string")
    assert cross["split"].isna().sum() == 0
    # no raw page titles anywhere in the public columns
    assert not cross["candidate_page_id"].astype(str).str.contains("Raw_Page_Title").any()
    for col in cross.columns:
        if cross[col].dtype == object:
            assert not cross[col].astype(str).str.contains("Raw_Page_Title", regex=False).any()


def test_v0_3_refuses_off_family_shard_via_fold_naming_leakage(tmp_path: Path) -> None:
    cross_root, objective_root = _write_fixture_sources(tmp_path, include_off_family=True)
    release_dir = tmp_path / "release" / "lafc-evict-v0.3-candidate"

    with pytest.raises(ValueError, match="non-wiki2018"):
        build_v0_3_candidate_release(
            V03BuildConfig(
                output_dir=release_dir,
                repo_root=_repo_root(),
                cross_family_root=cross_root,
                objective_root=objective_root,
                capacities=(32,),
                overwrite=True,
            )
        )


def test_raw_title_leakage_scan_detects_injected_leak() -> None:
    df = pd.DataFrame(
        {
            "candidate_page_id_raw": ["en:Leaked_Title", "en:Other_Title"],
            "object_id_public": ["obj_aaaa", "obj_bbbb"],
        }
    )
    clean_output = pd.DataFrame({"candidate_page_id": ["obj_aaaa", "obj_bbbb"]})
    leaked_output = pd.DataFrame({"candidate_page_id": ["obj_aaaa", "en:Leaked_Title"]})

    assert raw_title_leakage_scan(df, clean_output)["passed"] is True
    leaked = raw_title_leakage_scan(df, leaked_output)
    assert leaked["passed"] is False
    assert leaked["leaked_value_count"] == 1


def test_pseudonym_collision_scan_detects_collision() -> None:
    df = pd.DataFrame(
        {
            "candidate_page_id_raw": ["en:A", "en:B"],
            "object_id_public": ["obj_same", "obj_same"],
        }
    )
    scan = pseudonym_collision_scan(df)
    assert scan["passed"] is False
    assert scan["colliding_pseudonym_count"] == 1


def test_build_v0_3_wiki_release_cli(tmp_path: Path) -> None:
    cross_root, objective_root = _write_fixture_sources(tmp_path)
    release_dir = tmp_path / "release" / "lafc-evict-v0.3-candidate"

    subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "scripts" / "build_v0_3_wiki_release.py"),
            "--output-dir",
            str(release_dir),
            "--cross-family-root",
            str(cross_root),
            "--objective-root",
            str(objective_root),
            "--capacity",
            "32,64",
            "--overwrite",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert validate_v0_3_release(release_dir) == []
