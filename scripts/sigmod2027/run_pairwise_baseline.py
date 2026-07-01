#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from _baseline_common import load_manifest, parquet_schema_names, release_summary, repo_relative, require_columns, write_json

PAIRWISE_REQUIRED_COLUMNS = [
    "decision_id",
    "capacity",
    "horizon",
    "split",
    "trace_family",
    "trace_name",
    "label_a_better",
    "label_b_better",
    "is_tie",
]

PAIRWISE_FEATURE_COLUMNS = [
    "candidate_lru_score_a",
    "candidate_lru_score_b",
    "candidate_predictor_score_a",
    "candidate_predictor_score_b",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan or run a very light pairwise baseline over the shipped LAFC-Evict pairwise sample."
    )
    parser.add_argument(
        "--release-root",
        default="release/lafc-evict-v0.1-open-current-contract-preserved",
        help="Repo-relative preserved release path.",
    )
    parser.add_argument(
        "--pairwise-path",
        default="data/pairwise_sample/pairwise_sample.parquet",
        help="Pairwise sample path relative to the release root.",
    )
    parser.add_argument(
        "--output-dir",
        default="paper/sigmod2027/results/baselines/pairwise",
        help="Directory for plan or result JSON files.",
    )
    parser.add_argument(
        "--mode",
        choices=["plan", "run-light"],
        default="plan",
        help="Planning mode or a very light local run on the non-tie subset.",
    )
    parser.add_argument(
        "--baseline",
        choices=["majority_non_tie", "random_non_tie"],
        default="majority_non_tie",
        help="Baseline used for run-light mode.",
    )
    parser.add_argument("--seed", type=int, default=7, help="Seed for the random baseline.")
    return parser.parse_args()


def binary_log_loss(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    eps = 1e-12
    clipped = np.clip(y_prob, eps, 1.0 - eps)
    return float(-(y_true * np.log(clipped) + (1.0 - y_true) * np.log(1.0 - clipped)).mean())


def build_plan_payload(args: argparse.Namespace, manifest: dict[str, object], pairwise_path: Path, schema: list[str]) -> dict[str, object]:
    missing_required = require_columns(schema, PAIRWISE_REQUIRED_COLUMNS)
    missing_feature = require_columns(schema, PAIRWISE_FEATURE_COLUMNS)
    feature_ready = not missing_feature
    return {
        "task": "pairwise_preference",
        "status": "dry_run_checked",
        "mode": "plan",
        "release_root": args.release_root,
        "input_view": "pairwise_sample",
        "input_path": repo_relative(pairwise_path),
        "full_validation_status": "pending",
        "requires_large_memory_machine": False,
        "safe_for_anonymous_manuscript": False,
        "metrics": ["accuracy_non_tie", "binary_log_loss_non_tie", "roc_auc_if_score_based"],
        "baselines": [
            {"name": "random_non_tie", "status": "available_now"},
            {"name": "majority_non_tie", "status": "available_now"},
            {"name": "lru_indicator_pairwise", "status": "blocked_without_feature_join"},
            {"name": "predictor_score_pairwise", "status": "blocked_without_feature_join"},
            {"name": "logistic_regression_pairwise", "status": "blocked_without_feature_join"},
        ],
        "schema_check": {
            "required_columns": PAIRWISE_REQUIRED_COLUMNS,
            "available_columns": schema,
            "missing_required_columns": missing_required,
            "candidate_feature_columns_checked": PAIRWISE_FEATURE_COLUMNS,
            "missing_candidate_feature_columns": missing_feature,
            "feature_ready": feature_ready,
        },
        "release_summary": release_summary(manifest),
        "blockers": [
            "the shipped pairwise sample does not currently include candidate-side predictor or LRU feature columns",
            "feature-based pairwise baselines therefore require an augmented pairwise export or a candidate-row feature join on a large-memory execution environment",
            "full real-release validation is still pending",
        ],
        "recommended_next_step": "Run a light non-tie sanity baseline now, or prepare a feature join on a large-memory execution environment for richer pairwise models.",
    }


def run_light_baseline(args: argparse.Namespace, pairwise_path: Path, plan_payload: dict[str, object]) -> dict[str, object]:
    columns = ["split", "label_a_better", "label_b_better", "is_tie"]
    df = pd.read_parquet(pairwise_path, columns=columns)
    non_tie = df[df["is_tie"] == 0].copy()
    if non_tie.empty:
        raise ValueError("pairwise sample contains no non-tie rows to evaluate")

    non_tie["target"] = non_tie["label_a_better"].astype(int)
    train = non_tie[non_tie["split"] == "train"]
    if train.empty:
        raise ValueError("train split is empty on the non-tie subset")

    positive_rate = float(train["target"].mean())
    majority_label = int(positive_rate >= 0.5)
    rng = np.random.default_rng(args.seed)

    split_metrics: dict[str, dict[str, float | int | None]] = {}
    for split in ["train", "val", "test"]:
        split_df = non_tie[non_tie["split"] == split]
        if split_df.empty:
            continue

        y_true = split_df["target"].to_numpy(dtype=float)
        if args.baseline == "majority_non_tie":
            y_pred = np.full(len(split_df), majority_label, dtype=int)
            y_prob = np.full(len(split_df), positive_rate, dtype=float)
        else:
            y_pred = rng.integers(0, 2, size=len(split_df), dtype=int)
            y_prob = np.full(len(split_df), 0.5, dtype=float)

        split_metrics[split] = {
            "rows": int(len(split_df)),
            "positive_rate": float(y_true.mean()),
            "accuracy": float((y_pred == y_true).mean()),
            "log_loss": binary_log_loss(y_true, y_prob),
            "roc_auc": None,
        }

    return {
        "task": "pairwise_preference",
        "status": "available",
        "mode": "run_light",
        "baseline": args.baseline,
        "release_root": args.release_root,
        "input_view": "pairwise_sample",
        "input_path": repo_relative(pairwise_path),
        "evaluation_population": "non_tie_rows_only",
        "full_validation_status": "pending",
        "requires_large_memory_machine": False,
        "safe_for_anonymous_manuscript": False,
        "metrics": ["accuracy_non_tie", "binary_log_loss_non_tie"],
        "release_summary": plan_payload["release_summary"],
        "tie_row_count": int(df["is_tie"].sum()),
        "non_tie_row_count": int((df["is_tie"] == 0).sum()),
        "split_metrics": split_metrics,
        "notes": [
            "This is a lightweight sanity baseline over the shipped pairwise sample only.",
            "Feature-based pairwise baselines still require candidate-row feature joins or an augmented pairwise export.",
        ],
    }


def main() -> None:
    args = parse_args()
    release_root = Path(args.release_root)
    pairwise_path = release_root / args.pairwise_path
    output_dir = Path(args.output_dir)
    manifest = load_manifest(release_root)
    schema = parquet_schema_names(pairwise_path)
    plan_payload = build_plan_payload(args, manifest, pairwise_path, schema)

    if args.mode == "plan":
        write_json(output_dir / "plan.json", plan_payload)
        print(f"Wrote {output_dir / 'plan.json'}")
        return

    result = run_light_baseline(args, pairwise_path, plan_payload)
    write_json(output_dir / f"{args.baseline}.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
