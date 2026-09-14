"""Shared library for the full-population MRU continuation census.

Imports pilot_lib.py/metrics.py UNCHANGED from the already-validated pilot
and full-sample implementations, exactly as full_lib.py (the sampled
5,000-decision study) already did. No reimplementation of the core
simulate_rollout_misses/_simulate_lru_misses/tie-aware-metric logic.
"""
from __future__ import annotations

import sys
from pathlib import Path

PILOT_SCRIPTS_DIR = (
    "/home/soroush/projects/lafc-evict-dataset/repo/.claude/worktrees/"
    "continuation-sensitivity-pilot-20260914/analysis/"
    "continuation_policy_sensitivity_pilot_20260914/scripts"
)
if PILOT_SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, PILOT_SCRIPTS_DIR)

from pilot_lib import (  # noqa: E402,F401
    PROCESSED_TRACE_DIR,
    _simulate_lru_misses,
    assert_no_learned_policy,
    build_requests_from_lists,
    enumerate_decision_positions,
    load_trace,
    reconstruct_candidates_at_t,
    sha256_file,
    simulate_rollout_misses,
)
from metrics import (  # noqa: E402,F401
    cross_continuation_regret,
    kendall_tau_b,
    optimal_set_jaccard,
    pairwise_taxonomy,
)

FAMILIES = ("cloudphysics", "metacdn", "metakv", "twemcache", "wiki2018")
CAPACITIES = (32, 64, 128, 256)
HORIZONS = (4, 8, 16)
CONTINUATIONS = ("lru", "mru")  # census scope: no random, no SIEVE, no FIFO, no blind_oracle

EXPECTED_TRACE_SHA256 = {
    "cloudphysics": "fedb3d31ee3c1dd847d25f967392cdf0fdec1e9c1fbb6808772e281bc8d4fb57",
    "metacdn": "7301f02e1373cb7e06f1ed2c417a8ebe16581319354780f811c8d032391f4e73",
    "metakv": "4c229e841d546cd57a2edb6e3ddc53461ff4dc03d366e9d24e4239a89db7e0de",
    "twemcache": "62df27062ce2595c843fd91e01d26c9783ff8f165f6b26e983696eda7ada0bb9",
    "wiki2018": "3813084bebfcf463ac22a685494b46aea45aded55d314411c9fbb058b5d67608",
}
SPLIT_LABEL = {"cloudphysics": "test", "metacdn": "validation", "metakv": "test",
               "twemcache": "test", "wiki2018": "test"}


def losses_to_regrets(losses):
    best = min(losses.values())
    return {c: v - best for c, v in losses.items()}


def compute_compact_decision_record(family, capacity, t, horizon, candidates, pid, requests):
    """Computes LRU and MRU candidate losses for one (decision, horizon),
    derives the compact tie-aware summary, and returns it -- the raw
    per-candidate loss dicts are local to this function call and are
    discarded on return (never written to disk), per the census's
    stream-don't-materialize requirement.
    """
    assert_no_learned_policy(["lru", "mru"])
    future = requests[t + 1 : t + 1 + horizon]

    lru_losses = {}
    mru_losses = {}
    for candidate in candidates:
        forced_cache = [p for p in candidates if p != candidate] + [pid]
        lru_losses[candidate] = float(simulate_rollout_misses(
            cache_pages=forced_cache, future_reqs=future, capacity=capacity, reference_policy="lru"))
        mru_losses[candidate] = float(simulate_rollout_misses(
            cache_pages=forced_cache, future_reqs=future, capacity=capacity, reference_policy="mru"))

    lru_regrets = losses_to_regrets(lru_losses)
    mru_regrets = losses_to_regrets(mru_losses)

    lru_best = min(lru_losses.values())
    mru_best = min(mru_losses.values())
    opt_lru = {c for c, v in lru_regrets.items() if v == 0.0}
    opt_mru = {c for c, v in mru_regrets.items() if v == 0.0}
    union = opt_lru | opt_mru

    jaccard = optimal_set_jaccard(lru_regrets, mru_regrets)
    taxonomy = pairwise_taxonomy(lru_regrets, mru_regrets)
    tau = kendall_tau_b(lru_regrets, mru_regrets)
    ccr = cross_continuation_regret(lru_regrets, mru_losses)

    record = {
        "decision_id": f"{family}|c{capacity}|t{t}|h{horizon}",
        "family": family, "capacity": capacity, "horizon": horizon, "request_t": t,
        "candidate_count": len(candidates),
        "lru_min_loss": lru_best, "mru_min_loss": mru_best,
        "lru_optimal_set_size": len(opt_lru), "mru_optimal_set_size": len(opt_mru),
        "optimal_set_intersection_size": len(opt_lru & opt_mru), "optimal_set_union_size": len(union),
        "optimal_set_jaccard": jaccard,
        "kendall_tau_b": tau,
        **{f"pairwise_{k}": v for k, v in taxonomy.items()},
        "ccr_mean_over_LRU_optimal": ccr["mean_over_LRU_optimal"],
        "ccr_best_case": ccr["best_case"], "ccr_worst_case": ccr["worst_case"],
        "ccr_prob_still_optimal": ccr["prob_still_optimal"],
        "all_tied_lru": len(opt_lru) == len(candidates),
        "all_tied_mru": len(opt_mru) == len(candidates),
        "scored_split_label": SPLIT_LABEL[family],
        "status": "complete",
    }
    return record
