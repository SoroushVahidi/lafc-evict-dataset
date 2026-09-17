from __future__ import annotations
import sys, time
import duckdb

CANDIDATE_SOURCE = "release/lafc-evict-v0.1-open-current-contract-preserved/data/candidate_rows/**/*.parquet"
PAIRWISE_SOURCE = "analysis/pairwise_provenance_repair_20260913/artifacts/pairwise_sample_regenerated_canonical.parquet"
CLEAN_FEATURES = [
    "candidate_recency_rank", "candidate_age_norm", "candidate_lru_score",
    "candidate_is_lru_victim", "score_gap_to_lru_victim",
    "recent_candidate_request_rate", "recent_candidate_hit_rate",
]

con = duckdb.connect()
con.execute("SET threads TO 16")
t0 = time.time()

feat_a = ", ".join(f"a.{f} AS a_{f}" for f in CLEAN_FEATURES)
feat_b = ", ".join(f"b.{f} AS b_{f}" for f in CLEAN_FEATURES)

q = f"""
COPY (
  SELECT
    p.decision_id, p.capacity, p.horizon, p.split, p.trace_family,
    p.label_a_better, p.label_b_better, p.is_tie,
    {feat_a}, {feat_b}
  FROM read_parquet('{PAIRWISE_SOURCE}') p
  JOIN read_parquet('{CANDIDATE_SOURCE}', hive_partitioning=1) a
    ON a.trace_name = p.trace_name AND a.capacity = p.capacity AND a.horizon = p.horizon
   AND a.decision_id = p.decision_id AND a.candidate_page_id = p.candidate_a_page_id
  JOIN read_parquet('{CANDIDATE_SOURCE}', hive_partitioning=1) b
    ON b.trace_name = p.trace_name AND b.capacity = p.capacity AND b.horizon = p.horizon
   AND b.decision_id = p.decision_id AND b.candidate_page_id = p.candidate_b_page_id
) TO 'analysis/feature_provenance_repair_20260917/artifacts/clean_pairwise_features.parquet' (FORMAT PARQUET)
"""
con.execute(q)
n = con.execute(f"SELECT COUNT(*) FROM read_parquet('analysis/feature_provenance_repair_20260917/artifacts/clean_pairwise_features.parquet')").fetchone()[0]
print(f"wrote {n} rows, t={time.time()-t0:.1f}s")
