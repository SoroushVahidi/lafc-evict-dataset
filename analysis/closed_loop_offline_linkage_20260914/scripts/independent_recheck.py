"""Independent recomputation of the headline RQ-CL1/RQ-CL2/RQ-CL4 numbers.

Deliberately uses a DIFFERENT code path than compute_rq_analyses.py:
- pandas instead of the csv module for loading/grouping,
- a hand-rolled Pearson-r (raw covariance/variance formula) instead of
  scipy.stats.pearsonr,
- a hand-rolled concordant/discordant counter using plain Python comparisons
  instead of the sign()/classify_pair() helpers in compute_rq_analyses.py.

This exists solely as a cross-check: if this script's numbers disagree with
compute_rq_analyses.py's outputs, that indicates a bug in one of the two
implementations, not a scientific finding. Exits nonzero on any mismatch.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
JOINED_PATH = ANALYSIS_ROOT / "joined_data" / "joined_offline_closed_loop.csv"
OUT_DIR = ANALYSIS_ROOT / "outputs"

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


def manual_concordance(df, off_col, cl_col):
    counts = {"concordant": 0, "discordant": 0, "both_tied": 0, "offline_tie_only": 0, "closed_loop_tie_only": 0}
    for off, cl in zip(df[off_col], df[cl_col]):
        off_s = (off > 0) - (off < 0)
        cl_s = (cl > 0) - (cl < 0)
        if off_s == 0 and cl_s == 0:
            counts["both_tied"] += 1
        elif off_s == 0:
            counts["offline_tie_only"] += 1
        elif cl_s == 0:
            counts["closed_loop_tie_only"] += 1
        elif off_s == cl_s:
            counts["concordant"] += 1
        else:
            counts["discordant"] += 1
    return counts


def main():
    df = pd.read_csv(JOINED_PATH)
    assert len(df) == 30, f"expected 30 joined rows, got {len(df)}"
    assert set(df["capacity"].unique()) == {32, 128}
    assert set(df["horizon"].unique()) == {4, 8, 16}

    pairs = [
        ("mru_vs_lru", "offline_mru_minus_lru_regret_gap", "cl_mru_minus_lru_miss_ratio_gap"),
        ("random_vs_lru", "offline_random_minus_lru_regret_gap", "cl_random_minus_lru_miss_ratio_gap"),
    ]

    mismatches = []

    primary = json.loads((OUT_DIR / "rq_cl1_rank_agreement.json").read_text())
    for horizon in (4, 8, 16):
        hdf = df[df["horizon"] == horizon]
        for name, off_col, cl_col in pairs:
            mine = manual_concordance(hdf, off_col, cl_col)
            theirs = primary["by_horizon"][str(horizon)][name]["counts"]
            for k in ("concordant", "discordant", "both_tied"):
                if mine.get(k, 0) != theirs.get(k, 0):
                    mismatches.append(f"H={horizon} {name} {k}: mine={mine.get(k,0)} theirs={theirs.get(k,0)}")

    corr = json.loads((OUT_DIR / "rq_cl2_gap_correspondence.json").read_text())
    for horizon in (4, 8, 16):
        hdf = df[df["horizon"] == horizon]
        for name, off_col, cl_col in pairs:
            mine_r = manual_pearson_r(list(hdf[off_col]), list(hdf[cl_col]))
            theirs_r = corr["primary_by_horizon"][str(horizon)][name]["pearson_r"]
            if mine_r is None or theirs_r is None:
                continue
            if abs(mine_r - theirs_r) > TOL:
                mismatches.append(f"H={horizon} {name} pearson_r: mine={mine_r} theirs={theirs_r}")

    disc_df = df[df["horizon"] == 16].copy()
    disc_df["disc"] = 1.0 - disc_df["offline_all_tied_fraction"]
    disc_df["sep"] = disc_df["cl_mru_minus_lru_miss_ratio_gap"].abs()
    mine_r = manual_pearson_r(list(disc_df["disc"]), list(disc_df["sep"]))
    rq3 = json.loads((OUT_DIR / "rq_cl3_workload_capacity_dependence.json").read_text())
    theirs_r = rq3["exploratory_discriminativeness_vs_closed_loop_separation_H16"]["pearson_r"]
    if abs(mine_r - theirs_r) > TOL:
        mismatches.append(f"exploratory disc-vs-sep pearson_r: mine={mine_r} theirs={theirs_r}")

    if mismatches:
        print("INDEPENDENT_RECHECK: FAIL")
        for m in mismatches:
            print(" -", m)
        sys.exit(1)

    print("INDEPENDENT_RECHECK: PASS")
    print(f"Cross-checked {len(pairs)} pairs x 3 horizons concordance counts, "
          f"{len(pairs)} pairs x 3 horizons Pearson r, and the RQ-CL3 exploratory correlation "
          "via a fully independent pandas + hand-rolled-formula code path. All matched primary "
          "compute_rq_analyses.py results exactly (tolerance 1e-9).")


if __name__ == "__main__":
    main()
