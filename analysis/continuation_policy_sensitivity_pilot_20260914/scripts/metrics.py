"""Tie-aware continuation-sensitivity metrics, implemented exactly per
analysis/continuation_policy_sensitivity_design_20260914/DESIGN.md
Sections 6 and 6-bis. No arbitrary argmin tie-breaking anywhere.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from scipy import stats


def optimal_set(regrets: Dict[str, float]) -> set:
    return {c for c, r in regrets.items() if r == 0.0}


def optimal_set_jaccard(regrets_a: Dict[str, float], regrets_b: Dict[str, float]) -> Optional[float]:
    opt_a = optimal_set(regrets_a)
    opt_b = optimal_set(regrets_b)
    union = opt_a | opt_b
    if not union:
        return None
    return len(opt_a & opt_b) / len(union)


def pairwise_taxonomy(regrets_a: Dict[str, float], regrets_b: Dict[str, float]) -> Dict[str, int]:
    """All unordered candidate pairs, classified per DESIGN.md Section 6 item 2."""
    candidates = sorted(regrets_a.keys())
    counts = {
        "concordant": 0, "discordant": 0,
        "a_tie_b_strict": 0, "a_strict_b_tie": 0, "both_tied": 0,
    }
    n = len(candidates)
    for i in range(n):
        for j in range(i + 1, n):
            ci, cj = candidates[i], candidates[j]
            da = regrets_a[ci] - regrets_a[cj]
            db = regrets_b[ci] - regrets_b[cj]
            sa = (da > 0) - (da < 0)
            sb = (db > 0) - (db < 0)
            if sa == 0 and sb == 0:
                counts["both_tied"] += 1
            elif sa == 0:
                counts["a_tie_b_strict"] += 1
            elif sb == 0:
                counts["a_strict_b_tie"] += 1
            elif sa == sb:
                counts["concordant"] += 1
            else:
                counts["discordant"] += 1
    return counts


def kendall_tau_b(regrets_a: Dict[str, float], regrets_b: Dict[str, float]) -> Optional[float]:
    candidates = sorted(regrets_a.keys())
    if len(candidates) < 2:
        return None
    xs = [regrets_a[c] for c in candidates]
    ys = [regrets_b[c] for c in candidates]
    if len(set(xs)) < 2 or len(set(ys)) < 2:
        return None  # undefined: one side fully tied across all candidates
    tau, _p = stats.kendalltau(xs, ys)
    return float(tau)


def cross_continuation_regret(regrets_lru: Dict[str, float], losses_c: Dict[str, float]) -> Dict[str, float]:
    """DESIGN.md Section 6-bis. regrets_lru selects OptSet_LRU; losses_c are
    the alternative continuation's raw losses (not regrets) so we can compute
    R_C(d,e) = L_C(d,e) - min_e' L_C(d,e') directly against the C-optimum.
    """
    opt_lru = sorted(optimal_set(regrets_lru))
    if not opt_lru:
        raise ValueError("OptSet_LRU is empty -- should never happen (LRU is always its own optimum)")
    best_c = min(losses_c.values())
    r_values = [losses_c[e] - best_c for e in opt_lru]
    opt_c = optimal_set({c: losses_c[c] - best_c for c in losses_c})
    prob_still_optimal = len(set(opt_lru) & opt_c) / len(opt_lru)
    return {
        "mean_over_LRU_optimal": sum(r_values) / len(r_values),
        "best_case": min(r_values),
        "worst_case": max(r_values),
        "prob_still_optimal": prob_still_optimal,
        "n_LRU_optimal": len(opt_lru),
    }
