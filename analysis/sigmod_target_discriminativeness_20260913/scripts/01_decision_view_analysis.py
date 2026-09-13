#!/usr/bin/env python3
"""LAFC-Evict SIGMOD target-discriminativeness audit: decision_view analysis.

Reads the canonical SIGMOD-scale decision_view.parquet (2,363,286 rows, one
row per full-cache-miss eviction decision) from the preserved open release
and computes Phases 2-6 of the audit (reviewer-number reproduction,
decision-level discriminativeness, decision-weighted vs candidate-weighted
statistics, stratified matrices, nontrivial-subset analysis, horizon effect).

All quantities used here (candidate_count, optimal_candidate_count, tie_count,
regret_mean/std/max/sum, min_y_loss, max_y_value) are pre-existing decision_view
fields (see src/lafc_evict_dataset/views.py:build_decision_view) -- nothing is
re-derived from a fresh candidate_rows scan in this script. tie_count ==
optimal_candidate_count by construction (both count candidates at regret==0);
this is confirmed directly from build_decision_view's source.

Because y_loss is a small nonnegative integer (bounded by horizon) and
min_y_loss is likewise an integer per decision, per-candidate regret is exactly
integer-valued. This means P(regret>=1) is exactly derivable from decision_view
as (candidate_count - optimal_candidate_count) / candidate_count -- no
candidate_rows scan needed. P(regret>=2), and any candidate-weighted percentile
of the *individual* regret distribution, is NOT derivable from decision_view's
aggregate fields (mean/std/max only) and requires a separate pass over
candidate_rows -- see 02_candidate_level_regret_histogram.py.

Deterministic: no sampling, no RNG. Every statistic here is either a population
value (all 2,363,286 decisions) or an exact aggregate of one.
"""
from __future__ import annotations

import json
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[3]
RELEASE_ROOT = REPO_ROOT / "release" / "lafc-evict-v0.1-open-current-contract-preserved"
DECISION_VIEW = RELEASE_ROOT / "data" / "decision_view" / "decision_view.parquet"
OUT_DIR = Path(__file__).resolve().parent.parent / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

assert DECISION_VIEW.exists(), f"missing {DECISION_VIEW}"

con = duckdb.connect()
con.execute(f"CREATE VIEW dv AS SELECT * FROM '{DECISION_VIEW}'")

report: dict[str, object] = {}

# ---------------------------------------------------------------------------
# Provenance / row-count validation
# ---------------------------------------------------------------------------
n_decisions = con.execute("SELECT COUNT(*) FROM dv").fetchone()[0]
report["decision_view_row_count"] = n_decisions
report["decision_view_path"] = str(DECISION_VIEW)

dims = {}
for col in ["capacity", "horizon", "trace_family", "split", "dataset_source"]:
    dims[col] = [r[0] for r in con.execute(f"SELECT DISTINCT {col} FROM dv ORDER BY 1").fetchall()]
report["dimensions"] = dims

# Confirm tie_count == optimal_candidate_count everywhere (population check)
mismatch = con.execute("SELECT COUNT(*) FROM dv WHERE tie_count != optimal_candidate_count").fetchone()[0]
report["tie_count_equals_optimal_candidate_count_everywhere"] = (mismatch == 0)
report["tie_count_optimal_candidate_count_mismatch_rows"] = mismatch

# Confirm regret is exactly integer-valued (population check on regret_max/regret_mean*candidate_count granularity)
# We check regret_sum is integer-valued (sum of integers) as an indirect population check.
non_integer_sum = con.execute(
    "SELECT COUNT(*) FROM dv WHERE ABS(regret_sum - ROUND(regret_sum)) > 1e-6"
).fetchone()[0]
report["regret_sum_is_integer_valued_everywhere"] = (non_integer_sum == 0)
report["regret_sum_non_integer_rows"] = non_integer_sum

