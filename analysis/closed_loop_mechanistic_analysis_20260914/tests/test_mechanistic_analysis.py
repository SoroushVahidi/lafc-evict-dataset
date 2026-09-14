import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ANALYSIS_ROOT / "scripts"
OUT_DIR = ANALYSIS_ROOT / "outputs"
REPO_ROOT = ANALYSIS_ROOT.parents[1]
LINKAGE_ROOT = REPO_ROOT / "analysis" / "closed_loop_offline_linkage_20260914"
EVIDENCE_ROOT = REPO_ROOT / "analysis" / "closed_loop_tier1_evidence_20260914"

sys.path.insert(0, str(SCRIPTS_DIR))
from reuse_distance import stack_distances_fenwick, stack_distances_bruteforce  # noqa: E402


def test_no_simulator_module_imported_anywhere_in_scripts():
    for py in SCRIPTS_DIR.glob("*.py"):
        text = py.read_text(encoding="utf-8")
        assert "import lafc" not in text, f"{py} imports the simulator package"
        assert "from lafc" not in text, f"{py} imports from the simulator package"
        assert "run_policy(" not in text, f"{py} calls the simulator's run_policy()"
        assert "sys.path.insert(0, AUGMENTED_CACHING_SRC" not in text


def test_no_tier1_evidence_file_modified():
    manifest = json.loads((EVIDENCE_ROOT / "EVIDENCE_MANIFEST.json").read_text())
    for entry in manifest["files"]:
        p = EVIDENCE_ROOT / entry["frozen_relative_path"]
        actual = hashlib.sha256(p.read_bytes()).hexdigest()
        assert actual == entry["sha256_after_copy"], f"{p} has drifted from its frozen hash"


def test_no_linkage_artifact_modified():
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "log", "-1", "--format=%H", "analysis/tier1-offline-closed-loop-linkage-20260914"],
        capture_output=True, text=True,
    )
    linkage_head = result.stdout.strip()
    assert linkage_head, "could not resolve the linkage branch HEAD"
    # This worktree branched from c5c8422 == that HEAD; the linkage files
    # must be byte-identical to what's committed there (git diff empty).
    diff = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", linkage_head, "HEAD", "--", "analysis/closed_loop_offline_linkage_20260914"],
        capture_output=True, text=True,
    )
    assert diff.stdout == "", f"unexpected diff against frozen linkage artifacts:\n{diff.stdout}"


def test_exact_scored_windows_match_matrix_md():
    from analyze_trace_mechanisms import SCORED_WINDOWS
    expected = {
        "cloudphysics": [(16384, 20479), (20480, 24575)],
        "metacdn": [(0, 4095), (24576, 32767), (36864, 45055)],
        "metakv": [(0, 4095)],
        "twemcache": [(32768, 36863), (40960, 45055)],
        "wiki2018": [(24576, 28671)],
    }
    assert SCORED_WINDOWS == expected


def test_metakv_starts_at_request_zero():
    from analyze_trace_mechanisms import SCORED_WINDOWS
    lo, _hi = SCORED_WINDOWS["metakv"][0]
    assert lo == 0


def test_metacdn_remains_labeled_validation():
    from analyze_trace_mechanisms import SPLIT_LABEL
    assert SPLIT_LABEL["metacdn"] == "validation"
    for fam in ("cloudphysics", "metakv", "twemcache", "wiki2018"):
        assert SPLIT_LABEL[fam] == "test"


def test_capacities_restricted_to_32_and_128():
    from analyze_trace_mechanisms import CAPACITIES
    assert CAPACITIES == (32, 128)
    mech_rows = list(csv.DictReader(open(OUT_DIR / "mechanism_comparison.csv", newline="", encoding="utf-8")))
    caps = {int(r["capacity"]) for r in mech_rows}
    assert caps == {32, 128}


