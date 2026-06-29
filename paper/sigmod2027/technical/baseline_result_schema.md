# Baseline Result Schema

This file defines the JSON structure for baseline plans and lightweight baseline outputs under `paper/sigmod2027/results/baselines/`.

## Common top-level fields

```json
{
  "task": "pairwise_preference",
  "status": "planned",
  "mode": "plan",
  "release_root": "release/lafc-evict-v0.1-open-current-contract-preserved",
  "input_view": "pairwise_sample",
  "input_path": "release/.../data/pairwise_sample/pairwise_sample.parquet",
  "full_validation_status": "pending",
  "notes": []
}
```

## Required fields

- `task`
  - one of `value_regression`, `best_candidate`, `pairwise_preference`
- `status`
  - one of `planned`, `dry_run_checked`, `available`, `blocked`
- `mode`
  - one of `plan`, `run_light`, `run_hpc`
- `release_root`
  - repo-relative release path
- `input_view`
  - one of `candidate_rows`, `decision_view`, `pairwise_sample`
- `input_path`
  - repo-relative file or directory path
- `full_validation_status`
  - currently `pending`
- `requires_wolverine`
  - boolean
- `safe_for_anonymous_manuscript`
  - boolean
- `metrics`
  - list of metric names intended or computed
- `baselines`
  - list of baseline descriptors

## Optional fields

- `schema_check`
  - object with `required_columns`, `available_columns`, and `missing_columns`
- `release_summary`
  - manifest-backed counts relevant to the task
- `blockers`
  - list of explicit constraints preventing richer baselines
- `recommended_next_step`
  - short human-readable guidance
- `split_metrics`
  - object keyed by split for actual run outputs
- `artifact_paths`
  - output JSON, logs directory, or future plot/table paths

## Pairwise run-light result shape

For a lightweight pairwise baseline that runs on the shipped sample:

```json
{
  "task": "pairwise_preference",
  "status": "available",
  "mode": "run_light",
  "evaluation_population": "non_tie_rows_only",
  "tie_row_count": 879968,
  "non_tie_row_count": 120032,
  "split_metrics": {
    "train": {
      "rows": 1000,
      "accuracy": 0.5,
      "log_loss": 0.69
    }
  }
}
```

## Manuscript-safe wording

- Results based only on `pairwise_sample` should be described as pairwise-sample-backed.
- Results based on candidate rows should be marked as candidate-row-backed and Wolverine-side if the job is not lightweight.
- No result JSON should claim that the release is fully validated until full real-release validation actually runs.
