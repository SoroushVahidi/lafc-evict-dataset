"""Scientific analysis of the full continuation-sensitivity experiment.

Reads decision_metrics.csv (never the raw ~1GB JSONL) and computes:
- Stratified sets A/B/C/D exactly as pre-registered.
- Per-family/capacity/horizon breakdowns.
- Decision-level cluster bootstrap CIs (never candidate-row or seed-level).
- The pre-registered ROBUST/CONDITIONALLY_ROBUST/SENSITIVE/INCONCLUSIVE
  classification, applied verbatim from DESIGN.md Section 3.
- Diagnostic-oversample results, reported separately, never pooled into
  primary population statements.
"""
from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from full_lib import CAPACITIES, FAMILIES, HORIZONS  # noqa: E402

FULL_DIR = Path(__file__).resolve().parents[1]

BOOTSTRAP_RESAMPLES = 2000  # decision-level cluster bootstrap; see README for why not 10,000
BOOTSTRAP_SEED = 20260914


def load_rows(run_dir: Path):
    rows = list(csv.DictReader(open(run_dir / "decision_metrics.csv", newline="", encoding="utf-8")))
    for r in rows:
        r["capacity"] = int(r["capacity"])
        r["horizon"] = int(r["horizon"])
        r["baseline_lru_all_tied"] = r["baseline_lru_all_tied"] in ("True", "true", "1")
        r["alt_all_tied"] = r["alt_all_tied"] in ("True", "true", "1")
        for k in list(r.keys()):
            if k.startswith("pairwise_") or k.startswith("ccr_n_"):
                r[k] = int(float(r[k])) if r[k] not in ("", None) else 0
        for k in ("optimal_set_jaccard", "kendall_tau_b", "ccr_mean_over_LRU_optimal",
                   "ccr_best_case", "ccr_worst_case", "ccr_prob_still_optimal"):
            r[k] = float(r[k]) if r[k] not in ("", "None", None) else None
    return rows


def median(vals):
    s = sorted(vals)
    n = len(s)
    if n == 0:
        return None
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2


def pairwise_totals(rows):
    keys = ["pairwise_concordant", "pairwise_discordant", "pairwise_a_tie_b_strict", "pairwise_a_strict_b_tie", "pairwise_both_tied"]
    return {k: sum(r[k] for r in rows) for k in keys}


def summarize_set(rows):
    jaccards = [r["optimal_set_jaccard"] for r in rows if r["optimal_set_jaccard"] is not None]
    ccr_means = [r["ccr_mean_over_LRU_optimal"] for r in rows if r["ccr_mean_over_LRU_optimal"] is not None]
    prob_still_opt = [r["ccr_prob_still_optimal"] for r in rows if r["ccr_prob_still_optimal"] is not None]
    tot = pairwise_totals(rows)
    total_pairs = sum(tot.values())
    return {
        "n_decisions": len(rows),
        "mean_jaccard": sum(jaccards) / len(jaccards) if jaccards else None,
        "median_jaccard": median(jaccards),
        "min_jaccard": min(jaccards) if jaccards else None,
        "pairwise_totals": tot,
        "total_pairs": total_pairs,
        "strict_reversal_fraction": tot["pairwise_discordant"] / total_pairs if total_pairs else None,
        "mean_ccr": sum(ccr_means) / len(ccr_means) if ccr_means else None,
        "max_ccr": max(ccr_means) if ccr_means else None,
        "fraction_ccr_zero": sum(1 for v in ccr_means if v == 0.0) / len(ccr_means) if ccr_means else None,
        "mean_prob_still_optimal": sum(prob_still_opt) / len(prob_still_opt) if prob_still_opt else None,
    }


def cluster_bootstrap(rows, seed, n_resamples):
    """Decision-level cluster bootstrap: resample DECISIONS with replacement
    (never candidate rows or random seeds), recompute median Jaccard and
    mean CCR each time."""
    rng = random.Random(seed)
    n = len(rows)
    if n == 0:
        return None
    jaccard_boot = []
    ccr_boot = []
    for _ in range(n_resamples):
        sample = [rows[rng.randrange(n)] for _ in range(n)]
        js = [r["optimal_set_jaccard"] for r in sample if r["optimal_set_jaccard"] is not None]
        cs = [r["ccr_mean_over_LRU_optimal"] for r in sample if r["ccr_mean_over_LRU_optimal"] is not None]
        if js:
            jaccard_boot.append(median(js))
        if cs:
            ccr_boot.append(sum(cs) / len(cs))
    jaccard_boot.sort()
    ccr_boot.sort()

    def pct(sorted_vals, p):
        if not sorted_vals:
            return None
        idx = min(len(sorted_vals) - 1, max(0, round(p * (len(sorted_vals) - 1))))
        return sorted_vals[idx]

    return {
        "n_resamples": n_resamples, "n_decisions_per_resample": n, "seed": seed,
        "median_jaccard_ci95": [pct(jaccard_boot, 0.025), pct(jaccard_boot, 0.975)],
        "mean_ccr_ci95": [pct(ccr_boot, 0.025), pct(ccr_boot, 0.975)],
    }


