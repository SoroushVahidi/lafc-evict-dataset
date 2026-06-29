#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from _baseline_common import (
    FEATURE_COLUMNS,
    FULL_VALIDATION_STATUS,
    available_feature_columns,
    build_file_budget,
    budget_exhausted,
    candidate_file_inventory,
    candidate_schema_summary,
    checkpoint_path,
    consume_budget,
    ensure_output_dir_safe,
    guard_output_path,
    iter_candidate_batches,
    load_checkpoint,
    load_manifest,
    release_summary,
    remove_checkpoint,
    repo_relative,
    reset_outputs,
    save_checkpoint,
    write_json,
)


@dataclass
class MomentAccumulator:
    count: int
    sums: list[float]
    non_missing_counts: list[int]

    @classmethod
    def create(cls, dimension: int) -> "MomentAccumulator":
        return cls(count=0, sums=[0.0] * dimension, non_missing_counts=[0] * dimension)

    def update(self, matrix: np.ndarray) -> None:
        if matrix.size == 0:
            return
        self.count += int(matrix.shape[0])
        finite_mask = np.isfinite(matrix)
        sums = np.where(finite_mask, matrix, 0.0).sum(axis=0)
        counts = finite_mask.sum(axis=0)
        for index, value in enumerate(sums.tolist()):
            self.sums[index] += float(value)
            self.non_missing_counts[index] += int(counts[index])

    def means(self) -> list[float]:
        means: list[float] = []
        for value, count in zip(self.sums, self.non_missing_counts):
            means.append(0.0 if count == 0 else value / count)
        return means

    def to_state(self) -> dict[str, object]:
        return {
            "count": self.count,
            "sums": self.sums,
            "non_missing_counts": self.non_missing_counts,
        }

    @classmethod
    def from_state(cls, payload: dict[str, object]) -> "MomentAccumulator":
        return cls(
            count=int(payload.get("count", 0)),
            sums=[float(value) for value in payload.get("sums", [])],
            non_missing_counts=[int(value) for value in payload.get("non_missing_counts", [])],
        )


@dataclass
class SquaredErrorAccumulator:
    rows: int = 0
    y_sum: float = 0.0
    y_sum_squares: float = 0.0
    absolute_error_sum: float = 0.0
    squared_error_sum: float = 0.0
    constant_absolute_error_sum: float = 0.0
    constant_squared_error_sum: float = 0.0

    def update(self, y_true: np.ndarray, y_pred: np.ndarray, constant_pred: float) -> None:
        if y_true.size == 0:
            return
        self.rows += int(y_true.size)
        self.y_sum += float(y_true.sum())
        self.y_sum_squares += float(np.square(y_true).sum())
        self.absolute_error_sum += float(np.abs(y_pred - y_true).sum())
        self.squared_error_sum += float(np.square(y_pred - y_true).sum())
        self.constant_absolute_error_sum += float(np.abs(constant_pred - y_true).sum())
        self.constant_squared_error_sum += float(np.square(constant_pred - y_true).sum())

    def to_metrics(self) -> dict[str, float | int | None]:
        if self.rows == 0:
            return {
                "rows": 0,
                "mae": None,
                "rmse": None,
                "r2": None,
                "constant_predictor_mae": None,
                "constant_predictor_rmse": None,
            }
        mean = self.y_sum / self.rows
        sst = self.y_sum_squares - (self.rows * mean * mean)
        r2 = None if sst <= 0 else 1.0 - (self.squared_error_sum / sst)
        return {
            "rows": self.rows,
            "mae": self.absolute_error_sum / self.rows,
            "rmse": math.sqrt(self.squared_error_sum / self.rows),
            "r2": r2,
            "constant_predictor_mae": self.constant_absolute_error_sum / self.rows,
            "constant_predictor_rmse": math.sqrt(self.constant_squared_error_sum / self.rows),
        }

    def to_state(self) -> dict[str, object]:
        return {
            "rows": self.rows,
            "y_sum": self.y_sum,
            "y_sum_squares": self.y_sum_squares,
            "absolute_error_sum": self.absolute_error_sum,
            "squared_error_sum": self.squared_error_sum,
            "constant_absolute_error_sum": self.constant_absolute_error_sum,
            "constant_squared_error_sum": self.constant_squared_error_sum,
        }

    @classmethod
    def from_state(cls, payload: dict[str, object]) -> "SquaredErrorAccumulator":
        return cls(
            rows=int(payload.get("rows", 0)),
            y_sum=float(payload.get("y_sum", 0.0)),
            y_sum_squares=float(payload.get("y_sum_squares", 0.0)),
            absolute_error_sum=float(payload.get("absolute_error_sum", 0.0)),
            squared_error_sum=float(payload.get("squared_error_sum", 0.0)),
            constant_absolute_error_sum=float(payload.get("constant_absolute_error_sum", 0.0)),
            constant_squared_error_sum=float(payload.get("constant_squared_error_sum", 0.0)),
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan or run a streaming linear value-regression baseline over LAFC-Evict candidate rows."
    )
    parser.add_argument(
        "--release-root",
        default="release/lafc-evict-v0.1-open-current-contract-preserved",
        help="Repo-relative or absolute preserved release path.",
    )
    parser.add_argument(
        "--output-dir",
        default="paper/sigmod2027/results/baselines/value_regression",
        help="Directory for plan, checkpoint, and result outputs.",
    )
    parser.add_argument(
        "--target",
        choices=["y_loss", "y_value"],
        default="y_loss",
        help="Candidate-level regression target.",
    )
    parser.add_argument(
        "--mode",
        choices=["plan", "run"],
        default="plan",
        help="Plan mode inspects metadata/schema only; run mode streams candidate rows.",
    )
    parser.add_argument("--max-files", type=int, default=None, help="Process at most this many files per invocation.")
    parser.add_argument("--resume", action="store_true", help="Resume from an existing checkpoint.")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing outputs or checkpoints.")
    parser.add_argument(
        "--features",
        nargs="*",
        default=None,
        help="Optional explicit numeric feature list. Defaults to all available schema feature columns.",
    )
    return parser.parse_args(argv)


