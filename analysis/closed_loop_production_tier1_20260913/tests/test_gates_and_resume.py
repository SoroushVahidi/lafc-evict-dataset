import json

import pytest

import tier1_core as t1


def _complete_row(execution, scored_requests=100, hits=80, misses=20, evictions=5, runtime=0.01):
    cfg = t1.FAMILY_CONFIG[execution.family]
    return {
        "run_key": execution.run_key, "family": execution.family, "capacity": execution.capacity,
        "policy": execution.policy, "seed": execution.seed, "status": "complete", "error": "",
        "scored_split_label": cfg.scored_split_label,
        "scored_windows": json.dumps(list(cfg.scored_windows)),
        "scored_requests": scored_requests, "hits": hits, "misses": misses,
        "miss_ratio": misses / scored_requests, "evictions": evictions,
        "full_trace_requests": 50000, "full_trace_hits": 40000, "full_trace_misses": 10000,
        "runtime_sec": runtime,
    }


def _all_complete_rows(plan):
    return [_complete_row(e) for e in plan]


def test_gates_pass_on_a_fully_valid_synthetic_run():
    plan = t1.build_plan()
    rows = _all_complete_rows(plan)
    valid, gates = t1.is_run_scientifically_valid(plan, rows)
    failing = [g for g in gates if not g.passed]
    assert valid, f"unexpected failing gates: {failing}"


def test_gates_fail_on_hits_plus_misses_mismatch():
    plan = t1.build_plan()
    rows = _all_complete_rows(plan)
    rows[0] = dict(rows[0])
    rows[0]["misses"] = rows[0]["misses"] + 1  # break the identity
    valid, gates = t1.is_run_scientifically_valid(plan, rows)
    assert not valid
    names = {g.name for g in gates if not g.passed}
    assert "hits_plus_misses_equals_scored_requests" in names


def test_gates_fail_on_negative_count():
    plan = t1.build_plan()
    rows = _all_complete_rows(plan)
    rows[0] = dict(rows[0])
    rows[0]["evictions"] = -1
    valid, gates = t1.is_run_scientifically_valid(plan, rows)
    assert not valid
    names = {g.name for g in gates if not g.passed}
    assert "no_negative_counts" in names


def test_gates_fail_on_nan_miss_ratio():
    plan = t1.build_plan()
    rows = _all_complete_rows(plan)
    rows[0] = dict(rows[0])
    rows[0]["miss_ratio"] = float("nan")
    valid, gates = t1.is_run_scientifically_valid(plan, rows)
    assert not valid
    names = {g.name for g in gates if not g.passed}
    assert "no_nan_or_inf_numeric_outputs" in names


def test_gates_fail_on_out_of_range_miss_ratio():
    plan = t1.build_plan()
    rows = _all_complete_rows(plan)
    rows[0] = dict(rows[0])
    rows[0]["miss_ratio"] = 1.5
    valid, gates = t1.is_run_scientifically_valid(plan, rows)
    assert not valid
    names = {g.name for g in gates if not g.passed}
    assert "miss_ratio_in_valid_range" in names


def test_gates_fail_on_mismatched_scored_windows_within_cell():
    plan = t1.build_plan()
    rows = _all_complete_rows(plan)
    # Corrupt one cloudphysics/cap32/lru row's recorded windows so it disagrees
    # with the other rows in the same (family, capacity) cell.
    for i, r in enumerate(rows):
        if r["family"] == "cloudphysics" and r["capacity"] == 32 and r["policy"] == "lru":
            rows[i] = dict(r)
            rows[i]["scored_windows"] = json.dumps([[0, 1]])
            break
    valid, gates = t1.is_run_scientifically_valid(plan, rows)
    assert not valid
    names = {g.name for g in gates if not g.passed}
    assert "identical_scored_windows_within_cell" in names


def test_gates_fail_on_extra_random_seed_or_missing_seed():
    plan = t1.build_plan()
    rows = _all_complete_rows(plan)
    # Remove one random row for cloudphysics/32 (seed 0) -> only 19 seeds present.
    rows = [
        r for r in rows
        if not (r["family"] == "cloudphysics" and r["capacity"] == 32 and r["policy"] == "random" and r["seed"] == 0)
    ]
    valid, gates = t1.is_run_scientifically_valid(plan, rows)
    assert not valid  # incomplete plan -> not fully valid regardless of per-cell gate wording


def test_partial_run_is_never_marked_valid():
    plan = t1.build_plan()
    rows = _all_complete_rows(plan)[:-1]  # 229 of 230
    valid, gates = t1.is_run_scientifically_valid(plan, rows)
    assert not valid
    completeness_gate = [g for g in gates if g.name == "all_230_planned_executions_complete"][0]
    assert not completeness_gate.passed


def test_duplicate_execution_key_in_results_is_rejected():
    plan = t1.build_plan()
    rows = _all_complete_rows(plan)
    rows.append(dict(rows[0]))  # duplicate the first row's key
    valid, gates = t1.is_run_scientifically_valid(plan, rows)
    assert not valid
    names = {g.name for g in gates if not g.passed}
    assert "no_duplicate_execution_key" in names


