# Wolverine Baseline Plan

## Scope

This plan records the minimum later Wolverine work that is still worth running for the SIGMOD draft.
It intentionally does not submit jobs from the local machine.

## Current state on 2026-06-29

- The preserved release passed full real-release validation on 2026-06-29.
- Wolverine source-resume and finalizer work is still in flight.
- Do not launch any new Wolverine result-generation jobs until those source/finalizer jobs complete.
- The local repo already contains the light pairwise sanity outputs under `paper/sigmod2027/results/baselines/pairwise/`.
- The local repo does not yet contain a checked-in SIGMOD runner that produces final candidate-row label-distribution outputs.
- The local repo does not yet contain a checked-in SIGMOD runner that produces final value-regression or best-candidate result files; the current candidate-row scripts emit planning JSON only.

## Minimal remaining result set

| Result | Supports paper section | Exact input artifact | Exact expected output files | Run site | Full candidate-row scan | Estimated resources | Must wait for source/finalizer completion? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Candidate-row `y_loss` distribution summary | 8 Empirical Characterization | `release/lafc-evict-v0.1-open-current-contract-preserved/data/candidate_rows/` | `paper/sigmod2027/results/candidate_label_stats/y_loss_summary.json`, `paper/sigmod2027/results/candidate_label_stats/y_loss_summary.csv` | Wolverine | yes | `16` CPU, `64G` RAM, `2-4` hours if streamed shard-by-shard | yes |
| Candidate-row `y_value` distribution summary | 8 Empirical Characterization | `release/lafc-evict-v0.1-open-current-contract-preserved/data/candidate_rows/` | `paper/sigmod2027/results/candidate_label_stats/y_value_summary.json`, `paper/sigmod2027/results/candidate_label_stats/y_value_summary.csv` | Wolverine | yes | same job as `y_loss` if combined into one pass | yes |
| One value-regression baseline: `linear_regression` on `y_loss` | 7 Benchmark Tasks and Baselines | `release/lafc-evict-v0.1-open-current-contract-preserved/data/candidate_rows/` | `paper/sigmod2027/results/baselines/value_regression/linear_regression_y_loss.json` | Wolverine | yes | `24` CPU, `96G` RAM, `4-8` hours | yes |
| One best-candidate baseline: `best_candidate_from_linear_score` induced from the same `y_loss` score | 7 Benchmark Tasks and Baselines | `release/lafc-evict-v0.1-open-current-contract-preserved/data/candidate_rows/`, `release/lafc-evict-v0.1-open-current-contract-preserved/data/decision_view/decision_view.parquet` | `paper/sigmod2027/results/baselines/best_candidate/best_candidate_from_linear_score.json` | Wolverine | yes | `24` CPU, `96G` RAM, `4-8` hours if scored from the same linear pass | yes |
| Lightweight sanity check for the tie-heavy pairwise sample | 7 Benchmark Tasks and Baselines / 8 Empirical Characterization | `release/lafc-evict-v0.1-open-current-contract-preserved/data/pairwise_sample/pairwise_sample.parquet` | already available: `paper/sigmod2027/results/baselines/pairwise/results.json`, `results.csv`, `results.md` | already done locally | no candidate-row scan | already completed | no |

## Exact commands already available in the repo

These are the only current SIGMOD commands that are exact and checked in today.

### Pairwise sanity baseline

Already available; do not rerun just for planning.

```bash
python scripts/sigmod2027/run_pairwise_baseline.py \
  --mode run-light \
  --baseline majority_non_tie \
  --release-root release/lafc-evict-v0.1-open-current-contract-preserved \
  --output-dir paper/sigmod2027/results/baselines/pairwise

python scripts/sigmod2027/run_pairwise_baseline.py \
  --mode run-light \
  --baseline random_non_tie \
  --seed 7 \
  --release-root release/lafc-evict-v0.1-open-current-contract-preserved \
  --output-dir paper/sigmod2027/results/baselines/pairwise
```

### Candidate-row preflight plan stubs

Run these on Wolverine only after the source/finalizer jobs finish.
They verify manifest/schema assumptions and emit `plan.json`; they do not generate final candidate-row results.

```bash
python scripts/sigmod2027/run_value_regression_baseline.py \
  --release-root release/lafc-evict-v0.1-open-current-contract-preserved \
  --output-dir paper/sigmod2027/results/baselines/value_regression \
  --target y_loss

python scripts/sigmod2027/run_best_candidate_baseline.py \
  --release-root release/lafc-evict-v0.1-open-current-contract-preserved \
  --output-dir paper/sigmod2027/results/baselines/best_candidate
```

## Command gap that still exists

- No checked-in `scripts/sigmod2027/` command currently emits the final candidate-row `y_loss` / `y_value` summary files.
- No checked-in `scripts/sigmod2027/` command currently emits the final `linear_regression_y_loss.json` result file.
- No checked-in `scripts/sigmod2027/` command currently emits the final `best_candidate_from_linear_score.json` result file.
- Therefore the later Wolverine phase should start with the two preflight plan stubs above, then add the missing candidate-row runners before any Slurm submission for final results.

## Manuscript-safe labels

- Safe to cite now:
  - `manifest-backed`,
  - `decision-view-backed`,
  - `pairwise-sample-backed`,
  - `pairwise-sample-backed light sanity baseline`,
  - `preserved release passed full real-release validation on 2026-06-29`.
- Not safe to cite as available results yet:
  - `candidate-row-backed label distribution`,
  - `candidate-row-backed value-regression baseline`,
  - `candidate-row-backed best-candidate baseline`.

## What not to run locally

- Do not run any full candidate-row scan on the local machine.
- Do not run any command that reads every file under `release/.../data/candidate_rows/`.
- Do not submit Slurm jobs until Wolverine source/finalizer completion is confirmed.
- Do not describe plan-only JSON files as final baseline results.
