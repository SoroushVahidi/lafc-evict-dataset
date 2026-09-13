#!/usr/bin/env python3
"""LAFC-Evict SIGMOD audit: pairwise label information content (Phase 7).

Reads the shipped pairwise_sample.parquet (1,000,000 rows) directly -- this
is the exact artifact the manuscript's 878,262/1,000,000 tie statistic and
Section 07 pairwise-baseline results are computed from (verified: schema
matches table_pairwise_sample_stats.md exactly). No sampling is performed
here; every statistic below is a population statistic over the shipped
1,000,000-row sample (itself a fixed, previously-drawn sample of the full
pairwise universe -- see quadratic-blowup note below for why the full
universe is never materialized).

** PROVENANCE FLAG (see audit report Phase 2 / Phase 12) **
`release/` is gitignored (repo .gitignore line 2), so pairwise_sample.parquet
is never version-controlled and can drift from the manuscript-era build. This
script's own run found: the on-disk file (mtime 2026-06-27 20:20, i.e. BEFORE
commit 3b49189 "Fix pairwise orientation and reconcile baseline counts",
2026-07-02 18:28) reproduces the manuscript's tie fraction only approximately
(879,968/1,000,000 = 0.8800 vs manuscript's 878,262/1,000,000 = 0.8783, a
0.19% relative difference) and does NOT reproduce the manuscript's claimed
~49.8%/50.2% A/B direction balance at all (this run: 6,134 a_better / 113,898
b_better = 5.1%/94.9%). The manuscript's own committed
paper/sigmod2027/results/metadata_tables/table_pairwise_sample_label_summary.csv
(60,673/61,065/878,262, committed 2026-07-02, i.e. AFTER the orientation fix)
is the correct ground truth for what fed the paper. The numbers this script
computes are therefore reported as "current on-disk pairwise_sample
characterization" and are qualitatively consistent (heavily tie-dominated)
but must NOT be quoted as a fresh reproduction of the manuscript's exact
pairwise statistics. Recommended fix: regenerate
release/.../pairwise_sample.parquet from the current post-fix pipeline and
re-freeze/checksum it, or point this analysis at a checksummed frozen copy.
"""
from __future__ import annotations

import json
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[3]
RELEASE_ROOT = REPO_ROOT / "release" / "lafc-evict-v0.1-open-current-contract-preserved"
PAIRWISE_SAMPLE = RELEASE_ROOT / "data" / "pairwise_sample" / "pairwise_sample.parquet"
DECISION_VIEW = RELEASE_ROOT / "data" / "decision_view" / "decision_view.parquet"
OUT_DIR = Path(__file__).resolve().parent.parent / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

con = duckdb.connect()
con.execute(f"CREATE VIEW pw AS SELECT * FROM '{PAIRWISE_SAMPLE}'")
con.execute(f"CREATE VIEW dv AS SELECT * FROM '{DECISION_VIEW}'")

report: dict[str, object] = {}

n_rows = con.execute("SELECT COUNT(*) FROM pw").fetchone()[0]
report["pairwise_sample_row_count"] = n_rows

overall = con.execute(
    """
    SELECT
        SUM(is_tie) AS n_ties,
        SUM(label_a_better) AS n_a_better,
        SUM(label_b_better) AS n_b_better,
        COUNT(DISTINCT decision_id) AS n_unique_decisions
    FROM pw
    """
).fetchone()
n_ties, n_a_better, n_b_better, n_unique_decisions = overall
report["reviewer_tie_reproduction"] = {
    "n_ties": n_ties,
    "n_rows": n_rows,
    "tie_fraction": n_ties / n_rows,
    "reviewer_reported": "878,262 / 1,000,000",
    "matches_reviewer_number_exactly": n_ties == 878262,
}
n_strict = n_a_better + n_b_better
report["strict_preference"] = {
    "n_strict_pairs": n_strict,
    "strict_fraction": n_strict / n_rows,
    "n_a_better": n_a_better,
    "n_b_better": n_b_better,
    "direction_balance_a_better_share": n_a_better / n_strict,
    "direction_balance_b_better_share": n_b_better / n_strict,
}

