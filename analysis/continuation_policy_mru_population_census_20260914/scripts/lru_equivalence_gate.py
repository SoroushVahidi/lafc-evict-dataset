"""Blocking LRU-equivalence gate for the census, covering all 5 families x
all 4 capacities (including 64 and 256, never previously audited) x all 3
horizons, on a random sample of decisions per (family, capacity).
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from census_lib import (
    CAPACITIES, FAMILIES, HORIZONS, _simulate_lru_misses,
    enumerate_decision_positions, reconstruct_candidates_at_t, simulate_rollout_misses,
)

CENSUS_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = CENSUS_DIR / "outputs"
DECISIONS_PER_CELL = 25
SEED = 20260914


def compare_one(candidates, pid, requests, t, capacity, horizon):
    future = requests[t + 1 : t + 1 + horizon]
    n = 0
    mismatches = []
    max_diff = 0
    for candidate in candidates:
        forced_cache = [p for p in candidates if p != candidate] + [pid]
        canonical = _simulate_lru_misses(forced_cache, future, capacity=capacity)
        generalized = simulate_rollout_misses(cache_pages=forced_cache, future_reqs=future, capacity=capacity, reference_policy="lru")
        n += 1
        diff = abs(canonical - generalized)
        max_diff = max(max_diff, diff)
        if canonical != generalized:
            mismatches.append({"t": t, "candidate": candidate, "canonical": canonical, "generalized": generalized})
    return n, mismatches, max_diff


def main():
    rng = random.Random(SEED)
    total = 0
    all_mismatches = []
    max_diff_overall = 0

    for family in FAMILIES:
        for capacity in CAPACITIES:
            positions, requests = enumerate_decision_positions(family, capacity)
            sample = rng.sample(positions, min(DECISIONS_PER_CELL, len(positions)))
            for t in sample:
                candidates, pid = reconstruct_candidates_at_t(requests, capacity, t)
                for horizon in HORIZONS:
                    n, mism, max_diff = compare_one(candidates, pid, requests, t, capacity, horizon)
                    for m in mism:
                        m.update({"family": family, "capacity": capacity, "horizon": horizon})
                    total += n
                    all_mismatches.extend(mism)
                    max_diff_overall = max(max_diff_overall, max_diff)
            print(f"{family}/{capacity}: audited {len(sample)} decisions x {len(HORIZONS)} horizons")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = {
        "total_candidate_horizon_comparisons": total, "n_mismatches": len(all_mismatches),
        "mismatches": all_mismatches, "max_abs_difference": max_diff_overall,
        "coverage": f"{len(FAMILIES)} families x {len(CAPACITIES)} capacities (incl. 64,256) x {len(HORIZONS)} horizons x {DECISIONS_PER_CELL} random decisions/cell",
        "gate": "LRU_EQUIVALENCE_MISMATCHES", "gate_value": len(all_mismatches), "gate_pass": len(all_mismatches) == 0,
    }
    (OUT_DIR / "prelaunch_lru_equivalence_result.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print(f"\nTotal comparisons: {total}")
    print(f"LRU_EQUIVALENCE_MISMATCHES = {len(all_mismatches)}")
    print(f"Max absolute difference: {max_diff_overall}")
    if all_mismatches:
        print("GATE: FAIL -- DO NOT LAUNCH")
        raise SystemExit(1)
    print("GATE: PASS")


if __name__ == "__main__":
    main()
