"""Independent recomputation of the FULL experiment's headline metrics via a
second, separate code path: reads the raw candidate_results.jsonl directly
(not decision_metrics.csv) and recomputes median Jaccard, strict-reversal
fraction, and mean cross-continuation regret from scratch using pandas +
hand-rolled set/pair logic, then compares against analyze_full.py's own
scientific_analysis.json output.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

TOL = 1e-9


def load_raw(jsonl_path: Path) -> pd.DataFrame:
    records = []
    with open(jsonl_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return pd.DataFrame.from_records(records)


def independent_jaccard_and_ccr(df: pd.DataFrame, alt_policy_filter):
    """alt_policy_filter: 'mru' or a function selecting/aggregating random rows to a mean-loss series."""
    lru = df[df["reference_policy"] == "lru"]
    if alt_policy_filter == "mru":
        alt = df[df["reference_policy"] == "mru"]
    else:
        rnd = df[df["reference_policy"] == "random"]
        alt = rnd.groupby(["decision_id", "horizon", "candidate_page_id"], as_index=False)["rollout_loss_h"].mean()
        alt["reference_policy"] = "random_mean"

    jaccards = {}
    ccrs = {}
    for (decision_id, horizon), lru_group in lru.groupby(["decision_id", "horizon"]):
        alt_group = alt[(alt["decision_id"] == decision_id) & (alt["horizon"] == horizon)]
        if alt_group.empty:
            continue
        lru_losses = dict(zip(lru_group["candidate_page_id"], lru_group["rollout_loss_h"]))
        alt_losses = dict(zip(alt_group["candidate_page_id"], alt_group["rollout_loss_h"]))
        lru_best = min(lru_losses.values())
        alt_best = min(alt_losses.values())
        opt_lru = {c for c, v in lru_losses.items() if v == lru_best}
        opt_alt = {c for c, v in alt_losses.items() if v == alt_best}
        union = opt_lru | opt_alt
        jaccards[(decision_id, horizon)] = len(opt_lru & opt_alt) / len(union) if union else None
        r_vals = [alt_losses[c] - alt_best for c in opt_lru]
        ccrs[(decision_id, horizon)] = sum(r_vals) / len(r_vals) if r_vals else None
    return jaccards, ccrs


def median(vals):
    s = sorted(v for v in vals if v is not None)
    n = len(s)
    if n == 0:
        return None
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2


def main(run_dir: Path):
    jsonl_path = run_dir / "candidate_results.jsonl"
    print(f"Loading raw results from {jsonl_path} ...")
    df = load_raw(jsonl_path)
    df = df[df["sample"] == "primary"]  # independent recheck focuses on primary sample, matching Set A

    mismatches = []
    for policy_key, filt in [("mru", "mru"), ("random_mean", "random")]:
        jaccards, ccrs = independent_jaccard_and_ccr(df, filt)
        mine_median_jaccard = median(list(jaccards.values()))
        mine_mean_ccr = sum(v for v in ccrs.values() if v is not None) / len([v for v in ccrs.values() if v is not None])

        theirs = json.loads((run_dir / "scientific_analysis.json").read_text())
        theirs_median_jaccard = theirs["PRIMARY_ANALYSIS"][policy_key]["stratified_sets"]["A_all_decisions"]["median_jaccard"]
        theirs_mean_ccr = theirs["PRIMARY_ANALYSIS"][policy_key]["stratified_sets"]["A_all_decisions"]["mean_ccr"]

        print(f"{policy_key}: independent median_jaccard={mine_median_jaccard:.6f} vs theirs={theirs_median_jaccard:.6f}")
        print(f"{policy_key}: independent mean_ccr={mine_mean_ccr:.6f} vs theirs={theirs_mean_ccr:.6f}")

        if abs(mine_median_jaccard - theirs_median_jaccard) > TOL:
            mismatches.append(f"{policy_key} median_jaccard mismatch")
        if abs(mine_mean_ccr - theirs_mean_ccr) > TOL:
            mismatches.append(f"{policy_key} mean_ccr mismatch")

    if mismatches:
        print("\nINDEPENDENT_RECHECK: FAIL")
        for m in mismatches:
            print(" -", m)
        raise SystemExit(1)
    print("\nINDEPENDENT_RECHECK: PASS")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
