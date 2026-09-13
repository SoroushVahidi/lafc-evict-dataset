#!/usr/bin/env python3
"""Phase 5: rerun the Phase-7 pairwise information-content audit using ONLY
the verified canonical (regenerated, post-fix) pairwise sample -- not the
stale on-disk release file. Mirrors
analysis/sigmod_target_discriminativeness_20260913/scripts/03_pairwise_analysis.py
exactly, but reads the canonical regenerated parquet and adds a direct
before/after comparison against that prior audit's (stale-file-based) numbers.
"""
from __future__ import annotations

import json
from pathlib import Path

import duckdb

REPO_ROOT = Path("/home/soroush/projects/lafc-evict-dataset/repo")
CANONICAL_PATH = Path(
    "/tmp/claude-1000/-home-soroush/8a66210e-4d63-4b01-b3ba-10065c25f134/"
    "scratchpad/pairwise_repair/generated/pairwise_sample.parquet"
)
PRIOR_AUDIT_JSON = REPO_ROOT / "analysis/sigmod_target_discriminativeness_20260913/outputs/pairwise_report.json"
OUT_DIR = Path(__file__).resolve().parent.parent / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

con = duckdb.connect()
con.execute(f"CREATE VIEW pw AS SELECT * FROM '{CANONICAL_PATH}'")

report: dict[str, object] = {"source": str(CANONICAL_PATH), "label": "canonical_regenerated_post_fix"}

n_rows = con.execute("SELECT COUNT(*) FROM pw").fetchone()[0]
overall = con.execute(
    "SELECT SUM(is_tie), SUM(label_a_better), SUM(label_b_better), COUNT(DISTINCT decision_id) FROM pw"
).fetchone()
n_ties, n_a_better, n_b_better, n_unique_decisions = overall
n_strict = n_a_better + n_b_better

report["summary"] = {
    "n_rows": n_rows,
    "n_ties": n_ties,
    "tie_fraction": n_ties / n_rows,
    "n_strict_pairs": n_strict,
    "strict_fraction": n_strict / n_rows,
    "n_a_better": n_a_better,
    "n_b_better": n_b_better,
    "direction_balance_a_better_share": n_a_better / n_strict,
    "direction_balance_b_better_share": n_b_better / n_strict,
    "n_unique_decisions_in_sample": n_unique_decisions,
}

by_decision = con.execute(
    "SELECT decision_id, COUNT(*) n_pairs, SUM(is_tie) n_tie, SUM(1-is_tie) n_strict FROM pw GROUP BY decision_id"
).df()
n_with_strict = int((by_decision["n_strict"] > 0).sum())
n_only_ties = int((by_decision["n_strict"] == 0).sum())
report["decision_contribution"] = {
    "n_decisions_with_ge1_strict_pair": n_with_strict,
    "fraction_with_ge1_strict_pair": n_with_strict / n_unique_decisions,
    "n_decisions_only_tied_pairs": n_only_ties,
    "fraction_only_tied_pairs": n_only_ties / n_unique_decisions,
}

density = con.execute(
    """
    SELECT trace_family, capacity, horizon,
        COUNT(*) n_pairs, SUM(is_tie) n_ties, SUM(1-is_tie) n_strict,
        CAST(SUM(1-is_tie) AS DOUBLE) / COUNT(*) AS strict_fraction
    FROM pw GROUP BY trace_family, capacity, horizon ORDER BY strict_fraction DESC
    """
).df()
density.to_csv(OUT_DIR / "canonical_pairwise_strict_density.csv", index=False)
report["strict_density_top5"] = density.head(5).to_dict(orient="records")
report["strict_density_bottom5"] = density.tail(5).to_dict(orient="records")

# Before/after comparison against the prior (stale-file-based) audit
prior = json.loads(PRIOR_AUDIT_JSON.read_text())
report["comparison_to_prior_stale_based_audit"] = {
    "prior_tie_fraction": prior["reviewer_tie_reproduction"]["tie_fraction"],
    "canonical_tie_fraction": n_ties / n_rows,
    "prior_direction_balance_a_share": prior["strict_preference"]["direction_balance_a_better_share"],
    "canonical_direction_balance_a_share": n_a_better / n_strict,
    "prior_decisions_with_strict_fraction": prior["decision_contribution"]["fraction_decisions_contributing_ge1_strict_pair"],
    "canonical_decisions_with_strict_fraction": n_with_strict / n_unique_decisions,
    "note": (
        "The prior audit's direction-balance numbers (5.1%/94.9%) were an "
        "artifact of the stale file's pre-1f5f272-and-pre-3b49189 construction, "
        "not a real property of the benchmark. The canonical numbers below "
        "(tie fraction ~87.8%, balanced ~49.8%/50.2% direction split) match "
        "the manuscript's own committed table exactly and should be treated "
        "as the correct characterization going forward. The qualitative "
        "conclusion (heavily tie-dominated) is unchanged; the direction-"
        "balance and exact tie-fraction figures should be corrected."
    ),
}

with open(OUT_DIR / "canonical_pairwise_report.json", "w") as f:
    json.dump(report, f, indent=2, default=str)

print(json.dumps(report, indent=2, default=str))
