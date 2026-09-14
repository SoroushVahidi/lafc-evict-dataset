"""LAFC-Evict Tier-1 closed-loop production harness (core library).

This module encodes exactly the approved production design frozen at
`experiment/closed-loop-production-design-20260913` (commit `adc7c64...`):

  analysis/closed_loop_production_design_20260913/DESIGN.md
  analysis/closed_loop_production_design_20260913/MATRIX.md
  analysis/closed_loop_production_design_20260913/VALIDITY_GATES.md
  analysis/closed_loop_production_design_20260913/RUNTIME_ESTIMATE.md

It does NOT invent a different experiment. Every family/capacity/policy/seed/
window value below is copied verbatim from those documents. If a future
change to the design is approved, this file must be updated to match it
explicitly -- do not silently reinterpret the design.

Scope of this module: Tier 1 only (LRU, MRU, random, SIEVE). This module
contains NO code path that can construct or invoke a learned policy
(evict_value_v1 or otherwise). `assert_no_learned_policy` is a fail-fast
guard applied to every generated plan and to every individual execution
request, independent of each other, so that a bug in one does not silently
defeat the other.

Terminology discipline (per the canonical handoff and production design):
scored evidence windows are always described as "temporally held-out test
window(s)" or, for MetaCDN, explicitly as "validation-window evidence" --
never as "held-out traces" and never as "an unseen trace". See
`FAMILY_CONFIG[*]["evidence_label"]` and `FAMILY_CONFIG[*]["split_caveat"]`.

Continuation-policy sensitivity and Tier 2 (evict_value_v1) are explicitly
out of scope for this module and for Tier 1 generally.
"""

from __future__ import annotations

import csv
import getpass
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Repository locations
# ---------------------------------------------------------------------------

# This file lives at:
#   <lafc-evict worktree>/analysis/closed_loop_production_tier1_20260913/scripts/tier1_core.py
THIS_FILE = Path(__file__).resolve()
TIER1_DIR = THIS_FILE.parent.parent
LAFC_EVICT_REPO_ROOT = TIER1_DIR.parent.parent

AUGMENTED_CACHING_REPO = Path("/home/soroush/projects/augmented-caching/repo")
AUGMENTED_CACHING_SRC = str(AUGMENTED_CACHING_REPO / "src")
PROCESSED_TRACE_DIR = AUGMENTED_CACHING_REPO / "data" / "processed"

EXPECTED_SIMULATOR_BRANCH = "chore/repository-polish"
EXPECTED_SIMULATOR_HEAD = "ceb36705b59d0d16db55d0fc0bfb63a5c7a2a6a1"

# Files Tier 1 actually imports/depends on in the simulator repository.
# (evict_value_v1.py and its feature/model helper modules are deliberately
# NOT in this list: Tier 1 must never import them.)
SIMULATOR_DEPENDENCY_FILES = [
    "src/lafc/policies/base.py",
    "src/lafc/policies/lru.py",
    "src/lafc/policies/sieve.py",
    "src/lafc/runner/run_policy.py",
    "src/lafc/simulator/cache_state.py",
    "src/lafc/simulator/request_trace.py",
    "src/lafc/types.py",
]

# Modules that implement learned-policy code. These are recorded here for
# documentation/provenance purposes only -- they are NOT gated on
# `sys.modules` membership, because `lafc.runner.run_policy` (a required
# Tier-1 dependency) transitively imports `lafc.policies.evict_value_v1` at
# module load time as a structural fact of the simulator repository (see the
# NOTE in `_import_simulator_modules`). The actual fail-fast guard Tier 1
# relies on is name-based: `assert_no_learned_policy()`.
FORBIDDEN_SIMULATOR_MODULES = {
    "lafc.policies.evict_value_v1",
    "lafc.evict_value_features_v1",
    "lafc.evict_value_model_v1",
}

# ---------------------------------------------------------------------------
# Tier-1 matrix (verbatim from MATRIX.md / DESIGN.md)
# ---------------------------------------------------------------------------

FAMILIES: Tuple[str, ...] = ("cloudphysics", "metacdn", "metakv", "twemcache", "wiki2018")
CAPACITIES: Tuple[int, ...] = (32, 128)
DETERMINISTIC_POLICIES: Tuple[str, ...] = ("lru", "mru", "sieve")
STOCHASTIC_POLICIES: Tuple[str, ...] = ("random",)
POLICIES: Tuple[str, ...] = DETERMINISTIC_POLICIES + STOCHASTIC_POLICIES
RANDOM_SEEDS: Tuple[int, ...] = tuple(range(20))  # 0..19 inclusive

# Policies that are categorically forbidden in Tier 1, by name. Any policy
# object whose `.name` matches this set must never be run through this
# module's Tier-1 execution path.
LEARNED_POLICY_NAMES = frozenset({"evict_value_v1"})

OFFLINE_HORIZON_PRIMARY = 16
OFFLINE_HORIZONS_SECONDARY: Tuple[int, ...] = (4, 8, 16)

EXPECTED_TOTAL_EXECUTIONS = (
    len(FAMILIES) * len(CAPACITIES) * len(DETERMINISTIC_POLICIES)
    + len(FAMILIES) * len(CAPACITIES) * len(STOCHASTIC_POLICIES) * len(RANDOM_SEEDS)
)
assert EXPECTED_TOTAL_EXECUTIONS == 230, EXPECTED_TOTAL_EXECUTIONS


@dataclass(frozen=True)
class FamilySplit:
    trace_name: str
    trace_relpath: str  # relative to PROCESSED_TRACE_DIR
    expected_sha256: str
    scored_windows: Tuple[Tuple[int, int], ...]
    scored_split_label: str  # "test" or "validation", per the checked-in design
    evidence_label: str  # human-readable classification string
    split_caveat: str
    learned_policy_classification: str  # from VALIDITY_GATES.md, Tier-1 informational only


