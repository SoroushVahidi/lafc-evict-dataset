from __future__ import annotations
import json, sys, time
import numpy as np
import duckdb

SOURCE = "release/lafc-evict-v0.1-open-current-contract-preserved/data/candidate_rows/**/*.parquet"
CLEAN_FEATURES = [
    "candidate_recency_rank", "candidate_age_norm", "candidate_lru_score",
    "candidate_is_lru_victim", "score_gap_to_lru_victim",
    "recent_candidate_request_rate", "recent_candidate_hit_rate",
]

def main():
    con = duckdb.connect()
    con.execute("SET threads TO 16")
    con.execute("SET memory_limit='40GB'")
    t0 = time.time()

    p = len(CLEAN_FEATURES)
    # Build sums needed for normal equations: XtX ((p+1)x(p+1) incl intercept), Xty (p+1)
    feat_terms = ["1.0"] + CLEAN_FEATURES
    xtx_terms = []
    for i in range(p + 1):
        for j in range(i, p + 1):
            xtx_terms.append(f"SUM(({feat_terms[i]}) * ({feat_terms[j]})) AS xtx_{i}_{j}")
    xty_terms = [f"SUM(({feat_terms[i]}) * y_loss) AS xty_{i}" for i in range(p + 1)]
    n_term = "COUNT(*) AS n"

    q = f"""
    SELECT {n_term}, {', '.join(xtx_terms)}, {', '.join(xty_terms)}
    FROM read_parquet('{SOURCE}', hive_partitioning=1)
    WHERE split = 'train'
    """
    row = con.execute(q).fetchone()
    cols = [d[0] for d in con.description]
    result = dict(zip(cols, row))
    print(f"train sums computed t={time.time()-t0:.1f}s n={result['n']}", file=sys.stderr)

    XtX = np.zeros((p + 1, p + 1))
    for i in range(p + 1):
        for j in range(i, p + 1):
            v = result[f"xtx_{i}_{j}"]
            XtX[i, j] = v
            XtX[j, i] = v
    Xty = np.array([result[f"xty_{i}"] for i in range(p + 1)])

    coef = np.linalg.lstsq(XtX, Xty, rcond=None)[0]
    print(f"fit done t={time.time()-t0:.1f}s", file=sys.stderr)

    out = {
        "n_train": result["n"],
        "features": ["intercept"] + CLEAN_FEATURES,
        "coefficients": coef.tolist(),
        "fit_seconds": time.time() - t0,
    }
    with open("analysis/feature_provenance_repair_20260917/artifacts/clean_linear_regression_fit.json", "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