# ---------------------------------------------------------------------------
# PHASE 2: reproduce reviewer numbers exactly, from first principles
# ---------------------------------------------------------------------------
# Per-decision random-optimal probability = optimal_candidate_count / candidate_count
# Reviewer statistic = DECISION-WEIGHTED MEAN of this per-decision probability
# (unweighted mean over the 2,363,286 decisions -- each decision counts once
# regardless of its candidate_count). This matches the reconciliation report's
# methodology exactly (single DuckDB aggregation over decision_view).
row = con.execute(
    """
    SELECT
        AVG(CAST(optimal_candidate_count AS DOUBLE) / candidate_count) AS random_optimal_prob_decision_weighted,
        AVG(regret_mean) AS random_expected_regret_decision_weighted,
        SUM(optimal_candidate_count) AS total_optimal_candidates,
        SUM(candidate_count) AS total_candidates,
        SUM(regret_sum) AS total_regret,
        AVG(candidate_count) AS mean_candidate_count,
        AVG(optimal_candidate_count) AS mean_optimal_set_size,
        STDDEV_POP(optimal_candidate_count) AS std_optimal_set_size,
        MIN(optimal_candidate_count) AS min_optimal_set_size,
        MAX(optimal_candidate_count) AS max_optimal_set_size
    FROM dv
    """
).fetchone()
(
    random_optimal_prob_dw, random_expected_regret_dw, total_optimal, total_cand,
    total_regret, mean_cand_count, mean_opt_size, std_opt_size, min_opt_size, max_opt_size,
) = row

random_optimal_prob_cw = total_optimal / total_cand
random_expected_regret_cw = total_regret / total_cand

report["phase2_reviewer_reproduction"] = {
    "random_optimal_probability": {
        "decision_weighted_mean_of_per_decision_prob": random_optimal_prob_dw,
        "candidate_weighted_pooled": random_optimal_prob_cw,
        "reviewer_reported": 0.9912,
        "reconciliation_report_value": 0.9912418754543462,
        "matches_reconciliation_report": abs(random_optimal_prob_dw - 0.9912418754543462) < 1e-9,
    },
    "random_expected_regret": {
        "decision_weighted_mean_of_per_decision_regret_mean": random_expected_regret_dw,
        "candidate_weighted_pooled": random_expected_regret_cw,
        "reviewer_reported": 0.0088,
        "reconciliation_report_value": 0.008826200441884731,
        "matches_reconciliation_report": abs(random_expected_regret_dw - 0.008826200441884731) < 1e-9,
    },
    "mean_optimal_set_size": mean_opt_size,
    "std_optimal_set_size": std_opt_size,
    "min_optimal_set_size": min_opt_size,
    "max_optimal_set_size": max_opt_size,
    "mean_candidate_count": mean_cand_count,
    "methodology": (
        "Both reviewer numbers are DECISION-WEIGHTED means over all 2,363,286 "
        "decisions in decision_view.parquet -- a population statistic, not a "
        "sample estimate. No seed/sampling procedure is involved because "
        "decision_view already IS the full population of decisions "
        "(candidate_count and optimal_candidate_count are exact per-decision "
        "counts). 'Optimal' means membership in the tied argmin set "
        "(regret==0), i.e. ties count as optimal. Regret is raw miss-count "
        "regret (y_loss - min_y_loss within the decision), unweighted by "
        "candidate count beyond the per-decision mean itself."
    ),
}

