# Experiments Plan

## Goal

Define the minimum empirical package needed for a credible SIGMOD Experiment & Analysis benchmark submission without inventing unavailable results.

## Mandatory benchmark characterization

### 1. Dataset scale table

Include at minimum:

- total candidate rows,
- total decision rows,
- pairwise sample rows,
- number of selected families,
- number of excluded families,
- release size,
- number of Parquet shards,
- number of benchmark files.

### 2. Composition breakdowns

Produce aggregate counts by:

- trace family,
- split,
- capacity,
- horizon,
- trace family x split if page budget allows.

### 3. Label distribution statistics

For `y_loss` and `y_value`:

- mean,
- standard deviation,
- min and max,
- selected percentiles,
- optionally per-family summaries.

### 4. Tie and regret statistics

From the decision view:

- fraction of decisions with ties,
- distribution of `tie_count`,
- distribution of `optimal_candidate_count`,
- regret mean/std/max distributions,
- hardest families or regimes by regret spread.

### 5. Decision-level candidate-count statistics

- candidate-count histogram,
- mean/median candidates per decision,
- per-family or per-capacity variation if it materially differs.

### 6. Pairwise-sample statistics

- class balance for pairwise preference labels,
- tie fraction,
- per-family or per-split composition,
- relation between pairwise outcomes and decision tie structure.

## Mandatory benchmark tasks

### 7. Candidate-level value prediction

- Regression target: `y_loss` or `y_value`.
- Report error metrics such as MAE and RMSE.
- Include split-aware evaluation.

### 8. Best-candidate prediction

- Predict the best candidate within a decision.
- Treat as ranking or decision-level classification.
- Report top-1 accuracy and a regret-aware metric if available.

### 9. Pairwise preference prediction

- Predict whether candidate A is better than candidate B.
- Report accuracy and ROC-AUC if class balance supports it.

## Minimum baseline set

### Required simple baselines

- LRU-derived heuristic baseline.
- Predictor-score baseline using `candidate_predictor_score`.
- Linear regression / logistic regression.
- One tree-based baseline:
  random forest or gradient boosting, whichever is already practical in the existing environment.

### Optional only if practical

- Small MLP baseline if it can be trained and evaluated quickly with clear value.

Do not expand into heavy deep-learning baselines unless the pipeline already exists and is stable.

## Downstream systems experiment

- Include a cache-performance downstream experiment only if the original pipeline already supports it and the result can be reproduced cleanly.
- Do not invent a simulator story or new deployment claims for this paper if the tooling is not already available.

## Suggested main-paper figure/table budget

- One scale/composition table.
- One decision complexity and tie/regret figure.
- One label-distribution figure.
- One baseline results table.
- Optional one family heterogeneity figure.

## What can move to appendix

- Extended per-family tables.
- Extended per-capacity and per-horizon breakdowns.
- Extra baseline variants.
- Additional feature ablations.
- Extra plots for pairwise-sample composition.
- Release-engineering implementation details beyond what is needed for the benchmark story.

## Current risks

- Full real-release validation passed on the preserved release on 2026-06-29.
- Full release anonymization is still pending.
- Some release-governance and redistribution review items are still marked as pending final review.
- Light pairwise sanity baseline results now exist in the repository, while value-regression and best-candidate baselines remain pending.
- The 12-page limit means the experiments section must stay compact and benchmark-focused.