def test_failed_rows_are_recorded_and_visible_not_dropped():
    plan = t1.build_plan()
    rows = _all_complete_rows(plan)
    rows[0] = dict(rows[0])
    rows[0]["status"] = "failed"
    rows[0]["error"] = "synthetic induced failure"
    valid, gates = t1.is_run_scientifically_valid(plan, rows)
    assert not valid  # a failed row means the run is not fully complete/valid
    visible = [g for g in gates if g.name == "failed_rows_present_and_visible"]
    assert visible and visible[0].passed
    assert "synthetic induced failure" not in [g.detail for g in gates]  # detail carries run_key, not error text
    completeness_gate = [g for g in gates if g.name == "all_230_planned_executions_complete"][0]
    assert not completeness_gate.passed


# --- Resume / durable storage tests -----------------------------------------


def test_append_and_load_result_rows_roundtrip(tmp_path):
    run_dir = tmp_path / "run1"
    run_dir.mkdir()
    plan = t1.build_plan()
    row = _complete_row(plan[0])
    t1.append_result_row(run_dir, row)
    loaded = t1.load_result_rows(run_dir)
    assert len(loaded) == 1
    assert loaded[0]["run_key"] == plan[0].run_key


def test_last_write_wins_for_a_given_run_key(tmp_path):
    run_dir = tmp_path / "run2"
    run_dir.mkdir()
    plan = t1.build_plan()
    row_fail = dict(_complete_row(plan[0]))
    row_fail["status"] = "failed"
    row_fail["error"] = "first attempt failed"
    t1.append_result_row(run_dir, row_fail)

    row_ok = _complete_row(plan[0])
    t1.append_result_row(run_dir, row_ok)

    loaded = t1.load_result_rows(run_dir)
    assert len(loaded) == 1
    assert loaded[0]["status"] == "complete"


def test_malformed_json_line_is_ignored_not_treated_as_complete(tmp_path):
    run_dir = tmp_path / "run3"
    run_dir.mkdir()
    plan = t1.build_plan()
    good = _complete_row(plan[0])
    t1.append_result_row(run_dir, good)
    # Append a corrupt/truncated line directly (simulating an interrupted write).
    with open(run_dir / t1.RESULTS_JSONL_NAME, "a", encoding="utf-8") as fh:
        fh.write('{"run_key": "cloudphysics|32|lru|none", "status": "compl\n')

    loaded = t1.load_result_rows(run_dir)
    assert len(loaded) == 1
    assert loaded[0]["run_key"] == plan[0].run_key
    assert loaded[0]["status"] == "complete"


def test_row_missing_recognizable_status_is_not_treated_as_complete(tmp_path):
    run_dir = tmp_path / "run4"
    run_dir.mkdir()
    with open(run_dir / t1.RESULTS_JSONL_NAME, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"run_key": "x|32|lru|none", "status": "running"}) + "\n")
    loaded = t1.load_result_rows(run_dir)
    assert loaded == []


def test_keys_to_skip_on_resume_default_skips_both_complete_and_failed(tmp_path):
    # Without --retry-failed, a failed execution must be treated the same as
    # a complete one for skip purposes: it stays failed and visible, and is
    # never silently re-run just because --resume was passed.
    run_dir = tmp_path / "run5"
    run_dir.mkdir()
    plan = t1.build_plan()
    ok_row = _complete_row(plan[0])
    fail_row = dict(_complete_row(plan[1]))
    fail_row["status"] = "failed"
    t1.append_result_row(run_dir, ok_row)
    t1.append_result_row(run_dir, fail_row)

    skip = t1.keys_to_skip_on_resume(run_dir, retry_failed=False)
    assert skip == {plan[0].run_key, plan[1].run_key}


def test_keys_to_skip_on_resume_with_retry_failed_excludes_failed_keys(tmp_path):
    # With the explicit --retry-failed decision, a previously failed
    # execution becomes eligible to run again (not skipped); a complete one
    # is still skipped.
    run_dir = tmp_path / "run5b"
    run_dir.mkdir()
    plan = t1.build_plan()
    ok_row = _complete_row(plan[0])
    fail_row = dict(_complete_row(plan[1]))
    fail_row["status"] = "failed"
    t1.append_result_row(run_dir, ok_row)
    t1.append_result_row(run_dir, fail_row)

    skip = t1.keys_to_skip_on_resume(run_dir, retry_failed=True)
    assert skip == {plan[0].run_key}
    assert plan[1].run_key not in skip


def test_new_run_dir_refuses_to_reuse_nonempty_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(t1, "outputs_root", lambda: tmp_path)
    run_dir = t1.new_run_dir(run_id="fixed_id")
    (run_dir / "marker.txt").write_text("x", encoding="utf-8")
    with pytest.raises(FileExistsError):
        t1.new_run_dir(run_id="fixed_id")
