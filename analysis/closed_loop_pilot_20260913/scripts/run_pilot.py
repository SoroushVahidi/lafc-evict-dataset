"""LAFC-Evict closed-loop cache-policy pilot (2026-09-13).

Read-only against the Augmented-caching simulator/policy code and its
processed request traces. Does NOT modify Augmented-caching in any way
(no new files written there, no git operations there). Does NOT touch
the lafc-evict-dataset release/generated data.

Scoring protocol (see REPORT.md Phase 2 for full derivation):

The release's train/val/test split is defined per (trace, capacity) as a
set of ~4096-request chunks (decision_chunk_id), each independently
labeled train/val/test -- NOT a single contiguous suffix. This script
replays each full 50,000-request trace continuously (so every policy's
cache state evolves naturally across the whole trace, exactly as in a
real deployment) and then reports metrics restricted to the requests
whose index falls in the release's held-out chunk windows for that
(trace, capacity=32) pair. metacdn has NO test-split chunks at
capacity=32 (confirmed directly against the release); its "held-out"
proxy here is therefore the VAL chunks, reported and labeled as such,
never as "test".
"""

from __future__ import annotations

import csv
import json
import random
import sys
import time
from pathlib import Path

AUGMENTED_CACHING_SRC = "/home/soroush/projects/augmented-caching/repo/src"
AUGMENTED_CACHING_MODELS = "/home/soroush/projects/augmented-caching/repo/models"
PROCESSED_TRACE_DIR = "/home/soroush/projects/augmented-caching/repo/data/processed"

sys.path.insert(0, AUGMENTED_CACHING_SRC)

from lafc.policies.base import BasePolicy  # noqa: E402
from lafc.policies.evict_value_v1 import EvictValueV1Policy  # noqa: E402
from lafc.policies.lru import LRUPolicy  # noqa: E402
from lafc.policies.sieve import SievePolicy  # noqa: E402
from lafc.runner.run_policy import run_policy  # noqa: E402
from lafc.simulator.request_trace import build_requests_from_lists  # noqa: E402
from lafc.types import CacheEvent, Page, PageId, Request  # noqa: E402

import collections  # noqa: E402
from typing import Dict, Optional  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent.parent / "outputs"

CAPACITY = 32

# Held-out chunk windows, derived directly from the canonical release's
# (trace_name, capacity=32, horizon={4,16}) decision_chunk_id -> split
# mapping (verified identical across horizons; see REPORT.md Phase 2).
# Windows are [lo, hi] inclusive request indices, chunk_id * 4096-aligned.
FAMILY_CONFIG = {
    "metacdn": {
        "trace_file": f"{PROCESSED_TRACE_DIR}/metacdn/trace.jsonl",
        "scored_split_label": "val",  # metacdn has NO test-split chunks at capacity=32
        "scored_windows": [(0, 4095), (24576, 32767), (36864, 45055)],
        "scored_chunk_ids": [0, 6, 7, 9, 10],
    },
    "twemcache": {
        "trace_file": f"{PROCESSED_TRACE_DIR}/twemcache/trace.jsonl",
        "scored_split_label": "test",
        "scored_windows": [(32768, 36863), (40960, 45055)],
        "scored_chunk_ids": [8, 10],
    },
}

RANDOM_SEEDS = list(range(20))

EVICT_VALUE_MODEL_PATH = f"{AUGMENTED_CACHING_MODELS}/evict_value_wulver_v1_best_heavy_r1.pkl"

# Leakage gate result (see REPORT.md Phase 3): the "best_heavy_r1" model's
# (horizon, model) combination was selected by minimizing an aggregate
# validation mean_regret_vs_oracle. metacdn has zero test-split rows in
# the entire heavy_r1 dataset (any capacity), so its only "held-out" proxy
# (val) was itself used for model selection -- not clean. twemcache's
# test chunks (8, 10) were never used in model selection or training.
EVICT_VALUE_V1_ALLOWED_FAMILIES = {"twemcache"}
EVICT_VALUE_V1_BLOCK_REASON = {
    "metacdn": (
        "BLOCKED_LEAKAGE_RISK: metacdn has zero test-split rows anywhere in the "
        "evict_value_v1_wulver_heavy_r1 dataset (any capacity); its only "
        "held-out proxy (val) was used by evict_value_wulver_v1_best_config_heavy_r1.json's "
        "own selection_rule ('minimize validation mean_regret_vs_oracle') to pick this "
        "very checkpoint, so scoring evict_value_v1 on metacdn's val chunks would be circular."
    )
}


