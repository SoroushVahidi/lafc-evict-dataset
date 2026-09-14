import pytest

import tier1_core as t1


def test_plan_has_exactly_230_executions():
    plan = t1.build_plan()
    assert len(plan) == 230


def test_plan_composition_matches_approved_design():
    plan = t1.build_plan()
    t1.assert_plan_valid(plan)  # must not raise

    by_policy = {}
    for e in plan:
        by_policy[e.policy] = by_policy.get(e.policy, 0) + 1
    assert by_policy == {"lru": 10, "mru": 10, "sieve": 10, "random": 200}

    assert {e.family for e in plan} == set(t1.FAMILIES)
    assert {e.capacity for e in plan} == {32, 128}
    assert {e.seed for e in plan if e.seed is not None} == set(range(20))


def test_plan_has_no_duplicate_keys():
    plan = t1.build_plan()
    keys = [e.run_key for e in plan]
    assert len(keys) == len(set(keys))


def test_plan_summary_reports_horizons_as_comparison_only():
    plan = t1.build_plan()
    summary = t1.plan_summary(plan)
    assert summary["total_executions"] == 230
    assert summary["offline_horizon_primary"] == 16
    assert summary["offline_horizons_secondary"] == [4, 8, 16]
    assert summary["offline_horizons_are_comparison_only_not_executions"] is True


def test_tampered_plan_is_rejected_by_assert_plan_valid():
    plan = t1.build_plan()
    tampered = plan[:-1]  # drop one execution -> 229
    with pytest.raises(AssertionError):
        t1.assert_plan_valid(tampered)


def test_tampered_plan_with_duplicate_key_is_rejected():
    plan = t1.build_plan()
    tampered = plan + [plan[0]]
    with pytest.raises(AssertionError):
        t1.assert_plan_valid(tampered)


def test_family_config_matches_matrix_md_windows():
    assert t1.FAMILY_CONFIG["cloudphysics"].scored_windows == ((16384, 20479), (20480, 24575))
    assert t1.FAMILY_CONFIG["metacdn"].scored_windows == ((0, 4095), (24576, 32767), (36864, 45055))
    assert t1.FAMILY_CONFIG["metakv"].scored_windows == ((0, 4095),)
    assert t1.FAMILY_CONFIG["twemcache"].scored_windows == ((32768, 36863), (40960, 45055))
    assert t1.FAMILY_CONFIG["wiki2018"].scored_windows == ((24576, 28671),)


def test_metacdn_is_labeled_validation_not_test():
    cfg = t1.FAMILY_CONFIG["metacdn"]
    assert cfg.scored_split_label == "validation"
    assert "validation" in cfg.evidence_label.lower()
    # The caveat is allowed to *deny* being an unseen trace ("never as an
    # unseen trace"); it must never assert one positively.
    assert "never as an unseen trace" in cfg.split_caveat.lower()
    assert cfg.learned_policy_classification == "BLOCKED_LEAKAGE_RISK"


def test_no_family_evidence_label_or_caveat_calls_windows_held_out_traces():
    banned = ("held-out trace", "held out trace")
    negation_phrases = ("not an unseen trace", "never as an unseen trace", "never an unseen trace")
    for family, cfg in t1.FAMILY_CONFIG.items():
        text = (cfg.evidence_label + " " + cfg.split_caveat).lower()
        for phrase in banned:
            assert phrase not in text, f"{family}: banned phrase {phrase!r} found"
        # If "unseen trace" appears at all, it must be in one of the approved
        # negated forms, never asserted positively.
        if "unseen trace" in text:
            assert any(p in text for p in negation_phrases), family
