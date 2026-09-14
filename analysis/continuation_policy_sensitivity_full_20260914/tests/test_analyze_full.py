import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from analyze_full import cluster_bootstrap, median, pairwise_totals, summarize_set  # noqa: E402


def _row(jaccard, ccr, discordant=0, concordant=1):
    return {
        "optimal_set_jaccard": jaccard, "ccr_mean_over_LRU_optimal": ccr,
        "ccr_prob_still_optimal": 1.0 if ccr == 0 else 0.5,
        "pairwise_concordant": concordant, "pairwise_discordant": discordant,
        "pairwise_a_tie_b_strict": 0, "pairwise_a_strict_b_tie": 0, "pairwise_both_tied": 0,
    }


def test_median_odd():
    assert median([1, 3, 2]) == 2


def test_median_even():
    assert median([1, 2, 3, 4]) == 2.5


def test_median_empty():
    assert median([]) is None


def test_pairwise_totals_sums_across_rows():
    rows = [_row(1.0, 0.0, discordant=1, concordant=2), _row(0.5, 1.0, discordant=0, concordant=3)]
    tot = pairwise_totals(rows)
    assert tot["pairwise_discordant"] == 1
    assert tot["pairwise_concordant"] == 5


def test_summarize_set_basic():
    rows = [_row(1.0, 0.0), _row(0.5, 2.0)]
    s = summarize_set(rows)
    assert s["n_decisions"] == 2
    assert s["mean_jaccard"] == 0.75
    assert s["median_jaccard"] == 0.75
    assert s["mean_ccr"] == 1.0


def test_summarize_set_empty():
    s = summarize_set([])
    assert s["n_decisions"] == 0
    assert s["mean_jaccard"] is None
    assert s["strict_reversal_fraction"] is None


def test_cluster_bootstrap_resamples_decisions_not_candidates():
    rows = [_row(1.0, 0.0) for _ in range(50)] + [_row(0.0, 5.0) for _ in range(50)]
    result = cluster_bootstrap(rows, seed=1, n_resamples=200)
    assert result["n_decisions_per_resample"] == 100
    lo, hi = result["median_jaccard_ci95"]
    assert 0.0 <= lo <= hi <= 1.0


def test_cluster_bootstrap_empty_returns_none():
    assert cluster_bootstrap([], seed=1, n_resamples=100) is None
