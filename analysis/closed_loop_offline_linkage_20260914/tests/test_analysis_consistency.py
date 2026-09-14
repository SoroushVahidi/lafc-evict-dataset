"""Consistency/audit assertions for the offline<->closed-loop linkage analysis.

Run with: python3 -m pytest analysis/closed_loop_offline_linkage_20260914/tests -v
(run scripts/build_joined_dataset.py and scripts/compute_rq_analyses.py first;
this test suite reads their outputs, it does not regenerate them, so a stale
run would be caught by the byte-count/row-count assertions below but not by
re-deriving the numbers itself -- that is independent_recheck.py's job.)
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ANALYSIS_ROOT / "data" / "joined_offline_closed_loop.csv"
OUT_DIR = ANALYSIS_ROOT / "outputs"
EVIDENCE_DIR = ANALYSIS_ROOT.parent / "closed_loop_tier1_evidence_20260914"


def load_joined():
    with open(DATA_PATH, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_joined_dataset_has_exactly_30_rows():
    rows = load_joined()
    assert len(rows) == 30


def test_no_capacity_64_or_256_leaked_into_analysis():
    rows = load_joined()
    caps = {row["capacity"] for row in rows}
    assert caps == {"32", "128"}, f"unexpected capacities in joined dataset: {caps}"


def test_all_three_horizons_present_for_every_family_capacity_cell():
    rows = load_joined()
    seen = {}
    for row in rows:
        seen.setdefault((row["family"], row["capacity"]), set()).add(row["horizon"])
    assert len(seen) == 10, f"expected 10 (family, capacity) cells, got {len(seen)}"
    for key, horizons in seen.items():
        assert horizons == {"4", "8", "16"}, f"{key}: missing horizon(s), got {horizons}"


def test_metacdn_is_never_labeled_test():
    rows = load_joined()
    for row in rows:
        if row["family"] == "metacdn":
            assert row["scored_split_label"] == "validation", row
        else:
            assert row["scored_split_label"] == "test", row


def test_wiki2018_is_exactly_degenerate_offline_and_closed_loop():
    rows = load_joined()
    for row in rows:
        if row["family"] == "wiki2018":
            assert float(row["offline_all_tied_fraction"]) == 1.0
            assert float(row["offline_mru_mean_regret"]) == 0.0
            assert float(row["offline_random_mean_regret"]) == 0.0
            assert float(row["cl_lru_miss_ratio"]) == 1.0
            assert float(row["cl_mru_miss_ratio"]) == 1.0
            assert float(row["cl_random_mean_miss_ratio"]) == 1.0
            assert float(row["cl_mru_minus_lru_miss_ratio_gap"]) == 0.0
            assert float(row["offline_mru_minus_lru_regret_gap"]) == 0.0


def test_no_sieve_offline_column_exists_anywhere():
    rows = load_joined()
    for row in rows:
        assert "offline_sieve_mean_regret" not in row
        assert "offline_sieve_optimal_rate" not in row
    # cl_sieve_miss_ratio IS present (closed-loop side has SIEVE) but must
    # never be paired against an offline SIEVE value, since none exists --
    # verified by inspecting the RQ script source rather than runtime here.
    rq_script = (ANALYSIS_ROOT / "scripts" / "compute_rq_analyses.py").read_text()
    assert "offline_sieve" not in rq_script


def test_rq_cl1_output_exists_and_covers_all_three_horizons():
    d = json.loads((OUT_DIR / "rq_cl1_rank_agreement.json").read_text())
    assert set(d["by_horizon"].keys()) == {"4", "8", "16"}
    for horizon in ("4", "8", "16"):
        for pair in ("mru_vs_lru", "random_vs_lru"):
            counts = d["by_horizon"][horizon][pair]["counts"]
            assert sum(counts.values()) == 10, f"H={horizon} {pair}: counts don't sum to 10 cells: {counts}"


def test_rq_cl1_pooled_secondary_is_labeled_as_pseudo_replicated():
    d = json.loads((OUT_DIR / "rq_cl1_rank_agreement.json").read_text())
    for pair, entry in d["pooled_across_horizons_SECONDARY"].items():
        assert "pseudo-replicated" in entry["note"].lower()
        assert entry["n_rows"] == 30


def test_rq_cl2_pooled_secondary_carries_a_caution_string():
    d = json.loads((OUT_DIR / "rq_cl2_gap_correspondence.json").read_text())
    for pair, entry in d["pooled_SECONDARY_pseudo_replicated"].items():
        assert "CAUTION" in entry
        assert "not" in entry["CAUTION"].lower()


def test_rq_cl2_primary_uses_n_equal_10_per_horizon():
    d = json.loads((OUT_DIR / "rq_cl2_gap_correspondence.json").read_text())
    for horizon in ("4", "8", "16"):
        for pair in ("mru_vs_lru", "random_vs_lru"):
            assert d["primary_by_horizon"][horizon][pair]["n"] == 10


def test_rq_cl2_excluding_wiki2018_uses_n_equal_8():
    d = json.loads((OUT_DIR / "rq_cl2_gap_correspondence.json").read_text())
    for horizon in ("4", "8", "16"):
        for pair in ("mru_vs_lru", "random_vs_lru"):
            assert d["excluding_wiki2018_by_horizon"][horizon][pair]["n"] == 8


def test_metakv_evidence_directory_frozen_run_matches_manifest_hashes():
    manifest = json.loads((EVIDENCE_DIR / "EVIDENCE_MANIFEST.json").read_text())
    import hashlib
    for entry in manifest["files"]:
        p = EVIDENCE_DIR / entry["frozen_relative_path"]
        assert p.exists(), f"missing frozen evidence file: {p}"
        actual = hashlib.sha256(p.read_bytes()).hexdigest()
        assert actual == entry["sha256_after_copy"], f"{p}: hash drift detected, expected {entry['sha256_after_copy']}, got {actual}"


def test_independent_recheck_script_passes():
    result = subprocess.run(
        [sys.executable, str(ANALYSIS_ROOT / "scripts" / "independent_recheck.py")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"independent_recheck.py failed:\n{result.stdout}\n{result.stderr}"
    assert "INDEPENDENT_RECHECK: PASS" in result.stdout


def test_rebuilding_joined_dataset_is_numerically_stable():
    """Deterministic rerun: rebuilding the joined CSV from the same frozen
    sources must reproduce byte-identical content (no timestamps, no
    nondeterministic ordering, no floating-point nondeterminism)."""
    before = DATA_PATH.read_bytes()
    result = subprocess.run(
        [sys.executable, str(ANALYSIS_ROOT / "scripts" / "build_joined_dataset.py")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    after = DATA_PATH.read_bytes()
    assert before == after, "rebuilding the joined dataset changed its bytes -- nondeterminism detected"
