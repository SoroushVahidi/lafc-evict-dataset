"""Problem-5 expanded closed-loop comparator policies (ARC, LIRS, S3-FIFO, W-TinyLFU).

Carried forward as harness-local ``BasePolicy`` subclasses, exactly the same
convention the existing Tier-1 harness uses for MRU/random (see
``analysis/closed_loop_production_tier1_20260913/scripts/tier1_core.py``,
``build_local_policy_classes``): these policies are NOT added to the
simulator repository's ``src/lafc/policies/`` so that the simulator's gated
dependency files stay byte-identical to the expected Tier-1 commit.

Each class wraps the corresponding reference C implementation from
``libcachesim`` (see ``IMPLEMENTATION_INVENTORY.md`` and
``COMPARATOR_PROTOCOL.md`` for the reuse-vs-reimplement decision and the
pre-registered policy set). All four policies here are deterministic: no
seed, no randomness in eviction/admission.

Unit-object semantics: every request is passed to libcachesim as
``obj_size=1``, matching ``build_requests_from_lists``'s uniform
``weight=1.0`` page cost in the simulator repository -- this file does not
introduce any size/weight heterogeneity.

No admission tuning: ARC and LIRS take no algorithm parameters at all.
S3-FIFO uses the algorithm's own published defaults
(``small_size_ratio=0.1``, ``ghost_size_ratio=0.9``,
``move_to_main_threshold=2``); this module never overrides them per family
or capacity. W-TinyLFU is used with its library defaults.

No future information: page ids are mapped to libcachesim's required
integer ``obj_id`` via a stable, order-of-first-appearance counter built
incrementally as requests arrive (see ``_PageIdMapper``), never precomputed
from the whole trace ahead of time.
"""

from __future__ import annotations

from typing import Dict, Optional

import libcachesim as lcs

from lafc.policies.base import BasePolicy
from lafc.types import CacheEvent, Page, PageId, Request


class _PageIdMapper:
    """Stable, streaming string PageId -> libcachesim integer obj_id map.

    Built incrementally as requests are seen (never precomputed from future
    requests), so it cannot leak future-trace information into the policy.
    """

    def __init__(self) -> None:
        self._map: Dict[PageId, int] = {}
        self._next_id: int = 1  # libcachesim obj_id 0 is a valid id too, but
        # starting at 1 avoids any accidental confusion with a default-zero
        # sentinel and matches no library requirement either way.

    def to_int(self, page_id: PageId) -> int:
        existing = self._map.get(page_id)
        if existing is not None:
            return existing
        new_id = self._next_id
        self._map[page_id] = new_id
        self._next_id += 1
        return new_id


class _LibCacheSimPolicyBase(BasePolicy):
    """Shared glue between a libcachesim CacheBase object and BasePolicy."""

    _cache_ctor = None  # set by subclass

    def reset(self, capacity: int, pages: Dict[PageId, Page]) -> None:
        super().reset(capacity, pages)
        self._lcs_cache = self._build_cache(capacity)
        self._id_map = _PageIdMapper()
        self._occupied = 0  # bookkeeping mirror of libcachesim's own resident
        # count, used only to report an `evicted` sentinel consistent with
        # the other Tier-1 policies' CacheEvent contract (see score_events's
        # eviction counting logic in tier1_core.py: "not hit and evicted is
        # not None"). libcachesim's own get() already enforces the actual
        # capacity constraint; this counter never influences behavior.

    def _build_cache(self, capacity: int):
        raise NotImplementedError

    def on_request(self, request: Request) -> CacheEvent:
        pid = request.page_id
        obj_id = self._id_map.to_int(pid)
        was_full_before = self._occupied >= self._cache.capacity
        lcs_req = lcs.Request(obj_id=obj_id, obj_size=1, clock_time=request.t)
        hit = self._lcs_cache.get(lcs_req)

        if hit:
            self._record_hit()
            return CacheEvent(t=request.t, page_id=pid, hit=True, cost=0.0)

        cost = self._pages[pid].weight
        self._record_miss(cost)
        evicted: Optional[PageId] = "<libcachesim-internal>" if was_full_before else None
        if not was_full_before:
            self._occupied += 1
        return CacheEvent(t=request.t, page_id=pid, hit=False, cost=cost, evicted=evicted)


class ARCPolicy(_LibCacheSimPolicyBase):
    """Adaptive Replacement Cache (Megiddo & Modha, FAST 2003).

    No parameters beyond cache size. Reference implementation from
    libcachesim (see COMPARATOR_PROTOCOL.md).
    """

    name: str = "arc"

    def _build_cache(self, capacity: int):
        return lcs.ARC(cache_size=capacity)


class LIRSPolicy(_LibCacheSimPolicyBase):
    """Low Inter-reference Recency Set (Jiang & Zhang, SIGMETRICS 2002).

    No parameters beyond cache size. Reference implementation from
    libcachesim.
    """

    name: str = "lirs"

    def _build_cache(self, capacity: int):
        return lcs.LIRS(cache_size=capacity)


class S3FIFOPolicy(_LibCacheSimPolicyBase):
    """S3-FIFO (Yang et al., SOSP 2023). Uses the algorithm's published
    default ratios; never tuned per family/capacity.
    """

    name: str = "s3fifo"

    def _build_cache(self, capacity: int):
        return lcs.S3FIFO(
            cache_size=capacity,
            small_size_ratio=0.1,
            ghost_size_ratio=0.9,
            move_to_main_threshold=2,
        )


class WTinyLFUPolicy(_LibCacheSimPolicyBase):
    """Window TinyLFU (Einziger, Friedman & Manes, TOS 2017).

    Admission-sketch + segmented-LRU main cache, fully bundled by the
    library; used with library defaults.

    NOT included in EXPANDED_POLICIES / production execution. Phase 3
    validation (see tests/test_expanded_policies_validation.py::
    test_wtinylfu_default_config_nonfunctional_at_capacity_32) found that
    libcachesim's WTinyLFU with its documented default `window_size=0.01`
    is completely non-functional (permanent miss, `get_n_obj()` stays 0
    forever) at cache_size=32 -- one of this manuscript's two required
    Tier-1 capacities -- because `round(0.01 * 32) == 0` degenerates the
    window-LRU segment to zero slots. It only becomes functional around
    cache_size>=100 (confirmed working at 100/110/120/128). Changing
    `window_size` away from its published default specifically to make it
    merely function at capacity 32 would be exactly the kind of
    trace/capacity-specific tuning the pre-registered protocol forbids, so
    this policy is excluded rather than patched. This class is kept,
    unused, purely as documentation of what was tried; see
    COMPARATOR_PROTOCOL.md's Phase-3 addendum for the pre-registration-
    consistent decision to keep the three primary policies (ARC, LIRS,
    S3-FIFO) as the full Problem-5 set.
    """

    name: str = "wtinylfu"

    def _build_cache(self, capacity: int):
        return lcs.WTinyLFU(cache_size=capacity)


EXPANDED_POLICIES = ("arc", "lirs", "s3fifo")


def build_expanded_policy(name: str) -> BasePolicy:
    if name == "arc":
        return ARCPolicy()
    if name == "lirs":
        return LIRSPolicy()
    if name == "s3fifo":
        return S3FIFOPolicy()
    if name == "wtinylfu":
        return WTinyLFUPolicy()
    raise ValueError(f"unknown Problem-5 expanded policy '{name}'")