# ---------------------------------------------------------------------------
# PHASE 3: decision-level target discriminativeness (population, both weightings)
# ---------------------------------------------------------------------------
row = con.execute(
    """
    SELECT
        COUNT(*) AS n_decisions,
        AVG(CASE WHEN optimal_candidate_count = candidate_count THEN 1.0 ELSE 0.0 END) AS all_tied_fraction,
        AVG(CASE WHEN optimal_candidate_count = 1 THEN 1.0 ELSE 0.0 END) AS unique_winner_fraction,
        AVG(CAST(optimal_candidate_count AS DOUBLE) / candidate_count) AS mean_optimal_set_fraction,
        MEDIAN(CAST(optimal_candidate_count AS DOUBLE) / candidate_count) AS median_optimal_set_fraction,
        AVG(regret_mean) AS mean_random_regret_decision_weighted,
        MEDIAN(regret_mean) AS median_random_regret_decision_weighted,
        APPROX_QUANTILE(regret_mean, 0.90) AS p90_random_regret,
        APPROX_QUANTILE(regret_mean, 0.95) AS p95_random_regret,
        APPROX_QUANTILE(regret_mean, 0.99) AS p99_random_regret,
        AVG(CASE WHEN regret_max >= 1 THEN 1.0 ELSE 0.0 END) AS fraction_loss_range_ge_1,
        AVG(CASE WHEN regret_max >= 2 THEN 1.0 ELSE 0.0 END) AS fraction_loss_range_ge_2,
        MAX(regret_max) AS max_observed_loss_range,
        AVG(CAST(candidate_count - optimal_candidate_count AS DOUBLE) / candidate_count) AS mean_prob_regret_ge_1_decision_weighted
    FROM dv
    """
).fetchone()
cols = [
    "n_decisions", "all_tied_fraction", "unique_winner_fraction",
    "mean_optimal_set_fraction", "median_optimal_set_fraction",
    "mean_random_regret_decision_weighted", "median_random_regret_decision_weighted",
    "p90_random_regret", "p95_random_regret", "p99_random_regret",
    "fraction_loss_range_ge_1", "fraction_loss_range_ge_2", "max_observed_loss_range",
    "mean_prob_regret_ge_1_decision_weighted",
]
phase3_decision_weighted = dict(zip(cols, row))

row = con.execute(
    """
    SELECT
        SUM(candidate_count) AS n_candidates,
        SUM(optimal_candidate_count) AS n_optimal_candidates,
        CAST(SUM(optimal_candidate_count) AS DOUBLE) / SUM(candidate_count) AS random_optimal_probability_candidate_weighted,
        CAST(SUM(candidate_count - optimal_candidate_count) AS DOUBLE) / SUM(candidate_count) AS prob_regret_ge_1_candidate_weighted,
        SUM(regret_sum) / SUM(candidate_count) AS mean_random_regret_candidate_weighted
    FROM dv
    """
).fetchone()
cols2 = [
    "n_candidates", "n_optimal_candidates", "random_optimal_probability_candidate_weighted",
    "prob_regret_ge_1_candidate_weighted", "mean_random_regret_candidate_weighted",
]
phase3_candidate_weighted = dict(zip(cols2, row))

report["phase3_discriminativeness"] = {
    "decision_weighted": phase3_decision_weighted,
    "candidate_weighted": phase3_candidate_weighted,
    "note_regret_ge_2": (
        "Exact P(regret>=2) at the per-candidate level cannot be derived from "
        "decision_view alone (only mean/std/max/sum of regret are stored per "
        "decision, not the full histogram). See "
        "outputs/candidate_regret_histogram.json for the exact value computed "
        "from a full candidate_rows scan."
    ),
    "explanation_decision_vs_candidate_weighted": (
        "Decision-weighted statistics give every decision equal weight "
        "regardless of how many candidates it has (mean over 2,363,286 "
        "per-decision probabilities/regrets). Candidate-weighted statistics "
        "pool all ~278M candidate rows together, so decisions with larger "
        "candidate pools (which, per table_candidate_count_stats, range 32-256 "
        "and differ systematically by capacity) contribute proportionally "
        "more mass. The two agree closely here (0.99124 vs candidate-weighted, "
        "see phase3_candidate_weighted) because optimal-set fraction does not "
        "vary sharply with candidate_count in this dataset, but they are not "
        "identical and must not be conflated -- averaging per-decision ratios "
        "is NOT the same as pooling numerators/denominators across decisions."
    ),
}

