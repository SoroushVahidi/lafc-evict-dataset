"""End-to-end exercise of run_production() itself, using a tiny synthetic
plan and synthetic in-memory trace data.

This is explicitly NOT a real Tier-1 family/capacity cell: the plan is
reduced (2 random seeds instead of 20) and the trace is a synthetic
in-memory sequence, not any real processed trace. The task authorizes
"synthetic micro-tests" / "tiny synthetic replay tests" during this
implementation task but forbids running a real family/capacity cell as a
substitute; this test respects that boundary while still exercising the
full run_production() code path (provenance capture, execution loop,
resume, output writing) that a future real launch would use unmodified.
"""

import json

import pytest

import tier1_core as t1


TINY_SEEDS = (0, 1)


def _tiny_plan():
    execs = []
    for policy in t1.DETERMINISTIC_POLICIES:
        execs.append(t1.Execution(family="cloudphysics", capacity=32, policy=policy, seed=None))
    for seed in TINY_SEEDS:
        execs.append(t1.Execution(family="cloudphysics", capacity=32, policy="random", seed=seed))
    return execs


def _tiny_assert_plan_valid(plan):
    keys = [e.run_key for e in plan]
    assert len(keys) == len(set(keys)), "duplicate keys in synthetic plan"
    t1.assert_no_learned_policy([e.policy for e in plan])


def _fake_load_processed_trace(path):
    import random as _random

    rng = _random.Random(99)
    page_ids = [str(rng.randrange(200)) for _ in range(50_000)]  # satisfies the 50k-request gate
    mods = t1._import_simulator_modules()
    return mods["build_requests_from_lists"](page_ids)


@pytest.fixture
def synthetic_env(monkeypatch):
    monkeypatch.setattr(t1, "build_plan", _tiny_plan)
    monkeypatch.setattr(t1, "assert_plan_valid", _tiny_assert_plan_valid)
    monkeypatch.setattr(t1, "load_processed_trace", _fake_load_processed_trace)
    monkeypatch.setitem(
        t1.FAMILY_CONFIG,
        "cloudphysics",
        t1.FamilySplit(
            trace_name=t1.FAMILY_CONFIG["cloudphysics"].trace_name,
            trace_relpath=t1.FAMILY_CONFIG["cloudphysics"].trace_relpath,
            expected_sha256=t1.FAMILY_CONFIG["cloudphysics"].expected_sha256,
            scored_windows=((0, 10_000),),
            scored_split_label="test",
            evidence_label="SYNTHETIC TEST FIXTURE ONLY -- not a real Tier-1 window",
            split_caveat="synthetic test fixture only, not a real Tier-1 window",
            learned_policy_classification="LEARNED_POLICY_SAFE_TEST",
        ),
    )
    return TINY_SEEDS


def test_run_production_end_to_end_writes_all_expected_outputs(tmp_path, synthetic_env):
    run_dir = tmp_path / "synthetic_run"
    run_dir.mkdir()

    manifest = t1.run_production(run_dir, resume=False, command_line="pytest-synthetic")

    assert (run_dir / "run_results.jsonl").exists()
    assert (run_dir / "run_results.csv").exists()
    assert (run_dir / "summary.csv").exists()
    assert (run_dir / "sanity_checks.json").exists()
    assert (run_dir / "provenance.json").exists()
    assert (run_dir / "run_manifest.json").exists()
    assert (run_dir / "tier1_run.log").exists()

    rows = t1.load_result_rows(run_dir)
    assert len(rows) == 5  # 3 deterministic + 2 random seeds
    assert all(r["status"] == "complete" for r in rows), rows
    for r in rows:
        assert r["hits"] + r["misses"] == r["scored_requests"]

    provenance = json.loads((run_dir / "provenance.json").read_text())
    assert provenance["lafc_evict"]["head"]  # non-empty
    assert provenance["simulator"]["expected_branch"] == "chore/repository-polish"
    assert "cloudphysics" in provenance["inputs"]

    # This synthetic run deliberately uses only 2 of the 20 required random
    # seeds (not the real Tier-1 count), so it must NOT be reported as a
    # scientifically valid Tier-1 run even though every row completed
    # against the (patched, tiny) plan it was given.
    assert manifest["run_valid"] is False
    sanity = json.loads((run_dir / "sanity_checks.json").read_text())
    gate_names_failed = {g["name"] for g in sanity["gates"] if not g["passed"]}
    assert "random_policy_seeds_exactly_0_to_19_when_present" in gate_names_failed
    # But every execution actually attempted must have completed cleanly.
    assert sanity["n_complete"] == 5
    assert sanity["n_failed"] == 0