# Verbatim from MATRIX.md ("Tier 1: Cheap Baseline Replay" scoring table) and
# DESIGN.md ("Family Inventory" / "evict_value_v1 Leakage Audit" tables).
# Trace SHA256 values are copied verbatim from DESIGN.md's trace-hash table.
FAMILY_CONFIG: Dict[str, FamilySplit] = {
    "cloudphysics": FamilySplit(
        trace_name="cloudphysics_alibaba_block_head_50k",
        trace_relpath="cloudphysics/trace.jsonl",
        expected_sha256="fedb3d31ee3c1dd847d25f967392cdf0fdec1e9c1fbb6808772e281bc8d4fb57",
        scored_windows=((16384, 20479), (20480, 24575)),
        scored_split_label="test",
        evidence_label="temporally held-out test window(s)",
        split_caveat=(
            "Test windows are temporal windows within one continuous trace, not an "
            "unseen trace."
        ),
        learned_policy_classification="LEARNED_POLICY_SAFE_TEST",
    ),
    "metacdn": FamilySplit(
        trace_name="metacdn_cdn_202303_head_50k",
        trace_relpath="metacdn/trace.jsonl",
        expected_sha256="7301f02e1373cb7e06f1ed2c417a8ebe16581319354780f811c8d032391f4e73",
        scored_windows=((0, 4095), (24576, 32767), (36864, 45055)),
        scored_split_label="validation",
        evidence_label="validation-window evidence (no independent test chunks)",
        split_caveat=(
            "MetaCDN has NO test-split chunks at these capacities. Scored windows are "
            "VALIDATION chunks and must be reported as validation-window evidence, "
            "never as test-window evidence and never as an unseen trace. Learned-policy "
            "scoring here would be circular (validation participated in model "
            "selection) and is BLOCKED_LEAKAGE_RISK -- out of scope for Tier 1, which "
            "contains no learned policy."
        ),
        learned_policy_classification="BLOCKED_LEAKAGE_RISK",
    ),
    "metakv": FamilySplit(
        trace_name="metakv_kvcache_202206_head_50k",
        trace_relpath="metakv/trace.jsonl",
        expected_sha256="4c229e841d546cd57a2edb6e3ddc53461ff4dc03d366e9d24e4239a89db7e0de",
        scored_windows=((0, 4095),),
        scored_split_label="test",
        evidence_label="temporally held-out test window(s)",
        split_caveat=(
            "Test window is the first chunk of the trace ([0,4095]); there is no "
            "leading unscored warmup before scoring begins, though the full trace "
            "still replays continuously beforehand within this window. Report this "
            "first-window/no-leading-warmup caveat alongside any metakv result."
        ),
        learned_policy_classification="LEARNED_POLICY_SAFE_TEST",
    ),
    "twemcache": FamilySplit(
        trace_name="twemcache_cluster26_sample100_50k",
        trace_relpath="twemcache/trace.jsonl",
        expected_sha256="62df27062ce2595c843fd91e01d26c9783ff8f165f6b26e983696eda7ada0bb9",
        scored_windows=((32768, 36863), (40960, 45055)),
        scored_split_label="test",
        evidence_label="temporally held-out test window(s)",
        split_caveat=(
            "Test windows are temporal windows within one continuous trace, not an "
            "unseen trace. This is the strongest pilot learned-policy cell, but Tier 1 "
            "itself runs no learned policy here."
        ),
        learned_policy_classification="LEARNED_POLICY_SAFE_TEST",
    ),
    "wiki2018": FamilySplit(
        trace_name="wiki2018_pageviews_en_50k",
        trace_relpath="wiki2018/trace.jsonl",
        expected_sha256="3813084bebfcf463ac22a685494b46aea45aded55d314411c9fbb058b5d67608",
        scored_windows=((24576, 28671),),
        scored_split_label="test",
        evidence_label="temporally held-out test window(s); offline-degenerate negative control",
        split_caveat=(
            "wiki2018 is the offline-degenerate control family: prior offline audit "
            "found all candidates tied, zero random regret, and no unique winner in "
            "every capacity/horizon cell. Learned-policy evaluation on wiki2018 is "
            "explicitly DEFERRED by the production design (safe test chunks exist but "
            "offline labels are fully degenerate); Tier 1 runs no learned policy on any "
            "family, including this one."
        ),
        learned_policy_classification="LEARNED_POLICY_SAFE_TEST",
    ),
}

assert set(FAMILY_CONFIG.keys()) == set(FAMILIES)


# ---------------------------------------------------------------------------
# Execution plan
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Execution:
    """One planned Tier-1 closed-loop replay execution."""

    family: str
    capacity: int
    policy: str
    seed: Optional[int]  # None for deterministic policies

    @property
    def run_key(self) -> str:
        seed_part = "none" if self.seed is None else str(self.seed)
        return f"{self.family}|{self.capacity}|{self.policy}|{seed_part}"


def assert_no_learned_policy(policy_names: List[str]) -> None:
    """Fail fast if any planned or requested policy name is a learned policy.

    Applied independently at plan-construction time AND at execution time so
    that a bug in one call site cannot silently defeat the other.
    """
    bad = sorted(set(policy_names) & LEARNED_POLICY_NAMES)
    if bad:
        raise RuntimeError(
            f"Tier-1 fail-fast guard: learned policy name(s) {bad} are not permitted "
            "in the Tier-1 execution path. Tier 2 is out of scope for this harness "
            "and must never be reached from here."
        )


def build_plan() -> List[Execution]:
    """Build the exact 230-execution Tier-1 plan from the module constants."""
    plan: List[Execution] = []
    for family in FAMILIES:
        for capacity in CAPACITIES:
            for policy in DETERMINISTIC_POLICIES:
                plan.append(Execution(family=family, capacity=capacity, policy=policy, seed=None))
            for policy in STOCHASTIC_POLICIES:
                for seed in RANDOM_SEEDS:
                    plan.append(
                        Execution(family=family, capacity=capacity, policy=policy, seed=seed)
                    )
    assert_no_learned_policy([e.policy for e in plan])
    return plan


def assert_plan_valid(plan: List[Execution]) -> None:
    """Programmatic assertion of the exact approved composition (per task spec)."""
    if len(plan) != 230:
        raise AssertionError(f"expected exactly 230 executions, got {len(plan)}")

    families_seen = {e.family for e in plan}
    if families_seen != set(FAMILIES):
        raise AssertionError(f"expected exactly families {set(FAMILIES)}, got {families_seen}")

    capacities_seen = {e.capacity for e in plan}
    if capacities_seen != set(CAPACITIES):
        raise AssertionError(f"expected exactly capacities {set(CAPACITIES)}, got {capacities_seen}")

    policies_seen = {e.policy for e in plan}
    if policies_seen != set(POLICIES):
        raise AssertionError(f"expected exactly policies {set(POLICIES)}, got {policies_seen}")

    seeds_seen = {e.seed for e in plan if e.seed is not None}
    if seeds_seen != set(RANDOM_SEEDS):
        raise AssertionError(f"expected exactly random seeds 0..19, got {sorted(seeds_seen)}")

    assert_no_learned_policy(list(policies_seen))

    keys = [e.run_key for e in plan]
    if len(keys) != len(set(keys)):
        dupes = sorted({k for k in keys if keys.count(k) > 1})
        raise AssertionError(f"duplicate execution key(s) in plan: {dupes}")

    for family in FAMILIES:
        for capacity in CAPACITIES:
            cell = [e for e in plan if e.family == family and e.capacity == capacity]
            det = [e for e in cell if e.policy in DETERMINISTIC_POLICIES]
            if len(det) != len(DETERMINISTIC_POLICIES):
                raise AssertionError(
                    f"cell {family}/{capacity}: expected exactly one run per deterministic "
                    f"policy ({DETERMINISTIC_POLICIES}), got {[e.policy for e in det]}"
                )
            rnd = [e for e in cell if e.policy == "random"]
            if len(rnd) != len(RANDOM_SEEDS):
                raise AssertionError(
                    f"cell {family}/{capacity}: expected exactly {len(RANDOM_SEEDS)} random "
                    f"seeds, got {len(rnd)}"
                )
            rnd_seeds = sorted(e.seed for e in rnd)
            if rnd_seeds != list(RANDOM_SEEDS):
                raise AssertionError(
                    f"cell {family}/{capacity}: random seeds {rnd_seeds} != expected "
                    f"{list(RANDOM_SEEDS)}"
                )


