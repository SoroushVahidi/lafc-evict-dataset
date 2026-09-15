#!/usr/bin/env python3
"""Figure 5: validated continuation-policy robustness.

Sources:
  - analysis/continuation_policy_mru_population_census_20260914/validated/
    20260914T042528Z_1a29e773a113/figure5_mru_continuation_data.csv
  - analysis/continuation_policy_mru_population_census_20260914/validated/
    20260914T042528Z_1a29e773a113/summary_by_capacity.csv
  - analysis/continuation_policy_sensitivity_full_20260914/outputs/
    20260914T040333Z_1f66342be435/scientific_analysis.json

The sampled random series is plotted only at capacities 32 and 128. There is
no population-scale random-continuation result in this figure.
"""
from __future__ import annotations

import csv
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
VALIDATED = (
    REPO_ROOT
    / "analysis/continuation_policy_mru_population_census_20260914/validated"
    / "20260914T042528Z_1a29e773a113"
)
FIG5_SOURCE = VALIDATED / "figure5_mru_continuation_data.csv"
POP_BY_CAP = VALIDATED / "summary_by_capacity.csv"
SAMPLED = (
    REPO_ROOT
    / "analysis/continuation_policy_sensitivity_full_20260914/outputs"
    / "20260914T040333Z_1f66342be435/scientific_analysis.json"
)
OUT = REPO_ROOT / "paper/performance_evaluation/latex/figures/figure5_continuation_robustness.pdf"

CAPS_ALL = [32, 64, 128, 256]
CAPS_SAMPLED = [32, 128]


def load_population_by_capacity() -> dict[int, dict[str, float]]:
    # Opening FIG5_SOURCE is intentional: this is the validated Figure 5 source
    # artifact. The capacity aggregates below come from the companion validated
    # summary table so plotted markers are weighted by decision-horizon units.
    with open(FIG5_SOURCE, newline="", encoding="utf-8") as fh:
        source_rows = list(csv.DictReader(fh))
    if not source_rows:
        raise RuntimeError(f"empty Figure 5 source data: {FIG5_SOURCE}")

    out: dict[int, dict[str, float]] = {}
    with open(POP_BY_CAP, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["analysis_set"] != "C_discriminative_under_LRU":
                continue
            cap = int(row["capacity"])
            out[cap] = {
                "jaccard": float(row["jaccard_mean"]),
                "ccr": float(row["ccr_mean"]),
                "still": float(row["fraction_lru_optimal_still_mru_optimal"]),
            }
    return out


def load_sampled() -> dict[str, dict[int, dict[str, float]]]:
    data = json.loads(SAMPLED.read_text(encoding="utf-8"))
    out: dict[str, dict[int, dict[str, float]]] = {}
    for policy in ("mru", "random_mean"):
        out[policy] = {}
        by_cap = data["PRIMARY_ANALYSIS"][policy]["by_capacity_setC"]
        for cap in CAPS_SAMPLED:
            cell = by_cap[str(cap)]
            out[policy][cap] = {
                "jaccard": float(cell["mean_jaccard"]),
                "ccr": float(cell["mean_ccr"]),
                "still": float(cell["mean_prob_still_optimal"]),
            }
    return out


def plot_series(ax, xs, ys, label, color, marker, linestyle="-", fillstyle="full"):
    ax.plot(
        xs,
        ys,
        label=label,
        color=color,
        marker=marker,
        linewidth=1.8,
        markersize=6,
        linestyle=linestyle,
        markerfacecolor=color if fillstyle == "full" else "white",
        markeredgecolor=color,
    )


def main() -> None:
    pop = load_population_by_capacity()
    sampled = load_sampled()

    fig, axes = plt.subplots(1, 3, figsize=(11.2, 3.6))
    metrics = [
        ("jaccard", "Mean optimal-set Jaccard", (0.68, 1.02), False),
        ("ccr", "Mean cross-continuation regret", (1e-5, 1.2), True),
        ("still", "Fraction LRU-optimal still optimal", (0.68, 1.02), False),
    ]
    colors = {
        "population_mru": "#4C72B0",
        "sampled_mru": "#55A868",
        "sampled_random": "#C44E52",
    }

    for ax, (metric, ylabel, ylim, logy) in zip(axes, metrics):
        plot_series(
            ax,
            CAPS_ALL,
            [pop[c][metric] for c in CAPS_ALL],
            "population MRU",
            colors["population_mru"],
            "o",
        )
        plot_series(
            ax,
            CAPS_SAMPLED,
            [sampled["mru"][c][metric] for c in CAPS_SAMPLED],
            "sampled MRU",
            colors["sampled_mru"],
            "D",
            linestyle="--",
            fillstyle="none",
        )
        plot_series(
            ax,
            CAPS_SAMPLED,
            [sampled["random_mean"][c][metric] for c in CAPS_SAMPLED],
            "sampled mean-random",
            colors["sampled_random"],
            "s",
            linestyle=":",
            fillstyle="none",
        )
        ax.set_xlabel("Capacity")
        ax.set_ylabel(ylabel)
        ax.set_xticks(CAPS_ALL)
        ax.grid(alpha=0.3, linewidth=0.4)
        if logy:
            ax.set_yscale("log")
            ax.axhline(1.0, color="#777777", linewidth=0.8, linestyle="--")
        else:
            ax.axhline(0.8, color="#777777", linewidth=0.8, linestyle="--")
        ax.set_ylim(*ylim)

    axes[0].text(252, 0.805, "ROBUST threshold", ha="right", va="bottom", fontsize=7, color="#666666")
    axes[1].text(252, 0.72, "1 miss threshold", ha="right", va="top", fontsize=7, color="#666666")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.99))
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
