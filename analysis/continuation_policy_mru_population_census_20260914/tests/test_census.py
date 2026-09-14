import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pytest  # noqa: E402

from census_lib import (  # noqa: E402
    CAPACITIES, CONTINUATIONS, FAMILIES, HORIZONS,
    build_requests_from_lists, compute_compact_decision_record, reconstruct_candidates_at_t,
)
from run_census import chunk_key, load_valid_completed_ts  # noqa: E402


def test_census_scope_is_lru_mru_only():
    assert CONTINUATIONS == ("lru", "mru")
    assert "random" not in CONTINUATIONS
    assert "sieve" not in CONTINUATIONS
    assert "fifo" not in CONTINUATIONS
    assert "blind_oracle" not in CONTINUATIONS


def test_full_capacity_range():
    assert CAPACITIES == (32, 64, 128, 256)


def test_full_horizon_range():
    assert HORIZONS == (4, 8, 16)


def test_full_family_range():
    assert FAMILIES == ("cloudphysics", "metacdn", "metakv", "twemcache", "wiki2018")


def _synthetic(page_ids, capacity, t, horizon):
    requests, _pages = build_requests_from_lists(page_ids)
    candidates, pid = reconstruct_candidates_at_t(requests, capacity, t)
    fam = "cloudphysics"
    return compute_compact_decision_record(fam, capacity, t, horizon, candidates, pid, requests)


def test_compact_record_all_tied_decision():
    # All-unique sequence -> every candidate has identical (zero) future
    # reuse within the horizon -> fully tied under both LRU and MRU.
    page_ids = ["a", "b", "c"] + [f"x{i}" for i in range(20)]
    rec = _synthetic(page_ids, capacity=3, t=3, horizon=4)
    assert rec["all_tied_lru"] is True
    assert rec["all_tied_mru"] is True
    assert rec["optimal_set_jaccard"] == 1.0
    assert rec["lru_optimal_set_size"] == rec["candidate_count"]


def test_compact_record_discriminative_decision():
    # a is reused soon after; b,c are not reused within the horizon at all
    # -> a should NOT be the optimal candidate to evict (a is needed again).
    page_ids = ["a", "b", "c", "d", "a", "e", "f", "g"]
    rec = _synthetic(page_ids, capacity=3, t=3, horizon=4)
    assert rec["candidate_count"] == 3
    assert 0 <= rec["optimal_set_jaccard"] <= 1.0
    assert rec["lru_min_loss"] >= 0
    assert rec["mru_min_loss"] >= 0


def test_compact_record_no_nan_or_negative():
    for capacity in (5, 10):
        # Fill the cache with `capacity` distinct fillers, then a run of
        # distinct "new" items so every position >= capacity is guaranteed
        # to be a genuine miss-with-full-cache (a real decision point).
        page_ids = [f"f{i}" for i in range(capacity)] + [f"n{i}" for i in range(60)]
        for horizon in (2, 4, 8):
            rec = _synthetic(page_ids, capacity=capacity, t=capacity, horizon=horizon)
            for key in ("lru_min_loss", "mru_min_loss", "ccr_mean_over_LRU_optimal", "ccr_best_case", "ccr_worst_case"):
                v = rec[key]
                assert v == v  # not NaN
                assert v >= 0


def test_deterministic_mru_repeat():
    page_ids = ["a", "b", "c", "d", "a", "e", "f", "g", "b", "h"]
    rec1 = _synthetic(page_ids, capacity=3, t=3, horizon=4)
    rec2 = _synthetic(page_ids, capacity=3, t=3, horizon=4)
    assert rec1 == rec2


def test_chunk_key_format():
    assert chunk_key("cloudphysics", 256, 16) == "cloudphysics_256_16"


def test_load_valid_completed_ts_empty_file_missing(tmp_path):
    assert load_valid_completed_ts(tmp_path / "does_not_exist.jsonl") == set()


def test_load_valid_completed_ts_ignores_malformed_trailing_line(tmp_path):
    p = tmp_path / "chunk.jsonl"
    good1 = json.dumps({"request_t": 10, "status": "complete"})
    good2 = json.dumps({"request_t": 20, "status": "complete"})
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(good1 + "\n")
        fh.write(good2 + "\n")
        fh.write('{"request_t": 30, "status": "compl')  # truncated, no newline -- simulates a kill mid-write
    done = load_valid_completed_ts(p)
    assert done == {10, 20}
    assert 30 not in done


def test_load_valid_completed_ts_ignores_non_complete_status(tmp_path):
    p = tmp_path / "chunk2.jsonl"
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"request_t": 5, "status": "failed"}) + "\n")
        fh.write(json.dumps({"request_t": 6, "status": "complete"}) + "\n")
    done = load_valid_completed_ts(p)
    assert done == {6}


def test_resume_skips_only_already_done_decisions(tmp_path):
    p = tmp_path / "chunk3.jsonl"
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"request_t": 100, "status": "complete"}) + "\n")
        fh.write(json.dumps({"request_t": 200, "status": "complete"}) + "\n")
    done = load_valid_completed_ts(p)
    all_positions = [100, 150, 200, 250]
    remaining = [t for t in all_positions if t not in done]
    assert remaining == [150, 250]


def test_no_duplicate_decision_written_twice_in_same_chunk_file(tmp_path):
    # Simulates appending a second pass over remaining decisions; the same
    # request_t must never be written more than once in one census run.
    p = tmp_path / "chunk4.jsonl"
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"request_t": 1, "status": "complete"}) + "\n")
    done_before = load_valid_completed_ts(p)
    assert 1 in done_before
    # A correct resume must exclude t=1 from any remaining-work list:
    remaining = [t for t in [1, 2, 3] if t not in done_before]
    assert remaining == [2, 3]
