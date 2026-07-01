from __future__ import annotations

import importlib
import json
import sys
from itertools import combinations
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from lafc_evict_dataset.schema import CANONICAL_COLUMNS, FEATURE_COLUMNS

PAIRWISE_BARE_COLUMNS = [
    "decision_id",
    "capacity",
    "horizon",
    "split",
    "trace_family",
    "trace_name",
    "candidate_a_page_id",
    "candidate_b_page_id",
    "y_loss_a",
    "y_loss_b",
    "y_loss_diff_a_minus_b",
    "label_a_better",
    "label_b_better",
    "is_tie",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _script_dir() -> Path:
    return _repo_root() / "scripts" / "sigmod2027"


def _load_module(name: str):
    script_dir = _script_dir()
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    module = importlib.import_module(name)
    return importlib.reload(module)


def _candidate_row(*, trace_name, trace_family, capacity, horizon, decision_id, decision_t, candidate_page_id, split, y_loss, y_value=0.0, **feature_overrides):
    row = {
        "trace_name": trace_name,
        "trace_family": trace_family,
        "dataset_source": "synthetic",
        "capacity": capacity,
        "horizon": horizon,
        "decision_id": decision_id,
        "decision_t": decision_t,
        "decision_chunk_id": 0,
        "candidate_page_id": candidate_page_id,
        "split": split,
        "y_loss": float(y_loss),
        "y_value": float(y_value),
    }
    for column in FEATURE_COLUMNS:
        row[column] = float(feature_overrides.get(column, 0.0))
    return row


def _bare_pairwise_rows(shared: dict[str, object], candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    ordered = sorted(candidates, key=lambda c: c["candidate_page_id"])
    for left, right in combinations(ordered, 2):
        rows.append(
            {
                **shared,
                "candidate_a_page_id": left["candidate_page_id"],
                "candidate_b_page_id": right["candidate_page_id"],
                "y_loss_a": float(left["y_loss"]),
                "y_loss_b": float(right["y_loss"]),
                "y_loss_diff_a_minus_b": float(left["y_loss"] - right["y_loss"]),
                "label_a_better": int(left["y_loss"] < right["y_loss"]),
                "label_b_better": int(right["y_loss"] < left["y_loss"]),
                "is_tie": int(left["y_loss"] == right["y_loss"]),
            }
        )
    return rows


def _build_release(root: Path) -> Path:
    splits = ["train", "val", "test"]
    decisions = {
        "d1": [("A", 1.0), ("B", 2.0), ("C", 3.0)],
        "d2": [("A", 2.0), ("B", 2.0), ("C", 1.0)],
    }
    candidate_partitions = []
    pairwise_rows: list[dict[str, object]] = []

    for split in splits:
        candidate_rows = []
        for decision_index, (decision_id, candidates) in enumerate(decisions.items()):
            min_loss = min(loss for _, loss in candidates)
            decision_candidates = []
            for page_id, loss in candidates:
                is_victim = 1.0 if loss == min_loss else 0.0
                candidate_rows.append(
                    _candidate_row(
                        trace_name="trace1",
                        trace_family="fam",
                        capacity=8,
                        horizon=2,
                        decision_id=decision_id,
                        decision_t=decision_index,
                        candidate_page_id=page_id,
                        split=split,
                        y_loss=loss,
                        y_value=-loss,
                        candidate_lru_score=loss,
                        candidate_predictor_score=loss * 2.0,
                        candidate_recency_rank=loss * 10.0,
                        candidate_age_norm=loss * 0.1,
                        candidate_is_lru_victim=is_victim,
                        candidate_is_predictor_victim=is_victim,
                    )
                )
                decision_candidates.append({"candidate_page_id": page_id, "y_loss": loss})
            shared = {
                "decision_id": decision_id,
                "capacity": 8,
                "horizon": 2,
                "split": split,
                "trace_family": "fam",
                "trace_name": "trace1",
            }
            pairwise_rows.extend(_bare_pairwise_rows(shared, decision_candidates))

        frame = pd.DataFrame.from_records(candidate_rows, columns=CANONICAL_COLUMNS)
        relative_path = f"data/candidate_rows/split={split}/trace_family=fam/capacity=8/horizon=2/candidate_rows.parquet"
        output_path = root / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(pa.Table.from_pandas(frame, preserve_index=False), output_path)
        candidate_partitions.append(
            {
                "path": relative_path,
                "row_count": int(len(frame)),
                "split": split,
                "trace_family": "fam",
                "capacity": 8,
                "horizon": 2,
            }
        )

    metadata_dir = root / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "dataset_name": "lafc-evict-pairwise-fixture",
        "version": "0.1",
        "release_type": "synthetic_sample",
        "schema_version": "lafc-evict-candidate-v1",
        "selected_families": ["fam"],
        "excluded_families": [],
        "row_counts": {
            "candidate_rows": sum(entry["row_count"] for entry in candidate_partitions),
            "decision_view": 0,
            "pairwise_sample": len(pairwise_rows),
        },
        "candidate_partitions": candidate_partitions,
    }
    (metadata_dir / "release_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    pairwise_dir = root / "data" / "pairwise_sample"
    pairwise_dir.mkdir(parents=True, exist_ok=True)
    pairwise_df = pd.DataFrame.from_records(pairwise_rows, columns=PAIRWISE_BARE_COLUMNS)
    pq.write_table(pa.Table.from_pandas(pairwise_df, preserve_index=False), pairwise_dir / "pairwise_sample.parquet")

    return root


@pytest.fixture()
def tiny_release(tmp_path: Path) -> Path:
    return _build_release(tmp_path / "tiny-release")


def test_augmented_join_row_count_matches_input(tiny_release: Path, tmp_path: Path) -> None:
    module = _load_module("build_augmented_pairwise_sample")
    output_dir = tmp_path / "pairwise_out_rowcount"
    module.main(["--release-root", str(tiny_release), "--output-dir", str(output_dir), "--mode", "run"])

    input_df = pd.read_parquet(tiny_release / "data" / "pairwise_sample" / "pairwise_sample.parquet")
    output_df = pd.read_parquet(output_dir / "augmented_pairwise_sample.parquet")

    assert len(output_df) == len(input_df)
    assert not (output_dir / ".augmented_pairwise_sample.checkpoint.json").exists()
    assert not (output_dir / ".augmented_pairwise_sample.shards").exists()


def test_augmented_join_has_ab_feature_suffixes(tiny_release: Path, tmp_path: Path) -> None:
    module = _load_module("build_augmented_pairwise_sample")
    output_dir = tmp_path / "pairwise_out_suffixes"
    module.main(["--release-root", str(tiny_release), "--output-dir", str(output_dir), "--mode", "run"])

    output_df = pd.read_parquet(output_dir / "augmented_pairwise_sample.parquet")
    for feature in module.CORE_FEATURE_COLUMNS:
        assert f"{feature}_a" in output_df.columns
        assert f"{feature}_b" in output_df.columns

    row = output_df[
        (output_df["decision_id"] == "d1")
        & (output_df["candidate_a_page_id"] == "A")
        & (output_df["candidate_b_page_id"] == "B")
        & (output_df["split"] == "train")
    ].iloc[0]
    assert row["candidate_lru_score_a"] == pytest.approx(1.0)
    assert row["candidate_lru_score_b"] == pytest.approx(2.0)
    assert row["candidate_predictor_score_a"] == pytest.approx(2.0)
    assert row["candidate_predictor_score_b"] == pytest.approx(4.0)


def test_missing_join_fails_loudly(tiny_release: Path, tmp_path: Path) -> None:
    pairwise_path = tiny_release / "data" / "pairwise_sample" / "pairwise_sample.parquet"
    df = pd.read_parquet(pairwise_path)
    df.loc[0, "candidate_a_page_id"] = "does-not-exist"
    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), pairwise_path)

    module = _load_module("build_augmented_pairwise_sample")
    output_dir = tmp_path / "pairwise_out_missing"
    with pytest.raises(ValueError, match="failed to join"):
        module.main(["--release-root", str(tiny_release), "--output-dir", str(output_dir), "--mode", "run"])


