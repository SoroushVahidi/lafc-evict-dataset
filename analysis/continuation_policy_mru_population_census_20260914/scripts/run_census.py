"""Full-population deterministic LRU-vs-MRU continuation census.

Streams compact decision-level records; NEVER materializes candidate-level
rows to disk (per-candidate loss dicts are computed and discarded inside
census_lib.compute_compact_decision_record). Checkpointed by
(family, capacity, horizon) chunk: each chunk is written to its own JSONL
file, marked complete with a `.done` sidecar (expected count + SHA256) only
after every decision in that chunk succeeds. Resume skips only decisions
already present as valid, complete JSON lines in a chunk's file -- a
malformed/truncated trailing line is detected and NOT counted as complete,
and is silently ignored (not retried automatically; the decision it
represents is simply re-run, which is safe since decisions are independent
and idempotent).
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from census_lib import (  # noqa: E402
    CAPACITIES, CONTINUATIONS, EXPECTED_TRACE_SHA256, FAMILIES, HORIZONS, PROCESSED_TRACE_DIR,
    compute_compact_decision_record, enumerate_decision_positions, load_trace,
    reconstruct_candidates_at_t, sha256_file,
)

CENSUS_DIR = Path(__file__).resolve().parents[1]
OUTPUTS_ROOT = CENSUS_DIR / "outputs"


def run_git(repo: str, args) -> str:
    out = subprocess.run(["git", "-C", repo] + args, capture_output=True, text=True, check=False)
    return out.stdout.strip()


def chunk_key(family, capacity, horizon):
    return f"{family}_{capacity}_{horizon}"


def _scan_chunk_lines(chunk_path: Path):
    """Parse a chunk file line-by-line. Returns (valid_lines, done_ts,
    n_malformed) where valid_lines is the exact list of raw text lines
    (no trailing newline) that parsed as complete decision records, in
    original order -- used both to compute the resume set and to rewrite
    the file cleanly (see rewrite_chunk_dropping_malformed)."""
    if not chunk_path.exists():
        return [], set(), 0
    valid_lines = []
    done = set()
    malformed = 0
    with open(chunk_path, "r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            if row.get("status") != "complete" or "request_t" not in row:
                malformed += 1
                continue
            valid_lines.append(line)
            done.add(row["request_t"])
    return valid_lines, done, malformed


def load_valid_completed_ts(chunk_path: Path) -> set:
    """Load the set of request_t values already recorded as valid, complete
    JSON lines in a chunk file. A malformed/truncated final line (e.g. from
    a killed process mid-write) is detected and excluded -- not counted as
    complete, never silently patched."""
    _valid_lines, done, malformed = _scan_chunk_lines(chunk_path)
    if malformed:
        print(f"  WARNING: {chunk_path.name}: {malformed} malformed/incomplete line(s) ignored (not counted as done)")
    return done


def rewrite_chunk_dropping_malformed(chunk_path: Path) -> int:
    """Rewrite chunk_path to contain ONLY its valid, complete lines, dropping
    any malformed/truncated content (e.g. a partially-written last line from
    a killed process) so a subsequent append never leaves permanent garbage
    embedded in the file. Returns the number of lines dropped. A no-op
    (returns 0) if the file has no malformed content, or doesn't exist."""
    if not chunk_path.exists():
        return 0
    valid_lines, _done, malformed = _scan_chunk_lines(chunk_path)
    if malformed == 0:
        return 0
    with open(chunk_path, "w", encoding="utf-8") as fh:
        for line in valid_lines:
            fh.write(line + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    print(f"  REPAIRED: {chunk_path.name}: dropped {malformed} malformed/truncated line(s) before resuming")
    return malformed


def process_chunk(run_dir: Path, family, capacity, horizon, log):
    chunks_dir = run_dir / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    key = chunk_key(family, capacity, horizon)
    chunk_path = chunks_dir / f"{key}.jsonl"
    done_marker = chunks_dir / f"{key}.done"

    positions, requests = enumerate_decision_positions(family, capacity)
    expected_count = len(positions)

    if done_marker.exists():
        marker = json.loads(done_marker.read_text())
        if marker.get("n_decisions") == expected_count:
            log(f"[{key}] already complete ({expected_count} decisions) -- skipping")
            return expected_count, expected_count

    rewrite_chunk_dropping_malformed(chunk_path)  # never append after a truncated/malformed trailing line
    already_done_ts = load_valid_completed_ts(chunk_path)
    remaining = [t for t in positions if t not in already_done_ts]
    log(f"[{key}] {len(already_done_ts)}/{expected_count} already done, {len(remaining)} remaining")

    n_written_this_call = 0
    with open(chunk_path, "a", encoding="utf-8") as fh:
        for i, t in enumerate(remaining):
            candidates, pid = reconstruct_candidates_at_t(requests, capacity, t)
            record = compute_compact_decision_record(family, capacity, t, horizon, candidates, pid, requests)
            fh.write(json.dumps(record, sort_keys=True) + "\n")
            n_written_this_call += 1
            if (i + 1) % 2000 == 0:
                fh.flush()
                os.fsync(fh.fileno())
                log(f"[{key}] {len(already_done_ts) + i + 1}/{expected_count} decisions complete")
        fh.flush()
        os.fsync(fh.fileno())

    final_ts = load_valid_completed_ts(chunk_path)
    if len(final_ts) == expected_count:
        done_marker.write_text(json.dumps({
            "n_decisions": expected_count, "chunk_sha256": sha256_file(chunk_path),
            "completed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }, indent=2), encoding="utf-8")
        log(f"[{key}] COMPLETE ({expected_count}/{expected_count})")
    else:
        log(f"[{key}] INCOMPLETE after this pass: {len(final_ts)}/{expected_count} -- will resume on next invocation")

    return len(final_ts), expected_count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    run_id = args.run_id
    if run_id is None:
        ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        short_commit = run_git(str(CENSUS_DIR.parents[1]), ["rev-parse", "--short=12", "HEAD"]) or "unknown"
        run_id = f"{ts}_{short_commit}"

    run_dir = OUTPUTS_ROOT / run_id
    if run_dir.exists() and any(run_dir.iterdir()) and not args.resume:
        raise FileExistsError(f"Refusing to reuse non-empty run directory {run_dir} without --resume")
    run_dir.mkdir(parents=True, exist_ok=True)

    log_lines = []

    def log(msg):
        line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}"
        print(line, flush=True)
        log_lines.append(line)
        if len(log_lines) % 20 == 0:
            (run_dir / "census.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    start_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    log(f"Census started: run_id={run_id} resume={args.resume}")
    log(f"Matrix: families={FAMILIES} capacities={CAPACITIES} horizons={HORIZONS} continuations={CONTINUATIONS}")

    for family in FAMILIES:
        trace_path = PROCESSED_TRACE_DIR / family / "trace.jsonl"
        actual_hash = sha256_file(trace_path)
        assert actual_hash == EXPECTED_TRACE_SHA256[family], f"{family}: trace hash mismatch"

    progress = {}
    total_expected = 0
    total_done = 0
    for family in FAMILIES:
        for capacity in CAPACITIES:
            for horizon in HORIZONS:
                n_done, n_expected = process_chunk(run_dir, family, capacity, horizon, log)
                progress[chunk_key(family, capacity, horizon)] = {"done": n_done, "expected": n_expected}
                total_done += n_done
                total_expected += n_expected
                (run_dir / "progress.json").write_text(json.dumps({
                    "total_done": total_done, "total_expected": total_expected,
                    "chunks": progress, "last_update_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }, indent=2, sort_keys=True), encoding="utf-8")

    end_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    lafc_repo = str(CENSUS_DIR.parents[1])
    secondary_repo = "/home/soroush/projects/augmented-caching/repo/.claude/worktrees/continuation-sensitivity-pilot-20260914"
    provenance = {
        "run_id": run_id, "start_time_utc": start_time, "end_time_utc": end_time,
        "total_decisions_done": total_done, "total_decisions_expected": total_expected,
        "families": list(FAMILIES), "capacities": list(CAPACITIES), "horizons": list(HORIZONS),
        "continuations": list(CONTINUATIONS),
        "primary_repo": {
            "path": lafc_repo, "branch": run_git(lafc_repo, ["branch", "--show-current"]),
            "head": run_git(lafc_repo, ["rev-parse", "HEAD"]), "git_status_short": run_git(lafc_repo, ["status", "--short"]),
        },
        "secondary_repo": {
            "path": secondary_repo, "branch": run_git(secondary_repo, ["branch", "--show-current"]),
            "head": run_git(secondary_repo, ["rev-parse", "HEAD"]), "git_status_short": run_git(secondary_repo, ["status", "--short"]),
        },
        "trace_sha256_verified": EXPECTED_TRACE_SHA256,
        "environment": {"python_version": sys.version, "platform": platform.platform()},
    }
    (run_dir / "provenance.json").write_text(json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8")
    (run_dir / "census.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    log(f"Census finished this invocation: {total_done}/{total_expected} decisions complete")
    print(f"\nRUN_ID={run_id}")


if __name__ == "__main__":
    main()
