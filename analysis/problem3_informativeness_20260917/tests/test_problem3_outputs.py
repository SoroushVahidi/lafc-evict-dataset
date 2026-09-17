from __future__ import annotations

import json
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "analysis" / "problem3_informativeness_20260917" / "outputs"
FIG = ROOT / "analysis" / "problem3_informativeness_20260917" / "figures"


def test_baseline_facts_reproduce_canonical_counts() -> None:
    facts = json.loads((OUT / "baseline_facts.json").read_text())
    assert facts["total_decision_horizon_count"] == 2_363_286
    assert facts["total_candidate_rows"] == 277_995_072
    assert abs(facts["all_tied_fraction"] - 0.676601985540472) < 1e-15
    assert abs(facts["random_optimal_probability"] - 0.9912418754543462) < 1e-15
    assert abs(facts["expected_uniform_random_regret"] - 0.008826200441884731) < 1e-15
    assert facts["unique_winner_fraction"] == 0.0
    assert facts["validation"]["zero_not_z"] == 0
    assert facts["validation"]["positive_z"] == 0


def test_protocol_was_committed_before_analysis_run() -> None:
    state = json.loads((OUT / "source_state.json").read_text())
    assert state["protocol_commit"] == "076e1cf7ea5e1d3d5058b8b1f3004328687e1aa5"
    assert state["source_sha"] == "a79da7235297eb2be3436a884195025f24df3c68"


def test_primary_summary_has_all_methods_and_no_count_drift() -> None:
    with (OUT / "primary_method_by_informativeness.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    expected_methods = {
        "uniform_random",
        "lru",
        "clean_linear",
        "clean_pairwise_logistic",
        "frozen_hgb",
    }
    assert {row["method"] for row in rows} == expected_methods
    totals = {method: 0 for method in expected_methods}
    for row in rows:
        totals[row["method"]] += int(row["n_decisions"])
    assert all(total == 2_363_286 for total in totals.values())

    z = [row for row in rows if row["informativeness_stratum"] == "Z"]
    assert z
    assert all(float(row["info_mean"]) == 0 for row in z)
    assert all(float(row["mean_regret"]) == 0 for row in z)
    assert all(float(row["optimal_selection_rate"]) == 1 for row in z)


def test_random_simulation_matches_analytical_expectation_on_sample() -> None:
    sim = json.loads((OUT / "random_simulation_validation.json").read_text())
    assert sim["n_decisions"] > 100_000
    assert abs(sim["mean_regret_delta"]) < 5e-4


def test_figures_and_table_sources_exist() -> None:
    assert (FIG / "figure_problem3_mean_regret_by_informativeness.pdf").is_file()
    assert (FIG / "figure_problem3_improvement_vs_random.pdf").is_file()
    assert (OUT / "table_informativeness_strata_source.csv").is_file()
    assert (
        ROOT
        / "paper/performance_evaluation/latex/tables/table_informativeness_strata.tex"
    ).is_file()
