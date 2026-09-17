#!/usr/bin/env python3
"""Figure 3 (rendered as document Figure 4): offline regret gap vs.
closed-loop miss-ratio gap, H=16.

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

Each panel uses its OWN axis limits (not shared/pooled) because
random-vs-LRU gaps are uniformly much smaller in magnitude than
MRU-vs-LRU gaps; forcing both onto one shared scale compressed panel (b)'s
points into an unreadable near-origin cluster and required a zoomed inset
to recover legibility. That inset (with connector lines into the main
panel) made the figure visually busy for only 10 points/panel and has been
removed in favor of simply letting each panel show its own natural range,
with the differing scales stated explicitly in the caption so they are
never mistaken for being identical.
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
# (pair, family, capacity) -> label offset, chosen by hand per point so the
# label clears both the marker and the axes. Only the two discordant cells
# from RQ-CL1 are labeled -- every other point is left unlabeled by design.
DISCORDANT_ANNOTATIONS = {
    ("mru_vs_lru", "cloudphysics", 32): (20, 62),
    ("random_vs_lru", "cloudphysics", 32): (-2, 58),
    ("random_vs_lru", "metakv", 128): (46, -10),
}
# A small number of leader lines pass close to a nearby (non-discordant)
# marker under a straight connector; curve just those with a matplotlib
# "arc3" connectionstyle so the line bows around the marker instead of
# through it. Left at the default straight line ("arc3,rad=0.0") elsewhere.
CONNECTIONSTYLE = {
    ("random_vs_lru", "cloudphysics", 32): "arc3,rad=0.35",
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

    fig, axes = plt.subplots(1, 2, figsize=(8.8, 4.2))

    for ax, (pair, panel_title) in zip(axes, PANELS):
        panel_rows = [r for r in rows if r["pair"] == pair]
        panel_x = [r["x"] for r in panel_rows]
        panel_y = [r["y"] for r in panel_rows]
        pad_x = 0.10 * (max(panel_x) - min(panel_x))
        pad_y = 0.10 * (max(panel_y) - min(panel_y))

        for r in panel_rows:
            fam, cap = r["family"], r["capacity"]
            is_discordant = (fam, cap) in {("cloudphysics", 32), ("metakv", 128)}
            ax.scatter(
                r["x"], r["y"], color=FAMILY_COLOR[fam], marker="o",
                s=85 if is_discordant else 55,
                edgecolor="black" if is_discordant else "none",
                linewidth=1.2, zorder=3,
            )
            offset = DISCORDANT_ANNOTATIONS.get((pair, fam, cap))
            if offset is not None:
                ax.annotate(
                    f"{annotation_name(fam)}/C={cap}", (r["x"], r["y"]),
                    xytext=offset, textcoords="offset points", fontsize=8,
                    zorder=4,
                    arrowprops=dict(
                        arrowstyle="-", color="black", linewidth=0.6,
                        shrinkA=0, shrinkB=4,
                        connectionstyle=CONNECTIONSTYLE.get((pair, fam, cap), "arc3,rad=0.0"),
                    ),
                )

        ax.axhline(0, color="grey", linewidth=0.6, zorder=1)
        ax.axvline(0, color="grey", linewidth=0.6, zorder=1)
        ax.set_xlim(min(panel_x) - pad_x, max(panel_x) + pad_x)
        ax.set_ylim(min(panel_y) - pad_y, max(panel_y) + pad_y)
        ax.set_xlabel("Offline regret gap (H=16)")
        ax.set_title(panel_title, fontsize=10)
        ax.grid(alpha=0.3, linewidth=0.4)
        ax.tick_params(labelsize=8.5)

    axes[0].set_ylabel("Closed-loop miss-ratio gap")

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
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
