from __future__ import annotations
import json
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss

df = pd.read_parquet("analysis/feature_provenance_repair_20260917/artifacts/clean_pairwise_features.parquet")
non_tie = df[df["is_tie"] == 0].copy()

results = {}

# 1-D LRU-score pairwise baseline: predict label_a_better if a_candidate_lru_score > b_candidate_lru_score
for split in ["train", "val", "test"]:
    sub = non_tie[non_tie["split"] == split]
    if len(sub) == 0:
        results[f"lru_score_pairwise_{split}"] = {"n": 0}
        continue
    pred = (sub["a_candidate_lru_score"] > sub["b_candidate_lru_score"]).astype(int)
    # ties in raw LRU score broken as "b_better" (0), matching typical convention
    y = sub["label_a_better"].astype(int)
    acc = accuracy_score(y, pred)
    results[f"lru_score_pairwise_{split}"] = {"n": int(len(sub)), "accuracy": float(acc)}

# random / majority non-tie sanity checks (test split)
test = non_tie[non_tie["split"] == "test"]
rng = np.random.default_rng(0)
random_pred = rng.integers(0, 2, size=len(test))
results["random_non_tie_test"] = {"n": int(len(test)), "accuracy": float(accuracy_score(test["label_a_better"].astype(int), random_pred))}
majority_class = int(test["label_a_better"].astype(int).mean() >= 0.5)
maj_pred = np.full(len(test), majority_class)
results["majority_non_tie_test"] = {"n": int(len(test)), "accuracy": float(accuracy_score(test["label_a_better"].astype(int), maj_pred))}

print(json.dumps(results, indent=2))
with open("analysis/feature_provenance_repair_20260917/artifacts/clean_remaining_baselines.json", "w") as f:
    json.dump(results, f, indent=2)
