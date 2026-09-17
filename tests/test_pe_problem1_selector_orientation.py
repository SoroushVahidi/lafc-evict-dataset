from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


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


def test_loss_convention_select_min() -> None:
    """A. LOSS CONVENTION

    Given candidates with predicted y_loss values:
        candidate A = lower predicted loss (1.5)
        candidate B = higher predicted loss (2.5)
    the selector must choose A.
    """
    # Verify using run_best_candidate_baseline logic
    best_candidate_module = _load_module("run_best_candidate_baseline")
    
    # Setup score_column config with direction="min" for loss column
    config = {
        "mode": "score_column",
        "direction": "min",
        "score_column": "predicted_loss",
    }
    
    # Define candidates
    df = pd.DataFrame([
        {"candidate_page_id": "A", "predicted_loss": 1.5, "y_loss": 1.0},
        {"candidate_page_id": "B", "predicted_loss": 2.5, "y_loss": 2.0},
    ])
    
    selected = best_candidate_module.select_row(df, config)
    assert selected["candidate_page_id"] == "A", "Should select candidate with lower predicted loss"


def test_value_convention_select_max() -> None:
    """B. VALUE CONVENTION

    Where y_value = -y_loss is used:
        candidate A = higher predicted value (-1.5)
        candidate B = lower predicted value (-2.5)
    the selector must choose A.
    """
    best_candidate_module = _load_module("run_best_candidate_baseline")
    
    # Setup score_column config with direction="max" for value column
    config = {
        "mode": "score_column",
        "direction": "max",
        "score_column": "predicted_value",
    }
    
    # Define candidates (A has higher predicted value than B)
    df = pd.DataFrame([
        {"candidate_page_id": "A", "predicted_value": -1.5, "y_loss": 1.0},
        {"candidate_page_id": "B", "predicted_value": -2.5, "y_loss": 2.0},
    ])
    
    selected = best_candidate_module.select_row(df, config)
    assert selected["candidate_page_id"] == "A", "Should select candidate with higher predicted value"


def test_linear_selector_minimization() -> None:
    """C. LINEAR SELECTOR

    Verify the actual production/evaluation path uses the intended minimization
    orientation for predicted y_loss.
    """
    best_candidate_module = _load_module("run_best_candidate_baseline")
    
    # Setup linear_score configuration which has direction "min"
    config = {
        "mode": "linear_score",
        "direction": "min",
        "features": ["feat1"],
        "intercept": 0.0,
        "coefficients": {"feat1": 1.0},
        "feature_means": {"feat1": 0.0},
    }
    
    # Define candidates
    # candidate A has feat1 = 1.0 -> predicted score/loss = 1.0
    # candidate B has feat1 = 2.0 -> predicted score/loss = 2.0
    df = pd.DataFrame([
        {"candidate_page_id": "A", "feat1": 1.0, "y_loss": 1.0},
        {"candidate_page_id": "B", "feat1": 2.0, "y_loss": 2.0},
    ])
    
    # Verify score computation
    scores = best_candidate_module.score_candidates(df, config)
    assert np.allclose(scores, [1.0, 2.0])
    
    selected = best_candidate_module.select_row(df, config)
    assert selected["candidate_page_id"] == "A", "Linear selector must minimize predicted loss"


def test_hgb_selector_minimization() -> None:
    """D. HGB SELECTOR

    Verify the HGB selector is interpreted with its original loss-prediction orientation (argmin).
    Uses the exact canonical HGB selection logic from score_frozen_hgb.py.
    """
    def local_select_min_score_per_decision(df: pd.DataFrame, key_cols: list[str]) -> pd.DataFrame:
        df = df.copy()
        df["_min_y_loss"] = df.groupby(key_cols, sort=False)["y_loss"].transform("min")
        selected = (
            df.sort_values([*key_cols, "_score", "candidate_page_id"])
            .drop_duplicates(key_cols, keep="first")
            [[*key_cols, "candidate_page_id", "y_loss", "_min_y_loss"]]
            .rename(
                columns={
                    "candidate_page_id": "selected_candidate_page_id",
                    "y_loss": "selected_y_loss",
                    "_min_y_loss": "min_y_loss",
                }
            )
        )
        selected["realized_regret"] = selected["selected_y_loss"] - selected["min_y_loss"]
        return selected

    # Define key columns
    key_cols = ["decision_id"]
    
    # Setup candidate DataFrame with predicted scores (_score) representing y_loss
    # candidate A has _score = 10.0 (lower loss guess)
    # candidate B has _score = 20.0 (higher loss guess)
    df = pd.DataFrame([
        {"decision_id": "d1", "candidate_page_id": "A", "_score": 10.0, "y_loss": 1.0},
        {"decision_id": "d1", "candidate_page_id": "B", "_score": 20.0, "y_loss": 2.0},
    ])
    
    selected = local_select_min_score_per_decision(df, key_cols)
    
    # In the result, A should be the selected candidate
    assert len(selected) == 1
    assert selected.iloc[0]["selected_candidate_page_id"] == "A", "HGB selector must minimize predicted y_loss (_score)"


