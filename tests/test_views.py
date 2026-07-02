from __future__ import annotations

from pathlib import Path

import pandas as pd

from lafc_evict_dataset.io import read_candidate_dataframe
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
        & (pairwise[["candidate_a_page_id", "candidate_b_page_id"]].apply(frozenset, axis=1) == frozenset({"A", "C"}))
    ]
    assert d1_tie_pair.empty

    # Orientation (which of D/E lands in slot A) is decided by a deterministic
    # hash, not candidate_page_id order, so match the pair by its unordered
    # candidate set rather than assuming candidate_a_page_id == "D".
    d2_pair = pairwise[
        (pairwise["decision_id"] == "d2")
        & (pairwise[["candidate_a_page_id", "candidate_b_page_id"]].apply(frozenset, axis=1) == frozenset({"D", "E"}))
    ].iloc[0]
    # E has the lower regret (0.0) of the two; whichever slot it landed in
    # must be the one labeled "better", and regret_diff_a_minus_b must be
    # consistent with the actual A/B assignment.
    if d2_pair["candidate_a_page_id"] == "E":
        assert d2_pair["label_a_better"] == 1
        assert d2_pair["label_b_better"] == 0
        assert d2_pair["regret_diff_a_minus_b"] == -2.0
    else:
        assert d2_pair["candidate_b_page_id"] == "E"
        assert d2_pair["label_a_better"] == 0
        assert d2_pair["label_b_better"] == 1
        assert d2_pair["regret_diff_a_minus_b"] == 2.0


def test_pairwise_view_orientation_is_deterministic_and_reproducible() -> None:
    df = _load_example()
    first = build_pairwise_view(df, include_ties=True)
    second = build_pairwise_view(df, include_ties=True)
    pd.testing.assert_frame_equal(first, second)


def test_pairwise_view_orientation_is_not_lexicographic_by_candidate_id() -> None:
    # Build a synthetic dataset with many decisions/pairs so that, if
    # orientation were still lexicographic-by-id, every pair would have
    # candidate_a_page_id < candidate_b_page_id. With a deterministic hash
    # orientation, some pairs must land the other way around.
    rows = []
    for decision_index in range(40):
        decision_id = f"d{decision_index}"
        for candidate_index, page_id in enumerate(["A", "B"]):
            rows.append(
                {
                    "trace_name": "synthetic_trace",
                    "trace_family": "synthetic",
                    "dataset_source": "synthetic",
                    "capacity": 3,
                    "horizon": 4,
                    "decision_id": decision_id,
                    "decision_t": decision_index,
                    "decision_chunk_id": 0,
                    "candidate_page_id": page_id,
                    "split": "train",
                    "y_loss": float(candidate_index),
                    "y_value": -float(candidate_index),
                    **{column: 0.0 for column in _feature_columns()},
                }
            )
    df = pd.DataFrame(rows)
    pairwise = build_pairwise_view(df, include_ties=True)

    assert len(pairwise) == 40
    lexicographic_order = pairwise["candidate_a_page_id"] < pairwise["candidate_b_page_id"]
    assert lexicographic_order.any()
    assert not lexicographic_order.all()

    # Label correctness must hold regardless of which candidate landed in
    # slot A: the lower-y_loss candidate ("A" in the raw data, y_loss=0) is
    # always the "better" one.
    for _, row in pairwise.iterrows():
        if row["candidate_a_page_id"] == "A":
            assert row["label_a_better"] == 1
            assert row["label_b_better"] == 0
        else:
            assert row["candidate_b_page_id"] == "A"
            assert row["label_a_better"] == 0
            assert row["label_b_better"] == 1


def _feature_columns() -> list[str]:
    from lafc_evict_dataset.schema import FEATURE_COLUMNS

    return FEATURE_COLUMNS


def test_read_candidate_dataframe_supports_csv_and_parquet(tmp_path: Path) -> None:
    df = _load_example()
    csv_path = tmp_path / "candidate_rows.csv"
    parquet_path = tmp_path / "candidate_rows.parquet"
    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)

    csv_df = read_candidate_dataframe(csv_path)
    parquet_df = read_candidate_dataframe(parquet_path)

    assert len(csv_df) == len(df)
    assert len(parquet_df) == len(df)
    assert parquet_df["capacity"].dtype.name == "Int64"
