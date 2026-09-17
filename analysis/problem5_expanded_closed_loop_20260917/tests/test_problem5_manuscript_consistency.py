"""Problem-5 Phase 9-10: validation that manuscript values equal generated
outputs, that the primary table equals a second, independent source of the
existing Tier-1 evidence (not just the already-derived linkage CSV), and
that the figure's source data is internally consistent with the table.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ANALYSIS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ANALYSIS_DIR.parents[1]
OUT_DIR = ANALYSIS_DIR / "outputs"
LATEX_DIR = REPO_ROOT / "paper" / "performance_evaluation" / "latex"

TIER1_EVIDENCE_SUMMARY = (
    REPO_ROOT / "analysis" / "closed_loop_tier1_evidence_20260914" / "run"
    / "20260914T023445Z_8a4cd32402a1" / "summary.csv"
)

DISPLAY_FAMILY = {
    "cloudphysics": "alibaba-block",
    "metacdn": "metacdn",
    "metakv": "metakv",
    "twemcache": "twemcache",
    "wiki2018": "wiki2018",
}


def _load_primary_table():
    return list(csv.DictReader(open(OUT_DIR / "problem5_primary_table.csv", encoding="utf-8")))


def test_primary_table_has_all_10_cells_and_7_policies():
    rows = _load_primary_table()
    assert len(rows) == 10
    cells = {(r["family"], r["capacity"]) for r in rows}
    assert len(cells) == 10
    for r in rows:
        for p in ("lru", "mru", "random", "sieve", "arc", "lirs", "s3fifo"):
            assert p in r and r[p] != ""


def test_expanded_policies_excludes_wtinylfu():
    import sys

    sys.path.insert(
        0,
        str(Path("/home/soroush/projects/augmented-caching/worktrees/problem5-expanded-baselines-20260917/src")),
    )
    sys.path.insert(0, str(ANALYSIS_DIR / "scripts"))
    from expanded_policies import EXPANDED_POLICIES

    assert "wtinylfu" not in EXPANDED_POLICIES
    assert set(EXPANDED_POLICIES) == {"arc", "lirs", "s3fifo"}


def test_existing_4_policy_values_match_frozen_tier1_evidence_summary_directly():
    """Cross-check against the RAW frozen Tier-1 evidence summary.csv
    (a different, more primary source than joined_offline_closed_loop.csv,
    which this analysis otherwise reads from) to confirm the existing
    LRU/MRU/random/SIEVE numbers were not altered when combined with the
    expanded policies.
    """
    tier1_rows = list(csv.DictReader(open(TIER1_EVIDENCE_SUMMARY, encoding="utf-8")))
    tier1_by_key = {}
    for r in tier1_rows:
        if r["status"] != "complete":
            continue
        key = (r["family"], int(r["capacity"]), r["policy"])
        tier1_by_key[key] = float(r["miss_ratio"])

    primary_rows = _load_primary_table()
    checked = 0
    for row in primary_rows:
        family, capacity = row["family"], int(row["capacity"])
        for policy in ("lru", "mru", "sieve"):
            expected = tier1_by_key[(family, capacity, policy)]
            actual = float(row[policy])
            assert abs(expected - actual) < 1e-9, (
                f"{family}/{capacity}/{policy}: frozen={expected} primary_table={actual}"
            )
            checked += 1
    assert checked == 10 * 3


def test_random_policy_matches_frozen_seed_mean_directly():
    tier1_rows = list(csv.DictReader(open(TIER1_EVIDENCE_SUMMARY, encoding="utf-8")))
    random_rows = [r for r in tier1_rows if r["policy"] == "random" and r["status"] == "complete"]
    by_key = {(r["family"], int(r["capacity"])): float(r["miss_ratio"]) for r in random_rows}

    primary_rows = _load_primary_table()
    for row in primary_rows:
        key = (row["family"], int(row["capacity"]))
        expected = by_key[key]
        actual = float(row["random"])
        assert abs(expected - actual) < 1e-9, f"{key}: frozen_mean={expected} primary_table={actual}"


def test_policy_spread_csv_matches_independent_recomputation_from_primary_table():
    """The figure's source data (policy_spread.csv) must equal a spread
    recomputed independently, in this test, from the primary table CSV."""
    primary_rows = {(r["family"], int(r["capacity"])): r for r in _load_primary_table()}
    spread_rows = list(csv.DictReader(open(OUT_DIR / "problem5_policy_spread.csv", encoding="utf-8")))
    assert len(spread_rows) == 10
    policies = ["lru", "mru", "random", "sieve", "arc", "lirs", "s3fifo"]
    for srow in spread_rows:
        key = (srow["family"], int(srow["capacity"]))
        prow = primary_rows[key]
        values = [float(prow[p]) for p in policies]
        recomputed_spread = max(values) - min(values)
        assert abs(recomputed_spread - float(srow["policy_spread_all7"])) < 1e-9


def test_manuscript_table_values_equal_generated_csv():
    """Parse the manuscript-committed .tex table and check every numeric
    cell equals the generated CSV, catching any manual edit drift."""
    tex = (LATEX_DIR / "tables" / "table_problem5_expanded_closed_loop.tex").read_text(encoding="utf-8")
    row_pattern = re.compile(
        r"^\s*([a-zA-Z0-9\-]+) & (\d+) & ([\d.]+) & ([\d.]+) & ([\d.]+) & ([\d.]+) & ([\d.]+) & ([\d.]+) & ([\d.]+) \\\\\s*$",
        re.MULTILINE,
    )
    matches = row_pattern.findall(tex)
    assert len(matches) == 10, f"expected 10 data rows in the manuscript table, found {len(matches)}"

    csv_by_key = {}
    for r in _load_primary_table():
        display = DISPLAY_FAMILY[r["family"]]
        csv_by_key[(display, int(r["capacity"]))] = r

    for fam, cap, lru, mru, random_, sieve, arc, lirs, s3fifo in matches:
        row = csv_by_key[(fam, int(cap))]
        for name, tex_val in [
            ("lru", lru), ("mru", mru), ("random", random_), ("sieve", sieve),
            ("arc", arc), ("lirs", lirs), ("s3fifo", s3fifo),
        ]:
            assert abs(float(tex_val) - float(row[name])) < 1e-4, (
                f"{fam}/{cap}/{name}: manuscript={tex_val} csv={row[name]}"
            )


def test_expanded_raw_results_internally_consistent():
    rows = [json.loads(line) for line in open(OUT_DIR / "problem5_expanded_run_results.jsonl", encoding="utf-8")]
    assert len(rows) == 30
    keys = [r["run_key"] for r in rows]
    assert len(keys) == len(set(keys))
    for r in rows:
        assert r["hits"] + r["misses"] == r["scored_requests"]
        assert 0.0 <= r["miss_ratio"] <= 1.0
        assert r["seed"] is None
        assert r["policy"] in ("arc", "lirs", "s3fifo")


def test_provenance_records_pinned_simulator_and_matching_trace_hashes():
    prov = json.loads((OUT_DIR / "problem5_expanded_provenance.json").read_text(encoding="utf-8"))
    assert prov["simulator_check"]["ok"] is True
    assert prov["simulator_check"]["head_matches_expected"] is True
    assert all(v["sha256_matches"] for v in prov["trace_check"].values())
    assert prov["n_executions"] == 30
