from __future__ import annotations
import json, time
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss

CLEAN_FEATURES = [
    "candidate_recency_rank", "candidate_age_norm", "candidate_lru_score",
    "candidate_is_lru_victim", "score_gap_to_lru_victim",
    "recent_candidate_request_rate", "recent_candidate_hit_rate",
]

t0 = time.time()
df = pd.read_parquet("analysis/feature_provenance_repair_20260917/artifacts/clean_pairwise_features.parquet")
print(f"loaded {len(df)} rows t={time.time()-t0:.1f}s")

non_tie = df[df["is_tie"] == 0].copy()
print(f"non_tie rows: {len(non_tie)}")

for f in CLEAN_FEATURES:
    non_tie[f"diff_{f}"] = non_tie[f"a_{f}"] - non_tie[f"b_{f}"]

diff_cols = [f"diff_{f}" for f in CLEAN_FEATURES]
y = non_tie["label_a_better"].astype(int)

train = non_tie[non_tie["split"] == "train"]
val = non_tie[non_tie["split"] == "val"]
test = non_tie[non_tie["split"] == "test"]

model = LogisticRegression(max_iter=1000)
model.fit(train[diff_cols], train["label_a_better"].astype(int))

results = {}
for name, split_df in [("train", train), ("val", val), ("test", test)]:
    if len(split_df) == 0:
        results[name] = {"n": 0}
        continue
    yt = split_df["label_a_better"].astype(int)
    proba = model.predict_proba(split_df[diff_cols])[:, 1]
    pred = (proba >= 0.5).astype(int)
    acc = accuracy_score(yt, pred)
    ll = log_loss(yt, proba, labels=[0, 1])
    # Wilson CI for accuracy
    n = len(yt)
    p = acc
    z = 1.959963985
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = (z * ((p * (1 - p) / n + z**2 / (4 * n**2)) ** 0.5)) / denom
    results[name] = {
        "n": int(n),
        "accuracy": float(acc),
        "log_loss": float(ll),
        "wilson_ci_95": [float(center - half), float(center + half)],
    }

out = {
    "features": CLEAN_FEATURES,
    "coefficients": model.coef_[0].tolist(),
    "intercept": float(model.intercept_[0]),
    "results": results,
    "fit_seconds": time.time() - t0,
}
with open("analysis/feature_provenance_repair_20260917/artifacts/clean_pairwise_logistic_eval.json", "w") as f:
    json.dump(out, f, indent=2)
print(json.dumps(out, indent=2))