def output_file_for_target(output_dir: Path, target: str) -> Path:
    return output_dir / f"linear_regression_{target}.json"


def plan_payload(
    *,
    args: argparse.Namespace,
    manifest: dict[str, object],
    release_root: Path,
    schema_summary: dict[str, object],
    features: list[str],
    inventory: list[dict[str, object]],
    output_path: Path,
    checkpoint: Path,
) -> dict[str, object]:
    return {
        "task": "value_regression",
        "status": "dry_run_checked",
        "mode": "plan",
        "release_root": str(release_root),
        "input_view": "candidate_rows",
        "input_path": repo_relative(release_root / "data" / "candidate_rows"),
        "target": args.target,
        "full_validation_status": FULL_VALIDATION_STATUS,
        "requires_wolverine": True,
        "safe_for_anonymous_manuscript": False,
        "metrics": ["rows", "MAE", "RMSE", "R2", "constant_predictor_MAE", "constant_predictor_RMSE"],
        "baseline": "linear_regression",
        "features": features,
        "schema_check": schema_summary,
        "candidate_partition_count": len(inventory),
        "release_summary": release_summary(manifest),
        "planned_output_file": repo_relative(output_path),
        "checkpoint_path": repo_relative(checkpoint),
        "notes": [
            "Plan mode reads release metadata and one candidate partition schema only.",
            "Run mode trains with streaming normal-equation accumulation and never loads the full release into memory.",
        ],
    }


def initial_state(features: list[str]) -> dict[str, object]:
    dimension = len(features)
    return {
        "stage": "fit_stats",
        "features": features,
        "fit_stats": {
            "next_file_index": 0,
            "feature_moments": MomentAccumulator.create(dimension).to_state(),
            "target_sum": 0.0,
            "target_count": 0,
            "train_rows": 0,
        },
        "fit_model": {
            "next_file_index": 0,
            "xtx": [[0.0] * (dimension + 1) for _ in range(dimension + 1)],
            "xty": [0.0] * (dimension + 1),
        },
        "evaluate": {
            "next_file_index": 0,
            "metrics": {split: SquaredErrorAccumulator().to_state() for split in ["train", "val", "test", "other"]},
        },
        "model": None,
    }


def load_state(checkpoint: dict[str, object], features: list[str]) -> dict[str, object]:
    state = checkpoint.get("state")
    if not isinstance(state, dict):
        raise ValueError("Checkpoint is missing state")
    if state.get("features") != features:
        raise ValueError("Checkpoint features do not match current invocation")
    return state


def normalize_split(split_value: object) -> str:
    text = str(split_value).strip().lower()
    if text in {"train", "val", "test"}:
        return text
    if text == "validation":
        return "val"
    return "other"


def filter_train_rows(batch, target: str, features: list[str]) -> tuple[np.ndarray, np.ndarray]:
    split_series = batch["split"].map(normalize_split)
    train = batch[split_series == "train"]
    if train.empty:
        return np.empty((0, len(features))), np.empty((0,))
    target_values = train[target].to_numpy(dtype=float)
    target_mask = np.isfinite(target_values)
    if not target_mask.any():
        return np.empty((0, len(features))), np.empty((0,))
    feature_matrix = train[features].to_numpy(dtype=float)[target_mask]
    return feature_matrix, target_values[target_mask]


def fill_missing_features(matrix: np.ndarray, feature_means: np.ndarray) -> np.ndarray:
    return np.where(np.isfinite(matrix), matrix, feature_means)


