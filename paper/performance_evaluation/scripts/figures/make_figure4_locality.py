#!/usr/bin/env python3
"""Figure 4: trace-derived locality vs. offline discriminativeness and
closed-loop policy separation (two panels, shared x-axis).

Source (validated, frozen, not recomputed):
  analysis/closed_loop_mechanistic_analysis_20260914/outputs/mechanism_comparison.csv

n=10 (family x capacity). Exploratory, not pre-registered; correlations are
reported in the caption from correlation_summary.csv, not treated as
population-scale inference.
"""
import csv
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
SRC = REPO_ROOT / "analysis/closed_loop_mechanistic_analysis_20260914/outputs/mechanism_comparison.csv"
CORR = REPO_ROOT / "analysis/closed_loop_mechanistic_analysis_20260914/outputs/correlation_summary.csv"
OUT = REPO_ROOT / "paper/performance_evaluation/latex/figures/figure4_locality.pdf"

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
DISPLAY_NAME = {"cloudphysics": "alibaba-block"}
MARKER = {32: "o", 128: "^"}


def load_corr():
    out = {}
    with open(CORR, newline="") as fh:
        for r in csv.DictReader(fh):
            out[r["comparison"]] = (r["n"], float(r["pearson_r"]))
    return out


def main():
    rows = []
    with open(SRC, newline="") as fh:
        for r in csv.DictReader(fh):
            rows.append(r)
    corr = load_corr()

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.0))
    for r in rows:
        fam, cap = r["family"], int(r["capacity"])
        x = float(r["predicted_lru_hit_rate"])
        y1 = float(r["offline_all_tied_fraction_H16"])
        y2 = float(r["cl_mru_minus_lru_miss_ratio_gap"])
        axes[0].scatter(x, y1, color=FAMILY_COLOR[fam], marker=MARKER[cap], s=55)
        axes[1].scatter(x, y2, color=FAMILY_COLOR[fam], marker=MARKER[cap], s=55)

    r0 = corr["pooled_n10_LRU_hit_rate_vs_offline_all_tied_fraction"][1]
    r1 = corr["pooled_n10_LRU_hit_rate_vs_closed_loop_MRU_LRU_gap"][1]
    axes[0].set_xlabel("Trace-derived LRU hit rate")
    axes[0].set_ylabel("Offline all-tied fraction (H=16)")
    axes[0].set_title(f"Locality vs. tie rate (r={r0:.2f}, n=10)", fontsize=9.5)
    axes[1].set_xlabel("Trace-derived LRU hit rate")
    axes[1].set_ylabel("Closed-loop |MRU-LRU| miss-ratio gap")
    axes[1].set_title(f"Locality vs. policy separation (r={r1:.2f}, n=10)", fontsize=9.5)
    for ax in axes:
        ax.grid(alpha=0.3, linewidth=0.4)

    fam_handles = [plt.Line2D([0], [0], marker="s", color="w",
                               markerfacecolor=c, markersize=8,
                               label=DISPLAY_NAME.get(f, f))
                   for f, c in FAMILY_COLOR.items()]
    cap_handles = [plt.Line2D([0], [0], marker=m, color="black", linestyle="",
                               markersize=7, label=f"cap={c}")
                  for c, m in MARKER.items()]
    fig.legend(handles=fam_handles + cap_handles, loc="upper center",
               ncol=7, frameon=False, bbox_to_anchor=(0.5, 1.08), fontsize=8)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
