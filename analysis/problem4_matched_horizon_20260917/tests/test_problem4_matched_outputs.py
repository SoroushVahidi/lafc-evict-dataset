from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "analysis" / "problem4_matched_horizon_20260917" / "outputs"
ART = ROOT / "analysis" / "problem4_matched_horizon_20260917" / "artifacts"
PAPER_TABLE = ROOT / "paper" / "performance_evaluation" / "latex" / "tables" / "table_matched_long_horizon_sensitivity.tex"


def read_csv(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_common_population_manifest_has_expected_full_count_and_unique_cells() -> None:
    manifest = json.loads((ART / "common_population_manifest.json").read_text(encoding="utf-8"))
    assert manifest["total_decisions"] == 787_762
    assert manifest["common_population_keys"] == "analysis/problem4_matched_horizon_20260917/artifacts/common_population_keys.parquet"
    assert manifest["common_population_keys_sha256"]
    cells = manifest["cells"]
    assert len(cells) == 20
    keys = {(row["trace_family"], int(row["capacity"])) for row in cells}
    assert len(keys) == 20
    assert sum(int(row["decision_count"]) for row in cells) == manifest["total_decisions"]
    assert all(row["key_sha256"] for row in cells)


def test_common_population_key_parquet_is_explicit_and_deduplicated() -> None:
    key_path = ART / "common_population_keys.parquet"
    assert key_path.exists()
    payload = subprocess.check_output(
        [
            "python",
            "-c",
            (
                "import duckdb, json, sys; "
                "con=duckdb.connect(); "
                "row=con.execute(\"\"\"select count(*), count(distinct physical_key), "
                "count(distinct trace_family || '|' || capacity::varchar) "
                "from read_parquet(?)\"\"\", [sys.argv[1]]).fetchone(); "
                "print(json.dumps(row))"
            ),
            str(key_path),
        ],
        cwd=ROOT,
        text=True,
    )
    n_rows, n_keys, n_cells = json.loads(payload)
    assert n_rows == 787_762
    assert n_keys == 787_762
    assert n_cells == 20


def test_matched_micro_uses_identical_decision_population_at_every_horizon() -> None:
    rows = read_csv("matched_primary_micro_summary.csv")
    assert [int(row["horizon"]) for row in rows] == [16, 32, 64, 128]
    decisions = {int(float(row["decisions"])) for row in rows}
    candidate_rows = {int(float(row["candidate_rows"])) for row in rows}
    assert decisions == {787_762}
    assert candidate_rows == {92_665_024}
    all_tied = [float(row["all_tied_fraction"]) for row in rows]
    regret = [float(row["expected_random_regret"]) for row in rows]
    assert all(a >= b for a, b in zip(all_tied, all_tied[1:]))
    assert all(a <= b for a, b in zip(regret, regret[1:]))


def test_validation_declares_h16_canonical_match_and_equal_counts() -> None:
    validation = json.loads((OUT / "validation.json").read_text(encoding="utf-8"))
    assert validation["status"] == "PASS"
    assert validation["equal_count_every_horizon"] is True
    assert validation["common_population_total"] == 787_762
    assert all(row["pass"] for row in validation["h16_matches_canonical_release"])


def test_old_vs_matched_records_the_denominator_correction() -> None:
    rows = {int(row["horizon"]): row for row in read_csv("old_vs_matched_micro_summary.csv")}
    assert int(rows[16]["old_decisions"]) == 787_762
    assert int(rows[16]["matched_decisions"]) == 787_762
    for horizon in (32, 64, 128):
        assert int(rows[horizon]["old_decisions"]) == 706_888
        assert int(rows[horizon]["matched_decisions"]) == 787_762
    assert float(rows[128]["matched_all_tied_fraction"]) < float(rows[16]["matched_all_tied_fraction"])
    assert float(rows[128]["matched_all_tied_fraction"]) > 0.5


def test_paired_transitions_are_true_decision_counts() -> None:
    rows = read_csv("matched_paired_transition_micro_summary.csv")
    for row in rows:
        n = int(float(row["n_decisions"]))
        transition_sum = (
            int(float(row["tied_to_tied"]))
            + int(float(row["tied_to_discriminative"]))
            + int(float(row["discriminative_to_tied"]))
            + int(float(row["discriminative_to_discriminative"]))
        )
        info_sum = (
            int(float(row["info_increase"]))
            + int(float(row["info_decrease"]))
            + int(float(row["info_unchanged"]))
        )
        assert n == 787_762
        assert transition_sum == n
        assert info_sum == n
        assert int(float(row["discriminative_to_tied"])) == 0


def test_paper_table_uses_matched_counts_and_generated_values() -> None:
    table = PAPER_TABLE.read_text(encoding="utf-8")
    rows = read_csv("matched_primary_micro_summary.csv")
    for row in rows:
        assert f"{int(row['horizon'])} & 787,762" in table
        assert f"{float(row['all_tied_fraction']):.4f}" in table
        assert f"{float(row['random_optimal_probability']):.4f}" in table
        assert f"{float(row['expected_random_regret']):.4f}" in table
