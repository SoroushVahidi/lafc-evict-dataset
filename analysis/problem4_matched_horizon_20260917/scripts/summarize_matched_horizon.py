from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from collections import defaultdict
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
ANALYSIS = ROOT / "analysis" / "problem4_matched_horizon_20260917"
OUT = ANALYSIS / "outputs"
ART = ANALYSIS / "artifacts"
FIG = ANALYSIS / "figures"
PAPER_FIG = ROOT / "paper" / "performance_evaluation" / "latex" / "figures"
PAPER_TAB = ROOT / "paper" / "performance_evaluation" / "latex" / "tables"

DECISION_VIEW = Path(
    "/home/soroush/projects/lafc-evict-dataset/repo/release/"
    "lafc-evict-v0.1-open-current-contract-preserved/data/decision_view/decision_view.parquet"
)
OLD_HORIZON = ROOT / "analysis" / "problem3_informativeness_20260917" / "outputs" / "horizon_h16_h128_primary_decision_micro_summary.csv"
OLD_COMBINED = ROOT / "analysis" / "problem3_informativeness_20260917" / "outputs" / "horizon_h16_h128_combined_family_capacity_horizon.csv"
CANONICAL_REGEN_MANIFEST = Path(
    "/home/soroush/projects/augmented-caching/worktrees/pe-h16-h128-comparative-integration-20260916/"
    "configs/pe_long_horizon_canonical_regen_20260916/manifest.json"
)

READER_FAMILY = {
    "cloudphysics": "alibaba-block",
    "metacdn": "metacdn",
    "metakv": "metakv",
    "twemcache": "twemcache",
    "wiki2018": "wiki2018",
}
HORIZONS = [16, 32, 64, 128]
CAPACITIES = [32, 64, 128, 256]