# ---------------------------------------------------------------------------
# PHASE 4: stratified matrix trace_family x capacity x horizon
# ---------------------------------------------------------------------------
strat = con.execute(
    """
    SELECT
        trace_family, capacity, horizon,
        COUNT(*) AS n_decisions,
        AVG(CASE WHEN optimal_candidate_count = candidate_count THEN 1.0 ELSE 0.0 END) AS all_tied_fraction,
        AVG(CASE WHEN optimal_candidate_count = 1 THEN 1.0 ELSE 0.0 END) AS unique_winner_fraction,
        AVG(CAST(optimal_candidate_count AS DOUBLE) / candidate_count) AS mean_optimal_set_fraction,
        MEDIAN(CAST(optimal_candidate_count AS DOUBLE) / candidate_count) AS median_optimal_set_fraction,
        AVG(CAST(optimal_candidate_count AS DOUBLE) / candidate_count) AS random_optimal_probability,
        AVG(regret_mean) AS mean_random_regret,
        MEDIAN(regret_mean) AS median_random_regret,
        APPROX_QUANTILE(regret_mean, 0.90) AS p90_random_regret,
        APPROX_QUANTILE(regret_mean, 0.95) AS p95_random_regret,
        APPROX_QUANTILE(regret_mean, 0.99) AS p99_random_regret,
        AVG(CASE WHEN regret_max >= 1 THEN 1.0 ELSE 0.0 END) AS fraction_loss_range_ge_1,
        AVG(CASE WHEN regret_max >= 2 THEN 1.0 ELSE 0.0 END) AS fraction_loss_range_ge_2,
        MAX(regret_max) AS max_observed_loss_range
    FROM dv
    GROUP BY trace_family, capacity, horizon
    ORDER BY trace_family, capacity, horizon
    """
).df()
strat.to_csv(OUT_DIR / "phase4_stratified_family_capacity_horizon.csv", index=False)
report["phase4_stratified_matrix_rows"] = len(strat)
report["phase4_most_discriminative_cells"] = (
    strat.sort_values("mean_optimal_set_fraction").head(5)[
        ["trace_family", "capacity", "horizon", "n_decisions", "mean_optimal_set_fraction", "all_tied_fraction", "mean_random_regret"]
    ].to_dict(orient="records")
)
report["phase4_least_discriminative_cells"] = (
    strat.sort_values("mean_optimal_set_fraction", ascending=False).head(5)[
        ["trace_family", "capacity", "horizon", "n_decisions", "mean_optimal_set_fraction", "all_tied_fraction", "mean_random_regret"]
    ].to_dict(orient="records")
)

# Also stratify by split for completeness
strat_split = con.execute(
    """
    SELECT split,
        COUNT(*) AS n_decisions,
        AVG(CASE WHEN optimal_candidate_count = candidate_count THEN 1.0 ELSE 0.0 END) AS all_tied_fraction,
        AVG(CAST(optimal_candidate_count AS DOUBLE) / candidate_count) AS mean_optimal_set_fraction,
        AVG(regret_mean) AS mean_random_regret
    FROM dv GROUP BY split ORDER BY split
    """
).df()
strat_split.to_csv(OUT_DIR / "phase4_stratified_split.csv", index=False)

# Stratify by candidate_count decile (decision candidate-count effect)
strat_candcount = con.execute(
    """
    SELECT candidate_count,
        COUNT(*) AS n_decisions,
        AVG(CASE WHEN optimal_candidate_count = candidate_count THEN 1.0 ELSE 0.0 END) AS all_tied_fraction,
        AVG(CAST(optimal_candidate_count AS DOUBLE) / candidate_count) AS mean_optimal_set_fraction,
        AVG(regret_mean) AS mean_random_regret
    FROM dv GROUP BY candidate_count ORDER BY candidate_count
    """
).df()
strat_candcount.to_csv(OUT_DIR / "phase4_stratified_candidate_count.csv", index=False)

