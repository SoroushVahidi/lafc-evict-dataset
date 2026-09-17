"""Problem 7 Phase 16: regression tests against known-stale or previously
incorrect claims re-entering the manuscript.

Run from the repository root:
    pytest analysis/problem7_final_integrity_20260917/tests/test_no_stale_claims.py
"""
import pathlib
import re

LATEX_ROOT = pathlib.Path(__file__).resolve().parents[3] / "paper" / "performance_evaluation" / "latex"


def _read_all():
    text = (LATEX_ROOT / "main.tex").read_text()
    for f in sorted((LATEX_ROOT / "sections").glob("*.tex")):
        text += "\n" + f.read_text()
    for f in sorted((LATEX_ROOT / "tables").glob("*.tex")):
        text += "\n" + f.read_text()
    return text


def test_superseded_long_horizon_denominator_absent():
    text = _read_all()
    assert "706,888" not in text
    assert "706888" not in text


def test_matched_horizon_population_present_and_consistent():
    text = _read_all()
    assert text.count("787,762") >= 4  # dataset table + decision breakdown + matched-horizon table (x4 rows) + prose


def test_lru_9_of_10_always_scoped_to_original_four():
    """The historical '9 of 10' figure must never appear without being
    explicitly tied to the original/4-policy comparator set nearby."""
    text = _read_all()
    for m in re.finditer(r".{160}9 of 10.{40}", text):
        window = m.group(0)
        assert re.search(r"four|4[- ]polic", window, re.IGNORECASE), (
            f"Found unscoped '9 of 10' claim: ...{window}..."
        )


def test_expanded_comparator_headline_present():
    text = _read_all()
    assert "4 of\n10 cells" in text or "4 of 10 cells" in text or re.search(r"4 of\s*\n?\s*10 cells", text)


def test_five_of_six_cells_under_threshold_not_four():
    """Regression test for the C10 finding: this Problem-7 pass corrected
    'four of the six' to 'five of the six' cells with <3.2% relative gap."""
    text = _read_all()
    assert "four of\nthe six cells" not in text
    assert "five of\nthe six cells" in text or "five of the six cells" in text


def test_correlation_robustness_caveat_present():
    text = _read_all()
    assert "LOFO" in text
    assert "family-level\npermutation" in text or "family-level permutation" in text


def test_no_undefined_style_placeholder_bib_entries_remain():
    bib = (LATEX_ROOT / "refs.bib").read_text()
    removed_keys = [
        "chapelle2011yahoo", "joachims2017unbiasedltr", "li2011offlinecb",
        "liu2009ltr", "narita2019efficient", "qin2010letor",
        "saito2020pairwise", "swaminathan2015crm", "berger2018foopfoo",
        "fedchenko2018fnncache", "kirilin2020rlcache",
    ]
    for key in removed_keys:
        assert key not in bib, f"orphaned bib entry {key} should have been removed"


def test_dataset_scale_headline_numbers_present():
    text = _read_all()
    assert "277,995,072" in text
    assert "2,363,286" in text