def plan_summary(plan: List[Execution]) -> Dict[str, object]:
    by_policy: Dict[str, int] = {}
    for e in plan:
        by_policy[e.policy] = by_policy.get(e.policy, 0) + 1
    return {
        "total_executions": len(plan),
        "families": sorted({e.family for e in plan}),
        "capacities": sorted({e.capacity for e in plan}),
        "policies": sorted({e.policy for e in plan}),
        "random_seeds": sorted({e.seed for e in plan if e.seed is not None}),
        "executions_by_policy": by_policy,
        "cells": len(FAMILIES) * len(CAPACITIES),
        "offline_horizon_primary": OFFLINE_HORIZON_PRIMARY,
        "offline_horizons_secondary": list(OFFLINE_HORIZONS_SECONDARY),
        "offline_horizons_are_comparison_only_not_executions": True,
    }


# ---------------------------------------------------------------------------
# Policy adapters
#
# LRU and SIEVE are imported directly from the clean, committed simulator
# implementation (src/lafc/policies/{lru,sieve}.py). MRU and random do not
# exist in the simulator repository; per DESIGN.md ("Policy Readiness"):
# "Include Tier 1 by carrying pilot-local adapter in the production analysis
# script, not by editing simulator code." The two classes below are carried
# forward FAITHFULLY from the frozen pilot script
# (analysis/closed_loop_pilot_20260913/scripts/run_pilot.py, sha256
# 4a80279e6b80c05fc8daa4cd06b28efe75c6c89f047e91a4f1a6bddbc47b0e84) with no
# behavioral changes -- only renamed imports to match this module's layout.
# ---------------------------------------------------------------------------


def _import_simulator_modules():
    """Import the required lafc simulator modules.

    NOTE on FORBIDDEN_SIMULATOR_MODULES: `lafc.runner.run_policy` (a required
    Tier-1 dependency -- it defines the `run_policy()` function every
    execution calls) unconditionally imports `EvictValueV1Policy` at module
    level and even constructs one default instance into its own internal
    POLICY_REGISTRY dict as an import-time side effect (see
    src/lafc/runner/run_policy.py lines ~73/126). That import is therefore
    unavoidable merely by importing `run_policy` -- it is a structural fact
    of the simulator repository, not something this harness chooses to do,
    and the registry entry is never invoked (module import only calls
    `EvictValueV1Policy()`'s cheap `__init__`, never `.reset()`/`.on_request()`
    on real data). For that reason this function does NOT gate on
    `sys.modules` membership -- doing so would make it impossible to import
    `run_policy` at all. The actual, functioning fail-fast guard is
    `assert_no_learned_policy()`, applied BY NAME at plan-build time
    (`build_plan`), plan-validation time (`assert_plan_valid`), and
    individual construction/execution time (`build_policy`,
    `run_one_execution`) -- Tier 1's own code path never reads from or
    touches `run_policy`'s internal POLICY_REGISTRY dict; it always passes a
    policy object this module constructed itself directly into
    `run_policy(policy, requests, pages, capacity)`.
    """
    if AUGMENTED_CACHING_SRC not in sys.path:
        sys.path.insert(0, AUGMENTED_CACHING_SRC)

    from lafc.policies.base import BasePolicy  # noqa: E402
    from lafc.policies.lru import LRUPolicy  # noqa: E402
    from lafc.policies.sieve import SievePolicy  # noqa: E402
    from lafc.runner.run_policy import run_policy  # noqa: E402
    from lafc.simulator.request_trace import build_requests_from_lists  # noqa: E402
    from lafc.types import CacheEvent, Page, PageId, Request  # noqa: E402

    return {
        "BasePolicy": BasePolicy,
        "LRUPolicy": LRUPolicy,
        "SievePolicy": SievePolicy,
        "run_policy": run_policy,
        "build_requests_from_lists": build_requests_from_lists,
        "CacheEvent": CacheEvent,
        "Page": Page,
        "PageId": PageId,
        "Request": Request,
    }


def build_local_policy_classes():
    """Build MRUPolicy and UniformRandomPolicy, carried forward verbatim
    (behavior-for-behavior) from the frozen pilot script's local classes.
    """
    mods = _import_simulator_modules()
    BasePolicy = mods["BasePolicy"]
    CacheEvent = mods["CacheEvent"]

    import collections
    from typing import Optional as _Optional

    class MRUPolicy(BasePolicy):
        """Most-Recently-Used eviction: evict the page used most recently.

        Carried forward verbatim from
        analysis/closed_loop_pilot_20260913/scripts/run_pilot.py::MRUPolicy.
        Not present in the augmented-caching simulator repository by design.
        """

        name: str = "mru"

        def reset(self, capacity, pages) -> None:
            super().reset(capacity, pages)
            self._order: "collections.OrderedDict" = collections.OrderedDict()

        def on_request(self, request):
            pid = request.page_id
            evicted: _Optional[object] = None

            if self.in_cache(pid):
                self._order.move_to_end(pid)
                self._record_hit()
                return CacheEvent(t=request.t, page_id=pid, hit=True, cost=0.0)

            cost = self._pages[pid].weight
            self._record_miss(cost)

            if self._cache.is_full():
                evicted, _ = self._order.popitem(last=True)  # evict MOST-recently-used
                self._evict(evicted)

            self._add(pid)
            self._order[pid] = None
            return CacheEvent(t=request.t, page_id=pid, hit=False, cost=cost, evicted=evicted)

    class UniformRandomPolicy(BasePolicy):
        """Evict a uniformly-random resident page on a full-cache miss.

        Carried forward verbatim from
        analysis/closed_loop_pilot_20260913/scripts/run_pilot.py::UniformRandomPolicy.
        Deterministic given a seed (a fresh random.Random instance per reset()).
        """

        name: str = "random"

        def __init__(self, seed: int) -> None:
            self.seed = seed

        def reset(self, capacity, pages) -> None:
            super().reset(capacity, pages)
            self._resident: list = []
            self._resident_set: set = set()
            self._rng = random.Random(self.seed)

        def on_request(self, request):
            pid = request.page_id
            evicted: _Optional[object] = None

            if self.in_cache(pid):
                self._record_hit()
                return CacheEvent(t=request.t, page_id=pid, hit=True, cost=0.0)

            cost = self._pages[pid].weight
            self._record_miss(cost)

            if self._cache.is_full():
                idx = self._rng.randrange(len(self._resident))
                evicted = self._resident.pop(idx)
                self._resident_set.discard(evicted)
                self._evict(evicted)

            self._add(pid)
            self._resident.append(pid)
            self._resident_set.add(pid)

            return CacheEvent(t=request.t, page_id=pid, hit=False, cost=cost, evicted=evicted)

    return {"MRUPolicy": MRUPolicy, "UniformRandomPolicy": UniformRandomPolicy}


def build_policy(policy_name: str, seed: Optional[int] = None):
    """Construct a fresh policy instance for one execution.

    Raises via assert_no_learned_policy() if policy_name is a learned policy;
    this is checked BEFORE any import/construction happens.
    """
    assert_no_learned_policy([policy_name])
    mods = _import_simulator_modules()
    if policy_name == "lru":
        return mods["LRUPolicy"]()
    if policy_name == "sieve":
        return mods["SievePolicy"]()
    local = build_local_policy_classes()
    if policy_name == "mru":
        return local["MRUPolicy"]()
    if policy_name == "random":
        if seed is None:
            raise ValueError("random policy requires an explicit seed")
        return local["UniformRandomPolicy"](seed=seed)
    raise ValueError(f"unknown Tier-1 policy '{policy_name}'")


