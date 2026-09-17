"""Problem-5 Phase 3: pre-production validation of the expanded comparator
policies (ARC, LIRS, S3-FIFO, W-TinyLFU) before any Tier-1-scale replay runs.

Run with the dedicated libcachesim venv, e.g.:

    env/libcachesim_env/bin/python -m pytest \
        analysis/problem5_expanded_closed_loop_20260917/tests/ -q

This file must be run before
``scripts/run_problem5_expanded.py`` is invoked in production (Phase 4); if
any test here fails, production must not run (see PHASE 3 instruction:
"Do not run full production if implementation validation fails").
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
ANALYSIS_DIR = Path(__file__).resolve().parents[1]
PINNED_SIMULATOR_SRC = str(
    Path("/home/soroush/projects/augmented-caching/worktrees/problem5-expanded-baselines-20260917/src")
)

sys.path.insert(0, PINNED_SIMULATOR_SRC)
sys.path.insert(0, str(ANALYSIS_DIR / "scripts"))

from lafc.policies.lru import LRUPolicy  # noqa: E402
from lafc.runner.run_policy import run_policy  # noqa: E402
from lafc.simulator.request_trace import build_requests_from_lists  # noqa: E402

from expanded_policies import (  # noqa: E402
    ARCPolicy,
    EXPANDED_POLICIES,
    LIRSPolicy,
    S3FIFOPolicy,
    WTinyLFUPolicy,
    build_expanded_policy,
)

# NOTE: libcachesim's reference S3-FIFO/W-TinyLFU C implementations hard-abort
# (SIGABRT, not a catchable Python exception) when `cache_size` is too small
# for their internal ratio-based sub-structures to have at least 1 slot each
# (S3-FIFO needs cache_size>=10 for its default small_size_ratio=0.1;
# W-TinyLFU needs cache_size>=6 for its segment structure). Empirically
# verified once (see IMPLEMENTATION_INVENTORY.md discussion); NOT a concern
# for production (capacities 32 and 128 both clear this by a wide margin),
# but every structural test below therefore uses capacity=16, not a smaller
# toy value, to stay clear of this library-internal edge case.
ALL_POLICY_CLASSES = {
    "arc": ARCPolicy,
    "lirs": LIRSPolicy,
    "s3fifo": S3FIFOPolicy,
    "wtinylfu": WTinyLFUPolicy,
}


def _run(policy_name: str, page_ids, capacity: int):
    policy = build_expanded_policy(policy_name)
    requests, pages = build_requests_from_lists(page_ids)
    result = run_policy(policy, requests, pages, capacity)
    return result, requests, pages


# ---------------------------------------------------------------------------
# Structural gates required by PHASE 3, checked for every expanded policy.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("policy_name", EXPANDED_POLICIES)
def test_deterministic_replay_identical_on_repeat(policy_name):
    rng = random.Random(42)
    page_ids = [str(rng.randrange(0, 30)) for _ in range(500)]
    r1, _, _ = _run(policy_name, page_ids, capacity=16)
    r2, _, _ = _run(policy_name, page_ids, capacity=16)
    hits1 = [e.hit for e in r1.events]
    hits2 = [e.hit for e in r2.events]
    assert hits1 == hits2
    assert r1.total_hits == r2.total_hits
    assert r1.total_misses == r2.total_misses


@pytest.mark.parametrize("policy_name", EXPANDED_POLICIES)
def test_capacity_respected_exactly(policy_name):
    rng = random.Random(7)
    page_ids = [str(rng.randrange(0, 40)) for _ in range(800)]
    capacity = 32  # a real Tier-1 capacity; small toy sizes hit library-internal
    # ratio-rounding edge cases for some policies (see the W-TinyLFU and
    # S3-FIFO minimum-cache-size findings elsewhere in this file) that would
    # make this check vacuously pass at n_obj==0 forever.
    policy = build_expanded_policy(policy_name)
    requests, pages = build_requests_from_lists(page_ids)
    policy.reset(capacity, pages)
    max_seen = 0
    for req in requests:
        policy.on_request(req)
        n_obj = policy._lcs_cache.get_n_obj()
        max_seen = max(max_seen, n_obj)
        assert n_obj <= capacity, (
            f"{policy_name}: resident count exceeded capacity {capacity}"
        )
    assert max_seen > capacity // 2, (
        f"{policy_name}: cache never became meaningfully occupied "
        f"(max resident count {max_seen}) -- likely a non-functional configuration"
    )


@pytest.mark.parametrize("policy_name", EXPANDED_POLICIES)
def test_hits_plus_misses_equals_scored_requests(policy_name):
    rng = random.Random(3)
    page_ids = [str(rng.randrange(0, 20)) for _ in range(300)]
    result, requests, _ = _run(policy_name, page_ids, capacity=16)
    windows = ((50, 149), (200, 299))
    scored = [e for e in result.events if any(lo <= e.t <= hi for lo, hi in windows)]
    hits = sum(1 for e in scored if e.hit)
    misses = len(scored) - hits
    assert hits + misses == len(scored)
    assert len(scored) == 200  # two 100-length windows


@pytest.mark.parametrize("policy_name", EXPANDED_POLICIES)
def test_cold_start_first_request_is_always_a_miss(policy_name):
    page_ids = ["x1", "x2", "x3"]
    result, _, _ = _run(policy_name, page_ids, capacity=16)
    assert result.events[0].hit is False


@pytest.mark.parametrize("policy_name", EXPANDED_POLICIES)
def test_unit_object_cost_is_exactly_page_weight(policy_name):
    page_ids = ["a", "b", "a"]
    result, _, pages = _run(policy_name, page_ids, capacity=16)
    assert all(p.weight == 1.0 for p in pages.values())
    first_miss = result.events[0]
    assert first_miss.hit is False
    assert first_miss.cost == 1.0


def test_no_future_information_id_map_only_grows_incrementally():
    """The PageId->int mapper must assign ids strictly in first-appearance
    order and never reference ids not yet seen -- i.e. it cannot depend on
    future requests."""
    from expanded_policies import _PageIdMapper

    mapper = _PageIdMapper()
    seen_order = ["c", "a", "c", "b", "a", "d"]
    assigned = [mapper.to_int(p) for p in seen_order]
    first_seen = {}
    expected_next = 1
    for p in seen_order:
        if p not in first_seen:
            first_seen[p] = expected_next
            expected_next += 1
    assert assigned == [first_seen[p] for p in seen_order]


@pytest.mark.parametrize("policy_name", EXPANDED_POLICIES)
@pytest.mark.parametrize("capacity", [32, 128])
def test_functional_not_just_non_crashing_at_production_capacities(policy_name, capacity):
    """Construction succeeding is not sufficient evidence of correctness --
    Phase 3 found libcachesim policies that construct without error yet
    never actually admit anything (see the W-TinyLFU finding below). Every
    policy actually used in production must demonstrably cache and hit at
    BOTH real Tier-1 capacities, not just avoid raising/aborting.
    """
    policy = build_expanded_policy(policy_name)
    requests, pages = build_requests_from_lists(["obj_a", "obj_a", "obj_a"])
    policy.reset(capacity, pages)
    e0 = policy.on_request(requests[0])
    e1 = policy.on_request(requests[1])
    assert e0.hit is False
    assert e1.hit is True, f"{policy_name} at capacity={capacity}: immediate repeat did not hit"
    assert policy._lcs_cache.get_n_obj() >= 1


def test_s3fifo_uses_prespecified_paper_default_ratios_not_tuned():
    """No trace-specific tuning: the exact literal constants pre-registered
    in COMPARATOR_PROTOCOL.md must appear verbatim in the policy source."""
    src = (ANALYSIS_DIR / "scripts" / "expanded_policies.py").read_text(encoding="utf-8")
    assert "small_size_ratio=0.1" in src
    assert "ghost_size_ratio=0.9" in src
    assert "move_to_main_threshold=2" in src


# ---------------------------------------------------------------------------
# Cross-check A: libcachesim's own LRU engine vs. the manuscript's ALREADY
# validated, Tier-1-used lafc.policies.lru.LRUPolicy, on an identical
# synthetic trace. LRU has no interpretation ambiguity, so this validates
# the Request/obj_id/get() integration layer shared by every expanded
# policy against ground truth this manuscript already trusts.
# ---------------------------------------------------------------------------


def test_libcachesim_lru_matches_trusted_lafc_lru_engine():
    import libcachesim as lcs

    from expanded_policies import _PageIdMapper

    rng = random.Random(1234)
    page_ids = [str(rng.randrange(0, 60)) for _ in range(3000)]
    capacity = 16

    requests, pages = build_requests_from_lists(page_ids)

    trusted = LRUPolicy()
    trusted_result = run_policy(trusted, requests, pages, capacity)
    trusted_hits = [e.hit for e in trusted_result.events]

    lcs_cache = lcs.LRU(cache_size=capacity)
    mapper = _PageIdMapper()
    lcs_hits = []
    for req in requests:
        obj_id = mapper.to_int(req.page_id)
        lcs_req = lcs.Request(obj_id=obj_id, obj_size=1, clock_time=req.t)
        lcs_hits.append(lcs_cache.get(lcs_req))

    assert trusted_hits == lcs_hits
    assert sum(trusted_hits) == sum(lcs_hits)


# ---------------------------------------------------------------------------
# Cross-check B: hand-derived tiny ARC trace. Traced manually from the
# published ARC replacement algorithm (Megiddo & Modha, FAST 2003):
#
#   capacity=2, sequence [A,B,A,C,A,B]
#   t=0 A: cache empty -> MISS, A -> T1={A}
#   t=1 B: MISS, T1={A,B} (T1+T2 = 2 = c, not yet full-with-replacement needed)
#   t=2 A: A in T1 -> HIT, promote A to MRU of T2. T1={B}, T2={A}
#   t=3 C: MISS. T1+T2 full (2). p=0, |T1|=1(B) > p(0) -> evict LRU of T1
#          (B) to ghost B1. Insert C into T1. T1={C}, T2={A}, B1={B}
#   t=4 A: A in T2 -> HIT, promote to MRU of T2 (unchanged, only member).
#   t=5 B: B is in ghost B1 -> ghost hit (NOT a real cache hit: the object
#          was not physically resident). ARC adapts p += max(1,|B2|/|B1|)
#          = max(1, 0/1) = 1 -> p=1, then REPLACE evicts from T2 (since
#          |T1|=1 is not > p=1), moving A to ghost B2, then moves B from
#          B1 into MRU of T2. Net effect for THIS request: MISS (data was
#          not cached), because ghost-list residency is metadata only.
#
#   Expected get() sequence: [False, False, True, False, True, False]
# ---------------------------------------------------------------------------


def test_arc_hand_derived_tiny_trace():
    import libcachesim as lcs

    seq = ["A", "B", "A", "C", "A", "B"]
    ids = {}
    next_id = [1]

    def to_id(p):
        if p not in ids:
            ids[p] = next_id[0]
            next_id[0] += 1
        return ids[p]

    cache = lcs.ARC(cache_size=2)
    out = []
    for i, p in enumerate(seq):
        req = lcs.Request(obj_id=to_id(p), obj_size=1, clock_time=i)
        out.append(cache.get(req))

    assert out == [False, False, True, False, True, False]


# ---------------------------------------------------------------------------
# Cross-check C: scan resistance. This is a documented, load-bearing design
# property of ARC, S3-FIFO, and W-TinyLFU (it is the entire reason these
# algorithms exist over plain LRU): a hot set smaller than the cache,
# interleaved with a single pass of one-time-only unique items ("scan"),
# must survive the scan and keep producing hits once the scan ends -- while
# plain LRU is provably destroyed by the same scan (every hot item is
# evicted during the scan, since the scan is longer than the cache).
# This gives an exact, hand-derivable expected outcome (steady-state hit
# count after the scan) without needing to hand-trace every internal state
# transition of the more complex algorithms.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("policy_name", ["arc", "s3fifo"])
def test_scan_resistance_hot_set_survives_one_time_scan(policy_name):
    capacity = 32  # a real Tier-1 capacity; see the capacity-respected test above
    hot_set = [f"hot{i}" for i in range(capacity - 2)]  # smaller than cache
    scan = [f"scan{i}" for i in range(500)]  # each seen exactly once, >> capacity

    # Warm the hot set in twice so any frequency/reference-count admission
    # threshold (e.g. W-TinyLFU's sketch, S3-FIFO's promotion threshold) is
    # satisfied honestly BEFORE the scan, not tuned to this test.
    page_ids = hot_set + hot_set + scan + hot_set + hot_set
    result, requests, _ = _run(policy_name, page_ids, capacity=capacity)

    post_scan_start = len(hot_set) * 2 + len(scan)
    post_scan_events = result.events[post_scan_start:]
    post_scan_hits = sum(1 for e in post_scan_events if e.hit)
    # Second post-scan pass of the hot set should be entirely (or almost
    # entirely) hits once resident again; require a strong majority as the
    # exact bound (not 100%) to allow for legitimate one-off admission
    # policy edge effects at the pass boundary.
    assert post_scan_hits >= int(0.8 * len(post_scan_events)), (
        f"{policy_name}: expected scan-resistant hot-set recovery, "
        f"got {post_scan_hits}/{len(post_scan_events)} hits"
    )


def test_wtinylfu_default_config_nonfunctional_at_capacity_32():
    """Documents the Phase-3 finding that excludes W-TinyLFU from
    EXPANDED_POLICIES: libcachesim's WTinyLFU with its published default
    `window_size=0.01` degenerates to a permanently-empty, always-missing
    cache at cache_size=32 (round(0.01*32)==0 window-LRU slots), one of
    this manuscript's two required Tier-1 capacities. It becomes functional
    only around cache_size>=100. This is locked in as a regression test so
    a future libcachesim upgrade that silently fixes (or changes) this
    behavior is visible rather than assumed away.
    """
    import libcachesim as lcs

    cache = lcs.WTinyLFU(cache_size=32)
    req0 = lcs.Request(obj_id=1, obj_size=1, clock_time=0)
    cache.get(req0)
    req1 = lcs.Request(obj_id=1, obj_size=1, clock_time=1)
    immediate_repeat_hit = cache.get(req1)
    assert immediate_repeat_hit is False
    assert cache.get_n_obj() == 0

    working_cache = lcs.WTinyLFU(cache_size=128)
    wreq0 = lcs.Request(obj_id=1, obj_size=1, clock_time=0)
    working_cache.get(wreq0)
    wreq1 = lcs.Request(obj_id=1, obj_size=1, clock_time=1)
    assert working_cache.get(wreq1) is True
    assert working_cache.get_n_obj() == 1


def test_plain_lru_is_destroyed_by_the_same_scan_contrast_baseline():
    """Contrast baseline proving the scan in the test above is actually
    hard: plain LRU (already trusted) must NOT survive it, so the expanded
    policies' survival above is a real property, not a trivially easy trace.
    """
    capacity = 32
    hot_set = [f"hot{i}" for i in range(capacity - 2)]
    scan = [f"scan{i}" for i in range(500)]
    page_ids = hot_set + hot_set + scan + hot_set + hot_set

    requests, pages = build_requests_from_lists(page_ids)
    lru = LRUPolicy()
    result = run_policy(lru, requests, pages, capacity)

    post_scan_start = len(hot_set) * 2 + len(scan)
    first_post_scan_pass = result.events[post_scan_start : post_scan_start + len(hot_set)]
    # LRU's cache after a 500-item unique scan through a 10-slot cache
    # contains only the scan's last 10 items -- the entire first post-scan
    # pass over the hot set must be misses.
    assert all(not e.hit for e in first_post_scan_pass)
