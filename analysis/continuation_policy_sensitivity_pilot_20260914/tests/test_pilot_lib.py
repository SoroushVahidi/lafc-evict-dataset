import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pytest  # noqa: E402

from pilot_lib import (  # noqa: E402
    assert_no_learned_policy,
    reconstruct_candidates_at_t,
)


def test_learned_policy_guard_rejects_evict_value_v1():
    with pytest.raises(RuntimeError, match="learned policy"):
        assert_no_learned_policy(["evict_value_v1"])


def test_learned_policy_guard_allows_tier1_style_names():
    assert_no_learned_policy(["lru", "mru", "random"])  # must not raise


def test_reconstruct_candidates_at_t_matches_manual_replay():
    from pilot_lib import build_requests_from_lists

    page_ids = ["a", "b", "c", "d", "a", "e", "b"]
    requests, _pages = build_requests_from_lists(page_ids)
    capacity = 3
    # Manual trace: a,b,c fill the cache (positions 0,1,2). 'd' at position 3
    # is the first eviction decision; resident set is {a,b,c} in LRU order.
    candidates, pid = reconstruct_candidates_at_t(requests, capacity, 3)
    assert candidates == ["a", "b", "c"]
    assert pid == "d"


def test_reconstruct_candidates_at_t_raises_if_not_a_decision():
    from pilot_lib import build_requests_from_lists

    page_ids = ["a", "b"]
    requests, _pages = build_requests_from_lists(page_ids)
    with pytest.raises(AssertionError):
        reconstruct_candidates_at_t(requests, capacity=5, t=1)  # cache never fills at capacity 5
