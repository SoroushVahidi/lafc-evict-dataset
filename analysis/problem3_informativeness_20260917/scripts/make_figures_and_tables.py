from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
ANALYSIS = ROOT / "analysis" / "problem3_informativeness_20260917"
OUT = ANALYSIS / "outputs"
FIG = ANALYSIS / "figures"
PAPER_FIG = ROOT / "paper" / "performance_evaluation" / "latex" / "figures"
PAPER_TABLE = ROOT / "paper" / "performance_evaluation" / "latex" / "tables"

METHOD_LABELS = {
    "uniform_random": "Uniform random",
    "lru": "LRU",
    "clean_linear": "Clean linear",
    "clean_pairwise_logistic": "Clean pairwise",
    "frozen_hgb": "Frozen HGB",
}

METHOD_MARKERS = {
    "uniform_random": "o",
    "lru": "s",
    "clean_linear": "^",
    "clean_pairwise_logistic": "D",
    "frozen_hgb": "v",
}

METHOD_COLORS = {
    "uniform_random": "#4d4d4d",
    "lru": "#0072B2",
    "clean_linear": "#D55E00",
    "clean_pairwise_logistic": "#009E73",
    "frozen_hgb": "#CC79A7",
}

STRATA = ["Z", "Q1", "Q2", "Q3", "Q4"]


def _ordered_methods(df: pd.DataFrame) -> list[str]:
    return (
        df[["method", "method_order"]]
        .drop_duplicates()
        .sort_values("method_order")["method"]
        .tolist()
    )


def _save(fig: plt.Figure, basename: str) -> None:
    for directory in (FIG, PAPER_FIG):
        directory.mkdir(parents=True, exist_ok=True)
        fig.savefig(directory / f"{basename}.png", dpi=300, bbox_inches="tight")
        fig.savefig(directory / f"{basename}.pdf", bbox_inches="tight")


def make_figure_a(primary: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    for method in _ordered_methods(primary):
        df = primary[primary["method"] == method].sort_values("stratum_order")
        ax.plot(
            df["informativeness_stratum"],
            df["mean_regret"],
            marker=METHOD_MARKERS.get(method, "o"),
            linewidth=1.8,
            markersize=5,
            color=METHOD_COLORS.get(method),
            label=METHOD_LABELS.get(method, method),
        )
    ax.set_xlabel("Decision informativeness stratum")
    ax.set_ylabel("Mean realized regret (misses)")
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", color="#d0d0d0", linewidth=0.6)
    ax.legend(frameon=False, ncol=2, fontsize=8)
    fig.tight_layout()
    _save(fig, "figure_problem3_mean_regret_by_informativeness")
    plt.close(fig)


def make_figure_b(primary: pd.DataFrame) -> None:
    df = primary[primary["method"] != "uniform_random"].copy()
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    for method in _ordered_methods(df):
        m = df[df["method"] == method].sort_values("stratum_order")
        ax.plot(
            m["informativeness_stratum"],
            m["regret_improvement_vs_random"],
            marker=METHOD_MARKERS.get(method, "o"),
            linewidth=1.8,
            markersize=5,
            color=METHOD_COLORS.get(method),
            label=METHOD_LABELS.get(method, method),
        )
    ax.axhline(0, color="#222222", linewidth=0.8)
    ax.set_xlabel("Decision informativeness stratum")
    ax.set_ylabel("Regret improvement vs. random (misses)")
    ax.grid(axis="y", color="#d0d0d0", linewidth=0.6)
    ax.legend(frameon=False, ncol=2, fontsize=8)
    fig.tight_layout()
    _save(fig, "figure_problem3_improvement_vs_random")
    plt.close(fig)


def make_table(primary: pd.DataFrame) -> None:
    PAPER_TABLE.mkdir(parents=True, exist_ok=True)
    wanted = [
        "uniform_random",
        "lru",
        "clean_pairwise_logistic",
        "clean_linear",
        "frozen_hgb",
    ]
    available = [m for m in wanted if m in set(primary["method"])]
    rows = []
    for stratum in STRATA:
        s = primary[primary["informativeness_stratum"] == stratum]
        if s.empty:
            continue
        first = s.iloc[0]
        row = {
            "stratum": stratum,
            "n": int(first["n_decisions"]),
            "info_mean": float(first["info_mean"]),
        }
        for method in available:
            m = s[s["method"] == method].iloc[0]
            row[f"{method}_regret"] = float(m["mean_regret"])
            row[f"{method}_optimal"] = float(m["optimal_selection_rate"])
        rows.append(row)
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "table_informativeness_strata_source.csv", index=False)

    cols = "lrr" + "rr" * len(available)
    lines = [
        "\\begin{table}[t]",
        "  \\centering",
        "  \\caption{Informativeness-stratified selector utility. "
        "Regret is mean selected loss minus the decision minimum, in misses; "
        "Opt. is the optimal-set selection rate.}",
        "  \\label{tab:informativeness-strata}",
        "  \\resizebox{\\columnwidth}{!}{%",
        f"  \\begin{{tabular}}{{{cols}}}",
        "    \\toprule",
        "    Stratum & $n$ & E[random regret] & "
        + " & ".join(
            f"\\multicolumn{{2}}{{c}}{{{METHOD_LABELS[m]}}}" for m in available
        )
        + " \\\\",
        "    \\cmidrule(lr){4-" + str(3 + 2 * len(available)) + "}",
        "     & & & " + " & ".join(["regret & opt."] * len(available)) + " \\\\",
        "    \\midrule",
    ]
    for _, row in table.iterrows():
        cells = [
            row["stratum"],
            f"{int(row['n']):,}",
            f"{row['info_mean']:.4f}",
        ]
        for method in available:
            cells.append(f"{row[f'{method}_regret']:.4f}")
            cells.append(f"{row[f'{method}_optimal']:.4f}")
        lines.append("    " + " & ".join(cells) + " \\\\")
    lines.extend(["    \\bottomrule", "  \\end{tabular}%", "  }", "\\end{table}", ""])
    (PAPER_TABLE / "table_informativeness_strata.tex").write_text("\n".join(lines))


def main() -> None:
    primary = pd.read_csv(OUT / "primary_method_by_informativeness.csv")
    primary = primary[primary["informativeness_stratum"].isin(STRATA)].copy()
    make_figure_a(primary)
    make_figure_b(primary)
    make_table(primary)


if __name__ == "__main__":
    main()
