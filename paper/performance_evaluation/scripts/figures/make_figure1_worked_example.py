#!/usr/bin/env python3
"""Figure 1: the worked cache-decision example (docs/PE_WORKED_EXAMPLE.md).

Purely illustrative (no external data source -- the numbers here are the
hand-verified toy example, not a dataset artifact). Three rows (candidate
worlds A/B/C), four cache-state snapshots each, hit/miss annotated on the
connecting arrows, y_loss shown at the right of each row.
"""
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
OUT = REPO_ROOT / "paper/performance_evaluation/latex/figures/figure1_worked_example.pdf"

# (row label, [state after decision, after B, after E, after F], [(request, hit?)], y_loss)
ROWS = [
    ("World A\n(evict A)", ["B,C,D", "C,D,B", "D,B,E", "B,E,F"],
     [("B", True), ("E", False), ("F", False)], 2),
    ("World B\n(evict B)", ["A,C,D", "C,D,B", "D,B,E", "B,E,F"],
     [("B", False), ("E", False), ("F", False)], 3),
    ("World C\n(evict C)", ["A,B,D", "A,D,B", "D,B,E", "B,E,F"],
     [("B", True), ("E", False), ("F", False)], 2),
]


def draw_state_box(ax, cx, cy, text, w=1.5, h=0.6):
    ax.add_patch(Rectangle((cx - w / 2, cy - h / 2), w, h,
                            facecolor="#EEF3FA", edgecolor="black", linewidth=1.0))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=8)


def main():
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    xs = [0.9, 3.1, 5.3, 7.5]
    optimal_rows = {0, 2}  # World A and World C are optimal (tied), y_loss=2
    for ridx, (label, states, reqs, yloss) in enumerate(ROWS):
        y = 2.2 - ridx * 1.05
        ax.text(-1.55, y, label, ha="left", va="center", fontsize=9,
                fontweight="bold" if ridx in optimal_rows else "normal")
        for i, s in enumerate(states):
            draw_state_box(ax, xs[i], y, s)
        for i, (req, hit) in enumerate(reqs):
            arrow = FancyArrowPatch((xs[i] + 0.78, y), (xs[i + 1] - 0.78, y),
                                     arrowstyle="-|>", mutation_scale=12,
                                     color="#2E7D32" if hit else "#C62828")
            ax.add_patch(arrow)
            ax.text((xs[i] + xs[i + 1]) / 2, y + 0.28,
                     f"{req} {'HIT' if hit else 'MISS'}",
                     ha="center", va="bottom", fontsize=7.5,
                     color="#2E7D32" if hit else "#C62828")
        box_color = "#2E7D32" if ridx in optimal_rows else "#555555"
        ax.text(8.7, y, f"y_loss = {yloss}", ha="left", va="center",
                fontsize=9.5, fontweight="bold", color=box_color)

    ax.text(xs[0], 2.85, "after decision\n(evict + admit D)", ha="center", fontsize=7.5)
    ax.text(xs[1], 2.85, "after request B", ha="center", fontsize=7.5)
    ax.text(xs[2], 2.85, "after request E", ha="center", fontsize=7.5)
    ax.text(xs[3], 2.85, "after request F", ha="center", fontsize=7.5)

    ax.text(-1.55, -1.05, "Optimal candidate set = {A, C}\n(tied, y_loss=2); B is strictly worse (y_loss=3)",
            ha="left", va="center", fontsize=8.5, style="italic", color="#2E7D32")

    ax.set_xlim(-2.0, 10.5)
    ax.set_ylim(-1.5, 3.2)
    ax.axis("off")
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
