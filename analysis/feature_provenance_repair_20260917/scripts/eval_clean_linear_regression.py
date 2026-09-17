from __future__ import annotations
import json, sys, time
import numpy as np
import duckdb

SOURCE = "release/lafc-evict-v0.1-open-current-contract-preserved/data/candidate_rows/**/*.parquet"
fit = json.load(open("analysis/feature_provenance_repair_20260917/artifacts/clean_linear_regression_fit.json"))
CLEAN_FEATURES = fit["features"][1:]
coef = fit["coefficients"]
intercept = coef[0]
weights = coef[1:]

expr = " + ".join(f"({w}) * {f}" for w, f in zip(weights, CLEAN_FEATURES))
score_expr = f"({intercept}) + {expr}"

con = duckdb.connect()
con.execute("SET threads TO 16")
t0 = time.time()

results = {}
for split in ["train", "val", "test"]:
    q = f"""
    SELECT
      COUNT(*) AS n,
      AVG(ABS(y_loss - ({score_expr}))) AS mae,
      SQRT(AVG(POWER(y_loss - ({score_expr}), 2))) AS rmse,
      1.0 - SUM(POWER(y_loss - ({score_expr}), 2)) / SUM(POWER(y_loss - (SELECT AVG(y_loss) FROM read_parquet('{SOURCE}', hive_partitioning=1) WHERE split='{split}'), 2)) AS r2
    FROM read_parquet('{SOURCE}', hive_partitioning=1)
    WHERE split = '{split}'
    """
    row = con.execute(q).fetchone()
    cols = [d[0] for d in con.description]
    results[split] = dict(zip(cols, row))
    print(f"{split}: {results[split]} (t={time.time()-t0:.1f}s)", file=sys.stderr)

out = {"features": CLEAN_FEATURES, "coefficients": coef, "eval": results}
with open("analysis/feature_provenance_repair_20260917/artifacts/clean_linear_regression_eval.json", "w") as f:
    json.dump(out, f, indent=2, default=str)
print(json.dumps(out, indent=2, default=str))
