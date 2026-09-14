#!/usr/bin/env python3
"""Figure 3: offline regret gap vs. closed-loop miss-ratio gap, H=16.

Source (validated, frozen, not recomputed):
  analysis/closed_loop_offline_linkage_20260914/outputs/rq_cl2_scatter_data.csv

n=10 family x capacity cells per pair per horizon; this figure plots H=16
only (the primary horizon; see RQ-CL4 in
analysis/closed_loop_offline_linkage_20260914/SCIENTIFIC_SUMMARY.md), and
annotates the two discordant cells (cloudphysics/cap32, metakv/cap128)
named in RQ-CL1. Explicitly not a large-sample inference (n=10).
"""
import csv
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
SRC = REPO_ROOT / "analysis/closed_loop_offline_linkage_20260914/outputs/rq_cl2_scatter_data.csv"
OUT = REPO_ROOT / "paper/performance_evaluation/latex/figures/figure3_linkage_scatter.pdf"

FAMILY_COLOR = {
    "cloudphysics": "#4C72B0",
    "metacdn": "#55A868",
    "metakv": "#C44E52",
    "twemcache": "#8172B2",
    "wiki2018": "#999999",
}
PAIR_MARKER = {"mru_vs_lru": "o", "random_vs_lru": "^"}
DISCORDANT = {("cloudphysics", 32), ("metakv", 128)}


def main():
    rows = []
    with open(SRC, newline="") as fh:
        for r in csv.DictReader(fh):
            if int(r["horizon"]) == 16:
                rows.append(r)

    fig, ax = plt.subplots(figsize=(5.6, 4.6))
    for r in rows:
        fam = r["family"]
        cap = int(r["capacity"])
        pair = r["pair"]
        x = float(r["offline_gap"])
        y = float(r["closed_loop_gap"])
        ax.scatter(x, y, color=FAMILY_COLOR[fam], marker=PAIR_MARKER[pair],
                   s=70 if (fam, cap) in DISCORDANT else 45,
                   edgecolor="black" if (fam, cap) in DISCORDANT else "none",
                   linewidth=1.2, zorder=3)
        if (fam, cap) in DISCORDANT and pair == "mru_vs_lru":
            ax.annotate(f"{fam}/cap{cap}", (x, y), textcoords="offset points",
                        xytext=(6, 6), fontsize=7.5)

    ax.axhline(0, color="grey", linewidth=0.6)
    ax.axvline(0, color="grey", linewidth=0.6)
    ax.set_xlabel("Offline regret gap (H=16)")
    ax.set_ylabel("Closed-loop miss-ratio gap")
    ax.set_title("Offline vs. closed-loop gap, H=16 (n=10 cells x 2 pairs)", fontsize=10)

    fam_handles = [plt.Line2D([0], [0], marker="s", color="w",
                               markerfacecolor=c, markersize=8, label=f)
                   for f, c in FAMILY_COLOR.items()]
    pair_handles = [plt.Line2D([0], [0], marker=m, color="black", linestyle="",
                                markersize=7, label=p.replace("_", " "))
                    for p, m in PAIR_MARKER.items()]
    leg1 = ax.legend(handles=fam_handles, title="family", loc="upper left",
                      fontsize=7.5, title_fontsize=8, frameon=False)
    ax.add_artist(leg1)
    ax.legend(handles=pair_handles, title="pair", loc="lower right",
              fontsize=7.5, title_fontsize=8, frameon=False)
    ax.grid(alpha=0.3, linewidth=0.4)
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
