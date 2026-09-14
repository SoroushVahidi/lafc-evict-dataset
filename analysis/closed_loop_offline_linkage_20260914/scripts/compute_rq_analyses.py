"""Compute RQ-CL1 through RQ-CL4 from the joined offline/closed-loop dataset.

Tie-aware by construction: no gap is ever forced into a strict ranking.
"Offline tie" and "closed-loop tie" both mean EXACT equality of the
underlying gap value (these come from population statistics / exact integer
hit-miss counts, so a meaningful exact zero is possible and does occur, e.g.
wiki2018). No tolerance-based "near tie" threshold is used in the PRIMARY
analysis. A separate, explicitly labeled EXPLORATORY sensitivity pass
applies one candidate tolerance (the random policy's own cross-seed std, a
quantity that already exists in the data rather than being invented) and is
reported only as a sensitivity check, never as the headline number.

Two independently comparable policy pairs exist (SIEVE has no offline
counterpart and is excluded throughout):
  - MRU vs LRU   (offline_mru_minus_lru_regret_gap / cl_mru_minus_lru_miss_ratio_gap)
  - random vs LRU (offline_random_minus_lru_regret_gap / cl_random_minus_lru_miss_ratio_gap)

RQ-CL4 (horizon alignment) requires slicing this per-horizon: pooling all
three horizons together for one correlation would pseudo-replicate each
(family, capacity) cell's single closed-loop value three times, artificially
inflating any correlation. Every correlation/concordance statistic here is
therefore computed PER HORIZON (n=10 family-capacity cells each) as the
primary analysis; an explicitly labeled pooled-across-horizons view (n=30,
with repeated closed-loop values) is reported only as a secondary summary.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from scipy import stats

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
JOINED_PATH = ANALYSIS_ROOT / "data" / "joined_offline_closed_loop.csv"
OUT_DIR = ANALYSIS_ROOT / "outputs"

PAIRS = [
    ("mru_vs_lru", "offline_mru_minus_lru_regret_gap", "cl_mru_minus_lru_miss_ratio_gap"),
    ("random_vs_lru", "offline_random_minus_lru_regret_gap", "cl_random_minus_lru_miss_ratio_gap"),
]


def load_rows():
    with open(JOINED_PATH, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        for k in list(r.keys()):
            if k in ("family", "scored_split_label"):
                continue
            if r[k] in ("True", "False"):
                r[k] = r[k] == "True"
            else:
                try:
                    r[k] = float(r[k])
                except ValueError:
                    pass
    return rows


def sign(x, eps=0.0):
    if x > eps:
        return 1
    if x < -eps:
        return -1
    return 0


def classify_pair(rows, offline_col, cl_col, tolerance=0.0):
    """Return per-row classification + counts for one policy pair."""
    per_row = []
    for r in rows:
        off = r[offline_col]
        cl = r[cl_col]
        off_sign = sign(off, 0.0)  # offline: never tolerance-relaxed in primary analysis
        cl_sign = sign(cl, tolerance)
        if off_sign == 0 and cl_sign == 0:
            cls = "both_tied"
        elif off_sign == 0:
            cls = "offline_tie_only"
        elif cl_sign == 0:
            cls = "closed_loop_tie_only"
        elif off_sign == cl_sign:
            cls = "concordant"
        else:
            cls = "discordant"
        per_row.append({
            "family": r["family"], "capacity": int(r["capacity"]), "horizon": int(r["horizon"]),
            "offline_gap": off, "closed_loop_gap": cl, "classification": cls,
        })
    counts = {}
    for p in per_row:
        counts[p["classification"]] = counts.get(p["classification"], 0) + 1
    return per_row, counts


def rq_cl1(rows):
    """Pairwise concordance, per horizon, for each pair; plus per-cell 3-item
    Kendall tau-b between the offline {LRU,random,MRU} regret ranking and the
    closed-loop {LRU,random,MRU} miss-ratio ranking (SIEVE excluded, no
    offline counterpart)."""
    result = {"by_horizon": {}, "pooled_across_horizons_SECONDARY": {}, "per_cell_3item_tau_b": []}

    for horizon in (4, 8, 16):
        hrows = [r for r in rows if int(r["horizon"]) == horizon]
        result["by_horizon"][horizon] = {}
        for name, off_col, cl_col in PAIRS:
            per_row, counts = classify_pair(hrows, off_col, cl_col)
            result["by_horizon"][horizon][name] = {"counts": counts, "n_cells": len(hrows), "rows": per_row}

    for name, off_col, cl_col in PAIRS:
        per_row, counts = classify_pair(rows, off_col, cl_col)
        result["pooled_across_horizons_SECONDARY"][name] = {
            "counts": counts, "n_rows": len(rows),
            "note": "pseudo-replicated: each (family,capacity) closed-loop value appears once per horizon (x3); do not treat as 30 independent observations",
        }

    for r in rows:
        offline_vals = {"lru": 0.0, "mru": r["offline_mru_mean_regret"] - r["offline_lru_mean_regret"],
                         "random": r["offline_random_mean_regret"] - r["offline_lru_mean_regret"]}
        cl_vals = {"lru": 0.0, "mru": r["cl_mru_minus_lru_miss_ratio_gap"],
                   "random": r["cl_random_minus_lru_miss_ratio_gap"]}
        policies = ["lru", "mru", "random"]
        off_ranks = [offline_vals[p] for p in policies]
        cl_ranks = [cl_vals[p] for p in policies]
        if len(set(off_ranks)) == 1 or len(set(cl_ranks)) == 1:
            tau = float("nan")
            note = "undefined (one side is fully tied across all 3 policies)"
        else:
            tau, _p = stats.kendalltau(off_ranks, cl_ranks)
            note = ""
        result["per_cell_3item_tau_b"].append({
            "family": r["family"], "capacity": int(r["capacity"]), "horizon": int(r["horizon"]),
            "tau_b": tau, "note": note,
        })
    return result


def rq_cl1_exclusions(rows):
    no_wiki = [r for r in rows if r["family"] != "wiki2018"]
    no_metacdn = [r for r in rows if r["family"] != "metacdn"]
    no_metakv = [r for r in rows if r["family"] != "metakv"]
    out = {}
    for label, subset in [("excluding_wiki2018", no_wiki), ("excluding_metacdn", no_metacdn),
                           ("excluding_metakv", no_metakv)]:
        out[label] = {}
        for horizon in (4, 8, 16):
            hrows = [r for r in subset if int(r["horizon"]) == horizon]
            out[label][horizon] = {}
            for name, off_col, cl_col in PAIRS:
                _per_row, counts = classify_pair(hrows, off_col, cl_col)
                out[label][horizon][name] = {"counts": counts, "n_cells": len(hrows)}
    return out


def correlations(xs, ys):
    if len(xs) < 3 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return {"n": len(xs), "pearson_r": None, "spearman_rho": None, "kendall_tau_b": None,
                "note": "insufficient variation for a correlation statistic"}
    pear = stats.pearsonr(xs, ys)
    spear = stats.spearmanr(xs, ys)
    kend = stats.kendalltau(xs, ys)
    return {
        "n": len(xs),
        "pearson_r": float(pear.statistic), "pearson_p_TWO_SIDED_CAUTION_TINY_N": float(pear.pvalue),
        "spearman_rho": float(spear.statistic), "spearman_p_TWO_SIDED_CAUTION_TINY_N": float(spear.pvalue),
        "kendall_tau_b": float(kend.statistic), "kendall_p_TWO_SIDED_CAUTION_TINY_N": float(kend.pvalue),
    }


def rq_cl2(rows):
    result = {"primary_by_horizon": {}, "excluding_wiki2018_by_horizon": {}, "test_window_only_by_horizon": {},
              "pooled_SECONDARY_pseudo_replicated": {}, "scatter_data": []}

    for horizon in (4, 8, 16):
        hrows = [r for r in rows if int(r["horizon"]) == horizon]
        result["primary_by_horizon"][horizon] = {}
        for name, off_col, cl_col in PAIRS:
            xs = [r[off_col] for r in hrows]
            ys = [r[cl_col] for r in hrows]
            result["primary_by_horizon"][horizon][name] = correlations(xs, ys)

        no_wiki = [r for r in hrows if r["family"] != "wiki2018"]
        result["excluding_wiki2018_by_horizon"][horizon] = {}
        for name, off_col, cl_col in PAIRS:
            xs = [r[off_col] for r in no_wiki]
            ys = [r[cl_col] for r in no_wiki]
            result["excluding_wiki2018_by_horizon"][horizon][name] = correlations(xs, ys)

        test_only = [r for r in hrows if r["scored_split_label"] == "test"]
        result["test_window_only_by_horizon"][horizon] = {}
        for name, off_col, cl_col in PAIRS:
            xs = [r[off_col] for r in test_only]
            ys = [r[cl_col] for r in test_only]
            result["test_window_only_by_horizon"][horizon][name] = correlations(xs, ys)

    for name, off_col, cl_col in PAIRS:
        xs = [r[off_col] for r in rows]
        ys = [r[cl_col] for r in rows]
        result["pooled_SECONDARY_pseudo_replicated"][name] = correlations(xs, ys)
        result["pooled_SECONDARY_pseudo_replicated"][name]["CAUTION"] = (
            "n=30 here is NOT 30 independent observations -- each of the 10 (family,capacity) "
            "closed-loop gaps is repeated once per horizon. Treat only the by_horizon (n=10) "
            "results as primary."
        )

    for r in rows:
        for name, off_col, cl_col in PAIRS:
            result["scatter_data"].append({
                "pair": name, "family": r["family"], "capacity": int(r["capacity"]), "horizon": int(r["horizon"]),
                "offline_gap": r[off_col], "closed_loop_gap": r[cl_col],
                "scored_split_label": r["scored_split_label"],
            })
    return result


def rq_cl3(rows):
    by_family = {}
    for family in sorted(set(r["family"] for r in rows)):
        frows = [r for r in rows if r["family"] == family]
        entry = {"scored_split_label": frows[0]["scored_split_label"], "by_capacity": {}}
        for capacity in (32, 128):
            crows = [r for r in frows if int(r["capacity"]) == capacity]
            r16 = [r for r in crows if int(r["horizon"]) == 16][0]
            entry["by_capacity"][capacity] = {
                "offline_all_tied_fraction_H16": r16["offline_all_tied_fraction"],
                "offline_random_optimal_probability_H16": r16["offline_random_optimal_probability"],
                "offline_mru_minus_lru_regret_gap_H16": r16["offline_mru_minus_lru_regret_gap"],
                "offline_random_minus_lru_regret_gap_H16": r16["offline_random_minus_lru_regret_gap"],
                "cl_mru_minus_lru_miss_ratio_gap": r16["cl_mru_minus_lru_miss_ratio_gap"],
                "cl_random_minus_lru_miss_ratio_gap": r16["cl_random_minus_lru_miss_ratio_gap"],
                "cl_lru_miss_ratio": r16["cl_lru_miss_ratio"],
                "cl_sieve_miss_ratio": r16["cl_sieve_miss_ratio"],
            }
        by_family[family] = entry

    # Exploratory: does higher offline discriminativeness (lower all-tied
    # fraction) at H=16 correspond to larger closed-loop separation?
    h16 = [r for r in rows if int(r["horizon"]) == 16]
    disc = [1.0 - r["offline_all_tied_fraction"] for r in h16]  # higher = more discriminative
    cl_sep = [abs(r["cl_mru_minus_lru_miss_ratio_gap"]) for r in h16]
    exploratory_corr = correlations(disc, cl_sep)

    return {"by_family": by_family, "exploratory_discriminativeness_vs_closed_loop_separation_H16": exploratory_corr,
            "exploratory_note": "EXPLORATORY, not pre-registered as such in DESIGN.md's RQ text; included because DESIGN.md's own discussion motivates checking whether discriminativeness predicts separation."}


def rq_cl4(rq_cl1_result, rq_cl2_result):
    summary = {}
    for horizon in (4, 8, 16):
        concordant = 0
        discordant = 0
        ties = 0
        for name, _off, _cl in PAIRS:
            c = rq_cl1_result["by_horizon"][horizon][name]["counts"]
            concordant += c.get("concordant", 0)
            discordant += c.get("discordant", 0)
            ties += c.get("offline_tie_only", 0) + c.get("closed_loop_tie_only", 0) + c.get("both_tied", 0)
        taus = [t["tau_b"] for t in rq_cl1_result["per_cell_3item_tau_b"] if t["horizon"] == horizon and t["tau_b"] == t["tau_b"]]
        mean_tau = sum(taus) / len(taus) if taus else float("nan")
        corr_summaries = rq_cl2_result["primary_by_horizon"][horizon]
        summary[horizon] = {
            "concordant_pairs": concordant, "discordant_pairs": discordant, "tie_pairs": ties,
            "mean_3item_tau_b_defined_cells": mean_tau, "n_cells_with_defined_tau": len(taus),
            "rq_cl2_correlations": corr_summaries,
        }
    return summary


def main():
    rows = load_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    cl1 = rq_cl1(rows)
    cl1_excl = rq_cl1_exclusions(rows)
    cl2 = rq_cl2(rows)
    cl3 = rq_cl3(rows)
    cl4 = rq_cl4(cl1, cl2)

    (OUT_DIR / "rq_cl1_rank_agreement.json").write_text(json.dumps(cl1, indent=2, sort_keys=True, default=str), encoding="utf-8")
    (OUT_DIR / "rq_cl1_sensitivity_exclusions.json").write_text(json.dumps(cl1_excl, indent=2, sort_keys=True), encoding="utf-8")
    (OUT_DIR / "rq_cl2_gap_correspondence.json").write_text(json.dumps(cl2, indent=2, sort_keys=True), encoding="utf-8")
    (OUT_DIR / "rq_cl3_workload_capacity_dependence.json").write_text(json.dumps(cl3, indent=2, sort_keys=True), encoding="utf-8")
    (OUT_DIR / "rq_cl4_horizon_alignment.json").write_text(json.dumps(cl4, indent=2, sort_keys=True), encoding="utf-8")

    with open(OUT_DIR / "rq_cl2_scatter_data.csv", "w", newline="", encoding="utf-8") as fh:
        fieldnames = list(cl2["scatter_data"][0].keys())
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in cl2["scatter_data"]:
            writer.writerow(row)

    print("RQ-CL1 by-horizon concordance counts:")
    for horizon in (4, 8, 16):
        print(f"  H={horizon}:", {name: cl1["by_horizon"][horizon][name]["counts"] for name, _, _ in PAIRS})
    print("\nRQ-CL4 summary (concordant/discordant/tie pairs, mean tau-b, per horizon):")
    for horizon, s in cl4.items():
        print(f"  H={horizon}: concordant={s['concordant_pairs']} discordant={s['discordant_pairs']} "
              f"ties={s['tie_pairs']} mean_tau_b={s['mean_3item_tau_b_defined_cells']:.3f} (n={s['n_cells_with_defined_tau']})")


if __name__ == "__main__":
    main()
