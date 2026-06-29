from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

from lafc_evict_dataset.real_release import (
    dry_run_export_plan,
    filter_candidate_dataframe_by_family,
    infer_trace_family_from_path,
    summarize_candidate_source,
)
from lafc_evict_dataset.real_release_build import build_real_release
from lafc_evict_dataset.real_release_build import (
    _checksum_lines,
    _consolidate_partition_parquet_files,
    _count_candidate_rows,
    _duckdb_connect,
    _register_candidate_partitions,
)
from lafc_evict_dataset.real_release_migration import migrate_real_release_contract
from lafc_evict_dataset.real_release_validation import validate_real_release
from lafc_evict_dataset.release_metadata import collect_release_file_inventory
from lafc_evict_dataset.io import resolve_candidate_files
from lafc_evict_dataset.views import DECISION_VIEW_COLUMNS, build_decision_view


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _build_candidate_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    source_dir = tmp_path / "source"
    shard_dir = source_dir / "shards"
    shard_dir.mkdir(parents=True)

    columns = [
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
        "request_bucket",
        "request_confidence",
        "candidate_bucket",
        "candidate_confidence",
        "candidate_recency_rank",
        "candidate_age_norm",
        "candidate_predictor_score",
        "candidate_lru_score",
        "candidate_is_predictor_victim",
        "candidate_is_lru_victim",
        "score_gap_to_predictor_best",
        "score_gap_to_lru_victim",
        "bucket_gap_to_predictor_best",
        "bucket_gap_to_lru_victim",
        "confidence_gap_to_predictor_best",
        "confidence_gap_to_lru_victim",
        "cache_bucket_mean",
        "cache_bucket_std",
        "cache_bucket_min",
        "cache_bucket_max",
        "cache_unique_bucket_count",
        "cache_confidence_mean",
        "cache_confidence_std",
        "predictor_lru_disagree",
        "recent_candidate_request_rate",
        "recent_candidate_hit_rate",
    ]

    allowed = pd.DataFrame(
        [
            ["t1", "cloudphysics", "src", 32, 4, "d1", 1, 0, "A", "train", 1.0, -1.0, *([0.0] * 26)],
            ["t1", "cloudphysics", "src", 32, 4, "d1", 1, 0, "B", "train", 2.0, -2.0, *([0.0] * 26)],
            ["t1", "cloudphysics", "src", 32, 4, "d2", 2, 0, "C", "val", 1.0, -1.0, *([0.0] * 26)],
            ["t1", "cloudphysics", "src", 32, 4, "d2", 2, 0, "D", "val", 2.0, -2.0, *([0.0] * 26)],
            ["t1", "cloudphysics", "src", 32, 4, "d3", 3, 0, "E", "test", 1.0, -1.0, *([0.0] * 26)],
            ["t1", "cloudphysics", "src", 32, 4, "d3", 3, 0, "F", "test", 2.0, -2.0, *([0.0] * 26)],
        ],
        columns=columns,
    )
    blocked = pd.DataFrame(
        [
            ["t2", "citibike", "src", 32, 4, "d2", 1, 0, "C", "test", 1.0, -1.0, *([0.0] * 26)],
            ["t2", "citibike", "src", 32, 4, "d2", 1, 0, "D", "test", 2.0, -2.0, *([0.0] * 26)],
        ],
        columns=columns,
    )

    allowed_path = shard_dir / "cloudphysics_demo__cap32.part0000.csv"
    blocked_path = shard_dir / "citibike_demo__cap32.part0000.csv"
    allowed.to_csv(allowed_path, index=False)
    blocked.to_csv(blocked_path, index=False)

    manifest_path = source_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "format": "evict_value_v1_wulver_candidate_csv_shards",
                "shards": [
                    {"path": f"shards/{allowed_path.name}", "row_count": 6},
                    {"path": f"shards/{blocked_path.name}", "row_count": 2},
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    split_summary_path = source_dir / "split_summary.csv"
    split_summary_path.write_text(
        "\n".join(
            [
                "split,trace_family,capacity,horizon,row_count,decision_count",
                "train,cloudphysics,32,4,2,1",
                "val,cloudphysics,32,4,2,1",
                "test,cloudphysics,32,4,2,1",
                "test,citibike,32,4,2,1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    selection_path = tmp_path / "families.json"
    selection_path.write_text(
        json.dumps(
            {
                "selected_families": ["cloudphysics"],
                "excluded_families": [
                    {"family": "citibike", "reason": "blocked"},
                    {"family": "brightkite", "reason": "blocked"},
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return manifest_path, selection_path, source_dir


def _downgrade_real_release_to_stale_contract(release_dir: Path) -> None:
    candidate_paths = sorted((release_dir / "data" / "candidate_rows").rglob("candidate_rows.parquet"))
    candidates = pd.concat([pd.read_parquet(path) for path in candidate_paths], ignore_index=True)
    group_cols = ["decision_id", "capacity", "horizon", "split", "trace_family", "trace_name"]

    def _stale_row(group: pd.DataFrame) -> pd.Series:
        best = group["y_loss"].min()
        best_candidates = (
            group.loc[group["y_loss"] == best, "candidate_page_id"].astype(str).sort_values().tolist()
        )
        return pd.Series(
            {
                "candidate_count": int(group["candidate_page_id"].nunique()),
                "min_y_loss": float(group["y_loss"].min()),
                "max_y_loss": float(group["y_loss"].max()),
                "mean_y_loss": float(group["y_loss"].mean()),
                "tie_count": int((group["y_loss"] == best).sum()),
                "best_candidate_page_id": best_candidates[0],
            }
        )

    stale_decision_view = (
        candidates.groupby(group_cols, dropna=False, sort=True).apply(_stale_row).reset_index()
    )
    stale_decision_path = release_dir / "data" / "decision_view" / "decision_view.parquet"
    stale_decision_view.to_parquet(stale_decision_path, index=False)

    manifest_path = release_dir / "metadata" / "release_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("dataset_name", None)
    manifest.pop("row_counts", None)
    manifest["candidate_row_count"] = int(len(candidates))
    manifest["decision_row_count"] = int(len(stale_decision_view))
    pairwise_path = release_dir / "data" / "pairwise_sample" / "pairwise_sample.parquet"
    manifest["pairwise_sample_row_count"] = int(len(pd.read_parquet(pairwise_path))) if pairwise_path.exists() else None
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    checksums_path = release_dir / "metadata" / "checksums.sha256"
    checksums_path.write_text(
        "\n".join(_checksum_lines(release_dir, checksums_path)) + "\n",
        encoding="utf-8",
    )


def _build_stale_real_release_fixture(tmp_path: Path) -> Path:
    manifest_path, selection_path, _ = _build_candidate_fixture(tmp_path)
    release_dir = tmp_path / "stale-release"
    build_real_release(
        input_manifest=manifest_path,
        family_selection=selection_path,
        output_dir=release_dir,
        dataset_id="lafc-evict-v0.1-open",
        repo_root=_repo_root(),
        dry_run=False,
        overwrite=True,
        skip_disk_space_check=True,
        pairwise_sample=True,
        max_pairwise_rows=100,
        max_pairs_per_decision=4,
        duckdb_temp_dir=tmp_path / ".duckdb_tmp",
    )
    _downgrade_real_release_to_stale_contract(release_dir)
    return release_dir


def test_infer_trace_family_from_wulver_shard_path() -> None:
    family = infer_trace_family_from_path(
        Path("/tmp/cloudphysics_demo__cap32.part0000.csv"),
        known_families={"cloudphysics", "citibike"},
    )
    assert family == "cloudphysics"


def test_resolve_candidate_files_accepts_repo_root_relative_manifest_entries(tmp_path: Path) -> None:
    repo_like_root = tmp_path / "repo"
    manifest_dir = repo_like_root / "data" / "derived" / "evict_value_v1_wulver_heavy_r1"
    shard_dir = manifest_dir / "shards"
    shard_dir.mkdir(parents=True)
    shard_path = shard_dir / "cloudphysics_demo__cap32.part0000.csv"
    shard_path.write_text("trace_name,trace_family\nx,cloudphysics\n", encoding="utf-8")
    manifest_path = manifest_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "shards": [
                    {
                        "path": "data/derived/evict_value_v1_wulver_heavy_r1/shards/cloudphysics_demo__cap32.part0000.csv",
                        "row_count": 1,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    resolved = resolve_candidate_files(manifest_path)
    assert resolved == [shard_path.resolve()]


def test_summarize_candidate_source_detects_blocked_and_selected_stats(tmp_path: Path) -> None:
    manifest_path, _, _ = _build_candidate_fixture(tmp_path)

    summary = summarize_candidate_source(
        manifest_path,
        include_families={"cloudphysics"},
        exclude_families={"citibike"},
    )

    assert summary.manifest_path == manifest_path.resolve()
    assert summary.split_summary_path is not None
    assert summary.discovered_families == ("citibike", "cloudphysics")
    assert summary.blocked_families_present == ("citibike",)
    assert summary.selected_families == ("cloudphysics",)
    assert summary.shard_count_total == 2
    assert summary.shard_count_selected == 1
    assert summary.estimated_rows_total == 8
    assert summary.estimated_rows_selected == 6
    assert summary.splits == ("test", "train", "val")
    assert summary.capacities == (32,)
    assert summary.horizons == (4,)
    assert summary.ready_to_proceed is True


def test_filter_candidate_dataframe_by_family_removes_blocked_rows() -> None:
    example = pd.read_csv(_repo_root() / "examples" / "tiny_candidate_rows.csv")
    example.loc[example.index[:3], "trace_family"] = "citibike"

    filtered = filter_candidate_dataframe_by_family(
        example,
        include_families={"synthetic"},
        exclude_families={"citibike"},
    )

    assert set(filtered["trace_family"]) == {"synthetic"}


def test_export_dry_run_reports_metadata_without_writing_output(tmp_path: Path) -> None:
    manifest_path, _, _ = _build_candidate_fixture(tmp_path)
    output_dir = tmp_path / "release"
    script = _repo_root() / "scripts" / "export_lafc_evict_parquet.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--input-path",
            str(manifest_path),
            "--output-dir",
            str(output_dir),
            "--include-family",
            "cloudphysics",
            "--exclude-family",
            "citibike",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["mode"] == "dry_run"
    assert payload["selected_families"] == ["cloudphysics"]
    assert payload["excluded_families"] == ["citibike"]
    assert payload["estimated_selected_rows"] == 6
    assert not output_dir.exists()


def test_export_with_family_filters_writes_only_selected_rows(tmp_path: Path) -> None:
    manifest_path, _, source_dir = _build_candidate_fixture(tmp_path)
    output_dir = tmp_path / "release"
    script = _repo_root() / "scripts" / "export_lafc_evict_parquet.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--input-path",
            str(manifest_path),
            "--output-dir",
            str(output_dir),
            "--include-family",
            "cloudphysics",
            "--exclude-family",
            "citibike",
        ],
        cwd=source_dir,
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["row_count"] == 6
    assert payload["selected_families"] == ["cloudphysics"]
    assert payload["excluded_families"] == ["citibike"]
    files = list((output_dir / "candidate_rows").rglob("*.parquet"))
    assert len(files) == 3


def test_plan_real_release_writes_markdown_report(tmp_path: Path) -> None:
    manifest_path, selection_path, _ = _build_candidate_fixture(tmp_path)
    output_path = tmp_path / "readiness.md"
    script = _repo_root() / "scripts" / "plan_real_release.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--input-manifest",
            str(manifest_path),
            "--family-selection",
            str(selection_path),
            "--release-name",
            "lafc-evict-v0.1-open",
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    report = output_path.read_text(encoding="utf-8")
    assert payload["ready_to_proceed"] is True
    assert "lafc-evict-v0.1-open Readiness Audit" in report
    assert "build_real_release.py" in report


def test_dry_run_export_plan_rejects_overlapping_filters(tmp_path: Path) -> None:
    manifest_path, _, _ = _build_candidate_fixture(tmp_path)
    try:
        dry_run_export_plan(
            manifest_path,
            include_families={"cloudphysics"},
            exclude_families={"cloudphysics"},
        )
    except ValueError as exc:
        assert "overlap" in str(exc)
    else:
        raise AssertionError("Expected overlapping filters to fail")


def test_build_real_release_dry_run_does_not_write_release_data(tmp_path: Path) -> None:
    manifest_path, selection_path, _ = _build_candidate_fixture(tmp_path)
    output_dir = tmp_path / "release"
    script = _repo_root() / "scripts" / "build_real_release.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--input-manifest",
            str(manifest_path),
            "--family-selection",
            str(selection_path),
            "--output-dir",
            str(output_dir),
            "--dataset-id",
            "lafc-evict-v0.1-open",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["mode"] == "dry_run"
    assert payload["selected_families"] == ["cloudphysics"]
    assert payload["excluded_families"] == ["brightkite", "citibike"]
    assert not output_dir.exists()


def test_duckdb_connect_applies_resource_limits(tmp_path: Path) -> None:
    temp_dir = tmp_path / ".duckdb_tmp"
    con = _duckdb_connect(
        duckdb_threads=2,
        duckdb_memory_limit="1GB",
        duckdb_temp_dir=temp_dir,
    )
    try:
        assert con.execute("SELECT current_setting('threads')").fetchone()[0] == 2
        assert con.execute("SELECT current_setting('memory_limit')").fetchone()[0]
        assert con.execute("SELECT current_setting('temp_directory')").fetchone()[0] == str(temp_dir.resolve())
    finally:
        con.close()


def test_blocked_family_in_selection_hard_fails(tmp_path: Path) -> None:
    manifest_path, _, _ = _build_candidate_fixture(tmp_path)
    bad_selection = tmp_path / "bad_families.json"
    bad_selection.write_text(
        json.dumps(
            {
                "selected_families": ["citibike"],
                "excluded_families": [{"family": "brightkite", "reason": "blocked"}],
            }
        ),
        encoding="utf-8",
    )

    try:
        build_real_release(
            input_manifest=manifest_path,
            family_selection=bad_selection,
            output_dir=tmp_path / "release",
            dataset_id="lafc-evict-v0.1-open",
            dry_run=True,
        )
    except ValueError as exc:
        assert "Blocked families cannot be selected" in str(exc)
    else:
        raise AssertionError("Expected blocked family selection to fail")


def test_build_real_release_candidate_rows_stage_only_writes_candidates(tmp_path: Path) -> None:
    manifest_path, selection_path, _ = _build_candidate_fixture(tmp_path)
    output_dir = tmp_path / "release"

    result = build_real_release(
        input_manifest=manifest_path,
        family_selection=selection_path,
        output_dir=output_dir,
        dataset_id="lafc-evict-v0.1-open",
        repo_root=_repo_root(),
        dry_run=False,
        overwrite=True,
        skip_disk_space_check=True,
        stages=["candidate_rows"],
        duckdb_temp_dir=tmp_path / ".duckdb_tmp",
    )

    assert result.candidate_row_count == 6
    assert result.decision_row_count is None
    assert result.pairwise_sample_row_count is None
    assert result.manifest_path is None
    assert list((output_dir / "data" / "candidate_rows").rglob("candidate_rows.parquet"))
    assert not (output_dir / "data" / "decision_view").exists()
    assert not (output_dir / "data" / "pairwise_sample").exists()
    assert not (output_dir / "metadata").exists()
    assert not (output_dir / "README.md").exists()


def test_build_real_release_decision_view_stage_reads_emitted_candidate_parquet(tmp_path: Path) -> None:
    manifest_path, selection_path, _ = _build_candidate_fixture(tmp_path)
    output_dir = tmp_path / "release"

    build_real_release(
        input_manifest=manifest_path,
        family_selection=selection_path,
        output_dir=output_dir,
        dataset_id="lafc-evict-v0.1-open",
        repo_root=_repo_root(),
        dry_run=False,
        overwrite=True,
        skip_disk_space_check=True,
        stages=["candidate_rows"],
        duckdb_temp_dir=tmp_path / ".duckdb_tmp",
    )

    partition_path = next(
        (output_dir / "data" / "candidate_rows").rglob("candidate_rows.parquet")
    )
    partition = pd.read_parquet(partition_path)
    partition.loc[partition["candidate_page_id"] == "A", "y_loss"] = 0.0
    partition.to_parquet(partition_path, index=False)

    build_real_release(
        input_manifest=manifest_path,
        family_selection=selection_path,
        output_dir=output_dir,
        dataset_id="lafc-evict-v0.1-open",
        repo_root=_repo_root(),
        dry_run=False,
        overwrite=True,
        skip_disk_space_check=True,
        stages=["decision_view"],
        duckdb_temp_dir=tmp_path / ".duckdb_tmp",
    )

    decision_view = pd.read_parquet(output_dir / "data" / "decision_view" / "decision_view.parquet")
    expected_candidates = pd.concat(
        [pd.read_parquet(path) for path in sorted((output_dir / "data" / "candidate_rows").rglob("candidate_rows.parquet"))],
        ignore_index=True,
    )
    expected_decision_view = build_decision_view(expected_candidates)
    assert decision_view.columns.tolist() == DECISION_VIEW_COLUMNS
    pd.testing.assert_frame_equal(
        decision_view.sort_values(list(decision_view.columns)).reset_index(drop=True),
        expected_decision_view.sort_values(list(expected_decision_view.columns)).reset_index(drop=True),
        check_dtype=False,
    )


def test_build_real_release_pairwise_sample_stage_respects_caps(tmp_path: Path) -> None:
    manifest_path, selection_path, _ = _build_candidate_fixture(tmp_path)
    output_dir = tmp_path / "release"

    build_real_release(
        input_manifest=manifest_path,
        family_selection=selection_path,
        output_dir=output_dir,
        dataset_id="lafc-evict-v0.1-open",
        repo_root=_repo_root(),
        dry_run=False,
        overwrite=True,
        skip_disk_space_check=True,
        stages=["candidate_rows"],
        duckdb_temp_dir=tmp_path / ".duckdb_tmp",
    )

    result = build_real_release(
        input_manifest=manifest_path,
        family_selection=selection_path,
        output_dir=output_dir,
        dataset_id="lafc-evict-v0.1-open",
        repo_root=_repo_root(),
        dry_run=False,
        overwrite=True,
        skip_disk_space_check=True,
        stages=["pairwise_sample"],
        pairwise_sample=True,
        max_pairwise_rows=2,
        max_pairs_per_decision=1,
        duckdb_temp_dir=tmp_path / ".duckdb_tmp",
    )

    pairwise_path = output_dir / "data" / "pairwise_sample" / "pairwise_sample.parquet"
    pairwise = pd.read_parquet(pairwise_path)
    assert result.pairwise_sample_row_count == len(pairwise)
    assert len(pairwise) <= 2
    assert pairwise.groupby(["decision_id", "capacity", "horizon", "split", "trace_family", "trace_name"]).size().max() <= 1


def test_build_real_release_resume_skips_existing_non_empty_stage_outputs(tmp_path: Path) -> None:
    manifest_path, selection_path, _ = _build_candidate_fixture(tmp_path)
    output_dir = tmp_path / "release"

    build_real_release(
        input_manifest=manifest_path,
        family_selection=selection_path,
        output_dir=output_dir,
        dataset_id="lafc-evict-v0.1-open",
        repo_root=_repo_root(),
        dry_run=False,
        overwrite=True,
        skip_disk_space_check=True,
        stages=["candidate_rows"],
        duckdb_temp_dir=tmp_path / ".duckdb_tmp",
    )

    partition_path = next(
        (output_dir / "data" / "candidate_rows").rglob("candidate_rows.parquet")
    )
    before_mtime = partition_path.stat().st_mtime_ns

    result = build_real_release(
        input_manifest=manifest_path,
        family_selection=selection_path,
        output_dir=output_dir,
        dataset_id="lafc-evict-v0.1-open",
        repo_root=_repo_root(),
        dry_run=False,
        overwrite=False,
        resume=True,
        skip_disk_space_check=True,
        stages=["candidate_rows"],
        duckdb_temp_dir=tmp_path / ".duckdb_tmp",
    )

    assert partition_path.stat().st_mtime_ns == before_mtime
    assert result.candidate_row_count == 6


def test_build_real_release_writes_partitioned_candidates_and_views(tmp_path: Path) -> None:
    manifest_path, selection_path, _ = _build_candidate_fixture(tmp_path)
    output_dir = tmp_path / "release"

    result = build_real_release(
        input_manifest=manifest_path,
        family_selection=selection_path,
        output_dir=output_dir,
        dataset_id="lafc-evict-v0.1-open",
        repo_root=_repo_root(),
        dry_run=False,
        overwrite=True,
        skip_disk_space_check=True,
        pairwise_sample=True,
        max_pairwise_rows=100,
        max_pairs_per_decision=4,
        pairwise_seed=7,
        duckdb_temp_dir=tmp_path / ".duckdb_tmp",
    )

    assert result.candidate_row_count == 6
    assert result.decision_row_count == 3
    assert result.pairwise_sample_row_count is not None
    assert result.pairwise_sample_row_count <= 100

    partitions = list((output_dir / "data" / "candidate_rows").rglob("candidate_rows.parquet"))
    assert len(partitions) == 3
    assert (output_dir / "data" / "decision_view" / "decision_view.parquet").exists()
    assert (output_dir / "data" / "pairwise_sample" / "pairwise_sample.parquet").exists()
    assert not (output_dir / "data" / "pairwise").exists()

    manifest = json.loads((output_dir / "metadata" / "release_manifest.json").read_text(encoding="utf-8"))
    assert manifest["dataset_name"] == "lafc-evict-v0.1-open"
    assert manifest["selected_families"] == ["cloudphysics"]
    assert manifest["excluded_families"] == ["brightkite", "citibike"]
    assert manifest["blocked_families_absent"] is True
    assert manifest["schema_version"] == "lafc-evict-candidate-v1"
    assert manifest["row_counts"] == {
        "candidate_rows": 6,
        "decision_view": 3,
        "pairwise_sample": manifest["pairwise_sample_row_count"],
    }
    assert manifest["file_inventory"] == collect_release_file_inventory(output_dir)
    assert "metadata/release_manifest.json" in manifest["file_inventory"]
    assert "metadata/checksums.sha256" in manifest["file_inventory"]

    decision_view = pd.read_parquet(output_dir / "data" / "decision_view" / "decision_view.parquet")
    assert set(decision_view["trace_family"]) == {"cloudphysics"}
    assert decision_view.columns.tolist() == DECISION_VIEW_COLUMNS
    assert decision_view.loc[0, "tie_count"] >= 1
    assert decision_view.loc[0, "optimal_candidate_page_ids"] is not None
    assert decision_view.loc[0, "optimal_candidate_count"] >= 1

    errors = validate_real_release(output_dir)
    assert errors == []


def test_consolidate_partition_parquet_files_merges_existing_target_with_extra_fragments(tmp_path: Path) -> None:
    manifest_path, _, _ = _build_candidate_fixture(tmp_path)
    shard_path = resolve_candidate_files(manifest_path)[0]
    candidate_rows = pd.read_csv(shard_path)

    partition_dir = (
        tmp_path
        / "candidate_rows"
        / "split=train"
        / "trace_family=cloudphysics"
        / "capacity=32"
        / "horizon=4"
    )
    partition_dir.mkdir(parents=True)

    candidate_rows.iloc[:1].to_parquet(partition_dir / "candidate_rows.parquet", index=False)
    candidate_rows.iloc[1:2].to_parquet(partition_dir / "part-0001.parquet", index=False)

    con = _duckdb_connect()
    try:
        _consolidate_partition_parquet_files(con, tmp_path / "candidate_rows")
        _register_candidate_partitions(con, tmp_path / "candidate_rows")
        assert _count_candidate_rows(con) == 2
    finally:
        con.close()

    parquet_files = sorted(partition_dir.glob("*.parquet"))
    assert parquet_files == [partition_dir / "candidate_rows.parquet"]


def test_validation_catches_blocked_family_in_release(tmp_path: Path) -> None:
    manifest_path, selection_path, _ = _build_candidate_fixture(tmp_path)
    output_dir = tmp_path / "release"
    build_real_release(
        input_manifest=manifest_path,
        family_selection=selection_path,
        output_dir=output_dir,
        dataset_id="lafc-evict-v0.1-open",
        repo_root=_repo_root(),
        dry_run=False,
        overwrite=True,
        skip_disk_space_check=True,
        duckdb_temp_dir=tmp_path / ".duckdb_tmp",
    )

    blocked_partition = (
        output_dir
        / "data"
        / "candidate_rows"
        / "split=test"
        / "trace_family=citibike"
        / "capacity=32"
        / "horizon=4"
    )
    blocked_partition.mkdir(parents=True)
    pd.read_parquet(
        output_dir / "data" / "candidate_rows" / "split=train" / "trace_family=cloudphysics" / "capacity=32" / "horizon=4" / "candidate_rows.parquet"
    ).assign(trace_family="citibike").to_parquet(blocked_partition / "candidate_rows.parquet", index=False)

    errors = validate_real_release(output_dir)
    assert any("Blocked families present" in error for error in errors)


def test_validation_catches_y_value_mismatch_in_release(tmp_path: Path) -> None:
    manifest_path, selection_path, _ = _build_candidate_fixture(tmp_path)
    output_dir = tmp_path / "release"
    build_real_release(
        input_manifest=manifest_path,
        family_selection=selection_path,
        output_dir=output_dir,
        dataset_id="lafc-evict-v0.1-open",
        repo_root=_repo_root(),
        dry_run=False,
        overwrite=True,
        skip_disk_space_check=True,
        duckdb_temp_dir=tmp_path / ".duckdb_tmp",
    )

    partition_path = next((output_dir / "data" / "candidate_rows").rglob("candidate_rows.parquet"))
    corrupted = pd.read_parquet(partition_path)
    corrupted.loc[0, "y_value"] = 123.0
    corrupted.to_parquet(partition_path, index=False)

    errors = validate_real_release(output_dir)
    assert any("y_value must equal -y_loss" in error for error in errors)


def test_validation_catches_duplicate_candidate_id_within_decision(tmp_path: Path) -> None:
    manifest_path, selection_path, _ = _build_candidate_fixture(tmp_path)
    output_dir = tmp_path / "release"
    build_real_release(
        input_manifest=manifest_path,
        family_selection=selection_path,
        output_dir=output_dir,
        dataset_id="lafc-evict-v0.1-open",
        repo_root=_repo_root(),
        dry_run=False,
        overwrite=True,
        skip_disk_space_check=True,
        duckdb_temp_dir=tmp_path / ".duckdb_tmp",
    )

    partition_path = next((output_dir / "data" / "candidate_rows").rglob("candidate_rows.parquet"))
    duplicated = pd.read_parquet(partition_path)
    duplicated = pd.concat([duplicated, duplicated.iloc[[0]]], ignore_index=True)
    duplicated.to_parquet(partition_path, index=False)

    errors = validate_real_release(output_dir)
    assert any("Duplicate candidate_page_id within decision group" in error for error in errors)


def test_validation_catches_inconsistent_decision_metadata(tmp_path: Path) -> None:
    manifest_path, selection_path, _ = _build_candidate_fixture(tmp_path)
    output_dir = tmp_path / "release"
    build_real_release(
        input_manifest=manifest_path,
        family_selection=selection_path,
        output_dir=output_dir,
        dataset_id="lafc-evict-v0.1-open",
        repo_root=_repo_root(),
        dry_run=False,
        overwrite=True,
        skip_disk_space_check=True,
        duckdb_temp_dir=tmp_path / ".duckdb_tmp",
    )

    partition_path = next((output_dir / "data" / "candidate_rows").rglob("candidate_rows.parquet"))
    inconsistent = pd.read_parquet(partition_path)
    inconsistent.loc[inconsistent.index[-1], "decision_t"] = 999
    inconsistent.to_parquet(partition_path, index=False)

    errors = validate_real_release(output_dir)
    assert any("Inconsistent decision_t within decision group" in error for error in errors)


def test_validation_catches_cross_split_decision_id_reuse(tmp_path: Path) -> None:
    manifest_path, selection_path, _ = _build_candidate_fixture(tmp_path)
    output_dir = tmp_path / "release"
    build_real_release(
        input_manifest=manifest_path,
        family_selection=selection_path,
        output_dir=output_dir,
        dataset_id="lafc-evict-v0.1-open",
        repo_root=_repo_root(),
        dry_run=False,
        overwrite=True,
        skip_disk_space_check=True,
        duckdb_temp_dir=tmp_path / ".duckdb_tmp",
    )

    target_partition = output_dir / "data" / "candidate_rows" / "split=test" / "trace_family=cloudphysics" / "capacity=32" / "horizon=4" / "candidate_rows.parquet"
    target = pd.read_parquet(target_partition)
    reused = target.copy()
    reused["decision_id"] = "d1"
    reused["split"] = "test"
    pd.concat([target, reused.iloc[[0]]], ignore_index=True).to_parquet(target_partition, index=False)

    errors = validate_real_release(output_dir)
    assert any("spanning multiple splits without override" in error for error in errors)


def test_real_release_builder_does_not_use_pandas_concat() -> None:
    source = (_repo_root() / "src" / "lafc_evict_dataset" / "real_release_build.py").read_text(encoding="utf-8")
    assert "pd.concat" not in source
    assert "read_candidate_dataframe" not in source
    assert "pairwise_view" not in source


def test_migrate_real_release_contract_repairs_stale_manifest_and_decision_view(tmp_path: Path) -> None:
    source_release = _build_stale_real_release_fixture(tmp_path)
    migrated_release = tmp_path / "migrated-release"

    result = migrate_real_release_contract(
        source_release_dir=source_release,
        output_dir=migrated_release,
        repo_root=_repo_root(),
        staging_mode="copy",
        duckdb_temp_dir=tmp_path / ".duckdb_tmp_migrate",
    )

    assert result.candidate_rows_reused is True
    assert result.pairwise_sample_reused is True
    assert result.pairwise_sample_regenerated is False
    assert result.candidate_rows_staging_mode == "copy"

    manifest = json.loads((migrated_release / "metadata" / "release_manifest.json").read_text(encoding="utf-8"))
    assert manifest["dataset_name"] == "lafc-evict-v0.1-open"
    assert manifest["dataset_id"] == "lafc-evict-v0.1-open"
    assert manifest["row_counts"] == {
        "candidate_rows": 6,
        "decision_view": 3,
        "pairwise_sample": 3,
    }
    assert manifest["migration"]["source_release_directory"] == str(source_release.resolve())
    assert manifest["migration"]["decision_view_regenerated"] is True
    assert manifest["migration"]["candidate_rows_reused"] is True
    assert manifest["migration"]["pairwise_sample_reused"] is True
    assert manifest["file_inventory"] == collect_release_file_inventory(migrated_release)

    decision_view = pd.read_parquet(migrated_release / "data" / "decision_view" / "decision_view.parquet")
    assert decision_view.columns.tolist() == DECISION_VIEW_COLUMNS

    errors = validate_real_release(migrated_release)
    assert errors == []


def test_repair_release_metadata_script_repairs_file_inventory_and_checksums(tmp_path: Path) -> None:
    release_dir = _build_stale_real_release_fixture(tmp_path)
    migrated_release = tmp_path / "migrated-release"
    migrate_real_release_contract(
        source_release_dir=release_dir,
        output_dir=migrated_release,
        repo_root=_repo_root(),
        staging_mode="copy",
        duckdb_temp_dir=tmp_path / ".duckdb_tmp_migrate",
    )

    manifest_path = migrated_release / "metadata" / "release_manifest.json"
    checksums_path = migrated_release / "metadata" / "checksums.sha256"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["file_inventory"] = [
        path
        for path in manifest["file_inventory"]
        if path not in {"metadata/release_manifest.json", "metadata/checksums.sha256"}
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    checksums_path.write_text(
        "\n".join(_checksum_lines(migrated_release, checksums_path)) + "\n",
        encoding="utf-8",
    )

    script = _repo_root() / "scripts" / "repair_release_metadata.py"
    dry_run = subprocess.run(
        [sys.executable, str(script), "--release-root", str(migrated_release)],
        check=True,
        capture_output=True,
        text=True,
    )
    dry_run_payload = json.loads(dry_run.stdout)
    assert dry_run_payload["would_update_manifest"] is True
    assert dry_run_payload["missing_from_file_inventory"] == [
        "metadata/checksums.sha256",
        "metadata/release_manifest.json",
    ]

    subprocess.run(
        [sys.executable, str(script), "--release-root", str(migrated_release), "--apply"],
        check=True,
    )
    repaired_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert repaired_manifest["file_inventory"] == collect_release_file_inventory(migrated_release)
