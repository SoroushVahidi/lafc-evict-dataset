"""Problem-5 Phase 4: run the expanded comparator set on the exact Tier-1 protocol.

Re-uses, byte-for-byte, the family/capacity/scored-window/trace-hash constants
from ``analysis/closed_loop_production_tier1_20260913/scripts/tier1_core.py``
(imported directly, not re-typed) so there is a single source of truth for
the protocol. Does NOT re-run or modify the existing LRU/MRU/random/SIEVE
Tier-1 evidence.

Simulator dependency files (``lafc.policies.base``, ``lafc.runner.run_policy``,
``lafc.simulator.request_trace``, ``lafc.types``) are imported from a
dedicated worktree pinned to the exact commit Tier 1 itself was validated
against (``chore/repository-polish`` @ ``ceb36705b59d0d16db55d0fc0bfb63a5c7a2a6a1``)
rather than whatever branch the shared root checkout happens to be on right
now, so this run cannot silently drift onto different simulator code.

Trace files are read directly from the shared root checkout's
``data/processed/`` (the actual, gitignored trace data; verified against the
exact SHA256 values recorded in ``FAMILY_CONFIG`` before use, never written
to).
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]  # lafc-evict-dataset worktree root
ANALYSIS_DIR = Path(__file__).resolve().parents[1]

TIER1_SCRIPTS_DIR = REPO_ROOT / "analysis" / "closed_loop_production_tier1_20260913" / "scripts"
sys.path.insert(0, str(TIER1_SCRIPTS_DIR))
import tier1_core  # noqa: E402  (pure-data constants only; no lafc import at module load)

PINNED_SIMULATOR_WORKTREE = Path(
    "/home/soroush/projects/augmented-caching/worktrees/problem5-expanded-baselines-20260917"
)
PINNED_SIMULATOR_SRC = str(PINNED_SIMULATOR_WORKTREE / "src")
EXPECTED_SIMULATOR_BRANCH = tier1_core.EXPECTED_SIMULATOR_BRANCH
EXPECTED_SIMULATOR_HEAD = tier1_core.EXPECTED_SIMULATOR_HEAD

REAL_TRACE_ROOT = Path("/home/soroush/projects/augmented-caching/repo/data/processed")

sys.path.insert(0, PINNED_SIMULATOR_SRC)
sys.path.insert(0, str(ANALYSIS_DIR / "scripts"))

from lafc.runner.run_policy import run_policy  # noqa: E402
from lafc.simulator.request_trace import build_requests_from_lists  # noqa: E402

from expanded_policies import EXPANDED_POLICIES, build_expanded_policy  # noqa: E402


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_git(repo: Path, args) -> str:
    import subprocess

    out = subprocess.run(["git", "-C", str(repo)] + args, capture_output=True, text=True, check=False)
    return out.stdout.strip()


def check_pinned_simulator() -> dict:
    head = run_git(PINNED_SIMULATOR_WORKTREE, ["rev-parse", "HEAD"])
    status = run_git(PINNED_SIMULATOR_WORKTREE, ["status", "--porcelain"])
    ok = (head == EXPECTED_SIMULATOR_HEAD) and (status == "")
    dep_hashes = {}
    for relpath in tier1_core.SIMULATOR_DEPENDENCY_FILES:
        p = PINNED_SIMULATOR_WORKTREE / relpath
        dep_hashes[relpath] = sha256_file(p) if p.exists() else None
    return {
        "worktree": str(PINNED_SIMULATOR_WORKTREE),
        "expected_head": EXPECTED_SIMULATOR_HEAD,
        "actual_head": head,
        "clean": status == "",
        "head_matches_expected": head == EXPECTED_SIMULATOR_HEAD,
        "ok": ok,
        "dependency_file_sha256": dep_hashes,
    }


def check_traces() -> dict:
    result = {}
    for family, cfg in tier1_core.FAMILY_CONFIG.items():
        path = REAL_TRACE_ROOT / cfg.trace_relpath
        actual = sha256_file(path) if path.exists() else None
        result[family] = {
            "path": str(path),
            "exists": path.exists(),
            "expected_sha256": cfg.expected_sha256,
            "actual_sha256": actual,
            "sha256_matches": actual == cfg.expected_sha256,
        }
    return result


def load_trace(family: str):
    cfg = tier1_core.FAMILY_CONFIG[family]
    path = REAL_TRACE_ROOT / cfg.trace_relpath
    page_ids = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            page_ids.append(str(rec["item_id"]))
    return build_requests_from_lists(page_ids)


def main() -> None:
    out_dir = ANALYSIS_DIR / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    sim_check = check_pinned_simulator()
    trace_check = check_traces()
    if not sim_check["ok"]:
        raise RuntimeError(f"Pinned simulator worktree check failed: {sim_check}")
    if not all(v["sha256_matches"] for v in trace_check.values()):
        raise RuntimeError(f"Trace SHA256 mismatch: {trace_check}")

    rows = []
    trace_cache = {}
    t_start = time.perf_counter()
    for family in tier1_core.FAMILIES:
        if family not in trace_cache:
            trace_cache[family] = load_trace(family)
        requests, pages = trace_cache[family]
        assert len(requests) == 50000, f"{family}: expected 50000 requests, got {len(requests)}"
        cfg = tier1_core.FAMILY_CONFIG[family]
        for capacity in tier1_core.CAPACITIES:
            for policy_name in EXPANDED_POLICIES:
                policy = build_expanded_policy(policy_name)
                t0 = time.perf_counter()
                result = run_policy(policy, requests, pages, capacity)
                elapsed = time.perf_counter() - t0
                metrics = tier1_core.score_events(result.events, cfg.scored_windows)
                row = {
                    "run_key": f"{family}|{capacity}|{policy_name}|none",
                    "family": family,
                    "capacity": capacity,
                    "policy": policy_name,
                    "seed": None,
                    "status": "complete",
                    "error": "",
                    "scored_split_label": cfg.scored_split_label,
                    "scored_windows": json.dumps(list(cfg.scored_windows)),
                    "scored_requests": metrics["scored_requests"],
                    "hits": metrics["hits"],
                    "misses": metrics["misses"],
                    "miss_ratio": metrics["miss_ratio"],
                    "evictions": metrics["evictions"],
                    "full_trace_requests": len(result.events),
                    "full_trace_hits": result.total_hits,
                    "full_trace_misses": result.total_misses,
                    "runtime_sec": elapsed,
                }
                rows.append(row)
                print(
                    f"{family}/{capacity}/{policy_name}: "
                    f"miss_ratio={row['miss_ratio']:.6f} scored={row['scored_requests']} "
                    f"runtime={elapsed:.3f}s"
                )
    total_elapsed = time.perf_counter() - t_start

    raw_path = out_dir / "problem5_expanded_run_results.jsonl"
    with open(raw_path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    provenance = {
        "run_timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "lafc_evict_head": run_git(REPO_ROOT, ["rev-parse", "HEAD"]),
        "lafc_evict_branch": run_git(REPO_ROOT, ["branch", "--show-current"]),
        "simulator_check": sim_check,
        "trace_check": trace_check,
        "expanded_policies": list(EXPANDED_POLICIES),
        "families": list(tier1_core.FAMILIES),
        "capacities": list(tier1_core.CAPACITIES),
        "n_executions": len(rows),
        "total_runtime_sec": total_elapsed,
        "tier1_reference_run_id": "20260914T023445Z_8a4cd32402a1",
        "tier1_evidence_path": "analysis/closed_loop_tier1_evidence_20260914/",
    }
    (out_dir / "problem5_expanded_provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8"
    )

    # Sanity gates mirroring Tier 1's own gate philosophy.
    assert len(rows) == len(tier1_core.FAMILIES) * len(tier1_core.CAPACITIES) * len(EXPANDED_POLICIES)
    keys = [r["run_key"] for r in rows]
    assert len(keys) == len(set(keys)), "duplicate run_key(s) detected"
    for r in rows:
        assert r["hits"] + r["misses"] == r["scored_requests"], r["run_key"]
        assert 0.0 <= r["miss_ratio"] <= 1.0, r["run_key"]

    print(f"\nDone: {len(rows)} executions in {total_elapsed:.2f}s. Wrote {raw_path}")


if __name__ == "__main__":
    main()
