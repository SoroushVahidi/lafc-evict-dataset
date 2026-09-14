"""Run the FULL pre-registered continuation-sensitivity experiment: 5,000
primary + 500 diagnostic decisions, all 3 horizons {4,8,16}, LRU baseline +
MRU (deterministic) + random (10 CRN seeds).

Raw candidate-level results are appended to a JSONL file (large, ~1GB,
never committed to git). Decision-level tie-aware metrics are accumulated
and written to a compact CSV (small, committed). Resumable: re-running with
the same RUN_ID and --resume skips decisions already recorded complete.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from full_lib import (  # noqa: E402
    HORIZONS,
    RANDOM_SEEDS,
    EXPECTED_TRACE_SHA256,
    PROCESSED_TRACE_DIR,
    assert_no_learned_policy,
    cross_continuation_regret,
    kendall_tau_b,
    load_trace,
    optimal_set_jaccard,
    pairwise_taxonomy,
    reconstruct_candidates_at_t,
    sha256_file,
    simulate_rollout_misses,
)

FULL_DIR = Path(__file__).resolve().parents[1]
OUTPUTS_ROOT = FULL_DIR / "outputs"


def run_git(repo: str, args) -> str:
    out = subprocess.run(["git", "-C", repo] + args, capture_output=True, text=True, check=False)
    return out.stdout.strip()


def check_run_dir_available(run_dir: Path, resume: bool) -> None:
    if run_dir.exists() and any(run_dir.iterdir()) and not resume:
        raise FileExistsError(f"Refusing to reuse non-empty run directory {run_dir} without --resume")


def make_run_id() -> str:
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    short_commit = run_git(str(FULL_DIR.parents[1]), ["rev-parse", "--short=12", "HEAD"]) or "unknown"
    return f"{ts}_{short_commit}"


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


def completed_decision_keys(jsonl_path: Path):
    """Return set of (decision_id, horizon) already fully recorded (all of
    lru, mru, and 10 random seeds present) -- used only for --resume."""
    if not jsonl_path.exists():
        return set()
    seen = {}
    with open(jsonl_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = (row["decision_id"], row["horizon"])
            seen.setdefault(key, set()).add((row["reference_policy"], row.get("continuation_rng_seed")))
    expected = {("lru", None), ("mru", None)} | {("random", s) for s in RANDOM_SEEDS}
    return {k for k, v in seen.items() if v >= expected}


def process_decision(d, requests, candidates, pid, horizon, jsonl_fh, log):
    family, capacity, t = d["family"], d["capacity"], d["request_t"]
    # candidates/pid are reconstructed ONCE per decision by the caller and
    # reused across all 3 horizons -- they do not depend on horizon (the
    # resident set at the decision point is fixed before any horizon-length
    # rollout begins), so recomputing per-horizon would triple an O(t) full
    # LRU replay for no benefit.
    if d["candidate_count"] != len(candidates):
        raise AssertionError(f"{d['decision_id']}: candidate_count mismatch at reconstruction")

    lru_losses = compute_candidate_losses(candidates, pid, requests, t, capacity, horizon, "lru")
    mru_losses = compute_candidate_losses(candidates, pid, requests, t, capacity, horizon, "mru")
    random_losses_by_seed = {
        seed: compute_candidate_losses(candidates, pid, requests, t, capacity, horizon, "random", rng_seed=seed)
        for seed in RANDOM_SEEDS
    }

    def write_rows(policy, losses, seed=None):
        regrets = losses_to_regrets(losses)
        for c in candidates:
            jsonl_fh.write(json.dumps({
                "decision_id": d["decision_id"], "family": family, "capacity": capacity, "horizon": horizon,
                "sample": d["sample"], "reference_policy": policy, "continuation_rng_seed": seed,
                "candidate_page_id": c, "rollout_loss_h": losses[c], "rollout_regret_h": regrets[c],
                "candidate_is_rollout_optimal": regrets[c] == 0.0, "candidate_count": len(candidates),
                "status": "complete",
            }, sort_keys=True) + "\n")

    write_rows("lru", lru_losses)
    write_rows("mru", mru_losses)
    for seed, losses in random_losses_by_seed.items():
        write_rows("random", losses, seed=seed)
    jsonl_fh.flush()
    os.fsync(jsonl_fh.fileno())

    lru_regrets = losses_to_regrets(lru_losses)
    mru_regrets = losses_to_regrets(mru_losses)
    random_mean_losses = {c: sum(random_losses_by_seed[s][c] for s in RANDOM_SEEDS) / len(RANDOM_SEEDS) for c in candidates}
    random_mean_regrets = losses_to_regrets(random_mean_losses)

    decision_metric_rows = []
    for alt_policy, alt_regrets, alt_losses in [("mru", mru_regrets, mru_losses), ("random_mean", random_mean_regrets, random_mean_losses)]:
        jaccard = optimal_set_jaccard(lru_regrets, alt_regrets)
        taxonomy = pairwise_taxonomy(lru_regrets, alt_regrets)
        tau = kendall_tau_b(lru_regrets, alt_regrets)
        ccr = cross_continuation_regret(lru_regrets, alt_losses)
        decision_metric_rows.append({
            "decision_id": d["decision_id"], "family": family, "capacity": capacity, "horizon": horizon,
            "sample": d["sample"], "alt_policy": alt_policy,
            "baseline_lru_all_tied": d["baseline_lru_all_tied"],
            "alt_all_tied": all(v == 0.0 for v in alt_regrets.values()),
            "optimal_set_jaccard": jaccard, "kendall_tau_b": tau,
            **{f"pairwise_{k}": v for k, v in taxonomy.items()},
            **{f"ccr_{k}": v for k, v in ccr.items()},
        })
    return decision_metric_rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--run-id", default=None)
    args = ap.parse_args()

    primary = json.loads((FULL_DIR / "PRIMARY_MANIFEST.json").read_text())
    diagnostic = json.loads((FULL_DIR / "DIAGNOSTIC_MANIFEST.json").read_text())
    all_decisions = primary["decisions"] + diagnostic["decisions"]

    run_id = args.run_id or make_run_id()
    run_dir = OUTPUTS_ROOT / run_id
    check_run_dir_available(run_dir, args.resume)
    run_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = run_dir / "candidate_results.jsonl"
    already_done = completed_decision_keys(jsonl_path) if args.resume else set()

    log_lines = []

    def log(msg):
        line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}"
        print(line, flush=True)
        log_lines.append(line)

    start_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    log(f"Full experiment started: run_id={run_id} resume={args.resume} already_done={len(already_done)} decision-horizon pairs")

    trace_cache = {}
    all_decision_metrics = []
    n_processed = 0

    mode = "a" if args.resume else "w"
    with open(jsonl_path, mode, encoding="utf-8") as jsonl_fh:
        for idx, d in enumerate(all_decisions):
            family = d["family"]
            if family not in trace_cache:
                requests, _pages, _ids = load_trace(family)
                trace_path = PROCESSED_TRACE_DIR / family / "trace.jsonl"
                actual_hash = sha256_file(trace_path)
                assert actual_hash == EXPECTED_TRACE_SHA256[family], f"{family}: trace hash mismatch"
                trace_cache[family] = requests
            requests = trace_cache[family]

            horizons_needed = [h for h in HORIZONS if (d["decision_id"], h) not in already_done]
            if not horizons_needed:
                continue
            candidates, pid = reconstruct_candidates_at_t(requests, d["capacity"], d["request_t"])

            for horizon in horizons_needed:
                rows = process_decision(d, requests, candidates, pid, horizon, jsonl_fh, log)
                all_decision_metrics.extend(rows)
                n_processed += 1

            if (idx + 1) % 500 == 0:
                log(f"...{idx+1}/{len(all_decisions)} decisions fully processed (all horizons)")

    end_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    decision_metrics_path = run_dir / "decision_metrics.csv"
    if all_decision_metrics:
        with open(decision_metrics_path, "w", newline="", encoding="utf-8") as fh:
            fieldnames = list(all_decision_metrics[0].keys())
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for row in all_decision_metrics:
                writer.writerow(row)

    jsonl_size = jsonl_path.stat().st_size
    jsonl_sha256 = sha256_file(jsonl_path)

    lafc_repo = str(FULL_DIR.parents[1])
    secondary_repo = "/home/soroush/projects/augmented-caching/repo/.claude/worktrees/continuation-sensitivity-pilot-20260914"
    provenance = {
        "run_id": run_id,
        "start_time_utc": start_time, "end_time_utc": end_time,
        "resume": args.resume,
        "primary_manifest_sha256": primary["manifest_sha256_of_content_above"],
        "diagnostic_manifest_sha256": diagnostic["manifest_sha256_of_content_above"],
        "n_primary_decisions": primary["total_decisions"], "n_diagnostic_decisions": diagnostic["total_decisions"],
        "horizons": list(HORIZONS), "random_seeds": list(RANDOM_SEEDS),
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
        "raw_output": {"path": str(jsonl_path), "bytes": jsonl_size, "sha256": jsonl_sha256},
    }
    (run_dir / "provenance.json").write_text(json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8")

    n_decision_horizon_pairs_expected = len(all_decisions) * len(HORIZONS)
    n_lines = sum(1 for _ in open(jsonl_path, "r", encoding="utf-8"))
    summary = {
        "run_id": run_id,
        "n_decisions": len(all_decisions),
        "n_decision_horizon_pairs_expected": n_decision_horizon_pairs_expected,
        "n_decision_horizon_pairs_processed_this_invocation": n_processed,
        "n_raw_jsonl_lines": n_lines,
        "n_failed": 0,
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    manifest_out = {"run_id": run_id, "output_files": {}}
    for name in ("decision_metrics.csv", "provenance.json", "summary.json"):
        p = run_dir / name
        if p.exists():
            manifest_out["output_files"][name] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
    manifest_out["output_files"]["candidate_results.jsonl"] = {"sha256": jsonl_sha256, "bytes": jsonl_size, "note": "raw output, NOT committed to git"}
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest_out, indent=2, sort_keys=True), encoding="utf-8")

    (run_dir / "full_run.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    log(f"Full experiment finished: run_id={run_id}, {n_lines} raw candidate rows, {len(all_decision_metrics)} decision-metric rows this invocation")
    print(f"\nRUN_ID={run_id}")


if __name__ == "__main__":
    main()
