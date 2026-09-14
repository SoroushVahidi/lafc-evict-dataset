"""Run the frozen 80-decision pilot under MRU (deterministic) and random
(10-seed, CRN) continuation policies, and compute the pre-registered
tie-aware metrics against the LRU baseline. Diagnostic/correctness only --
never a scientific conclusion.
"""
from __future__ import annotations

import collections
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pilot_lib import (  # noqa: E402
    PILOT_HORIZON,
    assert_no_learned_policy,
    load_trace,
    reconstruct_candidates_at_t,
    sha256_file,
    sha256_text,
    simulate_rollout_misses,
)
from metrics import (  # noqa: E402
    cross_continuation_regret,
    kendall_tau_b,
    optimal_set_jaccard,
    pairwise_taxonomy,
)

PILOT_DIR = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PILOT_DIR / "PILOT_MANIFEST.json"
OUTPUTS_ROOT = PILOT_DIR / "outputs"
RANDOM_SEEDS = tuple(range(10))  # pre-registered starting seed count, DESIGN.md Section 8

PROCESSED_TRACE_DIR = Path("/home/soroush/projects/augmented-caching/repo/data/processed")
EXPECTED_TRACE_SHA256 = {
    "cloudphysics": "fedb3d31ee3c1dd847d25f967392cdf0fdec1e9c1fbb6808772e281bc8d4fb57",
    "metacdn": "7301f02e1373cb7e06f1ed2c417a8ebe16581319354780f811c8d032391f4e73",
    "metakv": "4c229e841d546cd57a2edb6e3ddc53461ff4dc03d366e9d24e4239a89db7e0de",
    "twemcache": "62df27062ce2595c843fd91e01d26c9783ff8f165f6b26e983696eda7ada0bb9",
    "wiki2018": "3813084bebfcf463ac22a685494b46aea45aded55d314411c9fbb058b5d67608",
}


def run_git(repo: str, args) -> str:
    out = subprocess.run(["git", "-C", repo] + args, capture_output=True, text=True, check=False)
    return out.stdout.strip()


def compute_candidate_losses(candidates, pid, requests, t, capacity, horizon, policy, rng_seed=None):
    assert_no_learned_policy([policy])
    future = requests[t + 1 : t + 1 + horizon]
    losses = {}
    for candidate in candidates:
        forced_cache = [p for p in candidates if p != candidate] + [pid]
        losses[candidate] = float(
            simulate_rollout_misses(
                cache_pages=forced_cache, future_reqs=future, capacity=capacity,
                reference_policy=policy, rng_seed=rng_seed,
            )
        )
    return losses


def losses_to_regrets(losses):
    best = min(losses.values())
    return {c: v - best for c, v in losses.items()}


def check_run_dir_available(run_dir: Path) -> None:
    """Raise FileExistsError if run_dir already exists and is non-empty --
    run directories are immutable per invocation, never silently reused."""
    if run_dir.exists() and any(run_dir.iterdir()):
        raise FileExistsError(f"Refusing to reuse non-empty run directory {run_dir}")


def make_run_id() -> str:
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    short_commit = run_git(str(PILOT_DIR.parents[1]), ["rev-parse", "--short=12", "HEAD"]) or "unknown"
    return f"{ts}_{short_commit}"


