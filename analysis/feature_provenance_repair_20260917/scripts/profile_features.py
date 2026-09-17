from __future__ import annotations
import json, sys, time
sys.path.insert(0, "src")
import duckdb
from lafc_evict_dataset.schema import FEATURE_COLUMNS

SOURCE = "release/lafc-evict-v0.1-open-current-contract-preserved/data/candidate_rows/**/*.parquet"

con = duckdb.connect()
con.execute(f"SET threads TO 16")
t0 = time.time()

total_rows = con.execute(f"SELECT COUNT(*) FROM read_parquet('{SOURCE}', hive_partitioning=1)").fetchone()[0]
print(f"total_rows={total_rows} (t={time.time()-t0:.1f}s)", file=sys.stderr)

agg_parts = []
for col in FEATURE_COLUMNS:
    agg_parts.append(f"COUNT(DISTINCT {col}) AS distinct_{col}")
    agg_parts.append(f"MIN({col}) AS min_{col}")
    agg_parts.append(f"MAX({col}) AS max_{col}")
    agg_parts.append(f"SUM(CASE WHEN {col} IS NULL THEN 1 ELSE 0 END) AS nulls_{col}")

q = f"SELECT {', '.join(agg_parts)} FROM read_parquet('{SOURCE}', hive_partitioning=1)"
row = con.execute(q).fetchone()
cols = [d[0] for d in con.description]
result = dict(zip(cols, row))
print(f"profiling done (t={time.time()-t0:.1f}s)", file=sys.stderr)

out = {"total_rows": total_rows, "profile": result}
with open("analysis/feature_provenance_repair_20260917/artifacts/feature_profile_raw.json", "w") as f:
    json.dump(out, f, indent=2, default=str)
print("wrote feature_profile_raw.json")
