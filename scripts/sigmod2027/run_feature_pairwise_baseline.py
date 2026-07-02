#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from _baseline_common import (
    current_git_commit,
    current_timestamp_utc,
    detected_validation_status,
    ensure_output_dir_safe,
    guard_output_path,
    load_manifest,
    parquet_schema_names,
    release_identity,
    release_summary,
    repo_relative,
    require_columns,
    write_csv,
    write_json,
)
from build_augmented_pairwise_sample import CORE_FEATURE_COLUMNS, OPTIONAL_FEATURE_COLUMNS

SPLITS = ["train", "val", "test"]

REQUIRED_AUGMENTED_COLUMNS = [
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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate feature-based pairwise-preference baselines over the augmented LAFC-Evict pairwise sample."
    )
    parser.add_argument(
        "--release-root",
        default="release/lafc-evict-v0.1-open-current-contract-preserved",
        help="Repo-relative or absolute preserved release path (used for release identity/summary metadata only).",
    )
    parser.add_argument(
        "--augmented-path",
        default="paper/sigmod2027/results/baselines/pairwise/augmented_pairwise_sample.parquet",
        help="Path to the augmented pairwise sample produced by build_augmented_pairwise_sample.py.",
    )
    parser.add_argument(
        "--linear-score-json",
        default="paper/sigmod2027/results/baselines/value_regression/linear_regression_y_loss.json",
        help="Value-regression JSON used for the linear_score_pairwise baseline.",
    )
    parser.add_argument(
        "--output-dir",
        default="paper/sigmod2027/results/baselines/pairwise",
        help="Directory for the feature_pairwise_results.{json,csv,md} outputs.",
    )
    parser.add_argument("--seed", type=int, default=7, help="Seed for the random_non_tie baseline.")
    parser.add_argument("--l2", type=float, default=1e-3, help="L2 regularization strength for logistic fits.")
    return parser.parse_args(argv)


