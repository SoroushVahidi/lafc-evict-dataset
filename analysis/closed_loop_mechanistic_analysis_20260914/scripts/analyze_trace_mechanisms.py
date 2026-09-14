"""Trace-only mechanistic characterization of the Tier-1 offline<->closed-loop
exceptions (cloudphysics/cap32, metakv/cap128) and controls.

Reads ONLY the raw processed request traces (item_id sequences) and the
already-frozen offline/closed-loop evidence. Never imports, constructs, or
invokes any cache-policy class from the augmented-caching simulator, and
never runs a new replay of any kind. See reuse_distance.py's module
docstring for why stack-distance computation is a trace statistic, not a
policy simulation.

Scored windows below are copied verbatim from MATRIX.md / the joined linkage
dataset (analysis/closed_loop_offline_linkage_20260914/joined_data/), and
cross-checked against it by tests/test_mechanistic_analysis.py.
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from reuse_distance import stack_distances_fenwick

REPO_ROOT = Path(__file__).resolve().parents[3]
ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
LINKAGE_ROOT = REPO_ROOT / "analysis" / "closed_loop_offline_linkage_20260914"
PROCESSED_TRACE_DIR = Path("/home/soroush/projects/augmented-caching/repo/data/processed")

OUT_DIR = ANALYSIS_ROOT / "outputs"

FAMILIES = ("cloudphysics", "metacdn", "metakv", "twemcache", "wiki2018")
CAPACITIES = (32, 128)

# Verbatim from MATRIX.md / joined_offline_closed_loop.csv's scored_split_label.
SCORED_WINDOWS: Dict[str, List[Tuple[int, int]]] = {
    "cloudphysics": [(16384, 20479), (20480, 24575)],
    "metacdn": [(0, 4095), (24576, 32767), (36864, 45055)],
    "metakv": [(0, 4095)],
    "twemcache": [(32768, 36863), (40960, 45055)],
    "wiki2018": [(24576, 28671)],
}
SPLIT_LABEL = {"cloudphysics": "test", "metacdn": "validation", "metakv": "test",
               "twemcache": "test", "wiki2018": "test"}


def load_trace(family: str) -> List[str]:
    path = PROCESSED_TRACE_DIR / family / "trace.jsonl"
    item_ids = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            item_ids.append(str(rec["item_id"]))
    assert len(item_ids) == 50000, f"{family}: expected 50000 requests, got {len(item_ids)}"
    return item_ids


def percentile(sorted_vals: List[float], p: float) -> Optional[float]:
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def concentration_shares(counts: Counter, total: int) -> Tuple[float, float, float]:
    freqs = sorted(counts.values(), reverse=True)
    n_distinct = len(freqs)

    def share(pct: float) -> float:
        k = max(1, round(n_distinct * pct))
        return sum(freqs[:k]) / total

    return share(0.01), share(0.05), share(0.10)


def shannon_entropy_bits(counts: Counter, total: int) -> float:
    h = 0.0
    for c in counts.values():
        p = c / total
        h -= p * math.log2(p)
    return h


def window_metrics(item_ids: List[str], stack_dists: List[Optional[int]],
                    first_seen_pos: Dict[str, int], windows: List[Tuple[int, int]]) -> dict:
    idxs: List[int] = []
    for lo, hi in windows:
        idxs.extend(range(lo, hi + 1))
    idxs.sort()
    n = len(idxs)

    window_items = [item_ids[i] for i in idxs]
    counts = Counter(window_items)
    unique_objects = len(counts)

    compulsory = sum(1 for i in idxs if first_seen_pos[item_ids[i]] == i)
    repeated = n - compulsory

    top1, top5, top10 = concentration_shares(counts, n)
    entropy = shannon_entropy_bits(counts, n)
    norm_entropy = entropy / math.log2(unique_objects) if unique_objects > 1 else 0.0

    reuse_dists = [stack_dists[i] for i in idxs if stack_dists[i] is not None]
    reuse_dists_sorted = sorted(reuse_dists)
    n_reuse = len(reuse_dists)
    reuse_within_32 = sum(1 for d in reuse_dists if d <= 32) / n_reuse if n_reuse else None
    reuse_within_128 = sum(1 for d in reuse_dists if d <= 128) / n_reuse if n_reuse else None
    reuse_beyond_128 = sum(1 for d in reuse_dists if d > 128) / n_reuse if n_reuse else None

    def working_set(w: int) -> float:
        sizes = []
        for i in idxs:
            lo = max(0, i - w + 1)
            sizes.append(len(set(item_ids[lo:i + 1])))
        return sum(sizes) / len(sizes)

    longest_streak = 0
    cur = 0
    for i in idxs:
        if first_seen_pos[item_ids[i]] == i:
            cur += 1
            longest_streak = max(longest_streak, cur)
        else:
            cur = 0

    pre_window_history = idxs[0]

    return {
        "scored_window_request_count": n,
        "unique_objects_in_window": unique_objects,
        "unique_over_request_ratio": unique_objects / n,
        "compulsory_fraction": compulsory / n,
        "repeated_fraction": repeated / n,
        "top1pct_share": top1, "top5pct_share": top5, "top10pct_share": top10,
        "shannon_entropy_bits": entropy, "normalized_entropy": norm_entropy,
        "reuse_distance_median": percentile(reuse_dists_sorted, 0.5),
        "reuse_distance_mean": (sum(reuse_dists) / n_reuse) if n_reuse else None,
        "reuse_distance_p10": percentile(reuse_dists_sorted, 0.10),
        "reuse_distance_p25": percentile(reuse_dists_sorted, 0.25),
        "reuse_distance_p75": percentile(reuse_dists_sorted, 0.75),
        "reuse_distance_p90": percentile(reuse_dists_sorted, 0.90),
        "n_reuse_events": n_reuse,
        "reuse_within_32_fraction": reuse_within_32,
        "reuse_within_128_fraction": reuse_within_128,
        "reuse_beyond_128_fraction": reuse_beyond_128,
        "working_set_size_32_mean": working_set(32),
        "working_set_size_128_mean": working_set(128),
        "longest_novel_streak": longest_streak,
        "pre_window_history_requests": pre_window_history,
        "cache_could_plausibly_be_warm": pre_window_history >= 128,
    }


def cold_start_metrics(item_ids: List[str], first_seen_pos: Dict[str, int],
                        windows: List[Tuple[int, int]]) -> dict:
    # Uses only the FIRST window (the one containing the smallest index) for
    # a clean "start of scored evidence" cold-start characterization; for
    # metakv this is the only window and starts at request 0.
    lo, hi = sorted(windows)[0]
    window_idxs = list(range(lo, hi + 1))
    window_items = [item_ids[i] for i in window_idxs]

    def max_possible_hits(prefix_n: int) -> int:
        prefix = window_items[:prefix_n]
        seen = set()
        hits = 0
        for it in prefix:
            if it in seen:
                hits += 1
            seen.add(it)
        return hits

    first_repeat_position = None
    seen = set()
    for pos, it in enumerate(window_items):
        if it in seen:
            first_repeat_position = pos
            break
        seen.add(it)

    unique_after = {}
    seen = set()
    checkpoints = {32, 64, 128, 256, 512, 1024}
    for pos, it in enumerate(window_items):
        seen.add(it)
        if (pos + 1) in checkpoints:
            unique_after[pos + 1] = len(seen)
    for n in checkpoints:
        unique_after.setdefault(n, len(set(window_items[:n])) if len(window_items) >= n else None)

    n = len(window_items)
    quarter_size = n // 4
    quarter_repeated = {}
    for q in range(4):
        qlo = q * quarter_size
        qhi = (q + 1) * quarter_size if q < 3 else n
        qidxs = window_idxs[qlo:qhi]
        rep = sum(1 for i in qidxs if first_seen_pos[item_ids[i]] != i)
        quarter_repeated[q + 1] = rep / len(qidxs) if qidxs else None

    result = {
        "max_possible_hits_in_first_32": max_possible_hits(min(32, n)),
        "max_possible_hits_in_first_128": max_possible_hits(min(128, n)),
        "first_repeat_position": first_repeat_position,
    }
    for k, v in unique_after.items():
        result[f"unique_count_after_{k}"] = v
    for q, v in quarter_repeated.items():
        result[f"quarter{q}_repeated_fraction"] = v
    return result


# Exact LRU hits, taken verbatim from the frozen Tier-1 evidence
# (analysis/closed_loop_tier1_evidence_20260914/run/20260914T023445Z_8a4cd32402a1/run_results.csv),
# used ONLY as a comparison target for the trace-only prediction below --
# never as an input to the trace computation itself.
ACTUAL_LRU_HITS = {
    ("cloudphysics", 32): 134, ("cloudphysics", 128): 360,
    ("metacdn", 32): 8619, ("metacdn", 128): 9236,
    ("metakv", 32): 1061, ("metakv", 128): 1110,
    ("twemcache", 32): 2039, ("twemcache", 128): 3109,
    ("wiki2018", 32): 0, ("wiki2018", 128): 0,
}

# Closed-loop miss ratios and offline all_tied_fraction (H=16), taken
# verbatim from the joined linkage dataset, used only for the exploratory
# trace-locality vs. discriminativeness/separation correlation below.
CLOSED_LOOP_MISS_RATIO = {
    ("cloudphysics", 32, "lru"): 0.9836, ("cloudphysics", 32, "mru"): 0.9999,
    ("cloudphysics", 128, "lru"): 0.9561, ("cloudphysics", 128, "mru"): 0.9989,
    ("metacdn", 32, "lru"): 0.5792, ("metacdn", 32, "mru"): 0.8535,
    ("metacdn", 128, "lru"): 0.5490, ("metacdn", 128, "mru"): 0.8506,
    ("metakv", 32, "lru"): 0.7410, ("metakv", 32, "mru"): 0.8152,
    ("metakv", 128, "lru"): 0.7290, ("metakv", 128, "mru"): 0.7915,
    ("twemcache", 32, "lru"): 0.7511, ("twemcache", 32, "mru"): 0.9548,
    ("twemcache", 128, "lru"): 0.6205, ("twemcache", 128, "mru"): 0.9492,
    ("wiki2018", 32, "lru"): 1.0, ("wiki2018", 32, "mru"): 1.0,
    ("wiki2018", 128, "lru"): 1.0, ("wiki2018", 128, "mru"): 1.0,
}
OFFLINE_ALL_TIED_H16 = {
    ("cloudphysics", 32): 0.8696, ("cloudphysics", 128): 0.6617,
    ("metacdn", 32): 0.0122, ("metacdn", 128): 0.0085,
    ("metakv", 32): 0.8668, ("metakv", 128): 0.8559,
    ("twemcache", 32): 0.2427, ("twemcache", 128): 0.1017,
    ("wiki2018", 32): 1.0, ("wiki2018", 128): 1.0,
}


def build_mechanism_comparison(trace_data) -> list:
    rows = []
    for family in FAMILIES:
        item_ids, first_seen_pos, stack_dists = trace_data[family]
        idxs = []
        for lo, hi in SCORED_WINDOWS[family]:
            idxs.extend(range(lo, hi + 1))
        n = len(idxs)
        for capacity in CAPACITIES:
            predicted_lru_hits = sum(1 for i in idxs if stack_dists[i] is not None and stack_dists[i] < capacity)
            actual = ACTUAL_LRU_HITS[(family, capacity)]
            cl_gap = CLOSED_LOOP_MISS_RATIO[(family, capacity, "mru")] - CLOSED_LOOP_MISS_RATIO[(family, capacity, "lru")]
            rows.append({
                "family": family, "capacity": capacity,
                "scored_window_request_count": n,
                "predicted_lru_hits_from_stack_distance": predicted_lru_hits,
                "actual_lru_hits_tier1": actual,
                "exact_match": predicted_lru_hits == actual,
                "predicted_lru_hit_rate": predicted_lru_hits / n,
                "offline_all_tied_fraction_H16": OFFLINE_ALL_TIED_H16[(family, capacity)],
                "cl_mru_minus_lru_miss_ratio_gap": cl_gap,
            })
    return rows


def correlation(xs, ys):
    from scipy import stats
    if len(set(xs)) < 2 or len(set(ys)) < 2:
        return {"n": len(xs), "pearson_r": None, "spearman_rho": None}
    pear = stats.pearsonr(xs, ys)
    spear = stats.spearmanr(xs, ys)
    return {"n": len(xs), "pearson_r": float(pear.statistic), "spearman_rho": float(spear.statistic)}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    trace_data = {}
    window_rows = []
    cold_start_rows = []

    for family in FAMILIES:
        item_ids = load_trace(family)
        first_seen_pos: Dict[str, int] = {}
        for i, it in enumerate(item_ids):
            if it not in first_seen_pos:
                first_seen_pos[it] = i
        stack_dists = stack_distances_fenwick(item_ids)
        trace_data[family] = (item_ids, first_seen_pos, stack_dists)

        wm = window_metrics(item_ids, stack_dists, first_seen_pos, SCORED_WINDOWS[family])
        wm_row = {"family": family, "scored_split_label": SPLIT_LABEL[family], **wm}
        window_rows.append(wm_row)

        csm = cold_start_metrics(item_ids, first_seen_pos, SCORED_WINDOWS[family])
        cold_start_rows.append({"family": family, **csm})

    with open(OUT_DIR / "trace_characteristics.csv", "w", newline="", encoding="utf-8") as fh:
        fieldnames = list(window_rows[0].keys())
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in window_rows:
            writer.writerow(r)

    with open(OUT_DIR / "early_window_characteristics.csv", "w", newline="", encoding="utf-8") as fh:
        fieldnames = list(cold_start_rows[0].keys())
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in cold_start_rows:
            writer.writerow(r)

    # reuse-distance summary, separately reported (redundant w/ trace_characteristics
    # but as its own dedicated file per the requested artifact layout)
    with open(OUT_DIR / "reuse_distance_summary.csv", "w", newline="", encoding="utf-8") as fh:
        fields = ["family", "n_reuse_events", "reuse_distance_median", "reuse_distance_mean",
                  "reuse_distance_p10", "reuse_distance_p25", "reuse_distance_p75", "reuse_distance_p90",
                  "reuse_within_32_fraction", "reuse_within_128_fraction", "reuse_beyond_128_fraction"]
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for r in window_rows:
            writer.writerow({k: r[k] for k in fields})

    mech_rows = build_mechanism_comparison(trace_data)
    with open(OUT_DIR / "mechanism_comparison.csv", "w", newline="", encoding="utf-8") as fh:
        fieldnames = list(mech_rows[0].keys())
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in mech_rows:
            writer.writerow(r)
    assert all(r["exact_match"] for r in mech_rows), "trace-only LRU-hit prediction failed to match Tier-1 evidence exactly"

    exploit_32 = [r["predicted_lru_hit_rate"] for r in mech_rows if r["capacity"] == 32]
    exploit_128 = [r["predicted_lru_hit_rate"] for r in mech_rows if r["capacity"] == 128]
    tied_32 = [r["offline_all_tied_fraction_H16"] for r in mech_rows if r["capacity"] == 32]
    tied_128 = [r["offline_all_tied_fraction_H16"] for r in mech_rows if r["capacity"] == 128]
    sep_32 = [r["cl_mru_minus_lru_miss_ratio_gap"] for r in mech_rows if r["capacity"] == 32]
    sep_128 = [r["cl_mru_minus_lru_miss_ratio_gap"] for r in mech_rows if r["capacity"] == 128]
    all_exploit = [r["predicted_lru_hit_rate"] for r in mech_rows]
    all_tied = [r["offline_all_tied_fraction_H16"] for r in mech_rows]
    all_sep = [r["cl_mru_minus_lru_miss_ratio_gap"] for r in mech_rows]

    corr_summary = {
        "pooled_n10_LRU_hit_rate_vs_offline_all_tied_fraction": correlation(all_exploit, all_tied),
        "pooled_n10_LRU_hit_rate_vs_closed_loop_MRU_LRU_gap": correlation(all_exploit, all_sep),
        "cap32_n5_LRU_hit_rate_vs_offline_all_tied_fraction": correlation(exploit_32, tied_32),
        "cap32_n5_LRU_hit_rate_vs_closed_loop_MRU_LRU_gap": correlation(exploit_32, sep_32),
        "cap128_n5_LRU_hit_rate_vs_offline_all_tied_fraction": correlation(exploit_128, tied_128),
        "cap128_n5_LRU_hit_rate_vs_closed_loop_MRU_LRU_gap": correlation(exploit_128, sep_128),
        "note": "n=5 per capacity, n=10 pooled across both capacities (not independent horizons -- these are the 5 families x 2 capacities actually tested, no pseudo-replication here since there is no horizon dimension on the trace-metric side). Exploratory, not pre-registered.",
    }
    (OUT_DIR / "correlation_summary.json").write_text(json.dumps(corr_summary, indent=2, sort_keys=True), encoding="utf-8")
    with open(OUT_DIR / "correlation_summary.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["comparison", "n", "pearson_r", "spearman_rho"])
        for k, v in corr_summary.items():
            if k == "note":
                continue
            writer.writerow([k, v["n"], v["pearson_r"], v["spearman_rho"]])

    # Per-cell diagnosis JSONs for the two exceptions + the wiki2018 control.
    def cell_row(family, capacity):
        return next(r for r in mech_rows if r["family"] == family and r["capacity"] == capacity)

    def window_row(family):
        return next(r for r in window_rows if r["family"] == family)

    def cold_row(family):
        return next(r for r in cold_start_rows if r["family"] == family)

    (OUT_DIR / "cloudphysics_cap32_diagnosis.json").write_text(json.dumps({
        "mechanism_comparison": cell_row("cloudphysics", 32),
        "trace_characteristics": window_row("cloudphysics"),
        "cold_start_characteristics": cold_row("cloudphysics"),
        "diagnosis": (
            "Only 17.5% of window requests are reuses at all (rest are compulsory misses "
            "relative to the full 50k-request trace history); of those reuses, only 9.4% fall "
            "within stack distance 32 and only 25.3% within 128 -- 74.7% of reuses occur beyond "
            "distance 128. The trace-only predicted LRU hit rate (0.094 x 0.175 = 1.6% at cap32, "
            "0.253 x 0.175 = 4.4% at cap128) EXACTLY reproduces the actual observed LRU hit counts "
            "(134/8192=1.64% at cap32, 360/8192=4.39% at cap128) via the closed-form stack-distance "
            "identity. This is a genuinely near-zero exploitable-locality-at-this-capacity-scale "
            "regime, not a data or methodology artifact -- the offline gap being near zero and the "
            "closed-loop discordance are two symptoms of the same underlying trace property."
        ),
        "classification": "DIRECTLY_OBSERVED (near-zero capacity-scale-relevant locality); Q1 answer = B, not A",
    }, indent=2, sort_keys=True), encoding="utf-8")

    (OUT_DIR / "metakv_cap128_diagnosis.json").write_text(json.dumps({
        "mechanism_comparison": cell_row("metakv", 128),
        "trace_characteristics": window_row("metakv"),
        "cold_start_characteristics": cold_row("metakv"),
        "diagnosis": (
            "MetaKV's reuse-distance distribution is short-median (2) but long-tailed (p75=285, "
            "p90=580): 57.4% of reuses are within distance 32, only rising to 60.0% by distance "
            "128 -- a narrow (2.6 percentage point, ~48-event) 'boundary zone' of reuses sitting "
            "right around the tested capacities, where policy-specific eviction-order differences "
            "(LRU's strict recency vs. SIEVE's second-chance/visited-bit mechanism vs. random's "
            "memorylessness) could plausibly diverge on which marginal items are retained. This is "
            "consistent with, but does not isolate, a causal mechanism for the observed "
            "random/SIEVE-vs-LRU reversal there. MetaKV is also the only family whose scored window "
            "starts at request 0 (empty cache, no warmup, confirmed independently by the audit's "
            "evictions=misses-capacity identity) -- but the trace-only data available cannot "
            "establish whether the cold start, the boundary-zone reuse structure, or their "
            "interaction is the operative cause."
        ),
        "classification": "CONSISTENT_WITH_MECHANISM (not causally isolated); Q2/Q5/Q6/Q7 answered qualitatively, not causally",
    }, indent=2, sort_keys=True), encoding="utf-8")

    (OUT_DIR / "wiki2018_diagnosis.json").write_text(json.dumps({
        "mechanism_comparison": [cell_row("wiki2018", 32), cell_row("wiki2018", 128)],
        "trace_characteristics": window_row("wiki2018"),
        "cold_start_characteristics": cold_row("wiki2018"),
        "diagnosis": (
            "wiki2018's scored window contains EXACTLY ZERO reuse events (n_reuse_events=0; "
            "unique_over_request_ratio=1.0; every one of the 4096 window requests is a first-ever "
            "occurrence in the full 50,000-request trace). Since a cache hit requires a repeated "
            "reference to an already-resident item, zero reuse events makes miss_ratio=1.0 a "
            "mathematical certainty for ANY eviction policy at ANY capacity -- not a statistical "
            "tendency, a deductive consequence of the trace itself containing no repeats in this "
            "window. This fully and exactly explains the observed exact tie among all four Tier-1 "
            "policies (and all 20 random seeds, std=0) at both capacities."
        ),
        "classification": "CAUSALLY_ESTABLISHED (by mathematical necessity, not statistical inference -- see report Section 23 for the justification of using this category here); Q9 = fully explained",
    }, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Wrote trace_characteristics.csv, early_window_characteristics.csv, "
          f"reuse_distance_summary.csv, mechanism_comparison.csv, correlation_summary.{{csv,json}}, "
          f"and 3 per-cell diagnosis JSONs for {len(FAMILIES)} families to {OUT_DIR}")
    return trace_data, window_rows, cold_start_rows


if __name__ == "__main__":
    main()
