# Baseline Jobs

## Goal

Define the smallest defensible baseline suite for the first SIGMOD benchmark paper without turning the project into a large training campaign.

## Current release constraints

- Full real-release validation passed on the preserved release on 2026-06-29.
- Wolverine source-resume and finalizer work is still running, so no new Wolverine result-generation jobs should be launched until that work finishes.
- Candidate-row label distributions are still pending because they require candidate-row scans.
- The shipped pairwise sample is lightweight and label-centric:
  - it includes `decision_id`, `capacity`, `horizon`, `split`, `trace_family`, `trace_name`, `candidate_a_page_id`, `candidate_b_page_id`, `y_loss_a`, `y_loss_b`, `y_loss_diff_a_minus_b`, `label_a_better`, `label_b_better`, and `is_tie`;
  - it does **not** include candidate-side feature columns such as predictor scores, LRU scores, recency ranks, or bucket/confidence features.
- As a result, feature-based pairwise baselines require either:
  - an augmented pairwise export, or
  - a join back to candidate-row features on Wolverine.

## Benchmark tasks

### Task 1. Value regression

- Objective:
  predict `y_loss` or `y_value` from candidate-level features.
- Primary data source:
  candidate rows.
- Metrics:
  `MAE`, `RMSE`, within-decision Spearman rank correlation, and top-1 regret if a decision-level reconstruction path is implemented.
- Status:
  runner implemented; result still pending because the full preserved-release run belongs on Wolverine.
- Local feasibility:
  not appropriate for local full-scale execution.
- Wolverine requirement:
  yes.

### Task 2. Best-candidate prediction

- Objective:
  identify the minimum-loss or maximum-value candidate within each decision.
- Primary data source:
  candidate rows grouped by decision, with decision-view metadata used for sanity checks.
- Metrics:
  top-1 accuracy, top-k accuracy, and regret of the selected candidate.
- Status:
  runner implemented; result still pending because the full preserved-release run belongs on Wolverine.
- Local feasibility:
  not appropriate for local full-scale execution.
- Wolverine requirement:
  yes.

### Task 3. Pairwise preference prediction

- Objective:
  predict which candidate has lower loss within a candidate pair.
- Primary data source:
  shipped pairwise sample first.
- Metrics:
  accuracy, binary log loss on the non-tie subset, and ROC-AUC if a score-producing model is available.
- Status:
  lightly runnable now and already satisfied for the minimum sanity-check need.
- Local feasibility:
  yes for very light baselines on the shipped pairwise sample.
- Wolverine requirement:
  only for feature-based pairwise models or feature joins back to candidate rows.

## Minimal baseline families

| Baseline family | Value regression | Best-candidate prediction | Pairwise preference | Current status |
| --- | --- | --- | --- | --- |
| Random | optional floor | yes | yes | pairwise version can run now |
| Majority / trivial class baseline | n/a | optional | yes | pairwise version can run now |
| LRU-derived heuristic | yes | yes | yes if feature join exists | requires candidate-row features |
| Predictor-score baseline | yes | yes | yes if feature join exists | requires candidate-row features |
| Linear / logistic model | yes | yes via induced ranking | yes | pairwise metadata-only variant is possible but weak; feature-based version requires candidate-row features |
| Gradient boosting | optional | optional | optional | likely Wolverine-side |
| Small MLP | optional | optional | optional | not required for first draft |

## Recommended first-pass execution order

1. Wait for Wolverine source-resume and finalizer completion.
2. Keep the existing pairwise non-tie sanity results as-is; no rerun is needed for planning.
3. Run one candidate-row label-summary job that emits both `y_loss` and `y_value` summaries in a single pass.
4. Run one `linear_regression` baseline on `y_loss`.
5. Run one `best_candidate_from_linear_score` baseline induced from that same `y_loss` score.

## Concrete baseline definitions

### Pairwise sample first

- `random_non_tie`
  - predict candidate A or B uniformly at random on non-tie rows only.
- `majority_non_tie`
  - fit the majority class on the train split of the non-tie subset and apply it to train/val/test.
- `metadata_only_logistic`
  - optional diagnostic model using only split/family/capacity/horizon if needed;
  - not recommended as a headline result because it does not use candidate-quality features.

### Candidate-row baselines for Wolverine

- `lru_score_regression`
  - use LRU-derived fields directly as the score or prediction.
- `predictor_score_regression`
  - use predictor score fields directly as the score or prediction.
- `linear_regression`
  - fit on candidate-level features for `y_loss` or `y_value`.
- `best_candidate_from_linear_score`
  - induce a decision-level ranking from the linear model score.
- `gradient_boosting`
  - optional second-pass model once the linear path is stable.

## Minimum missing baseline outputs still worth generating

- `paper/sigmod2027/results/baselines/value_regression/linear_regression_y_loss.json`
  - first candidate-row-backed value baseline worth generating for the paper.
- `paper/sigmod2027/results/baselines/best_candidate/best_candidate_from_linear_score.json`
  - first candidate-row-backed best-candidate baseline worth generating for the paper.
- No additional pairwise baseline output is required for the minimum SIGMOD draft because the current light non-tie sanity outputs already exist.

## Implemented runners

### Value regression

```bash
python scripts/sigmod2027/run_value_regression_baseline.py \
  --release-root release/lafc-evict-v0.1-open-current-contract-preserved \
  --output-dir paper/sigmod2027/results/baselines/value_regression \
  --target y_loss \
  --mode plan
```

- `--mode plan` inspects metadata/schema only.
- `--mode run` streams candidate rows, fits a streaming linear regression baseline, and emits `linear_regression_<target>.json`.
- `--max-files`, `--resume`, and `--overwrite` allow chunked or restart-safe execution.

### Best-candidate

```bash
python scripts/sigmod2027/run_best_candidate_baseline.py \
  --release-root release/lafc-evict-v0.1-open-current-contract-preserved \
  --output-dir paper/sigmod2027/results/baselines/best_candidate \
  --mode plan
```

- `--mode plan` inspects metadata/schema only.
- `--mode run` streams candidate rows decision-by-decision and emits `best_candidate_from_<scorer>.json`.
- The first intended SIGMOD result path uses `--linear-score-json` with the `linear_regression_y_loss.json` output from the value-regression runner.

## Blocking issues to track

- The current pairwise sample does not expose the candidate feature columns needed for LRU-derived, predictor-derived, or full logistic pairwise baselines.
- Candidate-row tasks require HPC because the release contains 277,995,072 candidate rows across 168 parquet shards.
- Full-release validation has passed on the preserved release, so baseline write-ups may state that result while still describing current numbers as preserved-release results rather than final published artifact results.
- The remaining risk is execution cost and result validation on Wolverine, not missing local runner implementations.

## Output expectations

Each baseline run or dry-run plan should produce:

- one machine-readable JSON file following `baseline_result_schema.md`,
- one clear statement of whether the baseline used pairwise-sample data only or candidate-row data,
- one note on whether the result is safe to cite in the anonymous manuscript,
- one `result_registry.md` entry or status update.