def binary_log_loss(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    eps = 1e-12
    clipped = np.clip(y_prob, eps, 1.0 - eps)
    return float(-(y_true * np.log(clipped) + (1.0 - y_true) * np.log(1.0 - clipped)).mean())


def standardize_fit(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = matrix.mean(axis=0)
    std = matrix.std(axis=0)
    std_safe = np.where(std > 1e-12, std, 1.0)
    return mean, std_safe


def standardize_apply(matrix: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
    return (matrix - mean) / std


def fit_logistic_regression(matrix: np.ndarray, target: np.ndarray, l2: float, max_iter: int = 50, tol: float = 1e-8) -> np.ndarray:
    rows, dimension = matrix.shape
    design = np.column_stack([np.ones(rows), matrix])
    beta = np.zeros(dimension + 1)
    reg_vec = np.concatenate([[0.0], np.full(dimension, l2)])
    for _ in range(max_iter):
        linear = np.clip(design @ beta, -30.0, 30.0)
        prob = 1.0 / (1.0 + np.exp(-linear))
        weight = np.clip(prob * (1.0 - prob), 1e-6, None)
        gradient = design.T @ (target - prob) - reg_vec * beta
        hessian = (design * weight[:, None]).T @ design + np.diag(reg_vec)
        try:
            delta = np.linalg.solve(hessian, gradient)
        except np.linalg.LinAlgError:
            delta = np.linalg.lstsq(hessian, gradient, rcond=None)[0]
        beta = beta + delta
        if np.max(np.abs(delta)) < tol:
            break
    return beta


def predict_proba(matrix: np.ndarray, beta: np.ndarray) -> np.ndarray:
    design = np.column_stack([np.ones(len(matrix)), matrix])
    linear = np.clip(design @ beta, -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-linear))


def fit_predict_1d(feature_diff: np.ndarray, target: np.ndarray, train_mask: np.ndarray, l2: float) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    matrix = feature_diff.reshape(-1, 1)
    mean, std = standardize_fit(matrix[train_mask])
    standardized = standardize_apply(matrix, mean, std)
    beta = fit_logistic_regression(standardized[train_mask], target[train_mask], l2=l2)
    y_prob = predict_proba(standardized, beta)
    y_pred = (y_prob >= 0.5).astype(int)
    model_info = {"intercept": float(beta[0]), "coefficient": float(beta[1]), "feature_mean": float(mean[0]), "feature_std": float(std[0])}
    return y_pred, y_prob, model_info


def _safe_div(numerator: float, denominator: float) -> float | None:
    return float(numerator) / denominator if denominator else None


def _f1(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None:
        return None
    if precision + recall == 0:
        return 0.0
    return float(2 * precision * recall / (precision + recall))


def compute_auroc(y_true: np.ndarray, y_prob: np.ndarray | None) -> float | None:
    """Rank-based (Mann-Whitney U) AUROC; avoids an sklearn dependency."""
    if y_prob is None or len(y_true) == 0:
        return None
    n_pos = int((y_true == 1).sum())
    n_neg = int((y_true == 0).sum())
    if n_pos == 0 or n_neg == 0:
        return None
    order = np.argsort(y_prob, kind="mergesort")
    sorted_probs = y_prob[order]
    ranks_sorted = np.arange(1, len(y_prob) + 1, dtype=float)
    i = 0
    n = len(sorted_probs)
    while i < n:
        j = i
        while j + 1 < n and sorted_probs[j + 1] == sorted_probs[i]:
            j += 1
        if j > i:
            ranks_sorted[i : j + 1] = ranks_sorted[i : j + 1].mean()
        i = j + 1
    ranks = np.empty(len(y_prob), dtype=float)
    ranks[order] = ranks_sorted
    sum_ranks_pos = ranks[y_true == 1].sum()
    return float((sum_ranks_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray | None) -> dict[str, object]:
    accuracy = float((y_pred == y_true).mean()) if len(y_true) else None
    log_loss = binary_log_loss(y_true, y_prob) if y_prob is not None and len(y_true) else None

    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())

    recall_a_better = _safe_div(tp, tp + fn) if len(y_true) else None
    recall_b_better = _safe_div(tn, tn + fp) if len(y_true) else None
    precision_a_better = _safe_div(tp, tp + fp) if len(y_true) else None
    precision_b_better = _safe_div(tn, tn + fn) if len(y_true) else None
    balanced_accuracy = (
        (recall_a_better + recall_b_better) / 2.0
        if recall_a_better is not None and recall_b_better is not None
        else None
    )
    f1_a_better = _f1(precision_a_better, recall_a_better)
    f1_b_better = _f1(precision_b_better, recall_b_better)
    macro_f1 = (
        (f1_a_better + f1_b_better) / 2.0 if f1_a_better is not None and f1_b_better is not None else None
    )

    return {
        "rows": int(len(y_true)),
        "positive_rate": float(y_true.mean()) if len(y_true) else None,
        "accuracy": accuracy,
        "balanced_accuracy": balanced_accuracy,
        "log_loss": log_loss,
        "recall_a_better": recall_a_better,
        "recall_b_better": recall_b_better,
        "macro_f1": macro_f1,
        "auroc": compute_auroc(y_true, y_prob),
    }


def evaluate_baseline(name: str, y_true: np.ndarray, splits: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray | None) -> dict[str, object]:
    overall = compute_metrics(y_true, y_pred, y_prob)
    split_metrics: dict[str, object] = {}
    for split in SPLITS:
        mask = splits == split
        if not mask.any():
            continue
        split_prob = y_prob[mask] if y_prob is not None else None
        split_metrics[split] = compute_metrics(y_true[mask], y_pred[mask], split_prob)
    return {"name": name, "overall": overall, "split_metrics": split_metrics}


def random_non_tie(non_tie: pd.DataFrame, target: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    y_pred = rng.integers(0, 2, size=len(non_tie))
    y_prob = np.full(len(non_tie), 0.5)
    return y_pred, y_prob


def majority_non_tie(target: np.ndarray, train_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    positive_rate = float(target[train_mask].mean()) if train_mask.any() else float(target.mean())
    majority_label = int(positive_rate >= 0.5)
    y_pred = np.full(len(target), majority_label)
    y_prob = np.full(len(target), positive_rate)
    return y_pred, y_prob


def score_column_pairwise(non_tie: pd.DataFrame, feature: str, target: np.ndarray, train_mask: np.ndarray, l2: float) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    column_a = f"{feature}_a"
    column_b = f"{feature}_b"
    diff = (non_tie[column_a].astype(float) - non_tie[column_b].astype(float)).fillna(0.0).to_numpy()
    y_pred, y_prob, model_info = fit_predict_1d(diff, target.astype(float), train_mask, l2)
    model_info["feature"] = feature
    return y_pred, y_prob, model_info


def linear_score_pairwise(
    non_tie: pd.DataFrame, target: np.ndarray, train_mask: np.ndarray, linear_score_path: Path, l2: float
) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    payload = json.loads(linear_score_path.read_text(encoding="utf-8"))
    model = payload.get("model", {})
    coefficients = model.get("coefficients", {})
    intercept = float(model.get("intercept", 0.0))
    feature_means = model.get("feature_means", {})
    if not isinstance(coefficients, dict) or not coefficients:
        raise ValueError(f"Linear-score JSON is missing model coefficients: {linear_score_path}")

    missing = [
        feature
        for feature in coefficients
        if f"{feature}_a" not in non_tie.columns or f"{feature}_b" not in non_tie.columns
    ]
    if missing:
        raise ValueError(
            "Augmented pairwise sample is missing candidate-side columns required by the linear-score model: "
            f"{missing}. Rebuild the augmented sample with these features included."
        )

    def predicted_loss(suffix: str) -> np.ndarray:
        predicted = np.full(len(non_tie), intercept, dtype=float)
        for feature, coefficient in coefficients.items():
            column = non_tie[f"{feature}_{suffix}"].astype(float).to_numpy()
            fill_value = float(feature_means.get(feature, 0.0))
            filled = np.where(np.isfinite(column), column, fill_value)
            predicted += filled * float(coefficient)
        return predicted

    predicted_loss_a = predicted_loss("a")
    predicted_loss_b = predicted_loss("b")
    diff = predicted_loss_b - predicted_loss_a
    y_pred, y_prob, model_info = fit_predict_1d(diff, target.astype(float), train_mask, l2)
    model_info["source_json"] = repo_relative(linear_score_path)
    model_info["features_used"] = sorted(coefficients)
    return y_pred, y_prob, model_info


def available_pair_features(columns: list[str]) -> list[str]:
    candidates = [*CORE_FEATURE_COLUMNS, *OPTIONAL_FEATURE_COLUMNS]
    return [feature for feature in candidates if f"{feature}_a" in columns and f"{feature}_b" in columns]


def logistic_regression_pairwise(
    non_tie: pd.DataFrame, target: np.ndarray, train_mask: np.ndarray, features: list[str], l2: float
) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    diffs = []
    for feature in features:
        column_a = f"{feature}_a"
        column_b = f"{feature}_b"
        diffs.append((non_tie[column_a].astype(float) - non_tie[column_b].astype(float)).fillna(0.0).to_numpy())
    matrix = np.column_stack(diffs) if diffs else np.zeros((len(non_tie), 0))
    mean, std = standardize_fit(matrix[train_mask])
    standardized = standardize_apply(matrix, mean, std)
    beta = fit_logistic_regression(standardized[train_mask], target.astype(float)[train_mask], l2=l2)
    y_prob = predict_proba(standardized, beta)
    y_pred = (y_prob >= 0.5).astype(int)
    model_info = {
        "intercept": float(beta[0]),
        "coefficients": dict(zip(features, (float(value) for value in beta[1:]))),
        "features_used": features,
    }
    return y_pred, y_prob, model_info


def class_imbalance_notes(baselines: dict[str, dict[str, object]]) -> list[str]:
    majority = baselines.get("majority_non_tie", {})
    split_metrics = majority.get("split_metrics", {})
    notes: list[str] = []
    rates = {split: metrics["positive_rate"] for split, metrics in split_metrics.items() if metrics.get("positive_rate") is not None}
    for split, rate in rates.items():
        notes.append(f"{split} split positive rate (label_a_better=1) is {rate:.4f}.")
    if rates and (max(rates.values()) - min(rates.values())) > 0.2:
        notes.append(
            "Positive rate varies substantially across splits, consistent with the tie-heavy, imbalanced "
            "nature of the shipped pairwise sample; headline accuracy numbers should always be read alongside "
            "log loss and split-level breakdowns."
        )
    return notes


def build_markdown(payload: dict[str, object]) -> str:
    lines = ["# Feature-Based Pairwise Baseline Results", ""]
    lines.append(f"- input file: `{payload['input_path']}`")
    lines.append(f"- evaluation mode: non-tie rows only ({payload['non_tie_row_count']:,} of {payload['pairwise_sample_rows_total']:,} rows)")
    lines.append(f"- tie rows skipped: {payload['tie_row_count']:,}")
    lines.append(f"- full real-release validation: {payload['full_validation_status']}")
    lines.append("")
    def _fmt(value: float | None) -> str:
        return "" if value is None else f"{value:.4f}"

    lines.append("## Overall results")
    lines.append("")
    lines.append(
        "| Baseline | Rows | Accuracy | Balanced accuracy | Log loss | Recall (a_better) | "
        "Recall (b_better) | Macro F1 | AUROC |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for name, baseline in payload["baselines"].items():
        overall = baseline.get("overall")
        if overall is None:
            continue
        lines.append(
            f"| `{name}` | {overall['rows']:,} | {_fmt(overall['accuracy'])} | "
            f"{_fmt(overall.get('balanced_accuracy'))} | {_fmt(overall['log_loss'])} | "
            f"{_fmt(overall.get('recall_a_better'))} | {_fmt(overall.get('recall_b_better'))} | "
            f"{_fmt(overall.get('macro_f1'))} | {_fmt(overall.get('auroc'))} |"
        )
    lines.append("")
    lines.append("## Split-level results")
    lines.append("")
    lines.append(
        "| Baseline | Split | Rows | Positive rate | Accuracy | Balanced accuracy | Log loss | "
        "Recall (a_better) | Recall (b_better) | Macro F1 | AUROC |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for name, baseline in payload["baselines"].items():
        if "split_metrics" not in baseline:
            continue
        for split in SPLITS:
            metrics = baseline["split_metrics"].get(split)
            if metrics is None:
                continue
            lines.append(
                f"| `{name}` | `{split}` | {metrics['rows']:,} | {_fmt(metrics['positive_rate'])} | "
                f"{_fmt(metrics['accuracy'])} | {_fmt(metrics.get('balanced_accuracy'))} | "
                f"{_fmt(metrics['log_loss'])} | {_fmt(metrics.get('recall_a_better'))} | "
                f"{_fmt(metrics.get('recall_b_better'))} | {_fmt(metrics.get('macro_f1'))} | "
                f"{_fmt(metrics.get('auroc'))} |"
            )
    lines.append("")
    lines.append("## Notes on class imbalance")
    lines.append("")
    for note in payload["notes_on_class_imbalance"]:
        lines.append(f"- {note}")
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    for limitation in payload["limitations"]:
        lines.append(f"- {limitation}")
    lines.append("")
    return "\n".join(lines)


def run(args: argparse.Namespace) -> dict[str, object]:
    release_root = Path(args.release_root)
    augmented_path = Path(args.augmented_path)
    linear_score_path = Path(args.linear_score_json)
    output_dir = ensure_output_dir_safe(Path(args.output_dir), release_root)

    schema = parquet_schema_names(augmented_path)
    missing = require_columns(schema, REQUIRED_AUGMENTED_COLUMNS)
    if missing:
        raise ValueError(f"Augmented pairwise sample is missing required columns: {missing}")

    df = pd.read_parquet(augmented_path)
    tie_count = int((df["is_tie"] == 1).sum())
    non_tie = df.loc[df["is_tie"] == 0].reset_index(drop=True)
    if non_tie.empty:
        raise ValueError("Augmented pairwise sample contains no non-tie rows to evaluate")

    target = non_tie["label_a_better"].astype(int).to_numpy()
    splits = non_tie["split"].astype(str).to_numpy()
    train_mask = splits == "train"
    if not train_mask.any():
        raise ValueError("Train split is empty on the non-tie subset")

    baselines: dict[str, dict[str, object]] = {}

    y_pred, y_prob = random_non_tie(non_tie, target, args.seed)
    baselines["random_non_tie"] = evaluate_baseline("random_non_tie", target, splits, y_pred, y_prob)

    y_pred, y_prob = majority_non_tie(target, train_mask)
    baselines["majority_non_tie"] = evaluate_baseline("majority_non_tie", target, splits, y_pred, y_prob)

    lru_pred, lru_prob, lru_model = score_column_pairwise(non_tie, "candidate_lru_score", target, train_mask, args.l2)
    entry = evaluate_baseline("lru_score_pairwise", target, splits, lru_pred, lru_prob)
    entry["model"] = lru_model
    baselines["lru_score_pairwise"] = entry

    pred_pred, pred_prob, pred_model = score_column_pairwise(non_tie, "candidate_predictor_score", target, train_mask, args.l2)
    entry = evaluate_baseline("predictor_score_pairwise", target, splits, pred_pred, pred_prob)
    entry["model"] = pred_model
    baselines["predictor_score_pairwise"] = entry

    if linear_score_path.exists():
        lin_pred, lin_prob, lin_model = linear_score_pairwise(non_tie, target, train_mask, linear_score_path, args.l2)
        entry = evaluate_baseline("linear_score_pairwise", target, splits, lin_pred, lin_prob)
        entry["model"] = lin_model
        baselines["linear_score_pairwise"] = entry
    else:
        baselines["linear_score_pairwise"] = {
            "name": "linear_score_pairwise",
            "status": "skipped",
            "reason": f"linear-score JSON not found: {repo_relative(linear_score_path)}",
        }

    logistic_features = available_pair_features(list(df.columns))
    if logistic_features:
        log_pred, log_prob, log_model = logistic_regression_pairwise(non_tie, target, train_mask, logistic_features, args.l2)
        entry = evaluate_baseline("logistic_regression_pairwise", target, splits, log_pred, log_prob)
        entry["model"] = log_model
        baselines["logistic_regression_pairwise"] = entry

    manifest = load_manifest(release_root) if (release_root / "metadata" / "release_manifest.json").exists() else None

    payload: dict[str, object] = {
        "task": "pairwise_preference",
        "status": "available",
        "mode": "run_feature",
        "timestamp_utc": current_timestamp_utc(),
        "git_commit": current_git_commit(),
        "release_root": str(release_root),
        "input_view": "augmented_pairwise_sample",
        "input_path": repo_relative(augmented_path),
        "linear_score_json": repo_relative(linear_score_path),
        "full_validation_status": detected_validation_status(release_root),
        "requires_large_memory_machine": True,
        "safe_for_anonymous_manuscript": True,
        "evaluation_population": "non_tie_rows_only",
        "pairwise_sample_rows_total": int(len(df)),
        "tie_row_count": tie_count,
        "non_tie_row_count": int(len(non_tie)),
        "baselines": baselines,
        "notes_on_class_imbalance": class_imbalance_notes(baselines),
        "notes": [
            "Candidate-side A/B features come from build_augmented_pairwise_sample.py, joined back to candidate rows.",
            "Score-based baselines (lru_score_pairwise, predictor_score_pairwise, linear_score_pairwise) fit a 1D "
            "logistic calibration on the train split of the score difference; the sign and slope are learned from data.",
        ],
        "limitations": [
            "Only the capped shipped pairwise sample is evaluated; the full quadratic pairwise view is never generated.",
            "Logistic fits use a small custom Newton-Raphson implementation with L2 regularization, not scikit-learn.",
        ],
    }
    if manifest is not None:
        payload["release_identity"] = release_identity(manifest)
        payload["release_summary"] = release_summary(manifest)

    write_json(output_dir / "feature_pairwise_results.json", payload)

    csv_rows = []
    for name, baseline in baselines.items():
        if "split_metrics" not in baseline:
            continue
        for split in SPLITS:
            metrics = baseline["split_metrics"].get(split)
            if metrics is None:
                continue
            csv_rows.append({"baseline": name, "split": split, **metrics})
    write_csv(output_dir / "feature_pairwise_results.csv", csv_rows)

    markdown = build_markdown(payload)
    (output_dir / "feature_pairwise_results.md").write_text(markdown, encoding="utf-8")

    print(json.dumps(payload, indent=2, sort_keys=True))
    return payload


def main(argv: list[str] | None = None) -> None:
    run(parse_args(argv))


if __name__ == "__main__":
    main()
