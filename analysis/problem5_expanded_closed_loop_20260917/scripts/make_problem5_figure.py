"""Problem-5 Phase 8: policy-spread vs. offline-discriminativeness figure.

One point per family x capacity cell (n=10): x = offline discriminative
fraction (1 - all_tied_fraction) at H=16, y = expanded 7-policy closed-loop
miss-ratio spread (max-min across LRU/MRU/random/SIEVE/ARC/LIRS/S3-FIFO).
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ANALYSIS_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = ANALYSIS_DIR / "outputs"
FIG_DIR = ANALYSIS_DIR / "figures"

# "cloudphysics" is the internal ingestion-path id for the family the
# manuscript always displays as "alibaba-block" (matches
# table_tier1_closed_loop.tex's naming).
DISPLAY_FAMILY = {
    "cloudphysics": "alibaba-block",
    "metacdn": "metacdn",
    "metakv": "metakv",
    "twemcache": "twemcache",
    "wiki2018": "wiki2018",
}
FAMILY_MARKERS = {
    "cloudphysics": "o",
    "metacdn": "s",
    "metakv": "^",
    "twemcache": "D",
    "wiki2018": "v",
}
FAMILY_COLORS = {
    "cloudphysics": "#4C72B0",
    "metacdn": "#DD8452",
    "metakv": "#55A868",
    "twemcache": "#C44E52",
    "wiki2018": "#8172B2",
}


def main() -> None:
    rows = list(csv.DictReader(open(OUT_DIR / "problem5_policy_spread.csv", encoding="utf-8")))

    fig, ax = plt.subplots(figsize=(6.0, 4.4))
    for row in rows:
        fam = row["family"]
        x = float(row["offline_discriminative_fraction"])
        y32 = None
        marker = FAMILY_MARKERS[fam]
        color = FAMILY_COLORS[fam]
        y = float(row["policy_spread_all7"])
        cap = int(row["capacity"])
        fillstyle = "full" if cap == 32 else "none"
        ax.scatter(
            [x], [y], marker=marker, s=90,
            facecolors=color if fillstyle == "full" else "none",
            edgecolors=color, linewidths=1.6,
            label=f"{DISPLAY_FAMILY[fam]} (cap {cap})",
        )

    ax.set_xlabel("Offline discriminative fraction (H=16, 1 - all-tied)")
    ax.set_ylabel("Expanded closed-loop policy spread\n(max-min miss ratio, 7 policies)")
    ax.set_title(
        "Closed-loop policy spread vs. offline discriminativeness\n(filled = capacity 32, open = capacity 128)",
        fontsize=10,
    )
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.02, max(float(r["policy_spread_all7"]) for r in rows) * 1.15)

    # De-duplicate legend by family only (marker shape), noting fill=capacity.
    handles = [
        plt.Line2D([0], [0], marker=FAMILY_MARKERS[f], color="w",
                   markerfacecolor=FAMILY_COLORS[f], markeredgecolor=FAMILY_COLORS[f],
                   markersize=9, label=DISPLAY_FAMILY[f])
        for f in FAMILY_MARKERS
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=8, frameon=False)
    fig.tight_layout()

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / "figure_problem5_policy_spread_vs_discriminativeness.pdf")
    fig.savefig(FIG_DIR / "figure_problem5_policy_spread_vs_discriminativeness.png", dpi=200)
    print("wrote figures")


if __name__ == "__main__":
    main()
