#!/usr/bin/env python3
"""Figure 2: target discriminativeness across family x capacity x horizon.

Source (validated, frozen, not recomputed):
  analysis/sigmod_target_discriminativeness_20260913/outputs/phase4_stratified_family_capacity_horizon.csv

Reads the CSV directly; no manuscript number is hard-coded. Run from the
repository root:
  python3 paper/performance_evaluation/scripts/figures/make_figure2_discriminativeness.py
"""
import csv
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
SRC = REPO_ROOT / "analysis/sigmod_target_discriminativeness_20260913/outputs/phase4_stratified_family_capacity_horizon.csv"
OUT = REPO_ROOT / "paper/performance_evaluation/latex/figures/figure2_discriminativeness.pdf"

FAMILIES = ["metacdn", "twemcache", "metakv", "cloudphysics", "wiki2018"]
CAPACITIES = [32, 64, 128, 256]
HORIZONS = [4, 8, 16]
COLORS = {32: "#4C72B0", 64: "#55A868", 128: "#C44E52", 256: "#8172B2"}


def load(path):
    rows = []
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            rows.append(row)
    return rows


def main():
    rows = load(SRC)
    data = {}
    for r in rows:
        key = (r["trace_family"], int(r["capacity"]), int(r["horizon"]))
        data[key] = 1.0 - float(r["all_tied_fraction"])  # discriminativeness

    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=True)
    x = range(len(FAMILIES))
    width = 0.2
    for ax, h in zip(axes, HORIZONS):
        for i, cap in enumerate(CAPACITIES):
            vals = [data.get((fam, cap, h), float("nan")) for fam in FAMILIES]
            offs = [xi + (i - 1.5) * width for xi in x]
            ax.bar(offs, vals, width=width, color=COLORS[cap], label=f"cap={cap}")
        ax.set_xticks(list(x))
        ax.set_xticklabels(FAMILIES, rotation=35, ha="right", fontsize=8)
        ax.set_title(f"H={h}", fontsize=10)
        ax.set_ylim(0, 1.02)
        ax.grid(axis="y", linewidth=0.4, alpha=0.5)
    axes[0].set_ylabel("Discriminativeness\n(1 - all-tied fraction)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=4, frameon=False,
               bbox_to_anchor=(0.5, 1.06), fontsize=9)
    fig.suptitle("")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