def git_value(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except Exception:
        return "UNKNOWN"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def key_manifest() -> dict[str, object]:
    con = duckdb.connect()
    key_path = ART / "common_population_keys.parquet"
    key_sql_path = str(key_path).replace("'", "''")
    ART.mkdir(parents=True, exist_ok=True)
    con.execute(
        f"""
        copy (
            select
                trace_family,
                case trace_family
                    when 'cloudphysics' then 'alibaba-block'
                    else trace_family
                end as reader_family,
                trace_name,
                capacity,
                decision_t,
                split,
                trace_name || '|' || trace_family || '|cap=' || capacity::varchar ||
                    '|t=' || decision_t::varchar || '|split=' || split as physical_key
            from read_parquet(?)
            where horizon = 16
            order by trace_family, capacity, trace_name, decision_t, split
        ) to '{key_sql_path}' (format parquet)
        """,
        [str(DECISION_VIEW)],
    )
    rows = con.execute(
        """
        select trace_family, trace_name, capacity, decision_t, split
        from read_parquet(?)
        order by trace_family, capacity, trace_name, decision_t, split
        """,
        [str(key_path)],
    ).fetchall()
    if len(rows) != len(set(rows)):
        raise AssertionError("duplicate canonical physical decision keys")
    by_cell: dict[tuple[str, int], list[tuple[str, str, int, int, str]]] = defaultdict(list)
    digest = hashlib.sha256()
    for row in rows:
        family, trace_name, capacity, decision_t, split = row
        key = f"{trace_name}|{family}|cap={int(capacity)}|t={int(decision_t)}|split={split}"
        digest.update(key.encode("utf-8"))
        digest.update(b"\n")
        by_cell[(str(family), int(capacity))].append(row)

    cells = []
    for (family, capacity), items in sorted(by_cell.items()):
        h = hashlib.sha256()
        split_counts: dict[str, int] = defaultdict(int)
        for trace_family, trace_name, cap, decision_t, split in items:
            key = f"{trace_name}|{trace_family}|cap={int(cap)}|t={int(decision_t)}|split={split}"
            h.update(key.encode("utf-8"))
            h.update(b"\n")
            split_counts[str(split)] += 1
        cells.append(
            {
                "trace_family": family,
                "reader_family": READER_FAMILY[family],
                "capacity": capacity,
                "decision_count": len(items),
                "key_sha256": h.hexdigest(),
                "min_decision_t": min(int(r[3]) for r in items),
                "max_decision_t": max(int(r[3]) for r in items),
                "split_counts": dict(sorted(split_counts.items())),
            }
        )
    manifest = {
        "artifact": "common matched H16/H32/H64/H128 physical decision population",
        "source_decision_view": str(DECISION_VIEW),
        "source_decision_view_sha256": sha256_file(DECISION_VIEW),
        "common_population_keys": str(key_path.relative_to(ROOT)),
        "common_population_keys_sha256": sha256_file(key_path),
        "physical_key_format": "trace_name|trace_family|cap=<capacity>|t=<decision_t>|split=<split>",
        "horizons": HORIZONS,
        "total_decisions": len(rows),
        "global_key_sha256": digest.hexdigest(),
        "cells": cells,
    }
    write_json(ART / "common_population_manifest.json", manifest)
    return manifest


def aggregate_metrics(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    raw = raw.copy()
    raw["reader_family"] = raw["trace_family"].map(READER_FAMILY)
    raw["candidate_rows"] = raw["n_decisions"] * raw["capacity"]

    def agg(group: pd.DataFrame) -> pd.Series:
        n = group["n_decisions"].sum()
        return pd.Series(
            {
                "cell_count": len(group),
                "decisions": n,
                "candidate_rows": group["candidate_rows"].sum(),
                "all_tied_fraction": (group["all_tied_fraction"] * group["n_decisions"]).sum() / n,
                "discriminative_fraction": (group["discriminative_fraction"] * group["n_decisions"]).sum() / n,
                "random_optimal_probability": (group["random_optimal_probability"] * group["n_decisions"]).sum() / n,
                "expected_random_regret": (group["expected_random_regret"] * group["n_decisions"]).sum() / n,
                "mean_optimal_set_fraction": (group["mean_optimal_set_fraction"] * group["n_decisions"]).sum() / n,
                "mean_loss_range": (group["mean_loss_range"] * group["n_decisions"]).sum() / n,
                "mean_strict_preference_density": (group["mean_strict_preference_density"] * group["n_decisions"]).sum() / n,
            }
        )

    micro = raw.groupby("horizon", as_index=False).apply(agg, include_groups=False).reset_index(drop=True)
    micro.insert(0, "weighting", "DECISION_MICRO")
    micro.insert(1, "scope", "MATCHED_ALL_FIVE_FAMILIES")
    family = raw.groupby(["reader_family", "trace_family", "horizon"], as_index=False).apply(agg, include_groups=False).reset_index(drop=True)
    capacity = raw.groupby(["capacity", "horizon"], as_index=False).apply(agg, include_groups=False).reset_index(drop=True)
    raw.to_csv(OUT / "matched_family_capacity_horizon_metrics.csv", index=False)
    micro.to_csv(OUT / "matched_primary_micro_summary.csv", index=False)
    family.to_csv(OUT / "matched_family_summary.csv", index=False)
    capacity.to_csv(OUT / "matched_capacity_summary.csv", index=False)
    return micro, family, capacity


def aggregate_pairs(pair_raw: pd.DataFrame) -> pd.DataFrame:
    def agg(group: pd.DataFrame) -> pd.Series:
        n = group["n_decisions"].sum()
        fields = [
            "tied_to_tied",
            "tied_to_discriminative",
            "discriminative_to_tied",
            "discriminative_to_discriminative",
            "info_increase",
            "info_decrease",
            "info_unchanged",
        ]
        values = {field: group[field].sum() for field in fields}
        values.update(
            {
                "n_decisions": n,
                "mean_delta_expected_random_regret": (group["mean_delta_expected_random_regret"] * group["n_decisions"]).sum() / n,
                "mean_delta_optimal_set_fraction": (group["mean_delta_optimal_set_fraction"] * group["n_decisions"]).sum() / n,
                "mean_delta_loss_range": (group["mean_delta_loss_range"] * group["n_decisions"]).sum() / n,
            }
        )
        return pd.Series(values)

    pair_raw = pair_raw.copy()
    pair_raw["reader_family"] = pair_raw["trace_family"].map(READER_FAMILY)
    micro = pair_raw.groupby("pair", as_index=False).apply(agg, include_groups=False).reset_index(drop=True)
    by_cell = pair_raw.sort_values(["trace_family", "capacity", "pair"])
    micro.to_csv(OUT / "matched_paired_transition_micro_summary.csv", index=False)
    by_cell.to_csv(OUT / "matched_paired_transition_by_cell.csv", index=False)
    return micro


def aggregate_mono(mono_raw: pd.DataFrame) -> pd.DataFrame:
    mono_raw = mono_raw.copy()
    mono_raw["reader_family"] = mono_raw["trace_family"].map(READER_FAMILY)
    sums = mono_raw[
        [
            "n_decisions",
            "h16_to_h128_info_increase",
            "h16_to_h128_info_decrease",
            "h16_to_h128_info_unchanged",
            "adjacent_all_nondecreasing",
            "adjacent_all_nonincreasing",
            "adjacent_mixed",
        ]
    ].sum()
    out = pd.DataFrame([sums])
    n = float(out.loc[0, "n_decisions"])
    for col in out.columns:
        if col != "n_decisions":
            out[f"{col}_fraction"] = out[col] / n
    out.to_csv(OUT / "matched_monotonicity_micro_summary.csv", index=False)
    mono_raw.to_csv(OUT / "matched_monotonicity_by_cell.csv", index=False)
    return out


def validate_against_canonical(raw: pd.DataFrame, manifest: dict[str, object]) -> dict[str, object]:
    con = duckdb.connect()
    h16 = raw[raw["horizon"] == 16].copy()
    canon = con.execute(
        """
        select
          trace_family,
          capacity,
          count(*) as n_decisions,
          avg((tie_count = candidate_count)::int) as all_tied_fraction,
          avg(optimal_candidate_count::double / candidate_count) as random_optimal_probability,
          avg(regret_mean) as expected_random_regret,
          avg(regret_max) as mean_loss_range
        from read_parquet(?)
        where horizon = 16
        group by trace_family, capacity
        order by trace_family, capacity
        """,
        [str(DECISION_VIEW)],
    ).fetchdf()
    merged = h16.merge(canon, on=["trace_family", "capacity"], suffixes=("_matched", "_canonical"))
    checks = []
    for _, row in merged.iterrows():
        for field in [
            "n_decisions",
            "all_tied_fraction",
            "random_optimal_probability",
            "expected_random_regret",
            "mean_loss_range",
        ]:
            a = float(row[f"{field}_matched"])
            b = float(row[f"{field}_canonical"])
            checks.append(
                {
                    "trace_family": row["trace_family"],
                    "capacity": int(row["capacity"]),
                    "field": field,
                    "matched": a,
                    "canonical": b,
                    "abs_diff": abs(a - b),
                    "pass": abs(a - b) < 1e-12,
                }
            )
    old = pd.read_csv(OLD_COMBINED)
    long = raw[raw["horizon"].isin([32, 64, 128])].copy()
    old_long = old[old["horizon"].isin([32, 64, 128])].copy()
    old_long = old_long.rename(columns={"internal_family": "trace_family", "decision_count": "n_decisions", "mean_random_regret": "expected_random_regret"})
    long_cmp = long.merge(old_long, on=["trace_family", "capacity", "horizon"], suffixes=("_matched", "_old"))
    long_checks = []
    for _, row in long_cmp.iterrows():
        same_expected = row["trace_family"] != "twemcache"
        fields = ["n_decisions", "all_tied_fraction", "random_optimal_probability", "expected_random_regret"]
        max_diff = max(abs(float(row[f"{f}_matched"]) - float(row[f"{f}_old"])) for f in fields)
        long_checks.append(
            {
                "trace_family": row["trace_family"],
                "capacity": int(row["capacity"]),
                "horizon": int(row["horizon"]),
                "expected_to_match_old": same_expected,
                "max_abs_diff": max_diff,
                "pass": (max_diff < 1e-12) if same_expected else (max_diff > 0),
            }
        )
    validation = {
        "status": "PASS" if all(c["pass"] for c in checks) and all(c["pass"] for c in long_checks) else "FAIL",
        "h16_matches_canonical_release": checks,
        "h32_h64_h128_old_artifact_comparison": long_checks,
        "equal_count_every_horizon": raw.groupby("horizon")["n_decisions"].sum().nunique() == 1,
        "common_population_total": manifest["total_decisions"],
        "source_branch": git_value("branch", "--show-current"),
        "source_head": git_value("rev-parse", "HEAD"),
    }
    write_json(OUT / "validation.json", validation)
    return validation


def old_vs_matched(micro: pd.DataFrame) -> pd.DataFrame:
    old = pd.read_csv(OLD_HORIZON)
    old = old.rename(columns={"mean_random_regret": "expected_random_regret"})
    rows = []
    for h in HORIZONS:
        m = micro[micro["horizon"] == h].iloc[0]
        if h == 16:
            o = old[old["horizon"] == 16].iloc[0]
        else:
            o = old[old["horizon"] == h].iloc[0]
        rows.append(
            {
                "horizon": h,
                "old_decisions": int(o["decisions"]),
                "matched_decisions": int(m["decisions"]),
                "old_all_tied_fraction": float(o["all_tied_fraction"]),
                "matched_all_tied_fraction": float(m["all_tied_fraction"]),
                "old_random_optimal_probability": float(o["random_optimal_probability"]),
                "matched_random_optimal_probability": float(m["random_optimal_probability"]),
                "old_expected_random_regret": float(o["expected_random_regret"]),
                "matched_expected_random_regret": float(m["expected_random_regret"]),
            }
        )
    out = pd.DataFrame(rows)
    old_h16 = out[out["horizon"] == 16].iloc[0]
    matched_h16 = out[out["horizon"] == 16].iloc[0]
    h32 = out[out["horizon"] == 32].iloc[0]
    decomposition = {
        "all_tied_population_effect_old_h16_to_matched_h16": matched_h16["matched_all_tied_fraction"] - old_h16["old_all_tied_fraction"],
        "all_tied_horizon_effect_matched_h16_to_h32": h32["matched_all_tied_fraction"] - matched_h16["matched_all_tied_fraction"],
        "regret_population_effect_old_h16_to_matched_h16": matched_h16["matched_expected_random_regret"] - old_h16["old_expected_random_regret"],
        "regret_horizon_effect_matched_h16_to_h32": h32["matched_expected_random_regret"] - matched_h16["matched_expected_random_regret"],
        "random_optimal_population_effect_old_h16_to_matched_h16": matched_h16["matched_random_optimal_probability"] - old_h16["old_random_optimal_probability"],
        "random_optimal_horizon_effect_matched_h16_to_h32": h32["matched_random_optimal_probability"] - matched_h16["matched_random_optimal_probability"],
    }
    out.to_csv(OUT / "old_vs_matched_micro_summary.csv", index=False)
    write_json(OUT / "old_vs_matched_decomposition.json", decomposition)
    return out


def make_table(micro: pd.DataFrame) -> None:
    PAPER_TAB.mkdir(parents=True, exist_ok=True)
    lines = [
        "\\begin{table}[t]",
        "  \\centering",
        "  \\small",
        "  \\caption{Matched-population long-horizon sensitivity. Every row uses the same canonical physical eviction-decision population.}",
        "  \\label{tab:matched-long-horizon}",
        "  \\begin{tabular}{rrrrrr}",
        "    \\toprule",
        "    Horizon & Decisions & All-tied & Discrim. & Rand. opt. & E[rand. regret] \\\\",
        "    \\midrule",
    ]
    for _, row in micro.sort_values("horizon").iterrows():
        lines.append(
            "    "
            + f"{int(row['horizon'])} & {int(row['decisions']):,} & "
            + f"{row['all_tied_fraction']:.4f} & {row['discriminative_fraction']:.4f} & "
            + f"{row['random_optimal_probability']:.4f} & "
            + f"{row['expected_random_regret']:.4f} \\\\"
        )
    lines.extend(["    \\bottomrule", "  \\end{tabular}", "\\end{table}", ""])
    (PAPER_TAB / "table_matched_long_horizon_sensitivity.tex").write_text("\n".join(lines), encoding="utf-8")


def make_figure(raw: pd.DataFrame, micro: pd.DataFrame) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    PAPER_FIG.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6.8, 3.6))
    raw = raw.copy()
    raw["cell"] = raw["trace_family"].map(READER_FAMILY) + " c" + raw["capacity"].astype(str)
    for _, cell in raw[["cell"]].drop_duplicates().iterrows():
        sub = raw[raw["cell"] == cell["cell"]].sort_values("horizon")
        ax.plot(sub["horizon"], sub["all_tied_fraction"], color="#b8b8b8", linewidth=0.8, alpha=0.7)
    ax.plot(
        micro["horizon"],
        micro["all_tied_fraction"],
        color="#0072B2",
        marker="o",
        linewidth=2.2,
        label="matched micro aggregate",
    )
    ax.set_xlabel("Horizon")
    ax.set_ylabel("All-tied fraction")
    ax.set_xticks(HORIZONS)
    ax.set_ylim(0, 1.02)
    ax.grid(axis="y", color="#d0d0d0", linewidth=0.6)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    for directory in [FIG, PAPER_FIG]:
        fig.savefig(directory / "figure_problem4_matched_long_horizon_sensitivity.pdf", bbox_inches="tight")
        fig.savefig(directory / "figure_problem4_matched_long_horizon_sensitivity.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    raw.to_csv(OUT / "figure_problem4_matched_long_horizon_source.csv", index=False)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)
    manifest = key_manifest()
    raw = pd.read_csv(OUT / "matched_cell_horizon_metrics_raw.csv")
    pair_raw = pd.read_csv(OUT / "matched_cell_pair_transitions_raw.csv")
    mono_raw = pd.read_csv(OUT / "matched_cell_monotonicity_raw.csv")
    micro, family, capacity = aggregate_metrics(raw)
    pairs = aggregate_pairs(pair_raw)
    mono = aggregate_mono(mono_raw)
    validation = validate_against_canonical(raw, manifest)
    if validation["status"] != "PASS":
        raise SystemExit("validation failed; see outputs/validation.json")
    old_vs_matched(micro)
    make_table(micro)
    make_figure(raw, micro)
    write_json(
        OUT / "source_state.json",
        {
            "source_branch": git_value("branch", "--show-current"),
            "source_sha": git_value("rev-parse", "HEAD"),
            "worktree": str(ROOT),
            "decision_view": str(DECISION_VIEW),
            "canonical_regen_manifest": str(CANONICAL_REGEN_MANIFEST),
            "matched_core_raw_files": [
                "matched_cell_horizon_metrics_raw.csv",
                "matched_cell_pair_transitions_raw.csv",
                "matched_cell_monotonicity_raw.csv",
            ],
        },
    )


if __name__ == "__main__":
    main()
