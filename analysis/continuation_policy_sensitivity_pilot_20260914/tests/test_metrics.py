import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from metrics import (  # noqa: E402
    cross_continuation_regret,
    kendall_tau_b,
    optimal_set_jaccard,
    pairwise_taxonomy,
)


def test_optimal_set_jaccard_identical_optimal_sets():
    a = {"x": 0.0, "y": 0.0, "z": 1.0}
    b = {"x": 0.0, "y": 0.0, "z": 2.0}
    assert optimal_set_jaccard(a, b) == 1.0


def test_optimal_set_jaccard_disjoint_optimal_sets():
    a = {"x": 0.0, "y": 1.0}
    b = {"x": 1.0, "y": 0.0}
    assert optimal_set_jaccard(a, b) == 0.0


def test_optimal_set_jaccard_partial_overlap():
    a = {"x": 0.0, "y": 0.0, "z": 1.0}
    b = {"x": 0.0, "y": 1.0, "z": 0.0}
    # opt_a = {x,y}, opt_b = {x,z}; intersection={x}, union={x,y,z}
    assert optimal_set_jaccard(a, b) == 1 / 3


def test_pairwise_taxonomy_both_tied():
    a = {"x": 0.0, "y": 0.0}
    b = {"x": 0.0, "y": 0.0}
    counts = pairwise_taxonomy(a, b)
    assert counts == {"concordant": 0, "discordant": 0, "a_tie_b_strict": 0, "a_strict_b_tie": 0, "both_tied": 1}


def test_pairwise_taxonomy_concordant():
    a = {"x": 0.0, "y": 1.0}
    b = {"x": 0.0, "y": 2.0}
    counts = pairwise_taxonomy(a, b)
    assert counts["concordant"] == 1
    assert counts["discordant"] == 0


def test_pairwise_taxonomy_discordant():
    a = {"x": 0.0, "y": 1.0}
    b = {"x": 1.0, "y": 0.0}
    counts = pairwise_taxonomy(a, b)
    assert counts["discordant"] == 1


def test_pairwise_taxonomy_a_tie_b_strict():
    a = {"x": 0.0, "y": 0.0}
    b = {"x": 0.0, "y": 1.0}
    counts = pairwise_taxonomy(a, b)
    assert counts["a_tie_b_strict"] == 1


def test_pairwise_taxonomy_a_strict_b_tie():
    a = {"x": 0.0, "y": 1.0}
    b = {"x": 0.0, "y": 0.0}
    counts = pairwise_taxonomy(a, b)
    assert counts["a_strict_b_tie"] == 1


def test_kendall_tau_b_perfect_agreement():
    a = {"x": 0.0, "y": 1.0, "z": 2.0}
    b = {"x": 0.0, "y": 5.0, "z": 10.0}
    assert kendall_tau_b(a, b) == 1.0


def test_kendall_tau_b_perfect_disagreement():
    a = {"x": 0.0, "y": 1.0, "z": 2.0}
    b = {"x": 2.0, "y": 1.0, "z": 0.0}
    assert kendall_tau_b(a, b) == -1.0


def test_kendall_tau_b_undefined_when_one_side_fully_tied():
    a = {"x": 0.0, "y": 0.0, "z": 0.0}
    b = {"x": 0.0, "y": 1.0, "z": 2.0}
    assert kendall_tau_b(a, b) is None


def test_cross_continuation_regret_single_lru_optimal_candidate():
    lru_regrets = {"x": 0.0, "y": 3.0}
    losses_c = {"x": 5.0, "y": 2.0}
    r = cross_continuation_regret(lru_regrets, losses_c)
    # OptSet_LRU = {x}; best_c = 2 (y); R_C(x) = 5 - 2 = 3
    assert r["mean_over_LRU_optimal"] == 3.0
    assert r["best_case"] == 3.0
    assert r["worst_case"] == 3.0
    assert r["prob_still_optimal"] == 0.0
    assert r["n_LRU_optimal"] == 1


def test_cross_continuation_regret_multiple_lru_optimal_candidates():
    lru_regrets = {"x": 0.0, "y": 0.0, "z": 5.0}
    losses_c = {"x": 4.0, "y": 1.0, "z": 1.0}
    r = cross_continuation_regret(lru_regrets, losses_c)
    # OptSet_LRU = {x,y}; best_c = 1; R_C(x)=3, R_C(y)=0
    assert r["mean_over_LRU_optimal"] == 1.5
    assert r["best_case"] == 0.0
    assert r["worst_case"] == 3.0
    # C-optimal set = {y, z} (both loss=1); overlap with {x,y} is {y} -> 1/2
    assert r["prob_still_optimal"] == 0.5


def test_cross_continuation_regret_no_change_gives_zero_regret_everywhere():
    lru_regrets = {"x": 0.0, "y": 1.0}
    losses_c = {"x": 0.0, "y": 1.0}
    r = cross_continuation_regret(lru_regrets, losses_c)
    assert r["mean_over_LRU_optimal"] == 0.0
    assert r["prob_still_optimal"] == 1.0
