"""Deterministically select and freeze the 80 pilot decision IDs BEFORE any
MRU/random continuation result is computed or inspected.

Selection uses ONLY baseline-LRU information (rollout_regret_h under
reference_policy='lru'), per DESIGN.md's explicit "do not condition
sampling on alternative-continuation results" constraint.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from pilot_lib import (
    DECISIONS_PER_CELL,
    PILOT_CELLS,
    PILOT_HORIZON,
    PILOT_SAMPLING_SEED,
    generate_lru_baseline_decision_summaries,
    sha256_text,
)

PILOT_DIR = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PILOT_DIR / "PILOT_MANIFEST.json"


SELECTION_SUBSAMPLE_SIZE = 500  # stage-1 pool size before stratified selection; see pilot_lib docstring


def select_decisions_for_cell(family: str, capacity: int, seed: int):
    summaries = generate_lru_baseline_decision_summaries(
        family, capacity, PILOT_HORIZON, subsample_size=SELECTION_SUBSAMPLE_SIZE, subsample_seed=seed,
    )
    by_id = {s["decision_id"]: s for s in summaries}

    all_tied_ids = []
    discriminative_ids = []
    for s in summaries:
        if s["all_tied"]:
            all_tied_ids.append(s["decision_id"])
        else:
            discriminative_ids.append(s["decision_id"])

    all_tied_ids.sort()
    discriminative_ids.sort()
    total = len(all_tied_ids) + len(discriminative_ids)

    n_tied_target = round(DECISIONS_PER_CELL * (len(all_tied_ids) / total)) if total else 0
    n_tied_target = min(n_tied_target, len(all_tied_ids), DECISIONS_PER_CELL)
    n_disc_target = min(DECISIONS_PER_CELL - n_tied_target, len(discriminative_ids))
    # If discriminative pool can't fill the remainder, backfill from tied pool.
    if n_tied_target + n_disc_target < DECISIONS_PER_CELL:
        shortfall = DECISIONS_PER_CELL - (n_tied_target + n_disc_target)
        n_tied_target = min(n_tied_target + shortfall, len(all_tied_ids))

    rng = random.Random(f"{seed}|{family}|{capacity}")
    chosen_tied = rng.sample(all_tied_ids, n_tied_target) if n_tied_target else []
    chosen_disc = rng.sample(discriminative_ids, n_disc_target) if n_disc_target else []
    chosen = sorted(chosen_tied + chosen_disc)

    assert len(chosen) == DECISIONS_PER_CELL, (
        f"{family}/{capacity}: expected {DECISIONS_PER_CELL} decisions, got {len(chosen)} "
        f"(pool sizes: all_tied={len(all_tied_ids)}, discriminative={len(discriminative_ids)})"
    )

    decisions_detail = []
    for decision_id in chosen:
        s = by_id[decision_id]
        decisions_detail.append({
            "decision_id": decision_id,
            "family": family,
            "capacity": capacity,
            "horizon": PILOT_HORIZON,
            "request_t": s["request_t"],
            "candidate_count": s["candidate_count"],
            "baseline_lru_all_tied": bool(s["all_tied"]),
            "baseline_lru_regret_max": float(s["regret_max"]),
        })
    return decisions_detail


def main():
    all_decisions = []
    for family, capacity in PILOT_CELLS:
        cell_decisions = select_decisions_for_cell(family, capacity, PILOT_SAMPLING_SEED)
        all_decisions.extend(cell_decisions)
        print(f"{family}/{capacity}: selected {len(cell_decisions)} decisions "
              f"({sum(1 for d in cell_decisions if d['baseline_lru_all_tied'])} all_tied, "
              f"{sum(1 for d in cell_decisions if not d['baseline_lru_all_tied'])} discriminative)")

    assert len(all_decisions) == len(PILOT_CELLS) * DECISIONS_PER_CELL

    manifest = {
        "pilot_sampling_seed": PILOT_SAMPLING_SEED,
        "pilot_cells": [{"family": f, "capacity": c} for f, c in PILOT_CELLS],
        "decisions_per_cell": DECISIONS_PER_CELL,
        "horizon": PILOT_HORIZON,
        "total_decisions": len(all_decisions),
        "decisions": all_decisions,
        "selection_uses_only_baseline_lru_information": True,
        "selection_pool_subsample_size_per_cell": SELECTION_SUBSAMPLE_SIZE,
        "selection_pool_note": (
            "Regret/tie summaries were computed only for a random subsample of up to "
            f"{SELECTION_SUBSAMPLE_SIZE} decision positions per cell (stage 1: all decision "
            "positions enumerated cheaply via plain LRU replay; stage 2: expensive rollout-regret "
            "computed only for this subsample), not the full population of eviction decisions in "
            "the 50,000-request trace -- a pragmatic approximation appropriate for an 80-decision "
            "correctness pilot. The full 5,000-decision study should use the full population or a "
            "separately justified, much larger subsample."
        ),
    }
    manifest_json = json.dumps(manifest, indent=2, sort_keys=True)
    manifest_hash = sha256_text(manifest_json)
    manifest["manifest_sha256_of_content_above"] = manifest_hash
    final_json = json.dumps(manifest, indent=2, sort_keys=True)

    MANIFEST_PATH.write_text(final_json, encoding="utf-8")
    print(f"\nFroze {len(all_decisions)} pilot decisions to {MANIFEST_PATH}")
    print(f"Manifest content hash (pre-hash-field): {manifest_hash}")


if __name__ == "__main__":
    main()