def update_fit_stats(state: dict[str, object], batch, target: str, features: list[str]) -> None:
    feature_matrix, target_values = filter_train_rows(batch, target, features)
    if target_values.size == 0:
        return
    moments = MomentAccumulator.from_state(state["fit_stats"]["feature_moments"])
    moments.update(feature_matrix)
    state["fit_stats"]["feature_moments"] = moments.to_state()
    state["fit_stats"]["target_sum"] = float(state["fit_stats"]["target_sum"]) + float(target_values.sum())
    state["fit_stats"]["target_count"] = int(state["fit_stats"]["target_count"]) + int(target_values.size)
    state["fit_stats"]["train_rows"] = int(state["fit_stats"]["train_rows"]) + int(target_values.size)


def finalize_fit_stats(state: dict[str, object]) -> None:
    moments = MomentAccumulator.from_state(state["fit_stats"]["feature_moments"])
    feature_means = moments.means()
    target_count = int(state["fit_stats"]["target_count"])
    target_mean = 0.0 if target_count == 0 else float(state["fit_stats"]["target_sum"]) / target_count
    state["model"] = {
        "feature_means": feature_means,
        "train_target_mean": target_mean,
        "coefficients": None,
        "intercept": None,
    }
    state["stage"] = "fit_model"


def update_fit_model(state: dict[str, object], batch, target: str, features: list[str]) -> None:
    feature_matrix, target_values = filter_train_rows(batch, target, features)
    if target_values.size == 0:
        return
    feature_means = np.asarray(state["model"]["feature_means"], dtype=float)
    filled = fill_missing_features(feature_matrix, feature_means)
    design = np.column_stack([np.ones(filled.shape[0], dtype=float), filled])
    xtx = np.asarray(state["fit_model"]["xtx"], dtype=float)
    xty = np.asarray(state["fit_model"]["xty"], dtype=float)
    xtx += design.T @ design
    xty += design.T @ target_values
    state["fit_model"]["xtx"] = xtx.tolist()
    state["fit_model"]["xty"] = xty.tolist()


def finalize_fit_model(state: dict[str, object]) -> None:
    xtx = np.asarray(state["fit_model"]["xtx"], dtype=float)
    xty = np.asarray(state["fit_model"]["xty"], dtype=float)
    coefficients = np.linalg.pinv(xtx) @ xty
    state["model"]["intercept"] = float(coefficients[0])
    state["model"]["coefficients"] = coefficients[1:].tolist()
    state["stage"] = "evaluate"


def update_evaluation(state: dict[str, object], batch, target: str, features: list[str]) -> None:
    target_values = batch[target].to_numpy(dtype=float)
    target_mask = np.isfinite(target_values)
    if not target_mask.any():
        return
    splits = batch["split"].map(normalize_split).to_numpy()[target_mask]
    feature_matrix = batch[features].to_numpy(dtype=float)[target_mask]
    y_true = target_values[target_mask]
    feature_means = np.asarray(state["model"]["feature_means"], dtype=float)
    coefficients = np.asarray(state["model"]["coefficients"], dtype=float)
    intercept = float(state["model"]["intercept"])
    constant_pred = float(state["model"]["train_target_mean"])
    filled = fill_missing_features(feature_matrix, feature_means)
    predictions = intercept + filled @ coefficients

    for split in np.unique(splits):
        split_mask = splits == split
        accumulator = SquaredErrorAccumulator.from_state(state["evaluate"]["metrics"][split])
        accumulator.update(y_true[split_mask], predictions[split_mask], constant_pred)
        state["evaluate"]["metrics"][split] = accumulator.to_state()


def finalize_evaluation(state: dict[str, object]) -> dict[str, object]:
    split_metrics: dict[str, object] = {}
    for split, payload in state["evaluate"]["metrics"].items():
        metrics = SquaredErrorAccumulator.from_state(payload).to_metrics()
        if metrics["rows"]:
            split_metrics[split] = metrics
    return split_metrics


def advance_stage(state: dict[str, object]) -> None:
    if state["stage"] == "fit_stats":
        finalize_fit_stats(state)
        return
    if state["stage"] == "fit_model":
        finalize_fit_model(state)
        return
    if state["stage"] == "evaluate":
        state["stage"] = "complete"
        return
    raise ValueError(f"Unknown stage: {state['stage']}")


def stage_file_index(state: dict[str, object]) -> int:
    if state["stage"] == "fit_stats":
        return int(state["fit_stats"]["next_file_index"])
    if state["stage"] == "fit_model":
        return int(state["fit_model"]["next_file_index"])
    if state["stage"] == "evaluate":
        return int(state["evaluate"]["next_file_index"])
    return 0


def set_stage_file_index(state: dict[str, object], value: int) -> None:
    if state["stage"] == "fit_stats":
        state["fit_stats"]["next_file_index"] = value
    elif state["stage"] == "fit_model":
        state["fit_model"]["next_file_index"] = value
    elif state["stage"] == "evaluate":
        state["evaluate"]["next_file_index"] = value