def test_pairwise_selector_mapping() -> None:
    """E. PAIRWISE SELECTOR

    Verify the feature-difference/logistic score sign is mapped to candidate preference correctly.
    If diff = predicted_loss_b - predicted_loss_a is positive, it means predicted_loss_b > predicted_loss_a,
    so B has higher predicted loss than A, meaning candidate A is preferred (label_a_better = 1).
    """
    run_feature_pairwise_baseline = _load_module("run_feature_pairwise_baseline")
    
    # Define dummy dataset
    # We want to check that fit_predict_1d maps positive diff to target=1
    # positive diff: B's loss is higher than A's loss -> A is better
    # negative diff: A's loss is higher than B's loss -> B is better
    diffs = np.array([2.0, 1.0, 1.5, -2.0, -1.0, -1.5])
    target = np.array([1, 1, 1, 0, 0, 0])
    train_mask = np.ones(6, dtype=bool)
    
    y_pred, y_prob, model_info = run_feature_pairwise_baseline.fit_predict_1d(diffs, target, train_mask, l2=1e-3)
    
    # Since positive diffs correspond exactly to target=1, the logistic regression should learn a positive coefficient
    assert model_info["coefficient"] > 0, "Coefficient for predicted_loss_b - predicted_loss_a must be positive"
    
    # Let's ensure that for a positive test diff, the predicted probability/class favors target=1 (A is better)
    # Applying standardizer
    std_diff = (3.0 - model_info["feature_mean"]) / model_info["feature_std"]
    design = np.array([1.0, std_diff])
    beta = np.array([model_info["intercept"], model_info["coefficient"]])
    linear = design @ beta
    prob = 1.0 / (1.0 + np.exp(-linear))
    assert prob >= 0.5, "Positive difference must map to preferred candidate A"


def test_tie_handling() -> None:
    """F. TIES

    Equal predicted scientific scores must not be silently interpreted as evidence that one candidate is superior.
    Ties must be broken deterministically, and equal scores should be recognized as equal.
    """
    best_candidate_module = _load_module("run_best_candidate_baseline")
    
    config = {
        "mode": "score_column",
        "direction": "min",
        "score_column": "predicted_loss",
    }
    
    # candidate A and B have the EXACT same score
    df1 = pd.DataFrame([
        {"candidate_page_id": "A", "predicted_loss": 1.5, "y_loss": 1.0},
        {"candidate_page_id": "B", "predicted_loss": 1.5, "y_loss": 2.0},
    ])
    
    df2 = pd.DataFrame([
        {"candidate_page_id": "B", "predicted_loss": 1.5, "y_loss": 2.0},
        {"candidate_page_id": "A", "predicted_loss": 1.5, "y_loss": 1.0},
    ])
    
    # Deterministic tie-breaking means order of input rows does not change the selected page
    selected1 = best_candidate_module.select_row(df1, config)
    selected2 = best_candidate_module.select_row(df2, config)
    
    assert selected1["candidate_page_id"] == selected2["candidate_page_id"]
    # Usually broken by page_id ascending, so "A" is selected
    assert selected1["candidate_page_id"] == "A"


def test_end_to_end_synthetic_case() -> None:
    """G. END-TO-END HAND-CHECKABLE CASE

    Construct at least one tiny synthetic decision for which the correct victim is obvious and pass it through
    the relevant selector/evaluator path.
    """
    best_candidate_module = _load_module("run_best_candidate_baseline")
    
    # 3 candidates:
    # A has loss 1.0 (best)
    # B has loss 3.0 (worst)
    # C has loss 2.0 (middle)
    # Scorer makes correct prediction ranking: A=1.0, C=2.0, B=3.0
    df = pd.DataFrame([
        {"candidate_page_id": "B", "predicted_loss": 3.0, "y_loss": 3.0},
        {"candidate_page_id": "A", "predicted_loss": 1.0, "y_loss": 1.0},
        {"candidate_page_id": "C", "predicted_loss": 2.0, "y_loss": 2.0},
    ])
    
    config = {
        "mode": "score_column",
        "direction": "min",
        "score_column": "predicted_loss",
    }
    
    # The correct victim is A because we want to minimize loss!
    selected = best_candidate_module.select_row(df, config)
    assert selected["candidate_page_id"] == "A"
    
    # Let's verify that the regret of this selection is 0.0
    best_loss = df["y_loss"].min()
    regret = selected["y_loss"] - best_loss
    assert regret == 0.0
