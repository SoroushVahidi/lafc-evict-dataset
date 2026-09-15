#!/usr/bin/env python3
"""Figure 3: offline regret gap vs. closed-loop miss-ratio gap, H=16.

Source (validated, frozen, not recomputed):
  analysis/closed_loop_offline_linkage_20260914/outputs/rq_cl2_scatter_data.csv

n=10 family x capacity cells per pair per horizon; this figure plots H=16
only (the primary horizon; see RQ-CL4 in
analysis/closed_loop_offline_linkage_20260914/SCIENTIFIC_SUMMARY.md).
Two side-by-side panels separate the two pairs (MRU-vs-LRU, random-vs-LRU)
so each panel needs only one marker shape; family is still color-coded and
shares one legend across both panels. Only the two discordant cells named
in RQ-CL1 are annotated (alibaba-block/cap32 in both panels, using the
internal family key "cloudphysics"; metakv/cap128 in the random-vs-LRU
panel only). Explicitly not a large-sample inference (n=10 per panel).
"""
import csv
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset

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
# Display-only relabeling: the internal family key "cloudphysics" is a
# historical identifier that does not reflect true trace provenance (see
# THIRD_PARTY_DATA.md) -- the underlying data is Alibaba's Cloud EBS block
# trace. Data lookups/keys above are unchanged; only the rendered text uses
# this mapping.
DISPLAY_NAME = {"cloudphysics": "Alibaba Block"}
ANNOTATION_NAME = {"cloudphysics": "alibaba-block"}
PANELS = [
    ("mru_vs_lru", "(a) MRU vs. LRU"),
    ("random_vs_lru", "(b) Random vs. LRU"),
]
# (family, capacity) -> which panels to annotate in, and a leader-line offset
# chosen by hand per point so the label clears both the marker and the axes.
DISCORDANT_ANNOTATIONS = {
    ("mru_vs_lru", "cloudphysics", 32): (28, -22),
    ("random_vs_lru", "cloudphysics", 32): (18, 14),
    ("random_vs_lru", "metakv", 128): (-15, -18),
}


def display_name(family):
    return DISPLAY_NAME.get(family, family)


def annotation_name(family):
    return ANNOTATION_NAME.get(family, family)


def main():
    rows = []
    with open(SRC, newline="") as fh:
        for r in csv.DictReader(fh):
            if int(r["horizon"]) == 16:
                rows.append(
                    {
                        "pair": r["pair"],
                        "family": r["family"],
                        "capacity": int(r["capacity"]),
                        "x": float(r["offline_gap"]),
                        "y": float(r["closed_loop_gap"]),
                    }
                )

    all_x = [r["x"] for r in rows]
    all_y = [r["y"] for r in rows]
    pad_x = 0.06 * (max(all_x) - min(all_x))
    pad_y = 0.06 * (max(all_y) - min(all_y))
    xlim = (min(all_x) - pad_x, max(all_x) + pad_x)
    ylim = (min(all_y) - pad_y, max(all_y) + pad_y)

    fig, axes = plt.subplots(1, 2, figsize=(8.4, 4.4), sharex=True, sharey=True)

    # Random-vs-LRU gaps are uniformly small in magnitude, so under the
    # shared axis scale required for cross-panel comparability its 10
    # points compress into one near-origin cluster; a zoomed inset on that
    # panel only restores per-point legibility there.
    INSET_XLIM = (-0.012, 0.052)
    INSET_YLIM = (-0.022, 0.055)
    inset_ax = None

    for ax, (pair, panel_title) in zip(axes, PANELS):
        panel_rows = [r for r in rows if r["pair"] == pair]
        target_axes = [ax]
        if pair == "random_vs_lru":
            inset_ax = inset_axes(ax, width="52%", height="52%", loc="lower right",
                                   borderpad=1.6)
            target_axes.append(inset_ax)

        for r in panel_rows:
            fam, cap = r["family"], r["capacity"]
            key = (fam, cap)
            is_discordant = key in {("cloudphysics", 32), ("metakv", 128)}
            for target in target_axes:
                target.scatter(
                    r["x"], r["y"], color=FAMILY_COLOR[fam], marker="o",
                    s=75 if is_discordant else 48,
                    edgecolor="black" if is_discordant else "none",
                    linewidth=1.2, zorder=3,
                )
            offset = DISCORDANT_ANNOTATIONS.get((pair, fam, cap))
            if offset is not None:
                annotate_on = inset_ax if pair == "random_vs_lru" else ax
                annotate_on.annotate(
                    f"{annotation_name(fam)}/C={cap}", (r["x"], r["y"]),
                    xytext=offset, textcoords="offset points",
                    fontsize=6.5 if pair == "random_vs_lru" else 7.5,
                    zorder=4,
                    arrowprops=dict(arrowstyle="-", color="black",
                                     linewidth=0.6, shrinkA=0, shrinkB=4),
                )

        ax.axhline(0, color="grey", linewidth=0.6, zorder=1)
        ax.axvline(0, color="grey", linewidth=0.6, zorder=1)
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.set_xlabel("Offline regret gap (H=16)")
        ax.set_title(panel_title, fontsize=10)
        ax.grid(alpha=0.3, linewidth=0.4)

    axes[0].set_ylabel("Closed-loop miss-ratio gap")

    inset_ax.axhline(0, color="grey", linewidth=0.5, zorder=1)
    inset_ax.axvline(0, color="grey", linewidth=0.5, zorder=1)
    inset_ax.set_xlim(*INSET_XLIM)
    inset_ax.set_ylim(*INSET_YLIM)
    inset_ax.set_xticks([0.0, 0.04])
    inset_ax.set_yticks([0.0, 0.04])
    inset_ax.tick_params(labelsize=6, length=2)
    inset_ax.grid(alpha=0.25, linewidth=0.3)
    for spine in inset_ax.spines.values():
        spine.set_linewidth(0.8)
    mark_inset(axes[1], inset_ax, loc1=2, loc2=1, fc="none",
               ec="0.5", linewidth=0.6)

    fam_handles = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=c,
                   markersize=7, label=display_name(f))
        for f, c in FAMILY_COLOR.items()
    ]
    fig.legend(
        handles=fam_handles, title="family", loc="lower center",
        ncol=len(FAMILY_COLOR), bbox_to_anchor=(0.5, -0.02),
        fontsize=8, title_fontsize=8.5, frameon=False,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
