"""Pre-launch blocking LRU-equivalence recheck for the FULL experiment.

Audits every one of the 5,500 frozen decisions (5,000 primary + 500
diagnostic) at all 3 horizons: compares the generalized rollout path
(reference_policy='lru') against the untouched canonical
_simulate_lru_misses(), candidate-by-candidate. This is a broader,
deterministic superset of the pilot's own audit (which covered only the 80
pilot decisions at H=16 plus a separate random broadening sample) --
here every frozen full-experiment decision is covered at every horizon
actually used in the full run, not a subsample.
"""
from __future__ import annotations

import json
from pathlib import Path

from full_lib import (
    HORIZONS,
    _simulate_lru_misses,
    load_trace,
    reconstruct_candidates_at_t,
    simulate_rollout_misses,
)

FULL_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = FULL_DIR / "outputs"


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
            mismatches.append({"t": t, "candidate": candidate, "canonical": canonical, "generalized": generalized})
    return n_compared, mismatches, max_abs_diff


def main():
    primary = json.loads((FULL_DIR / "PRIMARY_MANIFEST.json").read_text())
    diagnostic = json.loads((FULL_DIR / "DIAGNOSTIC_MANIFEST.json").read_text())
    all_decisions = primary["decisions"] + diagnostic["decisions"]

    trace_cache = {}
    total_compared = 0
    all_mismatches = []
    max_abs_diff_overall = 0

    for i, d in enumerate(all_decisions):
        family, capacity, t = d["family"], d["capacity"], d["request_t"]
        key = (family, capacity)
        if key not in trace_cache:
            requests, _pages, _ids = load_trace(family)
            trace_cache[key] = requests
        requests = trace_cache[key]
        candidates, pid = reconstruct_candidates_at_t(requests, capacity, t)

        for horizon in HORIZONS:
            n_cmp, mism, max_diff = compare_one(candidates, pid, requests, t, capacity, horizon)
            for m in mism:
                m["family"] = family
                m["capacity"] = capacity
                m["horizon"] = horizon
                m["decision_id"] = d["decision_id"]
            total_compared += n_cmp
            all_mismatches.extend(mism)
            max_abs_diff_overall = max(max_abs_diff_overall, max_diff)

        if (i + 1) % 1000 == 0:
            print(f"  ...{i+1}/{len(all_decisions)} decisions audited ({total_compared} comparisons so far)")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = {
        "n_decisions_audited": len(all_decisions),
        "n_horizons_per_decision": len(HORIZONS),
        "total_candidate_horizon_comparisons": total_compared,
        "mismatches": all_mismatches,
        "n_mismatches": len(all_mismatches),
        "max_abs_difference": max_abs_diff_overall,
        "gate": "LRU_EQUIVALENCE_MISMATCHES",
        "gate_value": len(all_mismatches),
        "gate_pass": len(all_mismatches) == 0,
    }
    (OUT_DIR / "prelaunch_lru_equivalence_result.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print(f"\nTotal candidate/horizon comparisons: {total_compared}")
    print(f"LRU_EQUIVALENCE_MISMATCHES = {len(all_mismatches)}")
    print(f"Max absolute difference: {max_abs_diff_overall}")
    if all_mismatches:
        print("GATE: FAIL -- STOP. Do not launch full MRU/random execution.")
        raise SystemExit(1)
    print("GATE: PASS")


if __name__ == "__main__":
    main()