# ---------------------------------------------------------------------------
# Trace loading and scoring (adapted from the frozen pilot script; identical
# semantics, generalized from a hardcoded 2-family/capacity-32-only config to
# the full 5-family/2-capacity Tier-1 matrix).
# ---------------------------------------------------------------------------


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_processed_trace(path: Path):
    mods = _import_simulator_modules()
    build_requests_from_lists = mods["build_requests_from_lists"]
    page_ids: List[str] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            page_ids.append(str(rec["item_id"]))
    return build_requests_from_lists(page_ids)


def in_scored_windows(t: int, windows: Tuple[Tuple[int, int], ...]) -> bool:
    return any(lo <= t <= hi for lo, hi in windows)


def score_events(events, windows: Tuple[Tuple[int, int], ...]) -> Dict[str, object]:
    scored = [e for e in events if in_scored_windows(e.t, windows)]
    n = len(scored)
    hits = sum(1 for e in scored if e.hit)
    misses = n - hits
    evictions = sum(1 for e in scored if (not e.hit) and e.evicted is not None)
    return {
        "scored_requests": n,
        "hits": hits,
        "misses": misses,
        "miss_ratio": (misses / n) if n else float("nan"),
        "evictions": evictions,
    }


def run_one_execution(execution: Execution, requests, pages, windows) -> Dict[str, object]:
    """Run exactly one planned execution and return a raw result row.

    `requests`/`pages` are the already-loaded full trace for `execution.family`
    (loaded once per family/capacity by the caller and reused across policies,
    to avoid redundant I/O across the 46 executions that share a trace).
    """
    assert_no_learned_policy([execution.policy])
    policy = build_policy(execution.policy, seed=execution.seed)
    mods = _import_simulator_modules()
    run_policy = mods["run_policy"]

    t0 = time.perf_counter()
    try:
        result = run_policy(policy, requests, pages, execution.capacity)
        elapsed = time.perf_counter() - t0
        metrics = score_events(result.events, windows)
        row = {
            "run_key": execution.run_key,
            "family": execution.family,
            "capacity": execution.capacity,
            "policy": execution.policy,
            "seed": execution.seed,
            "status": "complete",
            "error": "",
            "scored_split_label": FAMILY_CONFIG[execution.family].scored_split_label,
            "scored_windows": json.dumps(list(FAMILY_CONFIG[execution.family].scored_windows)),
            "scored_requests": metrics["scored_requests"],
            "hits": metrics["hits"],
            "misses": metrics["misses"],
            "miss_ratio": metrics["miss_ratio"],
            "evictions": metrics["evictions"],
            "full_trace_requests": len(result.events),
            "full_trace_hits": result.total_hits,
            "full_trace_misses": result.total_misses,
            "runtime_sec": elapsed,
        }
    except Exception as exc:  # noqa: BLE001 -- deliberately broad: record, don't crash the batch
        elapsed = time.perf_counter() - t0
        row = {
            "run_key": execution.run_key,
            "family": execution.family,
            "capacity": execution.capacity,
            "policy": execution.policy,
            "seed": execution.seed,
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "scored_split_label": FAMILY_CONFIG[execution.family].scored_split_label,
            "scored_windows": json.dumps(list(FAMILY_CONFIG[execution.family].scored_windows)),
            "scored_requests": None,
            "hits": None,
            "misses": None,
            "miss_ratio": None,
            "evictions": None,
            "full_trace_requests": None,
            "full_trace_hits": None,
            "full_trace_misses": None,
            "runtime_sec": elapsed,
        }
    return row


RAW_ROW_FIELDS = [
    "run_key", "family", "capacity", "policy", "seed", "status", "error",
    "scored_split_label", "scored_windows", "scored_requests", "hits", "misses",
    "miss_ratio", "evictions", "full_trace_requests", "full_trace_hits",
    "full_trace_misses", "runtime_sec",
]


# ---------------------------------------------------------------------------
# Aggregation (mirrors the frozen pilot's random-seed aggregation exactly)
# ---------------------------------------------------------------------------


def aggregate_random_rows(rows: List[Dict[str, object]]) -> Dict[str, object]:
    complete = [r for r in rows if r["status"] == "complete"]
    if not complete:
        return {"status": "no_complete_seeds", "n_seeds": 0}
    miss_ratios = [r["miss_ratio"] for r in complete]
    n = len(miss_ratios)
    mean_mr = sum(miss_ratios) / n
    if n > 1:
        var_mr = sum((x - mean_mr) ** 2 for x in miss_ratios) / (n - 1)
        std_mr = var_mr ** 0.5
    else:
        std_mr = float("nan")
    return {
        "status": "complete" if n == len(rows) else "partial",
        "scored_requests": complete[0]["scored_requests"],
        "hits": sum(r["hits"] for r in complete) / n,
        "misses": sum(r["misses"] for r in complete) / n,
        "miss_ratio": mean_mr,
        "miss_ratio_std": std_mr,
        "miss_ratio_min": min(miss_ratios),
        "miss_ratio_max": max(miss_ratios),
        "miss_ratio_ci95_lo": mean_mr - 1.96 * std_mr / (n ** 0.5) if n > 1 else float("nan"),
        "miss_ratio_ci95_hi": mean_mr + 1.96 * std_mr / (n ** 0.5) if n > 1 else float("nan"),
        "evictions": sum(r["evictions"] for r in complete) / n,
        "n_seeds": n,
    }


