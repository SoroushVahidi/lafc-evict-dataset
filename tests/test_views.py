from __future__ import annotations

from pathlib import Path

import pandas as pd

from lafc_evict_dataset.views import build_decision_view, build_pairwise_view


def _load_example() -> pd.DataFrame:
    return pd.read_csv(Path(__file__).resolve().parents[1] / "examples" / "tiny_candidate_rows.csv")


def test_decision_view_best_candidate_and_regret() -> None:
    df = _load_example()
    decision_view = build_decision_view(df)

    d1 = decision_view[(decision_view["decision_id"] == "d1") & (decision_view["horizon"] == 4)].iloc[0]
    assert d1["candidate_count"] == 3
    assert d1["min_y_loss"] == 1.0
    assert d1["optimal_candidate_page_ids"] == "A|C"
    assert d1["tie_count"] == 2
    assert d1["regret_sum"] == 2.0

    d2 = decision_view[(decision_view["decision_id"] == "d2") & (decision_view["horizon"] == 4)].iloc[0]
    assert d2["optimal_candidate_page_ids"] == "E"
    assert d2["regret_max"] == 4.0


def test_pairwise_view_skips_ties_by_default_and_labels_correctly() -> None:
    df = _load_example()
    pairwise = build_pairwise_view(df)
    pairwise_with_ties = build_pairwise_view(df, include_ties=True)

    assert len(pairwise) == 8
    assert len(pairwise_with_ties) == 9

    d1_tie_pair = pairwise[
        (pairwise["decision_id"] == "d1")
        & (pairwise["candidate_a_page_id"] == "A")
        & (pairwise["candidate_b_page_id"] == "C")
    ]
    assert d1_tie_pair.empty

    d2_pair = pairwise[
        (pairwise["decision_id"] == "d2")
        & (pairwise["candidate_a_page_id"] == "D")
        & (pairwise["candidate_b_page_id"] == "E")
    ].iloc[0]
    assert d2_pair["label_a_better"] == 0
    assert d2_pair["label_b_better"] == 1
    assert d2_pair["regret_diff_a_minus_b"] == 2.0
