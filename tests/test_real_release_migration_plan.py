from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

from lafc_evict_dataset.real_release_build import build_real_release
from lafc_evict_dataset.real_release_migration_plan import plan_real_release_migration


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _build_stale_release_fixture(tmp_path: Path) -> Path:
    repo_root = _repo_root()
    source_dir = tmp_path / "real_source"
    shard_dir = source_dir / "shards"
    shard_dir.mkdir(parents=True)

    candidate_rows = pd.read_csv(repo_root / "examples" / "tiny_candidate_rows.csv")
    candidate_rows["trace_name"] = "cloudphysics_trace"
    candidate_rows["trace_family"] = "cloudphysics"
    candidate_rows["dataset_source"] = "cloudphysics-open"
    shard_path = shard_dir / "cloudphysics_demo__cap3.part0000.csv"
    candidate_rows.to_csv(shard_path, index=False)

    manifest_path = source_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "format": "evict_value_v1_wulver_candidate_csv_shards",
                "shards": [{"path": f"shards/{shard_path.name}", "row_count": int(len(candidate_rows))}],
            },
            indent=2,
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
        )
        + "\n",
        encoding="utf-8",
    )

    release_dir = tmp_path / "release" / "lafc-evict-v0.1-open"
    build_real_release(
        input_manifest=manifest_path,
        family_selection=selection_path,
        output_dir=release_dir,
        dataset_id="lafc-evict-v0.1-open",
        repo_root=repo_root,
        dry_run=False,
        overwrite=True,
        skip_disk_space_check=True,
        pairwise_sample=True,
        max_pairwise_rows=100,
        max_pairs_per_decision=4,
        duckdb_temp_dir=tmp_path / ".duckdb_tmp",
    )

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

    stale_decision_view = candidates.groupby(group_cols, dropna=False, sort=True).apply(_stale_row).reset_index()
    stale_decision_view.to_parquet(
        release_dir / "data" / "decision_view" / "decision_view.parquet",
        index=False,
    )

    manifest = json.loads((release_dir / "metadata" / "release_manifest.json").read_text(encoding="utf-8"))
    manifest.pop("dataset_name", None)
    manifest.pop("row_counts", None)
    manifest["candidate_row_count"] = int(len(candidates))
    manifest["decision_row_count"] = int(len(stale_decision_view))
    manifest["pairwise_sample_row_count"] = int(
        len(pd.read_parquet(release_dir / "data" / "pairwise_sample" / "pairwise_sample.parquet"))
    )
    manifest["file_inventory"] = sorted(
        path.relative_to(release_dir).as_posix() for path in release_dir.rglob("*") if path.is_file()
    )
    (release_dir / "metadata" / "release_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    return release_dir


def test_plan_real_release_migration_detects_stale_contract_and_reuse_path(tmp_path: Path) -> None:
    release_dir = _build_stale_release_fixture(tmp_path)

    plan = plan_real_release_migration(release_dir, candidate_sample_size=3)

    assert plan.dataset_id == "lafc-evict-v0.1-open"
    assert plan.manifest_assessment.planned_current_manifest_shape["dataset_name"] == "lafc-evict-v0.1-open"
    assert plan.manifest_assessment.planned_current_manifest_shape["row_counts"] == {
        "candidate_rows": 9,
        "decision_view": 3,
        "pairwise_sample": 9,
    }
    assert plan.manifest_assessment.cheap_to_migrate is True
    assert "add dataset_name from dataset_id" in plan.manifest_assessment.updates_required
    assert "derive row_counts from legacy flat row-count fields" in plan.manifest_assessment.updates_required

    assert plan.decision_view.compatible is False
    assert "max_y_value" in plan.decision_view.missing_columns
    assert "optimal_candidate_page_ids" in plan.decision_view.missing_columns
    assert "best_candidate_page_id" in plan.decision_view.extra_columns
    assert "mean_y_loss" in plan.decision_view.extra_columns

    assert plan.pairwise_sample is not None
    assert plan.pairwise_sample.compatible is True
    assert plan.candidate_rows.compatible is True
    assert plan.candidate_rows.sampled_file_count == 3
    assert plan.candidate_rows_can_likely_be_reused is True
    assert plan.pairwise_sample_can_likely_be_reused is True
    assert plan.decision_view_regeneration_required is True
    assert plan.only_heavy_missing_piece_is_decision_view is True
    assert "scripts/migrate_real_release_contract.py" in plan.recommended_heavy_command


def test_plan_real_release_migration_cli_prints_json_plan(tmp_path: Path) -> None:
    release_dir = _build_stale_release_fixture(tmp_path)
    script = _repo_root() / "scripts" / "plan_real_release_migration.py"

    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--source-release-dir",
            str(release_dir),
            "--candidate-sample-size",
            "2",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["candidate_rows"]["sampled_file_count"] == 2
    assert payload["candidate_rows_can_likely_be_reused"] is True
    assert payload["pairwise_sample_can_likely_be_reused"] is True
    assert payload["decision_view_regeneration_required"] is True
    assert payload["only_heavy_missing_piece_is_decision_view"] is True
