from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pandas as pd
import pytest
import pyarrow as pa
import pyarrow.parquet as pq

from lafc_evict_dataset.release import build_sample_release
from lafc_evict_dataset.schema import DECISION_METADATA_COLUMNS


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _script_dir() -> Path:
    return _repo_root() / "scripts" / "sigmod2027"


def _example_path() -> Path:
    return _repo_root() / "examples" / "tiny_candidate_rows.csv"


def _load_sigmod_module(name: str):
    script_dir = _script_dir()
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    module = importlib.import_module(name)
    return importlib.reload(module)


@pytest.fixture()
def sample_release(tmp_path: Path) -> Path:
    release_root = tmp_path / "lafc-evict-sample-v0.1"
    build_sample_release(
        input_path=_example_path(),
        output_dir=release_root,
        overwrite=True,
        include_ties=True,
    )
    return release_root


def _write_manual_release(root: Path, partitions: list[tuple[str, pd.DataFrame]]) -> Path:
    candidate_entries = []
    for relative_path, frame in partitions:
        output_path = root / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(pa.Table.from_pandas(frame, preserve_index=False), output_path)
        candidate_entries.append(
            {
                "path": relative_path,
                "row_count": int(len(frame)),
                "split": str(frame.iloc[0]["split"]),
                "trace_family": str(frame.iloc[0]["trace_family"]),
                "capacity": int(frame.iloc[0]["capacity"]),
                "horizon": int(frame.iloc[0]["horizon"]),
            }
        )
    metadata_dir = root / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "dataset_name": "lafc-evict-manual",
        "version": "0.1",
        "release_type": "synthetic_sample",
        "schema_version": "lafc-evict-candidate-v1",
        "row_counts": {"candidate_rows": int(sum(len(frame) for _, frame in partitions)), "decision_view": 0, "pairwise_sample": 0},
        "candidate_partitions": candidate_entries,
    }
    (metadata_dir / "release_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return root


def test_plan_modes_do_not_iterate_candidate_rows(monkeypatch: pytest.MonkeyPatch, sample_release: Path, tmp_path: Path) -> None:
    def _boom(*args, **kwargs):
        raise AssertionError("plan mode should not iterate candidate rows")

    for module_name in [
        "run_candidate_label_stats",
        "run_value_regression_baseline",
        "run_best_candidate_baseline",
    ]:
        module = _load_sigmod_module(module_name)
        monkeypatch.setattr(module, "iter_candidate_batches", _boom, raising=True)
        module.main(
            [
                "--release-root",
                str(sample_release),
                "--output-dir",
                str(tmp_path / module_name),
                "--mode",
                "plan",
            ]
        )


def test_candidate_label_stats_runner_produces_expected_tiny_summaries(sample_release: Path, tmp_path: Path) -> None:
    module = _load_sigmod_module("run_candidate_label_stats")
    output_dir = tmp_path / "candidate_label_stats"
    module.main(
        [
            "--release-root",
            str(sample_release),
            "--output-dir",
            str(output_dir),
            "--mode",
            "run",
            "--target",
            "both",
        ]
    )

    input_df = pd.read_csv(_example_path())
    y_loss_payload = json.loads((output_dir / "y_loss_summary.json").read_text(encoding="utf-8"))
    y_value_payload = json.loads((output_dir / "y_value_summary.json").read_text(encoding="utf-8"))
    y_loss_csv = pd.read_csv(output_dir / "y_loss_summary.csv")

    assert y_loss_payload["overall_summary"]["count"] == len(input_df)
    assert y_loss_payload["overall_summary"]["missing_count"] == 0
    assert y_loss_payload["overall_summary"]["mean"] == pytest.approx(float(input_df["y_loss"].mean()))
    assert y_loss_payload["overall_summary"]["quantiles"]["q50"] == pytest.approx(float(input_df["y_loss"].median()))
    assert y_value_payload["overall_summary"]["max"] == pytest.approx(float(input_df["y_value"].max()))
    assert set(y_loss_csv["summary_scope"]) == {"overall", "group"}


def test_candidate_label_stats_resume_is_safe_and_does_not_modify_input(sample_release: Path, tmp_path: Path) -> None:
    module = _load_sigmod_module("run_candidate_label_stats")
    output_dir = tmp_path / "candidate_label_stats_resume"
    manifest_path = sample_release / "metadata" / "release_manifest.json"
    manifest_before = manifest_path.read_text(encoding="utf-8")
    candidate_before = {
        path: path.stat().st_mtime_ns for path in sorted((sample_release / "data" / "candidate_rows").rglob("candidate_rows.parquet"))
    }

    module.main(
        [
            "--release-root",
            str(sample_release),
            "--output-dir",
            str(output_dir),
            "--mode",
            "run",
            "--target",
            "both",
            "--max-files",
            "1",
        ]
    )

    assert (output_dir / ".candidate_label_stats.checkpoint.json").exists()
    assert not (output_dir / "y_loss_summary.json").exists()

    with pytest.raises(ValueError):
        module.main(
            [
                "--release-root",
                str(sample_release),
                "--output-dir",
                str(output_dir),
                "--mode",
                "run",
                "--target",
                "both",
            ]
        )

    module.main(
        [
            "--release-root",
            str(sample_release),
            "--output-dir",
            str(output_dir),
            "--mode",
            "run",
            "--target",
            "both",
            "--resume",
        ]
    )

    assert (output_dir / "y_loss_summary.json").exists()
    assert not (output_dir / ".candidate_label_stats.checkpoint.json").exists()
    assert manifest_path.read_text(encoding="utf-8") == manifest_before
    candidate_after = {
        path: path.stat().st_mtime_ns for path in sorted((sample_release / "data" / "candidate_rows").rglob("candidate_rows.parquet"))
    }
    assert candidate_after == candidate_before


def test_candidate_label_stats_resume_starts_fresh_when_checkpoint_is_missing(sample_release: Path, tmp_path: Path) -> None:
    module = _load_sigmod_module("run_candidate_label_stats")
    output_dir = tmp_path / "candidate_label_stats_resume_fresh"

    module.main(
        [
            "--release-root",
            str(sample_release),
            "--output-dir",
            str(output_dir),
            "--mode",
            "run",
            "--target",
            "both",
            "--resume",
        ]
    )

    assert (output_dir / "y_loss_summary.json").exists()
    assert (output_dir / "y_value_summary.json").exists()
    assert not (output_dir / ".candidate_label_stats.checkpoint.json").exists()


def test_value_regression_runner_emits_expected_json(sample_release: Path, tmp_path: Path) -> None:
    module = _load_sigmod_module("run_value_regression_baseline")
    output_dir = tmp_path / "value_regression"
    module.main(
        [
            "--release-root",
            str(sample_release),
            "--output-dir",
            str(output_dir),
            "--mode",
            "run",
            "--target",
            "y_loss",
            "--features",
            "candidate_predictor_score",
            "candidate_lru_score",
            "candidate_is_predictor_victim",
            "candidate_is_lru_victim",
            "candidate_recency_rank",
            "candidate_age_norm",
        ]
    )

    payload = json.loads((output_dir / "linear_regression_y_loss.json").read_text(encoding="utf-8"))
    assert payload["baseline"] == "linear_regression"
    assert payload["target"] == "y_loss"
    assert payload["model"]["training_rows"] > 0
    assert set(payload["model"]["coefficients"]) == {
        "candidate_predictor_score",
        "candidate_lru_score",
        "candidate_is_predictor_victim",
        "candidate_is_lru_victim",
        "candidate_recency_rank",
        "candidate_age_norm",
    }
    assert payload["split_metrics"]["train"]["rows"] > 0
    assert payload["split_metrics"]["test"]["rows"] > 0
    assert payload["timestamp_utc"]
    assert payload["git_commit"]


def test_value_regression_resume_starts_fresh_when_checkpoint_is_missing(sample_release: Path, tmp_path: Path) -> None:
    module = _load_sigmod_module("run_value_regression_baseline")
    output_dir = tmp_path / "value_regression_resume_fresh"

    module.main(
        [
            "--release-root",
            str(sample_release),
            "--output-dir",
            str(output_dir),
            "--mode",
            "run",
            "--target",
            "y_loss",
            "--resume",
        ]
    )

    assert (output_dir / "linear_regression_y_loss.json").exists()
    assert not (output_dir / ".value_regression_y_loss.checkpoint.json").exists()


def test_value_regression_resume_uses_existing_checkpoint(sample_release: Path, tmp_path: Path) -> None:
    module = _load_sigmod_module("run_value_regression_baseline")
    output_dir = tmp_path / "value_regression_resume_existing"

    module.main(
        [
            "--release-root",
            str(sample_release),
            "--output-dir",
            str(output_dir),
            "--mode",
            "run",
            "--target",
            "y_loss",
            "--max-files",
            "1",
        ]
    )

    assert (output_dir / ".value_regression_y_loss.checkpoint.json").exists()
    assert not (output_dir / "linear_regression_y_loss.json").exists()

    module.main(
        [
            "--release-root",
            str(sample_release),
            "--output-dir",
            str(output_dir),
            "--mode",
            "run",
            "--target",
            "y_loss",
            "--resume",
        ]
    )

    assert (output_dir / "linear_regression_y_loss.json").exists()
    assert not (output_dir / ".value_regression_y_loss.checkpoint.json").exists()


def test_corrupt_checkpoint_fails_clearly(tmp_path: Path) -> None:
    module = _load_sigmod_module("_baseline_common")
    checkpoint = tmp_path / "corrupt.checkpoint.json"
    checkpoint.write_text("{not valid json\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Checkpoint file is corrupt"):
        module.load_checkpoint(checkpoint)


def test_best_candidate_runner_supports_linear_score_json(sample_release: Path, tmp_path: Path) -> None:
    value_module = _load_sigmod_module("run_value_regression_baseline")
    best_module = _load_sigmod_module("run_best_candidate_baseline")

    value_dir = tmp_path / "value_regression_for_best"
    best_dir = tmp_path / "best_candidate"
    value_module.main(
        [
            "--release-root",
            str(sample_release),
            "--output-dir",
            str(value_dir),
            "--mode",
            "run",
            "--target",
            "y_loss",
        ]
    )

    linear_json = value_dir / "linear_regression_y_loss.json"
    best_module.main(
        [
            "--release-root",
            str(sample_release),
            "--output-dir",
            str(best_dir),
            "--mode",
            "run",
            "--linear-score-json",
            str(linear_json),
        ]
    )

    payload = json.loads((best_dir / "best_candidate_from_linear_score.json").read_text(encoding="utf-8"))
    assert payload["scorer"]["mode"] == "linear_score"
    assert payload["overall_metrics"]["decision_count"] == 3
    assert payload["overall_metrics"]["mean_regret"] is not None
    assert payload["group_metrics"]
    assert payload["timestamp_utc"]
    assert payload["git_commit"]


def test_best_candidate_runner_rejects_duplicate_manifest_partitions(tmp_path: Path) -> None:
    module = _load_sigmod_module("run_best_candidate_baseline")
    rows = pd.read_csv(_example_path())
    rows = rows[rows["decision_id"].isin(["d1", "d2"])].copy()
    first = rows[rows["candidate_page_id"].isin(["A", "B", "D", "E"])].copy()
    second = rows[rows["candidate_page_id"].isin(["C", "F"])].copy()
    release_root = _write_manual_release(
        tmp_path / "manual-release",
        [
            ("data/candidate_rows/part-000.parquet", first),
            ("data/candidate_rows/part-001.parquet", second),
        ],
    )

    output_dir = tmp_path / "best-manual"
    with pytest.raises(ValueError, match="Duplicate partitions found"):
        module.main(
            [
                "--release-root",
                str(release_root),
                "--output-dir",
                str(output_dir),
                "--mode",
                "run",
                "--score-column",
                "candidate_is_lru_victim",
            ]
        )


def test_decision_key_columns_is_canonical_nine_column_key() -> None:
    module = _load_sigmod_module("_baseline_common")
    assert module.decision_key_columns() == list(DECISION_METADATA_COLUMNS)
    assert len(module.decision_key_columns()) == 9


def test_best_candidate_runner_distinguishes_decisions_sharing_old_six_column_key(tmp_path: Path) -> None:
    """Regression test for the evaluator over-/under-counting bug.

    Two logical decisions here share every column of the old, narrower
    6-column key (split, trace_family, trace_name, capacity, horizon,
    decision_id) but differ in dataset_source. Their rows are interleaved
    non-contiguously in a single partition file. The old key would collapse
    them into one groupby group (undercounting); the canonical 9-column key
    must keep them separate.
    """
    base = pd.read_csv(_example_path())
    d1 = base[base["decision_id"] == "d1"].reset_index(drop=True)

    decision_a = d1.copy()
    decision_a["dataset_source"] = "synthetic"

    decision_b = d1.copy()
    decision_b["dataset_source"] = "synthetic_alt"
    decision_b["candidate_page_id"] = decision_b["candidate_page_id"] + "2"

    old_six_col_key = ["split", "trace_family", "trace_name", "capacity", "horizon", "decision_id"]
    combined = pd.concat(
        [
            decision_a.iloc[[0]],
            decision_b.iloc[[0]],
            decision_a.iloc[[1]],
            decision_b.iloc[[1]],
            decision_a.iloc[[2]],
            decision_b.iloc[[2]],
        ],
        ignore_index=True,
    )

    # Sanity check: the old 6-column key really does collapse these two
    # logical decisions into a single group (the bug this test guards against).
    old_key_group_count = combined.groupby(old_six_col_key, sort=False).ngroups
    assert old_key_group_count == 1

    # The canonical 9-column key must see them as two distinct decisions.
    nine_col_group_count = combined.groupby(list(DECISION_METADATA_COLUMNS), sort=False, dropna=False).ngroups
    assert nine_col_group_count == 2

    release_root = _write_manual_release(
        tmp_path / "manual-release-collision",
        [("data/candidate_rows/part-000.parquet", combined)],
    )

    module = _load_sigmod_module("run_best_candidate_baseline")
    output_dir = tmp_path / "best-manual-collision"
    module.main(
        [
            "--release-root",
            str(release_root),
            "--output-dir",
            str(output_dir),
            "--mode",
            "run",
            "--score-column",
            "candidate_is_lru_victim",
        ]
    )
    payload = json.loads((output_dir / "best_candidate_from_candidate_is_lru_victim.json").read_text(encoding="utf-8"))
    assert payload["overall_metrics"]["decision_count"] == 2


def test_best_candidate_runner_decision_count_matches_decision_view_row_count(
    sample_release: Path, tmp_path: Path
) -> None:
    manifest = json.loads((sample_release / "metadata" / "release_manifest.json").read_text(encoding="utf-8"))
    expected_decision_count = manifest["row_counts"]["decision_view"]

    module = _load_sigmod_module("run_best_candidate_baseline")
    output_dir = tmp_path / "best-candidate-smoke"
    module.main(
        [
            "--release-root",
            str(sample_release),
            "--output-dir",
            str(output_dir),
            "--mode",
            "run",
            "--score-column",
            "candidate_is_lru_victim",
        ]
    )
    payload = json.loads(
        (output_dir / "best_candidate_from_candidate_is_lru_victim.json").read_text(encoding="utf-8")
    )
    assert payload["overall_metrics"]["decision_count"] == expected_decision_count


def test_output_guard_rejects_release_root_destinations(sample_release: Path) -> None:
    module = _load_sigmod_module("run_candidate_label_stats")
    with pytest.raises(ValueError):
        module.main(
            [
                "--release-root",
                str(sample_release),
                "--output-dir",
                str(sample_release / "paper-results"),
                "--mode",
                "plan",
            ]
        )