def test_reuse_distance_matches_analytic_example():
    seq = list("ABCABA")
    expected = [None, None, None, 2, 2, 1]
    assert stack_distances_fenwick(seq) == expected
    assert stack_distances_bruteforce(seq) == expected


def test_reuse_distance_all_unique_sequence_is_all_none():
    seq = ["a", "b", "c", "d", "e"]
    assert stack_distances_fenwick(seq) == [None] * 5


def test_reuse_distance_immediate_repeat_is_zero():
    seq = ["a", "a", "b", "b"]
    assert stack_distances_fenwick(seq) == [None, 0, None, 0]


def test_reuse_distance_fenwick_matches_bruteforce_on_random_sequence():
    import random
    rng = random.Random(1234)
    seq = [str(rng.randrange(30)) for _ in range(500)]
    assert stack_distances_fenwick(seq) == stack_distances_bruteforce(seq)


def test_no_offline_sieve_metric_is_referenced_anywhere():
    for py in SCRIPTS_DIR.glob("*.py"):
        text = py.read_text(encoding="utf-8")
        assert "offline_sieve" not in text.lower()
    for f in OUT_DIR.glob("*.csv"):
        header = f.read_text(encoding="utf-8").splitlines()[0].lower()
        assert "offline_sieve" not in header


def test_mechanism_comparison_lru_prediction_matches_tier1_exactly():
    mech_rows = list(csv.DictReader(open(OUT_DIR / "mechanism_comparison.csv", newline="", encoding="utf-8")))
    assert len(mech_rows) == 10
    for r in mech_rows:
        assert r["exact_match"] == "True", (
            f"{r['family']}/{r['capacity']}: trace-only LRU-hit prediction did not match "
            f"Tier-1 evidence exactly ({r['predicted_lru_hits_from_stack_distance']} vs "
            f"{r['actual_lru_hits_tier1']})"
        )


def test_wiki2018_has_exactly_zero_reuse_events():
    with open(OUT_DIR / "trace_characteristics.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    wiki = next(r for r in rows if r["family"] == "wiki2018")
    assert wiki["n_reuse_events"] == "0"
    assert float(wiki["unique_over_request_ratio"]) == 1.0


def test_source_trace_hashes_recorded_and_match_design():
    # Cross-checks the same trace SHA256 values the production design and
    # Tier-1 harness already recorded, using an independent hashlib pass
    # over the same files this analysis itself read.
    expected = {
        "cloudphysics": "fedb3d31ee3c1dd847d25f967392cdf0fdec1e9c1fbb6808772e281bc8d4fb57",
        "metacdn": "7301f02e1373cb7e06f1ed2c417a8ebe16581319354780f811c8d032391f4e73",
        "metakv": "4c229e841d546cd57a2edb6e3ddc53461ff4dc03d366e9d24e4239a89db7e0de",
        "twemcache": "62df27062ce2595c843fd91e01d26c9783ff8f165f6b26e983696eda7ada0bb9",
        "wiki2018": "3813084bebfcf463ac22a685494b46aea45aded55d314411c9fbb058b5d67608",
    }
    from analyze_trace_mechanisms import PROCESSED_TRACE_DIR
    for family, expected_hash in expected.items():
        p = PROCESSED_TRACE_DIR / family / "trace.jsonl"
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        assert h.hexdigest() == expected_hash, f"{family}: trace hash drift detected"


def test_analysis_is_deterministic_on_rerun():
    before = (OUT_DIR / "mechanism_comparison.csv").read_bytes()
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "analyze_trace_mechanisms.py")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    after = (OUT_DIR / "mechanism_comparison.csv").read_bytes()
    assert before == after, "rerunning the analysis changed mechanism_comparison.csv -- nondeterminism detected"


def test_independent_recheck_script_passes():
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "independent_recheck.py")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"independent_recheck.py failed:\n{result.stdout}\n{result.stderr}"
    assert "INDEPENDENT_RECHECK: PASS" in result.stdout
