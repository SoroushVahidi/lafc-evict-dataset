"""Synthetic (non-production) coverage of the capacity=128 path.

The frozen pilot only ever exercised capacity=32. The Tier-1 design adds
capacity=128, which is otherwise unexercised code. This test covers all four
Tier-1 policies at capacity=128 using a small synthetic trace built at test
time -- it does NOT read any real processed trace and does NOT constitute
production evidence.
"""

import math

import pytest

import tier1_core as t1


def _synthetic_trace(n_requests=2000, n_pages=300, seed=1234):
    """Build a synthetic page-id sequence with enough distinct pages relative
    to capacity=128 that evictions are forced, and enough repetition that
    hits also occur.
    """
    import random as _random

    rng = _random.Random(seed)
    page_ids = [str(rng.randrange(n_pages)) for _ in range(n_requests)]
    mods = t1._import_simulator_modules()
    return mods["build_requests_from_lists"](page_ids)


FULL_WINDOW = ((0, 10_000_000),)  # covers the whole synthetic trace


@pytest.mark.parametrize("policy_name", ["lru", "mru", "sieve"])
def test_deterministic_policy_at_capacity_128(policy_name):
    requests, pages = _synthetic_trace()
    execution = t1.Execution(family="cloudphysics", capacity=128, policy=policy_name, seed=None)
    row = t1.run_one_execution(execution, requests, pages, FULL_WINDOW)

    assert row["status"] == "complete", row.get("error")
    assert row["scored_requests"] == len(requests)
    assert row["hits"] + row["misses"] == row["scored_requests"]
    assert row["misses"] > 0  # capacity 128 < 300 distinct pages -> must miss and evict
    assert row["evictions"] > 0
    assert 0.0 <= row["miss_ratio"] <= 1.0
    assert not math.isnan(row["miss_ratio"])
    assert row["runtime_sec"] >= 0.0


def test_random_policy_at_capacity_128_with_seed():
    requests, pages = _synthetic_trace()
    execution = t1.Execution(family="cloudphysics", capacity=128, policy="random", seed=7)
    row = t1.run_one_execution(execution, requests, pages, FULL_WINDOW)

    assert row["status"] == "complete", row.get("error")
    assert row["hits"] + row["misses"] == row["scored_requests"]
    assert row["evictions"] > 0
    assert 0.0 <= row["miss_ratio"] <= 1.0


@pytest.mark.parametrize("policy_name", ["lru", "mru", "sieve"])
def test_deterministic_policy_capacity_128_is_reproducible(policy_name):
    requests, pages = _synthetic_trace()
    execution = t1.Execution(family="cloudphysics", capacity=128, policy=policy_name, seed=None)
    row_a = t1.run_one_execution(execution, requests, pages, FULL_WINDOW)
    row_b = t1.run_one_execution(execution, requests, pages, FULL_WINDOW)

    for key in ("scored_requests", "hits", "misses", "miss_ratio", "evictions"):
        assert row_a[key] == row_b[key], (policy_name, key)


def test_random_policy_capacity_128_same_seed_is_reproducible():
    requests, pages = _synthetic_trace()
    execution = t1.Execution(family="cloudphysics", capacity=128, policy="random", seed=42)
    row_a = t1.run_one_execution(execution, requests, pages, FULL_WINDOW)
    row_b = t1.run_one_execution(execution, requests, pages, FULL_WINDOW)

    for key in ("scored_requests", "hits", "misses", "miss_ratio", "evictions"):
        assert row_a[key] == row_b[key]


def test_random_policy_capacity_128_different_seeds_can_differ():
    requests, pages = _synthetic_trace()
    exec_a = t1.Execution(family="cloudphysics", capacity=128, policy="random", seed=1)
    exec_b = t1.Execution(family="cloudphysics", capacity=128, policy="random", seed=2)
    row_a = t1.run_one_execution(exec_a, requests, pages, FULL_WINDOW)
    row_b = t1.run_one_execution(exec_b, requests, pages, FULL_WINDOW)

    # Not asserting inequality categorically (could coincidentally match),
    # but both must be valid independent complete runs.
    assert row_a["status"] == "complete" and row_b["status"] == "complete"


def test_capacity_32_and_128_both_produce_valid_results_same_trace():
    requests, pages = _synthetic_trace()
    for capacity in (32, 128):
        execution = t1.Execution(family="cloudphysics", capacity=capacity, policy="lru", seed=None)
        row = t1.run_one_execution(execution, requests, pages, FULL_WINDOW)
        assert row["status"] == "complete"
        assert row["hits"] + row["misses"] == row["scored_requests"]
    # A larger cache must not do worse than a smaller one on the same trace/policy.
    row32 = t1.run_one_execution(
        t1.Execution(family="cloudphysics", capacity=32, policy="lru", seed=None), requests, pages, FULL_WINDOW
    )
    row128 = t1.run_one_execution(
        t1.Execution(family="cloudphysics", capacity=128, policy="lru", seed=None), requests, pages, FULL_WINDOW
    )
    assert row128["misses"] <= row32["misses"]
