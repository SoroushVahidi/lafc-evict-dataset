# Wolverine Baseline Plan

## Scope

This plan records how to run the first candidate-row-heavy baseline jobs on Wolverine without submitting anything from the local machine.

## Execution order

1. Pairwise sample first:
   - lightweight non-tie sanity baselines can run locally;
   - feature-based pairwise baselines should move to Wolverine if they require joining back to candidate-row features.
2. Value regression on candidate rows.
3. Best-candidate prediction on candidate rows.

## Expected inputs

- Preserved release root:
  `release/lafc-evict-v0.1-open-current-contract-preserved`
- Candidate rows:
  `release/lafc-evict-v0.1-open-current-contract-preserved/data/candidate_rows/`
- Decision view:
  `release/lafc-evict-v0.1-open-current-contract-preserved/data/decision_view/decision_view.parquet`
- Pairwise sample:
  `release/lafc-evict-v0.1-open-current-contract-preserved/data/pairwise_sample/pairwise_sample.parquet`

## Planned outputs

- Baseline result JSON files:
  `paper/sigmod2027/results/baselines/<task>/`
- Logs:
  `paper/sigmod2027/results/baselines/logs/`
- Optional derived tables or plots:
  `paper/sigmod2027/results/baselines/<task>/figures/`

## Resource estimates

These are starting estimates only, not guarantees.

- Pairwise feature-join or richer pairwise model:
  - `4-8` CPU cores
  - `16-32G` RAM
  - `1-2` hours
- Value regression over candidate rows:
  - `16-32` CPU cores
  - `64-128G` RAM
  - several hours depending on feature materialization and model family
- Best-candidate prediction over candidate rows:
  - `16-32` CPU cores
  - `64-128G` RAM
  - several hours depending on grouping strategy and metrics

## Suggested Slurm skeletons

### Pairwise feature-join or richer pairwise baseline

```bash
#!/bin/bash
#SBATCH --job-name=lafc_pairwise_baseline
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=paper/sigmod2027/results/baselines/logs/pairwise-%j.out

cd /path/to/lafc-evict-dataset
python scripts/sigmod2027/run_pairwise_baseline.py \
  --release-root release/lafc-evict-v0.1-open-current-contract-preserved \
  --mode plan \
  --output-dir paper/sigmod2027/results/baselines/pairwise
```

### Value regression planning stub

```bash
#!/bin/bash
#SBATCH --job-name=lafc_value_regression
#SBATCH --cpus-per-task=24
#SBATCH --mem=96G
#SBATCH --time=08:00:00
#SBATCH --output=paper/sigmod2027/results/baselines/logs/value-%j.out

cd /path/to/lafc-evict-dataset
python scripts/sigmod2027/run_value_regression_baseline.py \
  --release-root release/lafc-evict-v0.1-open-current-contract-preserved \
  --output-dir paper/sigmod2027/results/baselines/value_regression
```

### Best-candidate planning stub

```bash
#!/bin/bash
#SBATCH --job-name=lafc_best_candidate
#SBATCH --cpus-per-task=24
#SBATCH --mem=96G
#SBATCH --time=08:00:00
#SBATCH --output=paper/sigmod2027/results/baselines/logs/best-candidate-%j.out

cd /path/to/lafc-evict-dataset
python scripts/sigmod2027/run_best_candidate_baseline.py \
  --release-root release/lafc-evict-v0.1-open-current-contract-preserved \
  --output-dir paper/sigmod2027/results/baselines/best_candidate
```

## Important caveats

- The pairwise sample currently lacks candidate feature columns, so feature-based pairwise models require an extra data-preparation step.
- Candidate-row jobs belong on Wolverine, not on the local machine.
- No Slurm jobs should be submitted until the task definitions and output schema are frozen enough to avoid churn.