class MRUPolicy(BasePolicy):
    """Most-Recently-Used eviction: evict the page used most recently.

    Defined locally in this pilot script (NOT added to Augmented-caching)
    since MRU does not exist anywhere in that repo's history. Mirrors
    LRUPolicy's OrderedDict bookkeeping exactly, but evicts from the
    most-recent end instead of the least-recent end.
    """

    name: str = "mru"

    def reset(self, capacity: int, pages: Dict[PageId, Page]) -> None:
        super().reset(capacity, pages)
        self._order: "collections.OrderedDict[PageId, None]" = collections.OrderedDict()

    def on_request(self, request: Request) -> CacheEvent:
        pid = request.page_id
        evicted: Optional[PageId] = None

        if self.in_cache(pid):
            self._order.move_to_end(pid)
            self._record_hit()
            return CacheEvent(t=request.t, page_id=pid, hit=True, cost=0.0)

        cost = self._pages[pid].weight
        self._record_miss(cost)

        if self._cache.is_full():
            evicted, _ = self._order.popitem(last=True)  # evict MOST-recently-used
            self._evict(evicted)

        self._add(pid)
        self._order[pid] = None
        return CacheEvent(t=request.t, page_id=pid, hit=False, cost=cost, evicted=evicted)


class UniformRandomPolicy(BasePolicy):
    """Evict a uniformly-random resident page on a full-cache miss.

    Defined locally in this pilot script (NOT added to Augmented-caching).
    Deterministic given a seed (a fresh random.Random instance per reset()).
    """

    name: str = "random"

    def __init__(self, seed: int) -> None:
        self.seed = seed

    def reset(self, capacity: int, pages: Dict[PageId, Page]) -> None:
        super().reset(capacity, pages)
        self._resident: list[PageId] = []
        self._resident_set: set[PageId] = set()
        self._rng = random.Random(self.seed)

    def on_request(self, request: Request) -> CacheEvent:
        pid = request.page_id
        evicted: Optional[PageId] = None

        if self.in_cache(pid):
            self._record_hit()
            return CacheEvent(t=request.t, page_id=pid, hit=True, cost=0.0)

        cost = self._pages[pid].weight
        self._record_miss(cost)

        if self._cache.is_full():
            idx = self._rng.randrange(len(self._resident))
            evicted = self._resident.pop(idx)
            self._resident_set.discard(evicted)
            self._evict(evicted)

        self._add(pid)
        self._resident.append(pid)
        self._resident_set.add(pid)

        return CacheEvent(t=request.t, page_id=pid, hit=False, cost=cost, evicted=evicted)


def load_processed_trace(path: str):
    page_ids: list[str] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            page_ids.append(str(rec["item_id"]))
    return build_requests_from_lists(page_ids)


def in_scored_windows(t: int, windows: list[tuple[int, int]]) -> bool:
    for lo, hi in windows:
        if lo <= t <= hi:
            return True
    return False


def score_events(events, windows: list[tuple[int, int]]) -> dict:
    scored = [e for e in events if in_scored_windows(e.t, windows)]
    n = len(scored)
    hits = sum(1 for e in scored if e.hit)
    misses = n - hits
    evictions = sum(1 for e in scored if (not e.hit) and e.evicted is not None)
    return {
        "scored_requests": n,
        "hits": hits,
        "misses": misses,
        "miss_ratio": (misses / n) if n else float("nan"),
        "evictions": evictions,
    }


def run_one(policy, requests, pages, capacity, windows) -> tuple[dict, float]:
    t0 = time.perf_counter()
    result = run_policy(policy, requests, pages, capacity)
    elapsed = time.perf_counter() - t0
    metrics = score_events(result.events, windows)
    metrics["full_trace_requests"] = len(result.events)
    metrics["full_trace_hits"] = result.total_hits
    metrics["full_trace_misses"] = result.total_misses
    metrics["runtime_sec"] = elapsed
    return metrics, elapsed