def build_summary_rows(all_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    """Build per (family, capacity, policy) summary rows, relative to LRU.

    Deterministic policies are preserved as single rows; the random policy is
    aggregated across its 20 seeds but the raw per-seed rows are NEVER
    discarded from run_results (see write layer) -- this function only
    produces the derived summary.csv content.
    """
    summary_rows: List[Dict[str, object]] = []
    for family in FAMILIES:
        for capacity in CAPACITIES:
            cell_rows = [r for r in all_rows if r["family"] == family and r["capacity"] == capacity]
            lru_rows = [r for r in cell_rows if r["policy"] == "lru" and r["status"] == "complete"]
            lru_misses = lru_rows[0]["misses"] if lru_rows else None

            for policy in DETERMINISTIC_POLICIES:
                prows = [r for r in cell_rows if r["policy"] == policy]
                if not prows:
                    continue
                r = prows[0]
                if r["status"] != "complete":
                    summary_rows.append(
                        {
                            "family": family, "capacity": capacity, "policy": policy,
                            "scored_split_label": FAMILY_CONFIG[family].scored_split_label,
                            "status": r["status"], "error": r.get("error", ""),
                        }
                    )
                    continue
                summary_rows.append(
                    {
                        "family": family,
                        "capacity": capacity,
                        "policy": policy,
                        "scored_split_label": FAMILY_CONFIG[family].scored_split_label,
                        "scored_requests": r["scored_requests"],
                        "hits": r["hits"],
                        "misses": r["misses"],
                        "miss_ratio": r["miss_ratio"],
                        "evictions": r["evictions"],
                        "relative_miss_diff_vs_lru": (
                            (r["misses"] - lru_misses) / lru_misses
                            if lru_misses else float("nan")
                        ),
                        "absolute_miss_diff_vs_lru": (
                            r["misses"] - lru_misses if lru_misses is not None else float("nan")
                        ),
                        "n_seeds": None,
                        "status": "complete",
                        "error": "",
                    }
                )

            rnd_rows = [r for r in cell_rows if r["policy"] == "random"]
            if rnd_rows:
                agg = aggregate_random_rows(rnd_rows)
                if agg.get("n_seeds", 0) == 0:
                    summary_rows.append(
                        {
                            "family": family, "capacity": capacity, "policy": "random",
                            "scored_split_label": FAMILY_CONFIG[family].scored_split_label,
                            "status": agg["status"], "error": "",
                        }
                    )
                else:
                    summary_rows.append(
                        {
                            "family": family,
                            "capacity": capacity,
                            "policy": "random",
                            "scored_split_label": FAMILY_CONFIG[family].scored_split_label,
                            "scored_requests": agg["scored_requests"],
                            "hits": agg["hits"],
                            "misses": agg["misses"],
                            "miss_ratio": agg["miss_ratio"],
                            "miss_ratio_std": agg["miss_ratio_std"],
                            "miss_ratio_min": agg["miss_ratio_min"],
                            "miss_ratio_max": agg["miss_ratio_max"],
                            "miss_ratio_ci95_lo": agg["miss_ratio_ci95_lo"],
                            "miss_ratio_ci95_hi": agg["miss_ratio_ci95_hi"],
                            "evictions": agg["evictions"],
                            "relative_miss_diff_vs_lru": (
                                (agg["misses"] - lru_misses) / lru_misses
                                if lru_misses else float("nan")
                            ),
                            "absolute_miss_diff_vs_lru": (
                                agg["misses"] - lru_misses if lru_misses is not None else float("nan")
                            ),
                            "n_seeds": agg["n_seeds"],
                            "status": agg["status"],
                            "error": "",
                        }
                    )
    return summary_rows


# ---------------------------------------------------------------------------
# Programmatic validity gates (translated from VALIDITY_GATES.md)
# ---------------------------------------------------------------------------


@dataclass
class GateResult:
    name: str
    passed: bool
    detail: str = ""


def evaluate_gates(plan: List[Execution], rows: List[Dict[str, object]]) -> List[GateResult]:
    """Evaluate every programmatic gate this task requires, over a completed
    (or partially completed) set of raw result rows. Does not mutate rows.
    """
    gates: List[GateResult] = []

    def add(name: str, passed: bool, detail: str = "") -> None:
        gates.append(GateResult(name=name, passed=passed, detail=detail))

    # Structural plan gates (cheap to re-check here too).
    try:
        assert_plan_valid(plan)
        add("plan_composition_exact", True)
    except AssertionError as exc:
        add("plan_composition_exact", False, str(exc))

    try:
        assert_no_learned_policy([r["policy"] for r in rows])
        add("no_learned_policy_in_results", True)
    except RuntimeError as exc:
        add("no_learned_policy_in_results", False, str(exc))

    by_key: Dict[str, Dict[str, object]] = {}
    dup_keys = []
    for r in rows:
        if r["run_key"] in by_key:
            dup_keys.append(r["run_key"])
        by_key[r["run_key"]] = r
    add("no_duplicate_execution_key", len(dup_keys) == 0, f"duplicates: {dup_keys}" if dup_keys else "")

    plan_keys = {e.run_key for e in plan}
    result_keys = {r["run_key"] for r in rows}
    add(
        "every_result_key_is_in_plan",
        result_keys.issubset(plan_keys),
        f"unexpected keys: {sorted(result_keys - plan_keys)}" if not result_keys.issubset(plan_keys) else "",
    )

    complete_rows = [r for r in rows if r["status"] == "complete"]
    failed_rows = [r for r in rows if r["status"] == "failed"]
    other_status = [r for r in rows if r["status"] not in ("complete", "failed")]
    add(
        "every_row_has_distinguishable_status",
        len(other_status) == 0,
        f"rows with unknown status: {[r['run_key'] for r in other_status]}" if other_status else "",
    )

    # Per-cell composition gates (only evaluated over rows present so far --
    # a partial/in-progress run is not expected to satisfy these yet, which
    # is why VALID/INVALID for a run is only asserted at 230/230 completion,
    # see is_run_scientifically_valid()).
    bad_windows = []
    for r in complete_rows:
        expected = tuple(tuple(w) for w in json.loads(r["scored_windows"]))
        canonical = FAMILY_CONFIG[r["family"]].scored_windows
        if expected != canonical:
            bad_windows.append(r["run_key"])
    add("scored_windows_match_authoritative_matrix", len(bad_windows) == 0,
        f"mismatched rows: {bad_windows}" if bad_windows else "")

    # All policies within a family/capacity cell must use identical scored windows.
    mismatched_cells = []
    for family in FAMILIES:
        for capacity in CAPACITIES:
            cell = [r for r in complete_rows if r["family"] == family and r["capacity"] == capacity]
            windows_used = {r["scored_windows"] for r in cell}
            if len(windows_used) > 1:
                mismatched_cells.append(f"{family}/{capacity}")
    add("identical_scored_windows_within_cell", len(mismatched_cells) == 0,
        f"cells with inconsistent windows: {mismatched_cells}" if mismatched_cells else "")

    bad_identity = []
    for r in complete_rows:
        if r["hits"] + r["misses"] != r["scored_requests"]:
            bad_identity.append(r["run_key"])
    add("hits_plus_misses_equals_scored_requests", len(bad_identity) == 0,
        f"rows: {bad_identity}" if bad_identity else "")

    negatives = []
    for r in complete_rows:
        for field_name in ("hits", "misses", "evictions", "scored_requests"):
            v = r.get(field_name)
            if v is not None and v < 0:
                negatives.append((r["run_key"], field_name))
    add("no_negative_counts", len(negatives) == 0, str(negatives) if negatives else "")

    bad_numeric = []
    for r in complete_rows:
        for field_name in ("miss_ratio", "runtime_sec"):
            v = r.get(field_name)
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                bad_numeric.append((r["run_key"], field_name, "not a number"))
                continue
            if fv != fv or fv in (float("inf"), float("-inf")):  # NaN/Inf check
                bad_numeric.append((r["run_key"], field_name, fv))
    add("no_nan_or_inf_numeric_outputs", len(bad_numeric) == 0, str(bad_numeric) if bad_numeric else "")

    bad_ratio = []
    for r in complete_rows:
        mr = r.get("miss_ratio")
        if mr is not None and not (0.0 <= mr <= 1.0):
            bad_ratio.append(r["run_key"])
    add("miss_ratio_in_valid_range", len(bad_ratio) == 0, str(bad_ratio) if bad_ratio else "")

    det_bad = []
    for family in FAMILIES:
        for capacity in CAPACITIES:
            for policy in DETERMINISTIC_POLICIES:
                matching = [
                    r for r in rows
                    if r["family"] == family and r["capacity"] == capacity and r["policy"] == policy
                ]
                if len(matching) > 1:
                    det_bad.append(f"{family}/{capacity}/{policy}: {len(matching)} rows")
    add("deterministic_policy_exactly_one_result_per_cell", len(det_bad) == 0,
        "; ".join(det_bad) if det_bad else "")

    rnd_bad = []
    for family in FAMILIES:
        for capacity in CAPACITIES:
            matching = [
                r for r in rows
                if r["family"] == family and r["capacity"] == capacity and r["policy"] == "random"
            ]
            seeds = sorted(r["seed"] for r in matching)
            if matching and seeds != list(RANDOM_SEEDS):
                rnd_bad.append(f"{family}/{capacity}: seeds {seeds}")
    add("random_policy_seeds_exactly_0_to_19_when_present", len(rnd_bad) == 0,
        "; ".join(rnd_bad) if rnd_bad else "")

    if failed_rows:
        add(
            "failed_rows_present_and_visible",
            True,
            f"{len(failed_rows)} failed row(s) recorded (not silently dropped): "
            f"{[r['run_key'] for r in failed_rows]}",
        )

    return gates


def is_run_scientifically_valid(plan: List[Execution], rows: List[Dict[str, object]]) -> Tuple[bool, List[GateResult]]:
    """A run is VALID iff every gate passes AND all 230 planned executions are
    present with status == 'complete'. Never mark VALID on a partial run.
    """
    gates = evaluate_gates(plan, rows)
    all_gates_pass = all(g.passed for g in gates)
    complete_keys = {r["run_key"] for r in rows if r["status"] == "complete"}
    plan_keys = {e.run_key for e in plan}
    fully_complete = complete_keys == plan_keys
    gates.append(
        GateResult(
            name="all_230_planned_executions_complete",
            passed=fully_complete,
            detail=f"{len(complete_keys)}/{len(plan_keys)} complete"
            if not fully_complete else "",
        )
    )
    return (all_gates_pass and fully_complete), gates


# ---------------------------------------------------------------------------
# Resume-safe result storage: one JSON line per completed/failed execution,
# appended with an fsync'd write-then-rename-free append (append is atomic
# at the OS level for O_APPEND writes under PIPE_BUF-sized lines, which every
# row here is). This is intentionally simple: Tier 1 is small (230 rows),
# so a single append-only JSONL file is sufficient durable provenance
# without building a distributed or transactional execution engine.
# ---------------------------------------------------------------------------

RESULTS_JSONL_NAME = "run_results.jsonl"


def append_result_row(run_dir: Path, row: Dict[str, object]) -> None:
    line = json.dumps(row, sort_keys=True)
    path = run_dir / RESULTS_JSONL_NAME
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def load_result_rows(run_dir: Path) -> List[Dict[str, object]]:
    """Load previously recorded rows, skipping (and reporting) any malformed
    line rather than silently treating it as valid data. The LAST row for a
    given run_key wins (in case of interrupted+re-appended rows), but only if
    that last row itself is well-formed JSON with a recognizable status.
    """
    path = run_dir / RESULTS_JSONL_NAME
    if not path.exists():
        return []
    by_key: Dict[str, Dict[str, object]] = {}
    malformed_lines = 0
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                malformed_lines += 1
                continue
            if "run_key" not in row or "status" not in row or row["status"] not in ("complete", "failed"):
                malformed_lines += 1
                continue
            by_key[row["run_key"]] = row
    if malformed_lines:
        sys.stderr.write(
            f"WARNING: {malformed_lines} malformed/partial line(s) in {path} were "
            "ignored (not treated as complete).\n"
        )
    return list(by_key.values())


def keys_to_skip_on_resume(run_dir: Path, retry_failed: bool = False) -> set:
    """Run_keys to NOT (re-)execute on a resumed run.

    Without retry_failed: both 'complete' AND 'failed' keys are skipped --
    a previously failed execution stays failed and visible; it is never
    silently retried just because --resume was passed. Only when
    retry_failed=True (an explicit, separate decision) are 'failed' keys
    excluded from this skip set, making them eligible to run again.
    """
    rows = load_result_rows(run_dir)
    if retry_failed:
        return {r["run_key"] for r in rows if r["status"] == "complete"}
    return {r["run_key"] for r in rows if r["status"] in ("complete", "failed")}


# ---------------------------------------------------------------------------
# Provenance: LAFC-Evict side
# ---------------------------------------------------------------------------


def _run_git(repo: Path, args: List[str]) -> str:
    out = subprocess.run(
        ["git", "-C", str(repo)] + args,
        capture_output=True, text=True, check=False,
    )
    return out.stdout.strip()


def lafc_evict_provenance() -> Dict[str, object]:
    repo = LAFC_EVICT_REPO_ROOT
    return {
        "path": str(repo),
        "branch": _run_git(repo, ["branch", "--show-current"]),
        "head": _run_git(repo, ["rev-parse", "HEAD"]),
        "git_status_short": _run_git(repo, ["status", "--short"]),
        "harness_script_sha256": sha256_file(THIS_FILE),
    }


def simulator_provenance(save_dir: Optional[Path] = None) -> Dict[str, object]:
    """Read-only introspection of the secondary simulator repository.

    Never rejects a run merely because unrelated files are dirty. The gate
    that matters for Tier 1 is that the specific dependency files Tier 1
    imports are unmodified relative to the expected HEAD; the rest of the
    repository's (expected, pre-existing) dirtiness is recorded for
    provenance but is not itself a failure condition.
    """
    repo = AUGMENTED_CACHING_REPO
    actual_branch = _run_git(repo, ["branch", "--show-current"])
    actual_head = _run_git(repo, ["rev-parse", "HEAD"])
    porcelain = _run_git(repo, ["status", "--porcelain"])

    dep_status: Dict[str, Dict[str, object]] = {}
    for relpath in SIMULATOR_DEPENDENCY_FILES:
        full = repo / relpath
        file_status = _run_git(repo, ["status", "--porcelain", "--", relpath])
        dep_status[relpath] = {
            "exists": full.exists(),
            "sha256": sha256_file(full) if full.exists() else None,
            "clean_relative_to_head": file_status == "",
            "git_status_line": file_status,
        }

    untracked = [
        line[3:] for line in porcelain.splitlines() if line.startswith("??")
    ]
    untracked_hashes = {}
    for name in untracked:
        p = repo / name
        try:
            if p.is_file():
                untracked_hashes[name] = sha256_file(p)
            else:
                untracked_hashes[name] = None
        except OSError as exc:
            untracked_hashes[name] = f"UNREADABLE: {exc}"

    tracked_diff = subprocess.run(
        ["git", "-C", str(repo), "diff"], capture_output=True, text=True, check=False
    ).stdout

    diff_record: Dict[str, object] = {"saved": False}
    if save_dir is not None and tracked_diff:
        save_dir.mkdir(parents=True, exist_ok=True)
        diff_path = save_dir / "augmented_caching_working_tree.diff"
        diff_path.write_text(tracked_diff, encoding="utf-8")
        diff_record = {
            "saved": True,
            "path": str(diff_path),
            "sha256": sha256_file(diff_path),
            "bytes": len(tracked_diff.encode("utf-8")),
        }
    elif tracked_diff:
        diff_record = {
            "saved": False,
            "reason": "no save_dir provided",
            "sha256": hashlib.sha256(tracked_diff.encode("utf-8")).hexdigest(),
            "bytes": len(tracked_diff.encode("utf-8")),
        }

    return {
        "path": str(repo),
        "expected_branch": EXPECTED_SIMULATOR_BRANCH,
        "actual_branch": actual_branch,
        "branch_matches_expected": actual_branch == EXPECTED_SIMULATOR_BRANCH,
        "expected_head": EXPECTED_SIMULATOR_HEAD,
        "actual_head": actual_head,
        "head_matches_expected": actual_head == EXPECTED_SIMULATOR_HEAD,
        "git_status_porcelain_full": porcelain,
        "dependency_file_status": dep_status,
        "all_dependency_files_clean": all(v["clean_relative_to_head"] for v in dep_status.values()),
        "untracked_file_names": untracked,
        "untracked_file_sha256": untracked_hashes,
        "tracked_working_tree_diff": diff_record,
        "note": (
            "This repository is intentionally, pre-existingly dirty overall. Only "
            "dependency_file_status entries gate Tier-1 validity; general dirtiness "
            "is recorded here for provenance and is never a rejection reason on its "
            "own, and this harness never cleans/resets/stashes/commits in this "
            "repository."
        ),
    }


def input_trace_provenance() -> Dict[str, Dict[str, object]]:
    result = {}
    for family, cfg in FAMILY_CONFIG.items():
        path = PROCESSED_TRACE_DIR / cfg.trace_relpath
        exists = path.exists()
        actual_sha = sha256_file(path) if exists else None
        result[family] = {
            "trace_name": cfg.trace_name,
            "path": str(path),
            "exists": exists,
            "size_bytes": path.stat().st_size if exists else None,
            "expected_sha256": cfg.expected_sha256,
            "actual_sha256": actual_sha,
            "sha256_matches": (actual_sha == cfg.expected_sha256) if exists else False,
            "scored_split_label": cfg.scored_split_label,
            "scored_windows": list(cfg.scored_windows),
            "evidence_label": cfg.evidence_label,
            "split_caveat": cfg.split_caveat,
            "learned_policy_classification_informational_only": cfg.learned_policy_classification,
        }
    return result


def environment_provenance() -> Dict[str, object]:
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "hostname": platform.node(),
        "user": getpass.getuser(),
        "pid": os.getpid(),
    }


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------


