#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from _baseline_common import (
    RunningNumericSummary,
    available_feature_columns,
    build_file_budget,
    budget_exhausted,
    candidate_file_inventory,
    candidate_schema_summary,
    checkpoint_path,
    consume_budget,
    current_git_commit,
    current_timestamp_utc,
    decode_group_key,
    detected_validation_status,
    decision_key_columns,
    duplicate_partition_keys,
    encode_group_key,
    ensure_output_dir_safe,
    guard_output_path,
    iter_candidate_batches,
    load_checkpoint,
    load_manifest,
    release_identity,
    release_summary,
    remove_checkpoint,
    repo_relative,
    reset_outputs,
    sanitize_output_name,
    save_checkpoint,
    write_json,
)

DEFAULT_SCORE_COLUMNS = [
    "candidate_is_lru_victim",
    "candidate_is_predictor_victim",
    "candidate_predictor_score",
    "candidate_lru_score",
]
GROUP_BY = ["split", "trace_family", "capacity", "horizon"]


@dataclass
class DecisionMetrics:
    decision_count: int = 0
    optimal_count: int = 0
    regret_sum: float = 0.0
    regret_summary: RunningNumericSummary = field(default_factory=RunningNumericSummary)

    def update(self, regret: float) -> None:
        self.decision_count += 1
        if regret <= 1e-12:
            self.optimal_count += 1
        self.regret_sum += float(regret)
        self.regret_summary.update(np.asarray([regret], dtype=float))

    def to_summary(self) -> dict[str, object]:
        regret = self.regret_summary.to_summary_dict()
        median = regret["quantiles"]["q50"]
        return {
            "decision_count": self.decision_count,
            "optimal_selection_rate": None if self.decision_count == 0 else self.optimal_count / self.decision_count,
            "mean_regret": None if self.decision_count == 0 else self.regret_sum / self.decision_count,
            "median_regret": median,
            "max_regret": regret["max"],
            "regret_quantiles_approximate": regret["quantiles_approximate"],
        }

    def to_state(self) -> dict[str, object]:
        return {
            "decision_count": self.decision_count,
            "optimal_count": self.optimal_count,
            "regret_sum": self.regret_sum,
            "regret_summary": self.regret_summary.to_state(),
        }

    @classmethod
    def from_state(cls, payload: dict[str, object]) -> "DecisionMetrics":
        metrics = cls()
        metrics.decision_count = int(payload.get("decision_count", 0))
        metrics.optimal_count = int(payload.get("optimal_count", 0))
        metrics.regret_sum = float(payload.get("regret_sum", 0.0))
        summary_payload = payload.get("regret_summary", {})
        if isinstance(summary_payload, dict):
            metrics.regret_summary = RunningNumericSummary.from_state(summary_payload)
        return metrics


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan or run a streaming best-candidate baseline over LAFC-Evict candidate rows."
    )
    parser.add_argument(
        "--release-root",
        default="release/lafc-evict-v0.1-open-current-contract-preserved",
        help="Repo-relative or absolute preserved release path.",
    )
    parser.add_argument(
        "--output-dir",
        default="paper/sigmod2027/results/baselines/best_candidate",
        help="Directory for plan, checkpoint, and result outputs.",
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
        "--score-column",
        default=None,
        help="Existing candidate-row score or indicator column to use for selection.",
    )
    parser.add_argument(
        "--linear-score-json",
        default=None,
        help="Value-regression JSON produced by run_value_regression_baseline.py. If set, choose the minimum predicted y_loss.",
    )
    return parser.parse_args(argv)


def detect_score_column(schema_columns: list[str], requested: str | None) -> str:
    if requested:
        if requested not in schema_columns:
            raise ValueError(f"Requested score column missing from candidate schema: {requested}")
        return requested
    for column in DEFAULT_SCORE_COLUMNS:
        if column in schema_columns:
            return column
    raise ValueError("No supported score column found in the candidate schema")


def scorer_config(args: argparse.Namespace, schema_columns: list[str]) -> dict[str, object]:
    if args.linear_score_json:
        payload = json.loads(Path(args.linear_score_json).read_text(encoding="utf-8"))
        model = payload.get("model", {})
        coefficients = model.get("coefficients", {})
        if not isinstance(coefficients, dict) or not coefficients:
            raise ValueError("Linear-score JSON is missing model coefficients")
        features = list(coefficients.keys())
        available_feature_columns(schema_columns, features)
        return {
            "mode": "linear_score",
            "direction": "min",
            "features": features,
            "intercept": float(model.get("intercept", 0.0)),
            "coefficients": {key: float(value) for key, value in coefficients.items()},
            "feature_means": {key: float(value) for key, value in model.get("feature_means", {}).items()},
            "source_json": str(Path(args.linear_score_json)),
        }
    column = detect_score_column(schema_columns, args.score_column)
    direction = "max"
    return {
        "mode": "score_column",
        "direction": direction,
        "score_column": column,
    }


def output_filename(config: dict[str, object]) -> str:
    if config["mode"] == "linear_score":
        return "best_candidate_from_linear_score.json"
    return f"best_candidate_from_{sanitize_output_name(str(config['score_column']))}.json"