def process_stage_file(state: dict[str, object], path: Path, target: str, features: list[str]) -> None:
    columns = ["split", target, *features]
    for batch in iter_candidate_batches(path, columns=columns):
        if state["stage"] == "fit_stats":
            update_fit_stats(state, batch, target, features)
        elif state["stage"] == "fit_model":
            update_fit_model(state, batch, target, features)
        elif state["stage"] == "evaluate":
            update_evaluation(state, batch, target, features)
        else:
            raise ValueError(f"Unknown stage: {state['stage']}")


def result_payload(
    *,
    args: argparse.Namespace,
    release_root: Path,
    manifest: dict[str, object],
    output_path: Path,
    inventory: list[dict[str, object]],
    state: dict[str, object],
) -> dict[str, object]:
    model = state["model"]
    return {
        "task": "value_regression",
        "status": "available",
        "mode": "run",
        "release_root": str(release_root),
        "input_view": "candidate_rows",
        "input_path": repo_relative(release_root / "data" / "candidate_rows"),
        "target": args.target,
        "full_validation_status": FULL_VALIDATION_STATUS,
        "requires_wolverine": True,
        "safe_for_anonymous_manuscript": True,
        "baseline": "linear_regression",
        "features": state["features"],
        "files_total": len(inventory),
        "release_summary": release_summary(manifest),
        "output_file": repo_relative(output_path),
        "model": {
            "intercept": model["intercept"],
            "coefficients": dict(zip(state["features"], model["coefficients"])),
            "feature_means": dict(zip(state["features"], model["feature_means"])),
            "train_target_mean": model["train_target_mean"],
            "training_rows": int(state["fit_stats"]["train_rows"]),
        },
        "split_metrics": finalize_evaluation(state),
        "notes": [
            "Training used streaming normal-equation accumulation over train rows only.",
            "Evaluation streamed candidate parquet files without loading the full release into memory.",
        ],
    }


def run(args: argparse.Namespace) -> None:
    release_root = Path(args.release_root)
    output_dir = ensure_output_dir_safe(Path(args.output_dir), release_root)
    manifest = load_manifest(release_root)
    inventory = candidate_file_inventory(release_root, manifest)
    schema_summary = candidate_schema_summary(release_root, manifest)
    features = available_feature_columns(schema_summary["available_columns"], args.features)
    output_path = guard_output_path(output_file_for_target(output_dir, args.target), release_root)
    checkpoint = guard_output_path(checkpoint_path(output_dir, f"value_regression_{args.target}"), release_root)

    if args.mode == "plan":
        payload = plan_payload(
            args=args,
            manifest=manifest,
            release_root=release_root,
            schema_summary=schema_summary,
            features=features,
            inventory=inventory,
            output_path=output_path,
            checkpoint=checkpoint,
        )
        write_json(output_dir / "plan.json", payload)
        print(f"Wrote {output_dir / 'plan.json'}")
        return

    reset_outputs(output_paths=[output_path], checkpoint_paths=[checkpoint], overwrite=args.overwrite, resume=args.resume)

    if args.resume:
        state = load_state(load_checkpoint(checkpoint), features)
    else:
        state = initial_state(features)

    budget = build_file_budget(args.max_files)

    while state["stage"] != "complete" and not budget_exhausted(budget):
        start_index = stage_file_index(state)
        for file_index in range(start_index, len(inventory)):
            if budget_exhausted(budget):
                break
            process_stage_file(state, inventory[file_index]["path"], args.target, features)
            set_stage_file_index(state, file_index + 1)
            save_checkpoint(
                checkpoint,
                {
                    "task": "value_regression",
                    "release_root": str(release_root),
                    "state": state,
                },
            )
            budget = consume_budget(budget)

        if state["stage"] != "complete" and stage_file_index(state) >= len(inventory):
            set_stage_file_index(state, 0)
            advance_stage(state)
            save_checkpoint(
                checkpoint,
                {
                    "task": "value_regression",
                    "release_root": str(release_root),
                    "state": state,
                },
            )

    if state["stage"] != "complete":
        print(
            json.dumps(
                {
                    "task": "value_regression",
                    "status": "partial",
                    "stage": state["stage"],
                    "files_total": len(inventory),
                    "files_processed_in_stage": stage_file_index(state),
                    "checkpoint_path": repo_relative(checkpoint),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return

    payload = result_payload(
        args=args,
        release_root=release_root,
        manifest=manifest,
        output_path=output_path,
        inventory=inventory,
        state=state,
    )
    write_json(output_path, payload)
    remove_checkpoint(checkpoint)
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> None:
    run(parse_args(argv))


if __name__ == "__main__":
    main()
