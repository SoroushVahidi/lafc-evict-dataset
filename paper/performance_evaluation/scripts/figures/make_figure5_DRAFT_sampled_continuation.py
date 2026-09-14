#!/usr/bin/env python3
"""Figure 5 DRAFT -- continuation-policy robustness, SAMPLED STUDY ONLY.

*** NOT FINAL MANUSCRIPT EVIDENCE. ***

This script and its output are a preview/interface only, built from the
validated sampled continuation-sensitivity study (capacities 32/128,
5,000-primary + 500-diagnostic decisions,
analysis/continuation_policy_sensitivity_full_20260914/,
RUN_ID 20260914T040333Z_1f66342be435). It must not be treated as, or
presented as, the final Figure 5.

The final Figure 5 requires the full-population MRU continuation census
(experiment/continuation-mru-population-census-20260914) to finish and be
independently validated. Until then this draft is NOT \\includegraphics'd
into the manuscript; see the %TODO-CENSUS marker in
sections/08e_continuation.tex.

Output is intentionally watermarked "PRELIMINARY - SAMPLED STUDY ONLY".
"""
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
SRC = (REPO_ROOT / "analysis/continuation_policy_sensitivity_full_20260914/outputs/"
       "20260914T040333Z_1f66342be435/scientific_analysis.json")
OUT = REPO_ROOT / "paper/performance_evaluation/latex/figures/figure5_DRAFT_sampled_only_PRELIMINARY.pdf"


def main():
    d = json.load(open(SRC))
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.0))
    caps = [32, 128]
    policies = [("mru", "#4C72B0", "MRU"), ("random_mean", "#C44E52", "mean-random")]

    ax = axes[0]
    width = 0.35
    for i, (key, color, label) in enumerate(policies):
        by_cap = d["PRIMARY_ANALYSIS"][key]["by_capacity_setC"]
        means = [by_cap[str(c)]["mean_jaccard"] for c in caps]
        medians = [by_cap[str(c)]["median_jaccard"] for c in caps]
        xs = [j + (i - 0.5) * width for j in range(len(caps))]
        ax.bar(xs, means, width=width, color=color, alpha=0.55, label=f"{label} mean")
        ax.scatter(xs, medians, color=color, marker="D", s=45, zorder=3,
                   label=f"{label} median")
    ax.set_xticks(range(len(caps)))
    ax.set_xticklabels([f"cap={c}" for c in caps])
    ax.set_ylabel("Optimal-set Jaccard vs. LRU continuation")
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=6.5, frameon=False, ncol=1, loc="lower left")
    ax.set_title("By capacity (Set C)", fontsize=9.5)

    ax = axes[1]
    horizons = [4, 8, 16]
    for key, color, label in policies:
        by_h = d["PRIMARY_ANALYSIS"][key]["by_horizon_setC"]
        medians = [by_h[str(h)]["median_jaccard"] for h in horizons]
        ax.plot(horizons, medians, marker="o", color=color, label=f"{label} median")
    ax.set_xlabel("Horizon H")
    ax.set_ylabel("Median optimal-set Jaccard")
    ax.set_xticks(horizons)
    ax.set_ylim(0, 1.05)
    ax.axhline(0.8, color="grey", linestyle="--", linewidth=0.8, label="ROBUST threshold")
    ax.legend(fontsize=7, frameon=False)
    ax.set_title("By horizon (Set C, both capacities pooled)", fontsize=9.5)

    for a in axes:
        a.grid(alpha=0.3, linewidth=0.4)

    fig.suptitle("PRELIMINARY — SAMPLED STUDY ONLY (capacities 32/128) — NOT FINAL FIGURE 5",
                 fontsize=9, color="darkred", y=1.03)
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT)
    print(f"wrote DRAFT (not embedded in manuscript) {OUT}")


if __name__ == "__main__":
    main()