def plan_payload(
    *,
    release_root: Path,
    manifest: dict[str, object],
    schema_summary: dict[str, object],
    inventory: list[dict[str, object]],
    config: dict[str, object],
    output_path: Path,
    checkpoint: Path,
) -> dict[str, object]:
    return {
        "task": "best_candidate",
        "status": "dry_run_checked",
        "mode": "plan",
        "timestamp_utc": current_timestamp_utc(),
        "git_commit": current_git_commit(),
        "release_root": str(release_root),
        "release_identity": release_identity(manifest),
        "input_view": "candidate_rows",
        "input_path": repo_relative(release_root / "data" / "candidate_rows"),
        "full_validation_status": detected_validation_status(release_root),
        "requires_wolverine": True,
        "safe_for_anonymous_manuscript": False,
        "metrics": ["decision_count", "optimal_selection_rate", "mean_regret", "median_regret"],
        "scorer": config,
        "schema_check": schema_summary,
        "candidate_partition_count": len(inventory),
        "release_summary": release_summary(manifest),
        "planned_output_file": repo_relative(output_path),
        "checkpoint_path": repo_relative(checkpoint),
        "notes": [
            "Plan mode reads release metadata and one candidate partition schema only.",
            "Run mode assumes candidate rows remain decision-contiguous within each partition, matching the release builder ordering.",
        ],
        "limitations": [
            "If a future release format ever shards one decision across multiple manifest-listed candidate parquet files, this runner relies on carryover logic rather than decision-view joins.",
        ],
    }


def initial_state(config: dict[str, object]) -> dict[str, object]:
    return {
        "stage": "evaluate",
        "scorer": config,
        "next_file_index": 0,
        "carryover_rows": [],
        "overall": DecisionMetrics().to_state(),
        "groups": {},
    }


def load_state(checkpoint: dict[str, object], config: dict[str, object]) -> dict[str, object]:
    state = checkpoint.get("state")
    if not isinstance(state, dict):
        raise ValueError("Checkpoint is missing state")
    if state.get("scorer") != config:
        raise ValueError("Checkpoint scorer configuration does not match current invocation")
    return state


def score_candidates(frame: pd.DataFrame, config: dict[str, object]) -> np.ndarray:
    if config["mode"] == "linear_score":
        values = np.full(len(frame), float(config["intercept"]), dtype=float)
        for feature in config["features"]:
            column = frame[feature].to_numpy(dtype=float)
            filled = np.where(np.isfinite(column), column, float(config["feature_means"].get(feature, 0.0)))
            values += filled * float(config["coefficients"][feature])
        return values
    return frame[str(config["score_column"])].to_numpy(dtype=float)


def select_row(frame: pd.DataFrame, config: dict[str, object]) -> pd.Series:
    scores = score_candidates(frame, config)
    if config["direction"] == "min":
        effective_scores = np.where(np.isfinite(scores), scores, np.inf)
        best_score = np.min(effective_scores)
        candidate_indices = np.flatnonzero(scores == best_score)
    else:
        effective_scores = np.where(np.isfinite(scores), scores, -np.inf)
        best_score = np.max(effective_scores)
        candidate_indices = np.flatnonzero(scores == best_score)
    if candidate_indices.size == 0:
        candidate_indices = np.asarray([0], dtype=int)
    candidates = frame.iloc[candidate_indices].copy()
    candidates = candidates.sort_values("candidate_page_id", kind="stable")
    return candidates.iloc[0]


def update_metrics(state: dict[str, object], group_key: str, regret: float) -> None:
    overall = DecisionMetrics.from_state(state["overall"])
    overall.update(regret)
    state["overall"] = overall.to_state()

    groups = state["groups"]
    metrics_payload = groups.get(group_key)
    metrics = DecisionMetrics.from_state(metrics_payload) if isinstance(metrics_payload, dict) else DecisionMetrics()
    metrics.update(regret)
    groups[group_key] = metrics.to_state()


def process_complete_frame(frame: pd.DataFrame, state: dict[str, object], config: dict[str, object]) -> None:
    if frame.empty:
        return
    for _, group in frame.groupby(decision_key_columns(), sort=False, dropna=False):
        valid_group = group[np.isfinite(group["y_loss"].to_numpy(dtype=float))]
        if valid_group.empty:
            continue
        selected = select_row(valid_group, config)
        best_loss = float(valid_group["y_loss"].min())
        regret = float(selected["y_loss"]) - best_loss
        group_key = encode_group_key([selected[column] for column in GROUP_BY])
        update_metrics(state, group_key, regret)


def split_complete_and_carryover(batch: pd.DataFrame, carryover_rows: list[dict[str, object]]) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    if carryover_rows:
        batch = pd.concat([pd.DataFrame(carryover_rows), batch], ignore_index=True)
    if batch.empty:
        return batch, []
    last_key = tuple(batch.iloc[-1][column] for column in decision_key_columns())
    key_frame = batch[decision_key_columns()]
    matches_last = np.ones(len(batch), dtype=bool)
    for column, value in zip(decision_key_columns(), last_key):
        matches_last &= key_frame[column].to_numpy() == value
    first_last_index = int(np.flatnonzero(matches_last)[0])
    complete = batch.iloc[:first_last_index].copy()
    carryover = batch.iloc[first_last_index:].to_dict(orient="records")
    return complete, carryover