def main():
    manifest = json.loads(MANIFEST_PATH.read_text())
    manifest_bytes_hash = sha256_file(MANIFEST_PATH)

    run_id = make_run_id()
    run_dir = OUTPUTS_ROOT / run_id
    check_run_dir_available(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    log_lines = []

    def log(msg):
        line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}"
        print(line)
        log_lines.append(line)

    start_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    log(f"Pilot run started: run_id={run_id}")

    trace_cache = {}
    candidate_rows = []
    decision_metrics = []

    for d in manifest["decisions"]:
        family, capacity, t, horizon = d["family"], d["capacity"], d["request_t"], d["horizon"]
        assert horizon == PILOT_HORIZON
        key = family
        if key not in trace_cache:
            requests, _pages, _ids = load_trace(family)
            trace_path = PROCESSED_TRACE_DIR / family / "trace.jsonl"
            actual_hash = sha256_file(trace_path)
            assert actual_hash == EXPECTED_TRACE_SHA256[family], f"{family}: trace hash mismatch"
            trace_cache[key] = requests
        requests = trace_cache[key]

        candidates, pid = reconstruct_candidates_at_t(requests, capacity, t)
        assert d["candidate_count"] == len(candidates), f"{d['decision_id']}: candidate_count mismatch"

        lru_losses = compute_candidate_losses(candidates, pid, requests, t, capacity, horizon, "lru")
        lru_regrets = losses_to_regrets(lru_losses)

        mru_losses = compute_candidate_losses(candidates, pid, requests, t, capacity, horizon, "mru")
        mru_regrets = losses_to_regrets(mru_losses)

        random_losses_by_seed = {
            seed: compute_candidate_losses(candidates, pid, requests, t, capacity, horizon, "random", rng_seed=seed)
            for seed in RANDOM_SEEDS
        }

        for policy, losses in [("lru", lru_losses), ("mru", mru_losses)]:
            regrets = losses_to_regrets(losses)
            for c in candidates:
                candidate_rows.append({
                    "decision_id": d["decision_id"], "family": family, "capacity": capacity, "horizon": horizon,
                    "reference_policy": policy, "continuation_rng_seed": None,
                    "candidate_page_id": c, "rollout_loss_h": losses[c], "rollout_regret_h": regrets[c],
                    "candidate_is_rollout_optimal": regrets[c] == 0.0, "candidate_count": len(candidates),
                    "status": "complete",
                })
        for seed, losses in random_losses_by_seed.items():
            regrets = losses_to_regrets(losses)
            for c in candidates:
                candidate_rows.append({
                    "decision_id": d["decision_id"], "family": family, "capacity": capacity, "horizon": horizon,
                    "reference_policy": "random", "continuation_rng_seed": seed,
                    "candidate_page_id": c, "rollout_loss_h": losses[c], "rollout_regret_h": regrets[c],
                    "candidate_is_rollout_optimal": regrets[c] == 0.0, "candidate_count": len(candidates),
                    "status": "complete",
                })

        random_mean_losses = {
            c: sum(random_losses_by_seed[s][c] for s in RANDOM_SEEDS) / len(RANDOM_SEEDS) for c in candidates
        }
        random_mean_regrets = losses_to_regrets(random_mean_losses)

        for policy_name, regrets, losses_for_regret in [
            ("mru", mru_regrets, mru_losses),
            ("random_mean", random_mean_regrets, random_mean_losses),
        ]:
            jaccard = optimal_set_jaccard(lru_regrets, regrets)
            taxonomy = pairwise_taxonomy(lru_regrets, regrets)
            tau = kendall_tau_b(lru_regrets, regrets)
            ccr = cross_continuation_regret(lru_regrets, losses_for_regret)
            decision_metrics.append({
                "decision_id": d["decision_id"], "family": family, "capacity": capacity, "horizon": horizon,
                "alt_policy": policy_name,
                "baseline_lru_all_tied": d["baseline_lru_all_tied"],
                "alt_all_tied": all(v == 0.0 for v in regrets.values()),
                "optimal_set_jaccard": jaccard,
                "kendall_tau_b": tau,
                **{f"pairwise_{k}": v for k, v in taxonomy.items()},
                **{f"ccr_{k}": v for k, v in ccr.items()},
            })

        log(f"Decision complete: {d['decision_id']} (family={family} capacity={capacity} "
            f"candidates={len(candidates)} baseline_all_tied={d['baseline_lru_all_tied']})")

    end_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    with open(run_dir / "candidate_results.csv", "w", newline="", encoding="utf-8") as fh:
        import csv
        fieldnames = list(candidate_rows[0].keys())
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in candidate_rows:
            writer.writerow(row)

    with open(run_dir / "decision_metrics.csv", "w", newline="", encoding="utf-8") as fh:
        import csv
        fieldnames = list(decision_metrics[0].keys())
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in decision_metrics:
            writer.writerow(row)

    secondary_repo = "/home/soroush/projects/augmented-caching/repo/.claude/worktrees/continuation-sensitivity-pilot-20260914"
    provenance = {
        "run_id": run_id,
        "PILOT_NOTICE": "PILOT -- NOT A SCIENTIFIC RESULT. Correctness/feasibility only.",
        "start_time_utc": start_time,
        "end_time_utc": end_time,
        "pilot_manifest_sha256": manifest_bytes_hash,
        "pilot_manifest_path": str(MANIFEST_PATH),
        "primary_repo": {
            "path": str(PILOT_DIR.parents[1]),
            "branch": run_git(str(PILOT_DIR.parents[1]), ["branch", "--show-current"]),
            "head": run_git(str(PILOT_DIR.parents[1]), ["rev-parse", "HEAD"]),
            "git_status_short": run_git(str(PILOT_DIR.parents[1]), ["status", "--short"]),
        },
        "secondary_repo": {
            "path": secondary_repo,
            "branch": run_git(secondary_repo, ["branch", "--show-current"]),
            "head": run_git(secondary_repo, ["rev-parse", "HEAD"]),
            "git_status_short": run_git(secondary_repo, ["status", "--short"]),
        },
        "random_seeds": list(RANDOM_SEEDS),
        "trace_sha256_verified": EXPECTED_TRACE_SHA256,
        "environment": {"python_version": sys.version, "platform": platform.platform()},
    }
    (run_dir / "provenance.json").write_text(json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8")

    n_complete = len(candidate_rows)
    summary = {
        "PILOT_NOTICE": "PILOT -- NOT A SCIENTIFIC RESULT.",
        "run_id": run_id,
        "n_decisions": len(manifest["decisions"]),
        "n_candidate_rows": n_complete,
        "n_failed": 0,
        "random_seeds_run": list(RANDOM_SEEDS),
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    manifest_out = {
        "run_id": run_id, "run_valid_pending_gates": True,
        "output_files": {},
    }
    for name in ("candidate_results.csv", "decision_metrics.csv", "summary.json", "provenance.json"):
        p = run_dir / name
        if p.exists():
            manifest_out["output_files"][name] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest_out, indent=2, sort_keys=True), encoding="utf-8")

    (run_dir / "pilot.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    log(f"Pilot run finished: run_id={run_id}, {n_complete} candidate rows written")
    print(f"\nRUN_ID={run_id}")


if __name__ == "__main__":
    main()