def test_feature_pairwise_baseline_runs_without_crashing(tiny_release: Path, tmp_path: Path) -> None:
    build_module = _load_module("build_augmented_pairwise_sample")
    value_module = _load_module("run_value_regression_baseline")
    baseline_module = _load_module("run_feature_pairwise_baseline")

    pairwise_out = tmp_path / "pairwise_out_full"
    build_module.main(["--release-root", str(tiny_release), "--output-dir", str(pairwise_out), "--mode", "run"])

    value_out = tmp_path / "value_out_full"
    value_module.main(
        [
            "--release-root",
            str(tiny_release),
            "--output-dir",
            str(value_out),
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

    results_out = tmp_path / "results_out_full"
    baseline_module.main(
        [
            "--release-root",
            str(tiny_release),
            "--augmented-path",
            str(pairwise_out / "augmented_pairwise_sample.parquet"),
            "--linear-score-json",
            str(value_out / "linear_regression_y_loss.json"),
            "--output-dir",
            str(results_out),
        ]
    )

    assert (results_out / "feature_pairwise_results.json").exists()
    assert (results_out / "feature_pairwise_results.csv").exists()
    assert (results_out / "feature_pairwise_results.md").exists()

    payload = json.loads((results_out / "feature_pairwise_results.json").read_text(encoding="utf-8"))
    assert payload["status"] == "available"
    assert payload["non_tie_row_count"] > 0
    assert payload["tie_row_count"] >= 1

    expected_baselines = [
        "random_non_tie",
        "majority_non_tie",
        "lru_score_pairwise",
        "predictor_score_pairwise",
        "linear_score_pairwise",
        "logistic_regression_pairwise",
    ]
    for name in expected_baselines:
        assert name in payload["baselines"], payload["baselines"].keys()
        baseline = payload["baselines"][name]
        assert baseline.get("status") != "skipped", f"{name} unexpectedly skipped: {baseline}"
        assert baseline["overall"]["accuracy"] is not None
        assert baseline["overall"]["log_loss"] is not None
        for split_metrics in baseline["split_metrics"].values():
            assert split_metrics["rows"] > 0