def result_payload(
    *,
    release_root: Path,
    manifest: dict[str, object],
    output_path: Path,
    inventory: list[dict[str, object]],
    state: dict[str, object],
) -> dict[str, object]:
    overall = DecisionMetrics.from_state(state["overall"]).to_summary()
    grouped = []
    for key in sorted(state["groups"]):
        summary = DecisionMetrics.from_state(state["groups"][key]).to_summary()
        grouped.append({**{column: value for column, value in zip(GROUP_BY, decode_group_key(key))}, **summary})
    return {
        "task": "best_candidate",
        "status": "available",
        "mode": "run",
        "timestamp_utc": current_timestamp_utc(),
        "git_commit": current_git_commit(),
        "release_root": str(release_root),
        "release_identity": release_identity(manifest),
        "input_view": "candidate_rows",
        "input_path": repo_relative(release_root / "data" / "candidate_rows"),
        "full_validation_status": detected_validation_status(release_root),
        "requires_wolverine": True,
        "safe_for_anonymous_manuscript": True,
        "scorer": state["scorer"],
        "files_total": len(inventory),
        "files_processed": len(inventory),
        "release_summary": release_summary(manifest),
        "output_file": repo_relative(output_path),
        "overall_metrics": overall,
        "group_metrics": grouped,
        "notes": [
            "Evaluation streamed candidate parquet files without loading the full release into memory.",
            "Decision regret is computed as selected y_loss minus the minimum y_loss within the same decision.",
        ],
        "limitations": [
            "The current implementation only evaluates y_loss-based regret, even when the scorer is not derived from a regression model.",
            "The default score-column path prefers explicit victim-indicator columns over raw score columns when both are present.",
        ],
    }


def run(args: argparse.Namespace) -> None:
    release_root = Path(args.release_root)
    output_dir = ensure_output_dir_safe(Path(args.output_dir), release_root)
    manifest = load_manifest(release_root)
    inventory = candidate_file_inventory(release_root, manifest)
    duplicates = duplicate_partition_keys(inventory)
    if duplicates:
        rendered = ", ".join(str(key) for key in duplicates)
        raise ValueError(
            "Best-candidate streaming runner requires at most one manifest candidate parquet file per "
            f"(split, trace_family, capacity, horizon) partition. Duplicate partitions found: {rendered}"
        )
    schema_summary = candidate_schema_summary(release_root, manifest)
    config = scorer_config(args, schema_summary["available_columns"])
    output_path = guard_output_path(output_dir / output_filename(config), release_root)
    checkpoint = guard_output_path(checkpoint_path(output_dir, output_path.stem), release_root)

    if args.mode == "plan":
        payload = plan_payload(
            release_root=release_root,
            manifest=manifest,
            schema_summary=schema_summary,
            inventory=inventory,
            config=config,
            output_path=output_path,
            checkpoint=checkpoint,
        )
        write_json(output_dir / "plan.json", payload)
        print(f"Wrote {output_dir / 'plan.json'}")
        return

    reset_outputs(output_paths=[output_path], checkpoint_paths=[checkpoint], overwrite=args.overwrite, resume=args.resume)
    if args.resume:
        state = load_state(load_checkpoint(checkpoint), config)
    else:
        state = initial_state(config)

    required_columns = ["candidate_page_id", "y_loss", *decision_key_columns()]
    if config["mode"] == "linear_score":
        required_columns.extend(config["features"])
    else:
        required_columns.append(str(config["score_column"]))
    required_columns = list(dict.fromkeys(required_columns))

    budget = build_file_budget(args.max_files)
    carryover_rows = state["carryover_rows"]
    for file_index in range(int(state["next_file_index"]), len(inventory)):
        if budget_exhausted(budget):
            break
        for batch in iter_candidate_batches(inventory[file_index]["path"], columns=required_columns):
            complete, carryover_rows = split_complete_and_carryover(batch, carryover_rows)
            process_complete_frame(complete, state, config)
        state["carryover_rows"] = carryover_rows
        state["next_file_index"] = file_index + 1
        save_checkpoint(
            checkpoint,
            {
                "task": "best_candidate",
                "release_root": str(release_root),
                "state": state,
            },
        )
        budget = consume_budget(budget)

    if int(state["next_file_index"]) < len(inventory):
        print(
            json.dumps(
                {
                    "task": "best_candidate",
                    "status": "partial",
                    "files_total": len(inventory),
                    "files_processed": int(state["next_file_index"]),
                    "checkpoint_path": repo_relative(checkpoint),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return

    if carryover_rows:
        process_complete_frame(pd.DataFrame(carryover_rows), state, config)
        state["carryover_rows"] = []

    payload = result_payload(
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