def apply_robustness_classification(set_c_summary_by_policy):
    """Verbatim from DESIGN.md Section 3 thresholds, applied to Set C
    (discriminative-under-LRU) for each alternative policy separately."""
    classifications = {}
    for policy, s in set_c_summary_by_policy.items():
        if s["n_decisions"] == 0 or s["median_jaccard"] is None:
            classifications[policy] = "INCONCLUSIVE"
            continue
        # fraction_ccr_le_1 is computed by main() and merged into s before this is called.
        if s.get("fraction_ccr_le_1") is None:
            classifications[policy] = "INCONCLUSIVE"
        elif s["median_jaccard"] >= 0.8 and s["fraction_ccr_le_1"] >= 0.8:
            classifications[policy] = "ROBUST"
        elif s["median_jaccard"] < 0.5 or s["fraction_ccr_le_1"] < 0.2:
            classifications[policy] = "SENSITIVE"
        else:
            classifications[policy] = "CONDITIONALLY_ROBUST"
    return classifications


def main(run_dir: Path):
    rows = load_rows(run_dir)
    primary_rows = [r for r in rows if r["sample"] == "primary"]
    diagnostic_rows = [r for r in rows if r["sample"] == "diagnostic"]

    result = {"PRIMARY_ANALYSIS": {}, "DIAGNOSTIC_ANALYSIS": {}}

    for policy in ("mru", "random_mean"):
        prows = [r for r in primary_rows if r["alt_policy"] == policy]
        set_a = prows
        set_b = [r for r in prows if not (r["baseline_lru_all_tied"] and r["alt_all_tied"])]
        set_c = [r for r in prows if not r["baseline_lru_all_tied"]]
        set_d = [r for r in prows if not r["baseline_lru_all_tied"] or not r["alt_all_tied"]]

        summaries = {}
        for label, subset in [("A_all_decisions", set_a), ("B_excluding_both_tied", set_b),
                               ("C_discriminative_under_LRU", set_c), ("D_discriminative_under_either", set_d)]:
            s = summarize_set(subset)
            ccr_vals = [r["ccr_mean_over_LRU_optimal"] for r in subset if r["ccr_mean_over_LRU_optimal"] is not None]
            s["fraction_ccr_le_1"] = (sum(1 for v in ccr_vals if v <= 1.0) / len(ccr_vals)) if ccr_vals else None
            summaries[label] = s

        by_family = {f: summarize_set([r for r in set_c if r["family"] == f]) for f in FAMILIES}
        by_capacity = {c: summarize_set([r for r in set_c if r["capacity"] == c]) for c in CAPACITIES}
        by_horizon = {h: summarize_set([r for r in set_c if r["horizon"] == h]) for h in HORIZONS}

        bootstrap = cluster_bootstrap(set_c, seed=BOOTSTRAP_SEED, n_resamples=BOOTSTRAP_RESAMPLES)

        result["PRIMARY_ANALYSIS"][policy] = {
            "stratified_sets": summaries, "by_family_setC": by_family,
            "by_capacity_setC": by_capacity, "by_horizon_setC": by_horizon,
            "bootstrap_setC": bootstrap,
        }

    for policy in ("mru", "random_mean"):
        drows = [r for r in diagnostic_rows if r["alt_policy"] == policy]
        result["DIAGNOSTIC_ANALYSIS"][policy] = summarize_set(drows)

    robustness_input = {p: result["PRIMARY_ANALYSIS"][p]["stratified_sets"]["C_discriminative_under_LRU"] for p in ("mru", "random_mean")}
    result["ROBUSTNESS_CLASSIFICATION"] = apply_robustness_classification(robustness_input)

    wiki_rows_by_policy = {p: [r for r in primary_rows if r["family"] == "wiki2018" and r["alt_policy"] == p] for p in ("mru", "random_mean")}
    result["WIKI2018_SPECIAL"] = {p: summarize_set(rs) for p, rs in wiki_rows_by_policy.items()}

    (run_dir / "scientific_analysis.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result["ROBUSTNESS_CLASSIFICATION"], indent=2))
    print(f"\nWrote {run_dir / 'scientific_analysis.json'}")
    return result


if __name__ == "__main__":
    main(Path(sys.argv[1]))