def run_preflight() -> Tuple[bool, Dict[str, object]]:
    """Non-destructive preflight check. Never executes a real closed-loop
    replay. Returns (ok, report).
    """
    report: Dict[str, object] = {}
    gate_results: List[Tuple[str, bool, str]] = []

    def gate(name: str, passed: bool, detail: str = "") -> None:
        gate_results.append((name, passed, detail))

    plan = build_plan()
    try:
        assert_plan_valid(plan)
        gate("plan_exact_230_and_composition", True)
    except AssertionError as exc:
        gate("plan_exact_230_and_composition", False, str(exc))

    try:
        assert_no_learned_policy(list(POLICIES))
        gate("no_learned_policy_in_static_policy_list", True)
    except RuntimeError as exc:
        gate("no_learned_policy_in_static_policy_list", False, str(exc))

    trace_prov = input_trace_provenance()
    all_traces_exist = all(v["exists"] for v in trace_prov.values())
    gate("all_trace_files_exist", all_traces_exist,
         "" if all_traces_exist else str({k: v["path"] for k, v in trace_prov.items() if not v["exists"]}))

    hash_mismatches = {k: (v["expected_sha256"], v["actual_sha256"])
                        for k, v in trace_prov.items() if v["exists"] and not v["sha256_matches"]}
    gate("all_trace_sha256_match_design", len(hash_mismatches) == 0, str(hash_mismatches))

    sim_prov = simulator_provenance(save_dir=None)
    gate("simulator_branch_matches_expected", sim_prov["branch_matches_expected"],
         f"actual={sim_prov['actual_branch']!r} expected={sim_prov['expected_branch']!r}")
    gate("simulator_head_matches_expected", sim_prov["head_matches_expected"],
         f"actual={sim_prov['actual_head']!r} expected={sim_prov['expected_head']!r}")
    gate("simulator_dependency_files_exist", all(v["exists"] for v in sim_prov["dependency_file_status"].values()))
    gate("simulator_dependency_files_clean_relative_to_head", sim_prov["all_dependency_files_clean"],
         str({k: v["git_status_line"] for k, v in sim_prov["dependency_file_status"].items()
              if not v["clean_relative_to_head"]}))

    # Split/window self-consistency: confirm the in-code constants equal the
    # exact values transcribed from MATRIX.md (protects against future
    # accidental edits to this file diverging from the approved design).
    expected_windows = {
        "cloudphysics": ((16384, 20479), (20480, 24575)),
        "metacdn": ((0, 4095), (24576, 32767), (36864, 45055)),
        "metakv": ((0, 4095),),
        "twemcache": ((32768, 36863), (40960, 45055)),
        "wiki2018": ((24576, 28671),),
    }
    window_mismatches = {
        f: FAMILY_CONFIG[f].scored_windows for f in FAMILIES
        if FAMILY_CONFIG[f].scored_windows != expected_windows[f]
    }
    gate("scored_windows_match_matrix_md", len(window_mismatches) == 0, str(window_mismatches))

    expected_split_labels = {
        "cloudphysics": "test", "metacdn": "validation", "metakv": "test",
        "twemcache": "test", "wiki2018": "test",
    }
    label_mismatches = {
        f: FAMILY_CONFIG[f].scored_split_label for f in FAMILIES
        if FAMILY_CONFIG[f].scored_split_label != expected_split_labels[f]
    }
    gate("split_labels_match_matrix_md", len(label_mismatches) == 0, str(label_mismatches))

    try:
        _import_simulator_modules()
        gate("simulator_modules_importable", True)
    except Exception as exc:  # noqa: BLE001
        gate("simulator_modules_importable", False, f"{type(exc).__name__}: {exc}")

    # Learned-policy safety is enforced by name (assert_no_learned_policy),
    # not by sys.modules membership -- see the NOTE in
    # _import_simulator_modules for why a module-import-based gate here would
    # be both unavoidable-to-fail and not actually meaningful. Re-verify the
    # name-based guard explicitly as a preflight gate instead:
    try:
        assert_no_learned_policy(list(POLICIES))
        build_policy_rejects_learned = False
        try:
            build_policy("evict_value_v1")
            build_policy_rejects_learned = False
        except RuntimeError:
            build_policy_rejects_learned = True
        gate("build_policy_rejects_learned_policy_name", build_policy_rejects_learned)
    except RuntimeError as exc:
        gate("build_policy_rejects_learned_policy_name", False, str(exc))

    ok = all(passed for _, passed, _ in gate_results)

    report["timestamp_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    report["plan_summary"] = plan_summary(plan)
    report["trace_provenance"] = trace_prov
    report["simulator_provenance"] = sim_prov
    report["environment"] = environment_provenance()
    report["gates"] = [{"name": n, "passed": p, "detail": d} for n, p, d in gate_results]
    report["preflight_ok"] = ok
    report["production_run_started"] = False
    return ok, report


# ---------------------------------------------------------------------------
# Production run (IMPLEMENTED but never invoked by this task; a future
# explicitly-approved launch is the only intended caller of run_production()).
# ---------------------------------------------------------------------------


def make_run_id() -> str:
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    short_commit = _run_git(LAFC_EVICT_REPO_ROOT, ["rev-parse", "--short=12", "HEAD"]) or "unknown"
    return f"{ts}_{short_commit}"


def outputs_root() -> Path:
    return TIER1_DIR / "outputs"


def new_run_dir(run_id: Optional[str] = None) -> Path:
    run_id = run_id or make_run_id()
    run_dir = outputs_root() / run_id
    if run_dir.exists() and any(run_dir.iterdir()):
        raise FileExistsError(
            f"Refusing to reuse non-empty run directory {run_dir}. Run directories are "
            "immutable per invocation; use --resume with an existing --run-dir to "
            "continue an incomplete run instead of creating a new one."
        )
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def setup_logging(log_path: Path):
    import logging

    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("tier1")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


def run_production(
    run_dir: Path,
    resume: bool = False,
    retry_failed: bool = False,
    command_line: Optional[str] = None,
) -> Dict[str, object]:
    """Execute the approved 230-run Tier-1 plan.

    This function is fully implemented so that a future, explicitly-approved
    launch has a real entry point, but it is NEVER called during this
    implementation/validation task. Callers outside tests must go through
    scripts/run_tier1.py's --run mode, which requires an explicit flag.

    Resume semantics:
      - Without --resume: run_dir must be new/empty (see new_run_dir()).
      - With --resume: run_keys already recorded with status=='complete' are
        skipped. Keys recorded as 'failed' are skipped UNLESS retry_failed is
        also set (an explicit, separate decision -- never automatic).
    """
    log_path = run_dir / "tier1_run.log"
    logger = setup_logging(log_path)

    plan = build_plan()
    assert_plan_valid(plan)

    provenance_path = run_dir / "provenance.json"
    start_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    provenance = {
        "run_id": run_dir.name,
        "start_time_utc": start_time,
        "command_line": command_line or " ".join(sys.argv),
        "lafc_evict": lafc_evict_provenance(),
        "simulator": simulator_provenance(save_dir=run_dir),
        "inputs": input_trace_provenance(),
        "environment": environment_provenance(),
        "experiment_plan_summary": plan_summary(plan),
        "resume": resume,
        "retry_failed": retry_failed,
        "run_state": "started",
    }
    provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8")
    logger.info("Tier-1 production run started: run_id=%s", run_dir.name)

    if not provenance["simulator"]["all_dependency_files_clean"]:
        raise RuntimeError(
            "Refusing to start: one or more simulator dependency files are not clean "
            "relative to the expected HEAD. See provenance.json:simulator."
        )
    mismatched = {
        k: v for k, v in provenance["inputs"].items() if v["exists"] and not v["sha256_matches"]
    }
    if mismatched:
        raise RuntimeError(f"Refusing to start: trace SHA256 mismatch(es): {mismatched}")

    skip_keys = set()
    if resume:
        skip_keys = keys_to_skip_on_resume(run_dir, retry_failed=retry_failed)
        logger.info(
            "Resuming: %d execution(s) already complete%s and will be skipped.",
            len(skip_keys),
            "" if retry_failed else " or previously failed (pass --retry-failed to retry those)",
        )
    else:
        existing = load_result_rows(run_dir)
        if existing:
            raise RuntimeError(
                f"run_dir {run_dir} already has {len(existing)} recorded result(s) but "
                "--resume was not set. Refusing to silently overwrite or duplicate."
            )

    # Group by (family, capacity) so each trace is loaded once and reused
    # across the policies that share it (mirrors the pilot's per-family loop).
    trace_cache: Dict[str, object] = {}
    for execution in plan:
        if execution.run_key in skip_keys:
            continue
        cfg = FAMILY_CONFIG[execution.family]
        if execution.family not in trace_cache:
            trace_path = PROCESSED_TRACE_DIR / cfg.trace_relpath
            requests, pages = load_processed_trace(trace_path)
            if len(requests) != 50000:
                row = {
                    "run_key": execution.run_key, "family": execution.family,
                    "capacity": execution.capacity, "policy": execution.policy,
                    "seed": execution.seed, "status": "failed",
                    "error": f"expected 50000 requests, got {len(requests)}",
                    "scored_split_label": cfg.scored_split_label,
                    "scored_windows": json.dumps(list(cfg.scored_windows)),
                    "scored_requests": None, "hits": None, "misses": None,
                    "miss_ratio": None, "evictions": None, "full_trace_requests": len(requests),
                    "full_trace_hits": None, "full_trace_misses": None, "runtime_sec": 0.0,
                }
                append_result_row(run_dir, row)
                logger.error("Trace length check FAILED for %s: %s", execution.family, row["error"])
                continue
            trace_cache[execution.family] = (requests, pages)
        requests, pages = trace_cache[execution.family]

        logger.info("Running %s", execution.run_key)
        row = run_one_execution(execution, requests, pages, cfg.scored_windows)
        append_result_row(run_dir, row)
        if row["status"] == "failed":
            logger.error("Execution FAILED: %s -- %s", execution.run_key, row["error"])
        else:
            logger.info(
                "Execution complete: %s scored_requests=%s miss_ratio=%.6f runtime_sec=%.4f",
                execution.run_key, row["scored_requests"], row["miss_ratio"], row["runtime_sec"],
            )

    all_rows = load_result_rows(run_dir)
    write_csv_outputs(run_dir, all_rows)

    valid, gates = is_run_scientifically_valid(plan, all_rows)
    sanity = {
        "gates": [{"name": g.name, "passed": g.passed, "detail": g.detail} for g in gates],
        "run_valid": valid,
        "n_complete": len([r for r in all_rows if r["status"] == "complete"]),
        "n_failed": len([r for r in all_rows if r["status"] == "failed"]),
        "n_planned": len(plan),
    }
    (run_dir / "sanity_checks.json").write_text(json.dumps(sanity, indent=2, sort_keys=True), encoding="utf-8")

    end_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    provenance["end_time_utc"] = end_time
    provenance["run_state"] = "complete" if valid else "complete_with_failures_or_incomplete"
    provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8")

    manifest = {
        "run_id": run_dir.name,
        "run_valid": valid,
        "n_planned": len(plan),
        "n_complete": sanity["n_complete"],
        "n_failed": sanity["n_failed"],
        "output_files": {},
    }
    for name in ("run_results.csv", "summary.csv", "sanity_checks.json", "provenance.json", "run_results.jsonl"):
        p = run_dir / name
        if p.exists():
            manifest["output_files"][name] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    logger.info("Tier-1 production run finished: run_valid=%s", valid)
    return manifest


def write_csv_outputs(run_dir: Path, all_rows: List[Dict[str, object]]) -> None:
    with open(run_dir / "run_results.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=RAW_ROW_FIELDS)
        writer.writeheader()
        for row in sorted(all_rows, key=lambda r: r["run_key"]):
            writer.writerow({k: row.get(k) for k in RAW_ROW_FIELDS})

    summary_rows = build_summary_rows(all_rows)
    if summary_rows:
        fieldnames = sorted({k for row in summary_rows for k in row.keys()})
        with open(run_dir / "summary.csv", "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for row in summary_rows:
                writer.writerow(row)


# ---------------------------------------------------------------------------
# Validate mode: re-check a completed (or partial) run directory without
# re-executing anything.
# ---------------------------------------------------------------------------


def run_validate(run_dir: Path) -> Tuple[bool, Dict[str, object]]:
    plan = build_plan()
    rows = load_result_rows(run_dir)
    valid, gates = is_run_scientifically_valid(plan, rows)
    report = {
        "run_dir": str(run_dir),
        "n_rows_loaded": len(rows),
        "n_planned": len(plan),
        "gates": [{"name": g.name, "passed": g.passed, "detail": g.detail} for g in gates],
        "run_valid": valid,
    }
    manifest_path = run_dir / "run_manifest.json"
    if manifest_path.exists():
        report["existing_manifest"] = json.loads(manifest_path.read_text(encoding="utf-8"))
    return valid, report
