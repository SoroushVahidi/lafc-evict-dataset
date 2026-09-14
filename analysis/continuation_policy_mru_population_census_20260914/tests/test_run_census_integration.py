"""End-to-end smoke test of run_census.py's process_chunk() -- the actual
checkpoint/resume/done-marker mechanics -- using a monkeypatched tiny
decision population (not a real family/capacity's full tens-of-thousands),
so this stays a cheap smoke test, not a scientific run.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import run_census  # noqa: E402
from census_lib import build_requests_from_lists  # noqa: E402


def _tiny_trace():
    # 5 fillers + 20 distinct "new" items -> every position >= 5 is a real
    # eviction decision at capacity 5.
    page_ids = [f"f{i}" for i in range(5)] + [f"n{i}" for i in range(20)]
    requests, _pages = build_requests_from_lists(page_ids)
    return requests


def test_process_chunk_end_to_end_and_marks_done(tmp_path, monkeypatch):
    requests = _tiny_trace()
    monkeypatch.setattr(run_census, "enumerate_decision_positions", lambda family, capacity: (list(range(5, 15)), requests))

    logs = []
    n_done, n_expected = run_census.process_chunk(tmp_path, "cloudphysics", 5, 4, logs.append)
    assert n_done == n_expected == 10

    done_marker = tmp_path / "chunks" / "cloudphysics_5_4.done"
    assert done_marker.exists()
    marker = json.loads(done_marker.read_text())
    assert marker["n_decisions"] == 10

    chunk_path = tmp_path / "chunks" / "cloudphysics_5_4.jsonl"
    lines = [json.loads(l) for l in chunk_path.read_text().splitlines() if l.strip()]
    assert len(lines) == 10
    assert {r["request_t"] for r in lines} == set(range(5, 15))
    assert all(r["status"] == "complete" for r in lines)


def test_process_chunk_skips_when_already_marked_done(tmp_path, monkeypatch):
    requests = _tiny_trace()
    monkeypatch.setattr(run_census, "enumerate_decision_positions", lambda family, capacity: (list(range(5, 15)), requests))
    logs = []
    run_census.process_chunk(tmp_path, "cloudphysics", 5, 4, logs.append)
    logs.clear()
    n_done, n_expected = run_census.process_chunk(tmp_path, "cloudphysics", 5, 4, logs.append)
    assert n_done == n_expected == 10
    assert any("already complete" in l for l in logs)


def test_process_chunk_resumes_after_simulated_truncation(tmp_path, monkeypatch):
    requests = _tiny_trace()
    monkeypatch.setattr(run_census, "enumerate_decision_positions", lambda family, capacity: (list(range(5, 15)), requests))
    logs = []
    run_census.process_chunk(tmp_path, "cloudphysics", 5, 4, logs.append)

    chunk_path = tmp_path / "chunks" / "cloudphysics_5_4.jsonl"
    done_marker = tmp_path / "chunks" / "cloudphysics_5_4.done"
    lines = chunk_path.read_text().splitlines()
    # Simulate an interrupted process: drop the done marker and truncate the
    # last line mid-write (as a killed process might leave it).
    done_marker.unlink()
    truncated = lines[:-1] + [lines[-1][: len(lines[-1]) // 2]]
    chunk_path.write_text("\n".join(truncated) + "\n", encoding="utf-8")

    remaining_before = run_census.load_valid_completed_ts(chunk_path)
    assert len(remaining_before) == 9  # the truncated 10th line must not count as complete

    logs2 = []
    n_done, n_expected = run_census.process_chunk(tmp_path, "cloudphysics", 5, 4, logs2.append)
    assert n_done == n_expected == 10  # the missing decision was re-run, not skipped or duplicated

    # The file must be fully clean afterward -- no leftover malformed line
    # embedded among valid ones (every line must parse).
    final_lines = [json.loads(l) for l in chunk_path.read_text().splitlines() if l.strip()]
    ts = [r["request_t"] for r in final_lines]
    assert sorted(ts) == list(range(5, 15))
    assert len(ts) == len(set(ts))  # no duplicate decision written twice


def test_rewrite_chunk_dropping_malformed_removes_only_bad_lines(tmp_path):
    chunk_path = tmp_path / "c.jsonl"
    good1 = json.dumps({"request_t": 1, "status": "complete"})
    good2 = json.dumps({"request_t": 2, "status": "complete"})
    chunk_path.write_text(good1 + "\n" + good2 + "\n" + '{"request_t": 3, "status": "comp', encoding="utf-8")

    dropped = run_census.rewrite_chunk_dropping_malformed(chunk_path)
    assert dropped == 1

    remaining_lines = [json.loads(l) for l in chunk_path.read_text().splitlines() if l.strip()]
    assert {r["request_t"] for r in remaining_lines} == {1, 2}
    assert all(l for l in chunk_path.read_text().splitlines())  # every line parses


def test_rewrite_chunk_dropping_malformed_is_noop_when_clean(tmp_path):
    chunk_path = tmp_path / "c2.jsonl"
    content = json.dumps({"request_t": 1, "status": "complete"}) + "\n"
    chunk_path.write_text(content, encoding="utf-8")
    dropped = run_census.rewrite_chunk_dropping_malformed(chunk_path)
    assert dropped == 0
    assert chunk_path.read_text() == content
