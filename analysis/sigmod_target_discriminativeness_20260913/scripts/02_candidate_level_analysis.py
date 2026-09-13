#!/usr/bin/env python3
"""LAFC-Evict SIGMOD audit: candidate-level regret histogram + simple-victim
diagnostics (Phases 3 regret>=2, 7 pairwise info content, 8 LRU/MRU/predictor).

This is the one script in the audit that scans the full candidate_rows table
(277,995,072 rows across 168 manifest-listed parquet partitions, ~2.7GB on
disk for the preserved open release). It performs exactly one join of
candidate_rows against decision_view (broadcast as the small side) on the
canonical 9-column decision key, then computes every Phase 3/7/8 aggregate
that decision_view's stored fields cannot supply (per-candidate regret
histogram >=2, LRU/MRU/predictor-victim regret, candidate-weighted
percentiles). No sampling: population aggregates over all rows.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[3]
RELEASE_ROOT = REPO_ROOT / "release" / "lafc-evict-v0.1-open-current-contract-preserved"
DECISION_VIEW = RELEASE_ROOT / "data" / "decision_view" / "decision_view.parquet"
PAIRWISE_SAMPLE = RELEASE_ROOT / "data" / "pairwise_sample" / "pairwise_sample.parquet"
CANDIDATE_GLOB = str(RELEASE_ROOT / "data" / "candidate_rows" / "**" / "*.parquet")
OUT_DIR = Path(__file__).resolve().parent.parent / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DECISION_KEY = [
    "trace_name", "dataset_source", "capacity", "horizon",
    "decision_id", "decision_t", "decision_chunk_id", "split",
]

con = duckdb.connect()
con.execute(f"PRAGMA threads={min(8, __import__('os').cpu_count() or 4)}")
con.execute(f"CREATE TABLE decision_meta AS SELECT {', '.join(DECISION_KEY)}, candidate_count, min_y_loss, trace_family FROM '{DECISION_VIEW}'")
n_meta = con.execute("SELECT COUNT(*) FROM decision_meta").fetchone()[0]
print(f"decision_meta rows: {n_meta}")

join_cond = " AND ".join(f"cr.{c} = dm.{c}" for c in DECISION_KEY)

t0 = time.time()
print("Scanning candidate_rows (277,995,072 rows) with join to decision_meta ...")
result = con.execute(
    f"""
    WITH cr AS (
        SELECT * FROM read_parquet('{CANDIDATE_GLOB}', hive_partitioning=1)
    ),
    joined AS (
        SELECT
            cr.y_loss - dm.min_y_loss AS regret,
            cr.candidate_recency_rank,
            cr.candidate_is_lru_victim,
            cr.candidate_is_predictor_victim,
            dm.candidate_count,
            dm.trace_family,
            cr.capacity,
            cr.horizon
        FROM cr JOIN decision_meta dm ON {join_cond}
    )
    SELECT
        COUNT(*) AS n_candidates,
        SUM(CASE WHEN regret = 0 THEN 1 ELSE 0 END) AS n_regret_eq_0,
        SUM(CASE WHEN regret >= 1 THEN 1 ELSE 0 END) AS n_regret_ge_1,
        SUM(CASE WHEN regret >= 2 THEN 1 ELSE 0 END) AS n_regret_ge_2,
        SUM(CASE WHEN regret >= 3 THEN 1 ELSE 0 END) AS n_regret_ge_3,
        AVG(regret) AS mean_regret_candidate_weighted,
        APPROX_QUANTILE(regret, 0.90) AS p90_regret_candidate_weighted,
        APPROX_QUANTILE(regret, 0.95) AS p95_regret_candidate_weighted,
        APPROX_QUANTILE(regret, 0.99) AS p99_regret_candidate_weighted,
        -- LRU victim diagnostic
        SUM(CASE WHEN candidate_is_lru_victim = 1 THEN 1 ELSE 0 END) AS n_lru_selections,
        SUM(CASE WHEN candidate_is_lru_victim = 1 AND regret = 0 THEN 1 ELSE 0 END) AS n_lru_optimal,
        SUM(CASE WHEN candidate_is_lru_victim = 1 THEN regret ELSE 0 END) AS sum_lru_regret,
        APPROX_QUANTILE(regret, 0.90) FILTER (WHERE candidate_is_lru_victim = 1) AS p90_lru_regret,
        APPROX_QUANTILE(regret, 0.95) FILTER (WHERE candidate_is_lru_victim = 1) AS p95_lru_regret,
        MEDIAN(regret) FILTER (WHERE candidate_is_lru_victim = 1) AS median_lru_regret,
        -- MRU victim diagnostic (max recency_rank == candidate_count - 1)
        SUM(CASE WHEN candidate_recency_rank = candidate_count - 1 THEN 1 ELSE 0 END) AS n_mru_selections,
        SUM(CASE WHEN candidate_recency_rank = candidate_count - 1 AND regret = 0 THEN 1 ELSE 0 END) AS n_mru_optimal,
        SUM(CASE WHEN candidate_recency_rank = candidate_count - 1 THEN regret ELSE 0 END) AS sum_mru_regret,
        APPROX_QUANTILE(regret, 0.90) FILTER (WHERE candidate_recency_rank = candidate_count - 1) AS p90_mru_regret,
        APPROX_QUANTILE(regret, 0.95) FILTER (WHERE candidate_recency_rank = candidate_count - 1) AS p95_mru_regret,
        MEDIAN(regret) FILTER (WHERE candidate_recency_rank = candidate_count - 1) AS median_mru_regret,
        -- predictor victim diagnostic
        SUM(CASE WHEN candidate_is_predictor_victim = 1 THEN 1 ELSE 0 END) AS n_predictor_selections,
        SUM(CASE WHEN candidate_is_predictor_victim = 1 AND regret = 0 THEN 1 ELSE 0 END) AS n_predictor_optimal,
        SUM(CASE WHEN candidate_is_predictor_victim = 1 THEN regret ELSE 0 END) AS sum_predictor_regret,
        APPROX_QUANTILE(regret, 0.90) FILTER (WHERE candidate_is_predictor_victim = 1) AS p90_predictor_regret,
        APPROX_QUANTILE(regret, 0.95) FILTER (WHERE candidate_is_predictor_victim = 1) AS p95_predictor_regret,
        MEDIAN(regret) FILTER (WHERE candidate_is_predictor_victim = 1) AS median_predictor_regret
    FROM joined
    """
).fetchone()
elapsed = time.time() - t0
print(f"Full scan+join completed in {elapsed:.1f}s")

cols = [
    "n_candidates", "n_regret_eq_0", "n_regret_ge_1", "n_regret_ge_2", "n_regret_ge_3",
    "mean_regret_candidate_weighted", "p90_regret_candidate_weighted", "p95_regret_candidate_weighted",
    "p99_regret_candidate_weighted",
    "n_lru_selections", "n_lru_optimal", "sum_lru_regret", "p90_lru_regret", "p95_lru_regret", "median_lru_regret",
    "n_mru_selections", "n_mru_optimal", "sum_mru_regret", "p90_mru_regret", "p95_mru_regret", "median_mru_regret",
    "n_predictor_selections", "n_predictor_optimal", "sum_predictor_regret", "p90_predictor_regret", "p95_predictor_regret", "median_predictor_regret",
]
overall = dict(zip(cols, result))

report = {"elapsed_seconds": elapsed, "overall": overall}

report["overall"]["prob_regret_ge_1_candidate_weighted"] = overall["n_regret_ge_1"] / overall["n_candidates"]
report["overall"]["prob_regret_ge_2_candidate_weighted"] = overall["n_regret_ge_2"] / overall["n_candidates"]
report["overall"]["prob_regret_ge_3_candidate_weighted"] = overall["n_regret_ge_3"] / overall["n_candidates"]
report["overall"]["random_optimal_rate_candidate_weighted"] = overall["n_regret_eq_0"] / overall["n_candidates"]

for name in ["lru", "mru", "predictor"]:
    n = overall[f"n_{name}_selections"]
    n_opt = overall[f"n_{name}_optimal"]
    s = overall[f"sum_{name}_regret"]
    report["overall"][f"{name}_optimal_selection_rate"] = (n_opt / n) if n else None
    report["overall"][f"{name}_mean_regret"] = (s / n) if n else None

# By trace_family / capacity / horizon for LRU/MRU/predictor (most informative slices)
t1 = time.time()
strat = con.execute(
    f"""
    WITH cr AS (
        SELECT * FROM read_parquet('{CANDIDATE_GLOB}', hive_partitioning=1)
    ),
    joined AS (
        SELECT
            cr.y_loss - dm.min_y_loss AS regret,
            cr.candidate_recency_rank,
            cr.candidate_is_lru_victim,
            cr.candidate_is_predictor_victim,
            dm.candidate_count,
            dm.trace_family,
            cr.capacity,
            cr.horizon
        FROM cr JOIN decision_meta dm ON {join_cond}
    )
    SELECT
        trace_family, capacity, horizon,
        SUM(CASE WHEN candidate_is_lru_victim = 1 THEN 1 ELSE 0 END) AS n_lru,
        SUM(CASE WHEN candidate_is_lru_victim = 1 AND regret = 0 THEN 1 ELSE 0 END) AS n_lru_opt,
        SUM(CASE WHEN candidate_is_lru_victim = 1 THEN regret ELSE 0 END) AS sum_lru_regret,
        SUM(CASE WHEN candidate_recency_rank = candidate_count - 1 THEN 1 ELSE 0 END) AS n_mru,
        SUM(CASE WHEN candidate_recency_rank = candidate_count - 1 AND regret = 0 THEN 1 ELSE 0 END) AS n_mru_opt,
        SUM(CASE WHEN candidate_recency_rank = candidate_count - 1 THEN regret ELSE 0 END) AS sum_mru_regret
    FROM joined
    GROUP BY trace_family, capacity, horizon
    ORDER BY trace_family, capacity, horizon
    """
).df()
print(f"Stratified LRU/MRU query completed in {time.time()-t1:.1f}s")
strat["lru_optimal_rate"] = strat["n_lru_opt"] / strat["n_lru"]
strat["lru_mean_regret"] = strat["sum_lru_regret"] / strat["n_lru"]
strat["mru_optimal_rate"] = strat["n_mru_opt"] / strat["n_mru"]
strat["mru_mean_regret"] = strat["sum_mru_regret"] / strat["n_mru"]
strat.to_csv(OUT_DIR / "phase8_lru_mru_stratified.csv", index=False)

with open(OUT_DIR / "candidate_level_report.json", "w") as f:
    json.dump(report, f, indent=2, default=str)

print(json.dumps(report, indent=2, default=str))
