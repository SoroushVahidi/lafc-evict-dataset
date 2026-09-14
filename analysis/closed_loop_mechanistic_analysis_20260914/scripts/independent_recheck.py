"""Independent cross-check of the mechanistic analysis's headline numbers.

Three independent checks, none of which reuses analyze_trace_mechanisms.py's
own code path:

1. Brute-force stack distance vs. the Fenwick-tree implementation, spot-
   checked on the first 4000 requests of every real trace (not just the
   synthetic example in tests/) -- O(n^2)-ish, too slow for the full
   50,000-request trace, fine for 4000.

2. A minimal, self-contained "bounded recency set" walk -- NOT the
   augmented-caching LRUPolicy class, not importing lafc at all -- that
   independently re-derives the LRU hit count for one full trace
   (cloudphysics) via a plain Python OrderedDict-free approach (a dict of
   last-seen positions plus a manually maintained sorted structure is
   overkill; instead this uses the direct definition "hit iff there are
   fewer than C distinct items between this reference and the previous one
   to the same item" via brute-force counting, i.e. deliberately NOT the
   Fenwick-tree code path) and compares against both the Fenwick-tree
   prediction and the actual Tier-1 evidence.

3. A hand-rolled Pearson r (raw covariance/variance formula, no scipy)
   recomputing the correlation_summary.csv numbers.

Exits nonzero on any mismatch.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reuse_distance import stack_distances_fenwick, stack_distances_bruteforce  # noqa: E402
from analyze_trace_mechanisms import (  # noqa: E402
    load_trace, SCORED_WINDOWS, ACTUAL_LRU_HITS,
)

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ANALYSIS_ROOT / "outputs"
SPOT_CHECK_N = 4000
TOL = 1e-9


def manual_pearson_r(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0:
        return None
    return cov / ((vx ** 0.5) * (vy ** 0.5))


def check_stack_distance_spot(family: str, item_ids) -> list:
    sample = item_ids[:SPOT_CHECK_N]
    fen = stack_distances_fenwick(sample)
    brute = stack_distances_bruteforce(sample)
    mismatches = [i for i in range(len(sample)) if fen[i] != brute[i]]
    return mismatches


def independent_lru_hit_count_bruteforce(item_ids, window_idxs, capacity) -> int:
    """Deliberately reimplements the 'hit iff <C distinct items since last
    reference' rule from scratch via brute-force backward counting, not
    calling reuse_distance.py at all, as a second, independent code path.
    """
    idx_set = set(window_idxs)
    last_pos = {}
    hits = 0
    for i, item in enumerate(item_ids):
        if item in last_pos:
            old_p = last_pos[item]
            distinct_between = len(set(item_ids[old_p + 1:i]))
            if i in idx_set and distinct_between < capacity:
                hits += 1
        last_pos[item] = i
    return hits


def main():
    mismatches_total = {}
    for family in ("cloudphysics", "metacdn", "metakv", "twemcache", "wiki2018"):
        item_ids = load_trace(family)
        mism = check_stack_distance_spot(family, item_ids)
        mismatches_total[family] = mism

    fail = False
    for family, mism in mismatches_total.items():
        if mism:
            fail = True
            print(f"STACK_DISTANCE_SPOTCHECK FAIL for {family}: {len(mism)} mismatches at positions {mism[:10]}...")
        else:
            print(f"STACK_DISTANCE_SPOTCHECK PASS for {family} (first {SPOT_CHECK_N} requests, "
                  f"Fenwick vs. brute-force, 0 mismatches)")

    # Independent brute-force LRU-hit recomputation for the two smallest
    # windows (metakv, wiki2018 -- 4096 requests each, so brute-force
    # backward counting is fast enough) and cloudphysics cap32 (the other
    # exception cell).
    for family, capacity in [("metakv", 32), ("metakv", 128), ("wiki2018", 32), ("wiki2018", 128),
                              ("cloudphysics", 32)]:
        item_ids = load_trace(family)
        window_idxs = []
        for lo, hi in SCORED_WINDOWS[family]:
            window_idxs.extend(range(lo, hi + 1))
        independent_hits = independent_lru_hit_count_bruteforce(item_ids, window_idxs, capacity)
        expected = ACTUAL_LRU_HITS[(family, capacity)]
        ok = independent_hits == expected
        print(f"INDEPENDENT_LRU_HIT_RECOMPUTE {family}/{capacity}: "
              f"independent={independent_hits} expected(Tier1)={expected} match={ok}")
        if not ok:
            fail = True

    corr = json.loads((OUT_DIR / "correlation_summary.json").read_text())
    mech_rows = list(csv.DictReader(open(OUT_DIR / "mechanism_comparison.csv", newline="", encoding="utf-8")))
    for r in mech_rows:
        r["capacity"] = int(r["capacity"])
        r["predicted_lru_hit_rate"] = float(r["predicted_lru_hit_rate"])
        r["offline_all_tied_fraction_H16"] = float(r["offline_all_tied_fraction_H16"])
        r["cl_mru_minus_lru_miss_ratio_gap"] = float(r["cl_mru_minus_lru_miss_ratio_gap"])

    all_exploit = [r["predicted_lru_hit_rate"] for r in mech_rows]
    all_tied = [r["offline_all_tied_fraction_H16"] for r in mech_rows]
    all_sep = [r["cl_mru_minus_lru_miss_ratio_gap"] for r in mech_rows]

    mine_r1 = manual_pearson_r(all_exploit, all_tied)
    theirs_r1 = corr["pooled_n10_LRU_hit_rate_vs_offline_all_tied_fraction"]["pearson_r"]
    mine_r2 = manual_pearson_r(all_exploit, all_sep)
    theirs_r2 = corr["pooled_n10_LRU_hit_rate_vs_closed_loop_MRU_LRU_gap"]["pearson_r"]

    for label, mine, theirs in [("tied_fraction", mine_r1, theirs_r1), ("mru_lru_gap", mine_r2, theirs_r2)]:
        ok = abs(mine - theirs) < TOL
        print(f"MANUAL_PEARSON_RECHECK {label}: mine={mine:.6f} theirs={theirs:.6f} match={ok}")
        if not ok:
            fail = True

    if fail:
        print("INDEPENDENT_RECHECK: FAIL")
        sys.exit(1)
    print("INDEPENDENT_RECHECK: PASS")


if __name__ == "__main__":
    main()