# ---------------------------------------------------------------------------
# PHASE 5: nontrivial subset analysis (transparent thresholds, not cherry-picked)
# ---------------------------------------------------------------------------
thresholds = {
    "not_all_tied": "optimal_candidate_count < candidate_count",
    "unique_optimal_victim": "optimal_candidate_count = 1",
    "optimal_set_fraction_le_0.5": "CAST(optimal_candidate_count AS DOUBLE) / candidate_count <= 0.5",
    "loss_range_ge_1": "regret_max >= 1",
    "loss_range_ge_2": "regret_max >= 2",
    "random_expected_regret_ge_0.1": "regret_mean >= 0.1",
    "random_expected_regret_ge_0.5": "regret_mean >= 0.5",
    "random_expected_regret_ge_1": "regret_mean >= 1.0",
}
nontrivial_results = {}
total_candidates_all = phase3_candidate_weighted["n_candidates"]
for name, predicate in thresholds.items():
    row = con.execute(
        f"""
        SELECT
            COUNT(*) AS n_decisions,
            SUM(candidate_count) AS candidate_row_coverage,
            AVG(regret_mean) AS mean_random_regret,
            MEDIAN(regret_mean) AS median_random_regret,
            AVG(CAST(optimal_candidate_count AS DOUBLE) / candidate_count) AS mean_optimal_set_fraction
        FROM dv WHERE {predicate}
        """
    ).fetchone()
    n_dec, cand_cov, mean_reg, med_reg, mean_opt_frac = row
    fam_dist = con.execute(
        f"SELECT trace_family, COUNT(*) FROM dv WHERE {predicate} GROUP BY trace_family ORDER BY trace_family"
    ).fetchall()
    cap_dist = con.execute(
        f"SELECT capacity, COUNT(*) FROM dv WHERE {predicate} GROUP BY capacity ORDER BY capacity"
    ).fetchall()
    hor_dist = con.execute(
        f"SELECT horizon, COUNT(*) FROM dv WHERE {predicate} GROUP BY horizon ORDER BY horizon"
    ).fetchall()
    nontrivial_results[name] = {
        "n_decisions": n_dec,
        "fraction_of_total_decisions": n_dec / n_decisions,
        "candidate_row_coverage": cand_cov,
        "fraction_of_total_candidate_rows": (cand_cov / total_candidates_all) if cand_cov else 0.0,
        "mean_random_regret": mean_reg,
        "median_random_regret": med_reg,
        "mean_optimal_set_fraction": mean_opt_frac,
        "trace_family_distribution": dict(fam_dist),
        "capacity_distribution": dict(cap_dist),
        "horizon_distribution": dict(hor_dist),
    }
report["phase5_nontrivial_subsets"] = nontrivial_results

# ---------------------------------------------------------------------------
# PHASE 6: horizon effect
# ---------------------------------------------------------------------------
horizon_effect = con.execute(
    """
    SELECT horizon,
        COUNT(*) AS n_decisions,
        AVG(CASE WHEN optimal_candidate_count = candidate_count THEN 1.0 ELSE 0.0 END) AS all_tied_fraction,
        AVG(CAST(optimal_candidate_count AS DOUBLE) / candidate_count) AS mean_optimal_set_fraction,
        AVG(CASE WHEN optimal_candidate_count = 1 THEN 1.0 ELSE 0.0 END) AS unique_winner_fraction,
        AVG(regret_mean) AS mean_random_regret,
        AVG(regret_max) AS mean_loss_range,
        MAX(regret_max) AS max_loss_range,
        COUNT(DISTINCT optimal_candidate_count) AS n_distinct_optimal_set_sizes_seen
    FROM dv GROUP BY horizon ORDER BY horizon
    """
).df()
horizon_effect.to_csv(OUT_DIR / "phase6_horizon_effect.csv", index=False)
report["phase6_horizon_effect"] = horizon_effect.to_dict(orient="records")

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
with open(OUT_DIR / "decision_view_report.json", "w") as f:
    json.dump(report, f, indent=2, default=str)

print(json.dumps({k: v for k, v in report.items() if k not in (
    "phase4_stratified_matrix_rows",)}, indent=2, default=str)[:3000])
print("\nFull report written to", OUT_DIR / "decision_view_report.json")