def _without_runtime(metrics: dict) -> dict:
    return {k: v for k, v in metrics.items() if k != "runtime_sec"}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_rows = []
    summary_rows = []
    sanity = {"determinism_checks": [], "notes": []}

    for family, cfg in FAMILY_CONFIG.items():
        requests, pages = load_processed_trace(cfg["trace_file"])
        assert len(requests) == 50000, f"{family}: expected 50000 requests, got {len(requests)}"
        windows = cfg["scored_windows"]

        family_results = {}

        # --- LRU (determinism check: run twice, assert identical) ---
        lru_metrics_1, _ = run_one(LRUPolicy(), requests, pages, CAPACITY, windows)
        lru_metrics_2, _ = run_one(LRUPolicy(), requests, pages, CAPACITY, windows)
        assert _without_runtime(lru_metrics_1) == _without_runtime(lru_metrics_2), "LRU is not deterministic!"
        sanity["determinism_checks"].append({"family": family, "policy": "lru", "reproducible": True})
        family_results["lru"] = lru_metrics_1
        raw_rows.append({"family": family, "policy": "lru", "seed": None, **lru_metrics_1})

        # --- MRU ---
        mru_metrics, _ = run_one(MRUPolicy(), requests, pages, CAPACITY, windows)
        family_results["mru"] = mru_metrics
        raw_rows.append({"family": family, "policy": "mru", "seed": None, **mru_metrics})

        # --- SIEVE ---
        sieve_metrics, _ = run_one(SievePolicy(), requests, pages, CAPACITY, windows)
        family_results["sieve"] = sieve_metrics
        raw_rows.append({"family": family, "policy": "sieve", "seed": None, **sieve_metrics})

        # --- uniform random, 20 seeds (determinism check on seed=0) ---
        random_metrics_list = []
        seed0_run_a, _ = run_one(UniformRandomPolicy(seed=0), requests, pages, CAPACITY, windows)
        seed0_run_b, _ = run_one(UniformRandomPolicy(seed=0), requests, pages, CAPACITY, windows)
        assert _without_runtime(seed0_run_a) == _without_runtime(seed0_run_b), "random seed=0 is not reproducible!"
        sanity["determinism_checks"].append({"family": family, "policy": "random(seed=0)", "reproducible": True})
        for seed in RANDOM_SEEDS:
            m, _ = run_one(UniformRandomPolicy(seed=seed), requests, pages, CAPACITY, windows)
            random_metrics_list.append(m)
            raw_rows.append({"family": family, "policy": "random", "seed": seed, **m})

        miss_ratios = [m["miss_ratio"] for m in random_metrics_list]
        mean_mr = sum(miss_ratios) / len(miss_ratios)
        var_mr = sum((x - mean_mr) ** 2 for x in miss_ratios) / (len(miss_ratios) - 1)
        std_mr = var_mr ** 0.5
        random_agg = {
            "scored_requests": random_metrics_list[0]["scored_requests"],
            "hits": sum(m["hits"] for m in random_metrics_list) / len(random_metrics_list),
            "misses": sum(m["misses"] for m in random_metrics_list) / len(random_metrics_list),
            "miss_ratio": mean_mr,
            "miss_ratio_std": std_mr,
            "miss_ratio_min": min(miss_ratios),
            "miss_ratio_max": max(miss_ratios),
            "miss_ratio_ci95_lo": mean_mr - 1.96 * std_mr / (len(miss_ratios) ** 0.5),
            "miss_ratio_ci95_hi": mean_mr + 1.96 * std_mr / (len(miss_ratios) ** 0.5),
            "evictions": sum(m["evictions"] for m in random_metrics_list) / len(random_metrics_list),
            "n_seeds": len(miss_ratios),
        }
        family_results["random"] = random_agg

        # --- evict_value_v1 (leakage-gated) ---
        if family in EVICT_VALUE_V1_ALLOWED_FAMILIES:
            policy = EvictValueV1Policy(model_path=EVICT_VALUE_MODEL_PATH, scorer_mode="artifact")
            ev_metrics, _ = run_one(policy, requests, pages, CAPACITY, windows)
            ev_metrics["status"] = "evaluated"
            family_results["evict_value_v1"] = ev_metrics
            raw_rows.append({"family": family, "policy": "evict_value_v1", "seed": None, **ev_metrics})
        else:
            family_results["evict_value_v1"] = {
                "status": "BLOCKED_LEAKAGE_RISK",
                "reason": EVICT_VALUE_V1_BLOCK_REASON.get(family, "blocked"),
            }
            raw_rows.append(
                {
                    "family": family,
                    "policy": "evict_value_v1",
                    "seed": None,
                    "status": "BLOCKED_LEAKAGE_RISK",
                }
            )

        # --- relative-to-LRU summary rows ---
        lru_miss_ratio = family_results["lru"]["miss_ratio"]
        lru_misses = family_results["lru"]["misses"]
        for pname, m in family_results.items():
            if m.get("status") == "BLOCKED_LEAKAGE_RISK":
                summary_rows.append(
                    {
                        "family": family,
                        "policy": pname,
                        "scored_split_label": cfg["scored_split_label"],
                        "status": "BLOCKED_LEAKAGE_RISK",
                    }
                )
                continue
            summary_rows.append(
                {
                    "family": family,
                    "policy": pname,
                    "scored_split_label": cfg["scored_split_label"],
                    "scored_requests": m["scored_requests"],
                    "hits": m["hits"],
                    "misses": m["misses"],
                    "miss_ratio": m["miss_ratio"],
                    "evictions": m["evictions"],
                    "relative_miss_diff_vs_lru": (m["misses"] - lru_misses) / lru_misses if lru_misses else float("nan"),
                    "absolute_miss_diff_vs_lru": m["misses"] - lru_misses,
                    "miss_ratio_std": m.get("miss_ratio_std"),
                    "n_seeds": m.get("n_seeds"),
                    "status": "evaluated",
                }
            )

    # --- write outputs ---
    with open(OUT_DIR / "run_results.csv", "w", newline="") as fh:
        fieldnames = sorted({k for row in raw_rows for k in row.keys()})
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in raw_rows:
            writer.writerow(row)

    with open(OUT_DIR / "summary.csv", "w", newline="") as fh:
        fieldnames = sorted({k for row in summary_rows for k in row.keys()})
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in summary_rows:
            writer.writerow(row)

    with open(OUT_DIR / "sanity_checks.json", "w") as fh:
        json.dump(sanity, fh, indent=2)

    print(json.dumps(summary_rows, indent=2))


if __name__ == "__main__":
    main()