# decisions contributing >=1 strict pair vs only-tied-pairs decisions
by_decision = con.execute(
    """
    SELECT decision_id,
        COUNT(*) AS n_pairs_sampled,
        SUM(is_tie) AS n_tie_pairs,
        SUM(1 - is_tie) AS n_strict_pairs
    FROM pw GROUP BY decision_id
    """
).df()
n_decisions_with_strict = int((by_decision["n_strict_pairs"] > 0).sum())
n_decisions_only_tied = int((by_decision["n_strict_pairs"] == 0).sum())
report["decision_contribution"] = {
    "n_unique_decisions_in_sample": n_unique_decisions,
    "n_decisions_contributing_ge1_strict_pair": n_decisions_with_strict,
    "fraction_decisions_contributing_ge1_strict_pair": n_decisions_with_strict / n_unique_decisions,
    "n_decisions_contributing_only_tied_pairs": n_decisions_only_tied,
    "fraction_decisions_only_tied_pairs": n_decisions_only_tied / n_unique_decisions,
    "mean_pairs_sampled_per_decision": float(by_decision["n_pairs_sampled"].mean()),
    "mean_strict_pairs_per_decision_among_contributors": float(
        by_decision.loc[by_decision["n_strict_pairs"] > 0, "n_strict_pairs"].mean()
    ),
}

# strict-pair density by capacity / horizon / family (within the shipped sample)
density = con.execute(
    """
    SELECT trace_family, capacity, horizon,
        COUNT(*) AS n_pairs,
        SUM(is_tie) AS n_ties,
        SUM(1-is_tie) AS n_strict,
        CAST(SUM(1-is_tie) AS DOUBLE) / COUNT(*) AS strict_fraction
    FROM pw GROUP BY trace_family, capacity, horizon
    ORDER BY strict_fraction DESC
    """
).df()
density.to_csv(OUT_DIR / "phase7_pairwise_strict_density.csv", index=False)
report["strict_pair_density_top5"] = density.head(5).to_dict(orient="records")
report["strict_pair_density_bottom5"] = density.tail(5).to_dict(orient="records")

# ---------------------------------------------------------------------------
# Quadratic pairwise-expansion weighting effect
# ---------------------------------------------------------------------------
# If the FULL pairwise universe were materialized (all C(candidate_count,2)
# pairs per decision) instead of a fixed 1,000,000-row sample, decisions with
# larger candidate_count would contribute quadratically more pairs. Quantify
# this using decision_view's candidate_count (population, not sample).
quad = con.execute(
    """
    SELECT
        SUM(candidate_count * (candidate_count - 1) / 2) AS full_universe_pair_count,
        COUNT(*) AS n_decisions,
        AVG(candidate_count * (candidate_count - 1) / 2) AS mean_pairs_per_decision,
        MIN(candidate_count * (candidate_count - 1) / 2) AS min_pairs_per_decision,
        MAX(candidate_count * (candidate_count - 1) / 2) AS max_pairs_per_decision
    FROM dv
    """
).fetchone()
full_pairs, n_dec_dv, mean_pairs, min_pairs, max_pairs = quad
report["quadratic_expansion_effect"] = {
    "full_pairwise_universe_size_if_materialized": int(full_pairs),
    "shipped_pairwise_sample_size": n_rows,
    "shipped_sample_coverage_of_full_universe": n_rows / full_pairs,
    "mean_pairs_per_decision_full_universe": mean_pairs,
    "min_pairs_per_decision_full_universe": int(min_pairs),
    "max_pairs_per_decision_full_universe": int(max_pairs),
    "ratio_max_to_min_pairs_per_decision": max_pairs / min_pairs,
    "interpretation": (
        "If the full pairwise universe were used instead of the capped "
        "1,000,000-row sample, a decision with candidate_count=256 would "
        "contribute (256*255/2)=32,640 pairs versus (32*31/2)=496 pairs for "
        "a candidate_count=32 decision -- a 65.8x weighting disparity purely "
        "from candidate-pool size, which correlates with capacity. This would "
        "systematically overweight large-capacity decisions in any pairwise-"
        "trained or pairwise-evaluated model relative to a decision-level "
        "view. The shipped 1,000,000-row sample avoids this by sampling "
        "pairs directly rather than materializing the full universe, but "
        "reports using the sample should still confirm the sample's own "
        "capacity/family mix (Table tab:pairwise-sample-summary) is not "
        "itself skewed relative to decision-level population shares."
    ),
}

# Compare shipped-sample capacity mix vs population capacity mix (decision-weighted)
sample_capacity_mix = con.execute(
    "SELECT capacity, COUNT(*) AS n FROM pw GROUP BY capacity ORDER BY capacity"
).df()
population_capacity_mix = con.execute(
    "SELECT capacity, COUNT(*) AS n FROM dv GROUP BY capacity ORDER BY capacity"
).df()
report["sample_vs_population_capacity_mix"] = {
    "pairwise_sample_pct": (sample_capacity_mix.set_index("capacity")["n"] / n_rows * 100).round(2).to_dict(),
    "decision_population_pct": (population_capacity_mix.set_index("capacity")["n"] / n_dec_dv * 100).round(2).to_dict(),
}

with open(OUT_DIR / "pairwise_report.json", "w") as f:
    json.dump(report, f, indent=2, default=str)

print(json.dumps(report, indent=2, default=str))