def test_run_production_refuses_to_silently_overwrite_without_resume(tmp_path, synthetic_env):
    run_dir = tmp_path / "synthetic_run2"
    run_dir.mkdir()
    t1.run_production(run_dir, resume=False, command_line="pytest-synthetic")

    with pytest.raises(RuntimeError, match="already has"):
        t1.run_production(run_dir, resume=False, command_line="pytest-synthetic-again")


def test_run_production_resume_skips_already_complete_and_does_not_duplicate(tmp_path, synthetic_env):
    run_dir = tmp_path / "synthetic_run3"
    run_dir.mkdir()
    t1.run_production(run_dir, resume=False, command_line="pytest-synthetic")
    rows_before = t1.load_result_rows(run_dir)
    assert len(rows_before) == 5

    # Resuming a fully-complete run must not duplicate or re-run anything.
    t1.run_production(run_dir, resume=True, command_line="pytest-synthetic-resume")
    rows_after = t1.load_result_rows(run_dir)
    assert len(rows_after) == 5
    assert {r["run_key"] for r in rows_before} == {r["run_key"] for r in rows_after}


def test_run_production_resume_after_partial_failure_only_retries_failed_with_explicit_flag(tmp_path, synthetic_env, monkeypatch):
    run_dir = tmp_path / "synthetic_run4"
    run_dir.mkdir()

    # Manually seed one failed row and one complete row, simulating an
    # interrupted prior attempt, then resume.
    plan = _tiny_plan()
    ok_row = {
        "run_key": plan[0].run_key, "family": plan[0].family, "capacity": plan[0].capacity,
        "policy": plan[0].policy, "seed": plan[0].seed, "status": "complete", "error": "",
        "scored_split_label": "test", "scored_windows": json.dumps([[0, 10000]]),
        "scored_requests": 10001, "hits": 9000, "misses": 1001, "miss_ratio": 0.1,
        "evictions": 500, "full_trace_requests": 50000, "full_trace_hits": 40000,
        "full_trace_misses": 10000, "runtime_sec": 0.01,
    }
    failed_row = dict(ok_row)
    failed_row["run_key"] = plan[1].run_key
    failed_row["family"] = plan[1].family
    failed_row["policy"] = plan[1].policy
    failed_row["seed"] = plan[1].seed
    failed_row["status"] = "failed"
    failed_row["error"] = "simulated prior interruption"
    t1.append_result_row(run_dir, ok_row)
    t1.append_result_row(run_dir, failed_row)

    manifest = t1.run_production(run_dir, resume=True, retry_failed=False, command_line="pytest-resume-no-retry")
    rows = t1.load_result_rows(run_dir)
    by_key = {r["run_key"]: r for r in rows}
    # The previously-failed key must still be failed (never auto-retried).
    assert by_key[plan[1].run_key]["status"] == "failed"
    assert by_key[plan[1].run_key]["error"] == "simulated prior interruption"
    # The other 3 planned keys (not previously attempted) must now be complete.
    for e in plan[2:]:
        assert by_key[e.run_key]["status"] == "complete"
    assert manifest["run_valid"] is False  # one row is still 'failed'
