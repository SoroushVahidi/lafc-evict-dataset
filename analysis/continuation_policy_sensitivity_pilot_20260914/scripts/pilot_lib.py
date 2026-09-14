"""Shared library for the continuation-policy-sensitivity correctness pilot.

Imports the generalized rollout module from the SECONDARY repo's isolated
pilot worktree (which carries the additive MRU/random support), never from
the dirty main checkout, and never the canonical
evict_value_wulver_v1.py/evict_value_dataset_v1.py generator files for
anything other than a read-only equivalence comparison.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

AUGMENTED_CACHING_PILOT_SRC = (
    "/home/soroush/projects/augmented-caching/repo/.claude/worktrees/"
    "continuation-sensitivity-pilot-20260914/src"
)
if AUGMENTED_CACHING_PILOT_SRC not in sys.path:
    sys.path.insert(0, AUGMENTED_CACHING_PILOT_SRC)

from lafc.evict_value_dataset_v1 import _simulate_lru_misses  # noqa: E402  (read-only, canonical reference)
from lafc.evict_value_v2_rollout import (  # noqa: E402
    EvictValueV2RolloutConfig,
    build_rollout_candidate_rows_v2,
    simulate_rollout_misses,
)
from lafc.simulator.request_trace import build_requests_from_lists  # noqa: E402

PROCESSED_TRACE_DIR = Path("/home/soroush/projects/augmented-caching/repo/data/processed")

# Verbatim from the four pre-registered pilot cells
# (analysis/continuation_policy_sensitivity_design_20260914/DESIGN.md Section 10).
PILOT_CELLS: List[Tuple[str, int]] = [
    ("twemcache", 32),
    ("cloudphysics", 32),
    ("metakv", 128),
    ("wiki2018", 32),
]
PILOT_HORIZON = 16
DECISIONS_PER_CELL = 20
PILOT_SAMPLING_SEED = 20260914

LEARNED_POLICY_NAMES = frozenset({"evict_value_v1", "evict_value_v1_guarded"})


def assert_no_learned_policy(policy_names: Sequence[str]) -> None:
    bad = sorted(set(policy_names) & LEARNED_POLICY_NAMES)
    if bad:
        raise RuntimeError(f"Continuation-sensitivity pilot fail-fast guard: learned policy name(s) {bad} not permitted here.")


def load_trace(family: str):
    path = PROCESSED_TRACE_DIR / family / "trace.jsonl"
    item_ids: List[str] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            item_ids.append(str(rec["item_id"]))
    assert len(item_ids) == 50000, f"{family}: expected 50000 requests, got {len(item_ids)}"
    requests, pages = build_requests_from_lists(item_ids)
    return requests, pages, item_ids


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def generate_lru_baseline_rows(family: str, capacity: int, horizon: int, requests=None) -> List[Dict[str, object]]:
    """Assert-guarded: builds the LRU-continuation candidate rows for a full
    trace at one capacity/horizon, using ONLY policy='lru' -- this is the
    baseline-side information the pilot's sampling is allowed to use.

    NOTE: uses build_rollout_candidate_rows_v2, which also computes full ML
    feature columns per candidate -- correct but needlessly slow for pure
    sampling purposes on a 50k-request trace at high candidate counts. Use
    generate_lru_baseline_decision_summaries() instead for sampling; this
    function is retained only where the feature columns are actually needed.
    """
    assert_no_learned_policy(["lru"])
    if requests is None:
        requests, _pages, _ids = load_trace(family)
    cfg = EvictValueV2RolloutConfig(horizons=(horizon,), reference_policy="lru")
    rows = build_rollout_candidate_rows_v2(
        requests=requests, capacity=capacity, trace_name=family, trace_family=family, cfg=cfg,
    )
    return rows


def enumerate_decision_positions(family: str, capacity: int):
    """Cheap, O(n) enumeration of every eviction-decision request index
    under pure LRU replay -- no rollout/regret computation at all. Used as
    stage 1 of a two-stage sampling design: enumerating positions is nearly
    free; computing rollout regret per candidate is the expensive part
    (especially at capacity=128 with tens of thousands of decisions in a
    50,000-request trace), so stage 2 only computes it for a random
    subsample of these positions, not the full population.
    """
    import collections

    requests, _pages, _ids = load_trace(family)
    order: "collections.OrderedDict" = collections.OrderedDict()
    positions = []
    for t, req in enumerate(requests):
        pid = req.page_id
        if pid in order:
            order.move_to_end(pid)
            continue
        if len(order) < capacity:
            order[pid] = None
            continue
        candidates = list(order.keys())
        positions.append(t)
        lru_victim = candidates[0]
        order.pop(lru_victim)
        order[pid] = None
    return positions, requests


def summarize_decision_at(requests, capacity: int, t: int, horizon: int, family: str) -> Dict[str, object]:
    """Compute the lean (feature-free) baseline-LRU summary for exactly one
    decision, using ONLY simulate_rollout_misses (reference_policy='lru').
    """
    assert_no_learned_policy(["lru"])
    candidates, pid = reconstruct_candidates_at_t(requests, capacity, t)
    future = requests[t + 1 : t + 1 + horizon]
    losses = {}
    for candidate in candidates:
        forced_cache = [p for p in candidates if p != candidate] + [pid]
        losses[candidate] = simulate_rollout_misses(
            cache_pages=forced_cache, future_reqs=future, capacity=capacity, reference_policy="lru",
        )
    best = min(losses.values())
    regret_max = max(v - best for v in losses.values())
    return {
        "decision_id": f"{family}|c{capacity}|t{t}|h{horizon}",
        "request_t": t,
        "candidate_count": len(candidates),
        "all_tied": regret_max == 0,
        "regret_max": regret_max,
    }


def generate_lru_baseline_decision_summaries(
    family: str, capacity: int, horizon: int, subsample_size: Optional[int] = None, subsample_seed: int = 0,
) -> List[Dict[str, object]]:
    """Two-stage lean enumeration: cheaply enumerate all decision positions,
    then compute the (expensive) rollout-regret summary only for a random
    subsample of up to `subsample_size` of them (all of them if
    subsample_size is None or exceeds the population). Documented as a
    pragmatic approximation appropriate for a small correctness pilot, not
    the full 5,000-decision study (which should use the full population or
    a much larger, separately justified subsample).
    """
    import random as _random

    positions, requests = enumerate_decision_positions(family, capacity)
    if subsample_size is not None and subsample_size < len(positions):
        rng = _random.Random(f"{subsample_seed}|{family}|{capacity}|subsample")
        positions = rng.sample(positions, subsample_size)
        positions.sort()

    return [summarize_decision_at(requests, capacity, t, horizon, family) for t in positions]


def group_by_decision(rows: Sequence[Dict[str, object]]) -> Dict[str, List[Dict[str, object]]]:
    grouped: Dict[str, List[Dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(str(row["decision_id"]), []).append(row)
    return grouped


def decision_is_all_tied(items: Sequence[Dict[str, object]]) -> bool:
    return all(float(r["rollout_regret_h"]) == 0.0 for r in items)


def reconstruct_candidates_at_t(requests, capacity: int, t: int):
    """Replay pure LRU forward to request index t and return the exact
    resident candidate set immediately before the decision at t, plus the
    requesting page id. Deterministic, capacity-generic, no feature
    computation (cheaper than build_rollout_candidate_rows_v2 for this
    reconstruction-only purpose).
    """
    import collections

    order: "collections.OrderedDict" = collections.OrderedDict()
    for tt in range(t + 1):
        pid = requests[tt].page_id
        if pid in order:
            order.move_to_end(pid)
            continue
        if len(order) < capacity:
            order[pid] = None
            continue
        candidates_here = list(order.keys())
        if tt == t:
            return candidates_here, pid
        victim = candidates_here[0]
        order.pop(victim)
        order[pid] = None
    raise AssertionError(f"request index {t} is not an eviction decision at capacity {capacity}")
