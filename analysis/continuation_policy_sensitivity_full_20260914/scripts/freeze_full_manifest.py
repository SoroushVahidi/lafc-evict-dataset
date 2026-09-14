"""Freeze the full-experiment decision manifest (5,000 primary + 500
diagnostic decisions) BEFORE any MRU/random continuation result is computed
or inspected. Selection uses ONLY baseline-LRU information at H=16 (the
design's primary stratification horizon), per DESIGN.md's explicit
constraint. Committed and pushed BEFORE the actual continuation run.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from full_lib import (
    CAPACITIES,
    DECISIONS_PER_PRIMARY_STRATUM,
    DIAGNOSTIC_DECISIONS_PER_FAMILY,
    FAMILIES,
    FULL_SAMPLING_SEED,
    PRIMARY_STRATIFICATION_HORIZON,
    SELECTION_SUBSAMPLE_SIZE,
    SPLIT_LABEL,
    enumerate_decision_positions,
    load_trace,
    sha256_text,
    summarize_decision_at,
)

FULL_DIR = Path(__file__).resolve().parents[1]
PRIMARY_MANIFEST_PATH = FULL_DIR / "PRIMARY_MANIFEST.json"
DIAGNOSTIC_MANIFEST_PATH = FULL_DIR / "DIAGNOSTIC_MANIFEST.json"


def subsample_pool(family: str, capacity: int, seed_key: str):
    positions, requests = enumerate_decision_positions(family, capacity)
    rng = random.Random(seed_key)
    pool_positions = positions if len(positions) <= SELECTION_SUBSAMPLE_SIZE else rng.sample(positions, SELECTION_SUBSAMPLE_SIZE)
    pool_positions.sort()
    summaries = [summarize_decision_at(requests, capacity, t, PRIMARY_STRATIFICATION_HORIZON, family) for t in pool_positions]
    return summaries, len(positions)


def select_primary_for_stratum(family: str, capacity: int):
    seed_key = f"{FULL_SAMPLING_SEED}|primary|{family}|{capacity}"
    summaries, population_size = subsample_pool(family, capacity, seed_key)
    all_tied = [s for s in summaries if s["all_tied"]]
    discriminative = [s for s in summaries if not s["all_tied"]]

    total_pool = len(all_tied) + len(discriminative)
    n_tied_target = round(DECISIONS_PER_PRIMARY_STRATUM * (len(all_tied) / total_pool)) if total_pool else 0
    n_tied_target = min(n_tied_target, len(all_tied), DECISIONS_PER_PRIMARY_STRATUM)
    n_disc_target = min(DECISIONS_PER_PRIMARY_STRATUM - n_tied_target, len(discriminative))
    if n_tied_target + n_disc_target < DECISIONS_PER_PRIMARY_STRATUM:
        shortfall = DECISIONS_PER_PRIMARY_STRATUM - (n_tied_target + n_disc_target)
        n_tied_target = min(n_tied_target + shortfall, len(all_tied))
        if n_tied_target + n_disc_target < DECISIONS_PER_PRIMARY_STRATUM:
            n_disc_target = min(n_disc_target + (DECISIONS_PER_PRIMARY_STRATUM - n_tied_target - n_disc_target), len(discriminative))

    rng = random.Random(f"{seed_key}|select")
    chosen = rng.sample(all_tied, n_tied_target) + rng.sample(discriminative, n_disc_target)
    assert len(chosen) == DECISIONS_PER_PRIMARY_STRATUM, (
        f"{family}/{capacity}: expected {DECISIONS_PER_PRIMARY_STRATUM}, got {len(chosen)} "
        f"(pool: tied={len(all_tied)} disc={len(discriminative)} population~{population_size})"
    )

    return [
        {
            "decision_id": s["decision_id"], "family": family, "capacity": capacity,
            "horizon_for_stratification": PRIMARY_STRATIFICATION_HORIZON,
            "request_t": s["request_t"], "candidate_count": s["candidate_count"],
            "baseline_lru_all_tied": bool(s["all_tied"]), "baseline_lru_regret_max": float(s["regret_max"]),
            "scored_split_label": SPLIT_LABEL[family], "sample": "primary",
            "population_size_estimate": population_size,
        }
        for s in chosen
    ]


def select_diagnostic_for_family(family: str):
    """Pool both capacities' subsample summaries for this family and take
    the highest-regret decile, then sample DIAGNOSTIC_DECISIONS_PER_FAMILY
    from it -- the frozen highest-regret/informative criterion."""
    pooled = []
    for capacity in CAPACITIES:
        seed_key = f"{FULL_SAMPLING_SEED}|diagnostic|{family}|{capacity}"
        summaries, _pop = subsample_pool(family, capacity, seed_key)
        for s in summaries:
            pooled.append({**s, "capacity": capacity})

    pooled.sort(key=lambda s: s["regret_max"], reverse=True)
    decile_cutoff = max(1, len(pooled) // 10)
    top_decile = pooled[:decile_cutoff]

    rng = random.Random(f"{FULL_SAMPLING_SEED}|diagnostic|{family}|select")
    n = min(DIAGNOSTIC_DECISIONS_PER_FAMILY, len(top_decile))
    chosen = rng.sample(top_decile, n)
    if n < DIAGNOSTIC_DECISIONS_PER_FAMILY:
        print(f"WARNING: {family}: only {n} decisions available in the top decile "
              f"(requested {DIAGNOSTIC_DECISIONS_PER_FAMILY})")

    return [
        {
            "decision_id": s["decision_id"], "family": family, "capacity": s["capacity"],
            "horizon_for_stratification": PRIMARY_STRATIFICATION_HORIZON,
            "request_t": s["request_t"], "candidate_count": s["candidate_count"],
            "baseline_lru_all_tied": bool(s["all_tied"]), "baseline_lru_regret_max": float(s["regret_max"]),
            "scored_split_label": SPLIT_LABEL[family], "sample": "diagnostic",
        }
        for s in chosen
    ]


def main():
    primary_decisions = []
    for family in FAMILIES:
        for capacity in CAPACITIES:
            cell = select_primary_for_stratum(family, capacity)
            primary_decisions.extend(cell)
            n_tied = sum(1 for d in cell if d["baseline_lru_all_tied"])
            print(f"[primary] {family}/{capacity}: {len(cell)} decisions ({n_tied} tied, {len(cell)-n_tied} discriminative)")

    diagnostic_decisions = []
    for family in FAMILIES:
        fam_diag = select_diagnostic_for_family(family)
        diagnostic_decisions.extend(fam_diag)
        print(f"[diagnostic] {family}: {len(fam_diag)} decisions")

    assert len(primary_decisions) == len(FAMILIES) * len(CAPACITIES) * DECISIONS_PER_PRIMARY_STRATUM

    primary_ids = {d["decision_id"] for d in primary_decisions}
    diagnostic_ids = {d["decision_id"] for d in diagnostic_decisions}
    overlap = primary_ids & diagnostic_ids
    print(f"\nPrimary/diagnostic decision_id overlap: {len(overlap)} decisions")

    primary_manifest = {
        "sample": "primary", "sampling_seed": FULL_SAMPLING_SEED,
        "families": list(FAMILIES), "capacities": list(CAPACITIES),
        "decisions_per_stratum": DECISIONS_PER_PRIMARY_STRATUM,
        "stratification_horizon": PRIMARY_STRATIFICATION_HORIZON,
        "selection_subsample_size_per_stratum": SELECTION_SUBSAMPLE_SIZE,
        "total_decisions": len(primary_decisions),
        "decisions": sorted(primary_decisions, key=lambda d: d["decision_id"]),
        "selection_uses_only_baseline_lru_information": True,
        "overlap_with_diagnostic_sample": sorted(overlap),
    }
    diagnostic_manifest = {
        "sample": "diagnostic", "sampling_seed": FULL_SAMPLING_SEED,
        "families": list(FAMILIES),
        "decisions_per_family": DIAGNOSTIC_DECISIONS_PER_FAMILY,
        "selection_criterion": "highest-regret-magnitude decile (pooled across both capacities' subsample pools), per family, per DESIGN.md/MATRIX.md",
        "stratification_horizon": PRIMARY_STRATIFICATION_HORIZON,
        "total_decisions": len(diagnostic_decisions),
        "decisions": sorted(diagnostic_decisions, key=lambda d: d["decision_id"]),
        "selection_uses_only_baseline_lru_information": True,
        "overlap_with_primary_sample": sorted(overlap),
    }

    for manifest, path in [(primary_manifest, PRIMARY_MANIFEST_PATH), (diagnostic_manifest, DIAGNOSTIC_MANIFEST_PATH)]:
        content = json.dumps(manifest, indent=2, sort_keys=True)
        h = sha256_text(content)
        manifest["manifest_sha256_of_content_above"] = h
        final = json.dumps(manifest, indent=2, sort_keys=True)
        path.write_text(final, encoding="utf-8")
        print(f"Froze {manifest['total_decisions']} decisions to {path} (hash {h})")


if __name__ == "__main__":
    main()
