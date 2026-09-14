"""Blocking gate: candidate-by-candidate exact-equality check between the
NEW generalized rollout path (continuation='lru') and the UNTOUCHED canonical
_simulate_lru_misses(), on an independently fixed audit sample.

Covers: the 80 frozen pilot decisions (all 4 regimes, tied + discriminative)
PLUS an additional broadening sample spanning all 5 families, both
capacities, and all 3 horizons -- never restricted to just H=16.

This never modifies, and never calls with mutation, the canonical generator
files (evict_value_wulver_v1.py / evict_value_dataset_v1.py) -- it only
imports _simulate_lru_misses read-only for direct comparison.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from pilot_lib import (
    PILOT_CELLS,
    _simulate_lru_misses,
    load_trace,
    reconstruct_candidates_at_t,
    sha256_text,
    simulate_rollout_misses,
)

PILOT_DIR = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PILOT_DIR / "PILOT_MANIFEST.json"
OUT_PATH = PILOT_DIR / "outputs"

ALL_FAMILIES = ("cloudphysics", "metacdn", "metakv", "twemcache", "wiki2018")
ALL_CAPACITIES = (32, 128)
ALL_HORIZONS = (4, 8, 16)
BROADENING_SAMPLE_SEED = 20260914  # same convention as pilot sampling; distinct RNG stream by salted key


def _decisions_from_trace(family: str, capacity: int):
    """Enumerate every eviction decision's (t, candidates) using a plain LRU
    replay (no feature computation needed here, so this is cheaper than
    build_rollout_candidate_rows_v2)."""
    import collections
    requests, _pages, _ids = load_trace(family)
    order: "collections.OrderedDict" = collections.OrderedDict()
    decisions = []
    for t, req in enumerate(requests):
        pid = req.page_id
        if pid in order:
            order.move_to_end(pid)
            continue
        if len(order) < capacity:
            order[pid] = None
            continue
        candidates = list(order.keys())
        decisions.append((t, candidates, pid, requests))
        lru_victim = candidates[0]
        order.pop(lru_victim)
        order[pid] = None
    return decisions


def compare_one(candidates, pid, requests, t, capacity, horizon):
    future = requests[t + 1 : t + 1 + horizon]
    mismatches = []
    n_compared = 0
    max_abs_diff = 0
    for candidate in candidates:
        forced_cache = [p for p in candidates if p != candidate] + [pid]
        canonical = _simulate_lru_misses(forced_cache, future, capacity=capacity)
        generalized = simulate_rollout_misses(
            cache_pages=forced_cache, future_reqs=future, capacity=capacity, reference_policy="lru",
        )
        n_compared += 1
        diff = abs(canonical - generalized)
        max_abs_diff = max(max_abs_diff, diff)
        if canonical != generalized:
            mismatches.append({
                "family": None, "t": t, "candidate": candidate,
                "canonical": canonical, "generalized": generalized,
            })
    return n_compared, mismatches, max_abs_diff


def main():
    manifest = json.loads(MANIFEST_PATH.read_text())
    pilot_decisions = manifest["decisions"]

    total_compared = 0
    all_mismatches = []
    max_abs_diff_overall = 0

    print("=== Auditing the 80 frozen pilot decisions (H=16 only, as pre-registered) ===")
    trace_cache = {}
    for d in pilot_decisions:
        family, capacity, t, horizon = d["family"], d["capacity"], d["request_t"], d["horizon"]
        key = (family, capacity)
        if key not in trace_cache:
            requests, _pages, _ids = load_trace(family)
            trace_cache[key] = requests
        requests = trace_cache[key]

        candidates, pid = reconstruct_candidates_at_t(requests, capacity, t)
        n_cmp, mism, max_diff = compare_one(candidates, pid, requests, t, capacity, horizon)
        for m in mism:
            m["family"] = family
            m["decision_id"] = d["decision_id"]
        total_compared += n_cmp
        all_mismatches.extend(mism)
        max_abs_diff_overall = max(max_abs_diff_overall, max_diff)

    print(f"Pilot-decision comparisons: {total_compared}, mismatches: {len(all_mismatches)}")

    print("\n=== Broadening audit: all 5 families x 2 capacities x 3 horizons, "
          "20 additional random decisions per (family, capacity) ===")
    rng = random.Random(BROADENING_SAMPLE_SEED)
    for family in ALL_FAMILIES:
        for capacity in ALL_CAPACITIES:
            decisions = _decisions_from_trace(family, capacity)
            if not decisions:
                continue
            sample = rng.sample(decisions, min(20, len(decisions)))
            for t, candidates, pid, requests in sample:
                for horizon in ALL_HORIZONS:
                    n_cmp, mism, max_diff = compare_one(candidates, pid, requests, t, capacity, horizon)
                    for m in mism:
                        m["family"] = family
                    total_compared += n_cmp
                    all_mismatches.extend(mism)
                    max_abs_diff_overall = max(max_abs_diff_overall, max_diff)

    OUT_PATH.mkdir(parents=True, exist_ok=True)
    result = {
        "total_candidate_horizon_comparisons": total_compared,
        "mismatches": all_mismatches,
        "n_mismatches": len(all_mismatches),
        "max_abs_difference": max_abs_diff_overall,
        "gate": "LRU_EQUIVALENCE_MISMATCHES",
        "gate_value": len(all_mismatches),
        "gate_pass": len(all_mismatches) == 0,
    }
    (OUT_PATH / "lru_equivalence_gate_result.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print(f"\nTotal candidate/horizon comparisons: {total_compared}")
    print(f"LRU_EQUIVALENCE_MISMATCHES = {len(all_mismatches)}")
    print(f"Max absolute difference: {max_abs_diff_overall}")
    if all_mismatches:
        print("GATE: FAIL -- STOP. Do not proceed to MRU/random pilot.")
        for m in all_mismatches[:10]:
            print(" ", m)
        raise SystemExit(1)
    print("GATE: PASS")


if __name__ == "__main__":
    main()
