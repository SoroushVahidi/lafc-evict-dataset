from __future__ import annotations
import json, sys, time
sys.path.insert(0, "src")
import duckdb

SOURCE = "release/lafc-evict-v0.1-open-current-contract-preserved/data/candidate_rows/**/*.parquet"
con = duckdb.connect()
con.execute("SET threads TO 16")
t0 = time.time()

checks = {}

# 1. Exact row-level alias check: predictor victim vs LRU victim
checks["predictor_victim_neq_lru_victim_count"] = con.execute(f"""
    SELECT COUNT(*) FROM read_parquet('{SOURCE}', hive_partitioning=1)
    WHERE candidate_is_predictor_victim != candidate_is_lru_victim
""").fetchone()[0]

# 2. score_gap_to_lru_victim vs candidate_lru_score: is it a deterministic within-decision transform?
#    Hypothesis: score_gap_to_lru_victim = candidate_lru_score - MAX(candidate_lru_score) OVER (decision)
checks["score_gap_matches_lru_minus_decision_max"] = con.execute(f"""
    WITH t AS (
        SELECT candidate_lru_score, score_gap_to_lru_victim,
               MAX(candidate_lru_score) OVER (PARTITION BY trace_name, capacity, horizon, decision_id) AS decision_max_lru
        FROM read_parquet('{SOURCE}', hive_partitioning=1)
    )
    SELECT COUNT(*) FROM t
    WHERE abs((candidate_lru_score - decision_max_lru) - score_gap_to_lru_victim) > 1e-9
""").fetchone()[0]

# 3. y_loss / y_value exact relationship check (should be y_value = -y_loss, already known, but confirm none of the 26 features equal y_loss/y_value exactly)
for feat in ["candidate_lru_score", "candidate_age_norm", "candidate_recency_rank",
             "recent_candidate_request_rate", "recent_candidate_hit_rate", "score_gap_to_lru_victim"]:
    checks[f"{feat}_equals_y_loss_count"] = con.execute(f"""
        SELECT COUNT(*) FROM read_parquet('{SOURCE}', hive_partitioning=1)
        WHERE {feat} = y_loss
    """).fetchone()[0]

print(f"done t={time.time()-t0:.1f}s")
with open("analysis/feature_provenance_repair_20260917/artifacts/alias_leakage_checks.json", "w") as f:
    json.dump(checks, f, indent=2)
print(json.dumps(checks, indent=2))
