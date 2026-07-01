# Wulver SIGMOD Result Submission Note — Feature-Based Pairwise Baseline

- Date/time: Wed Jul 1 13:44:34 EDT 2026
- Host: login02
- Branch: `wulver-sync-origin-master-with-finalizer-fixes-20260629`
- Commit at submission time: `4256374` (`Add SIGMOD computed result summaries`) — the new implementation files below are present in the working tree but not yet committed
- Release root: `/mmfs1/scratch/ikoutis/sv96/lafc-work/release/lafc-evict-v0.1-open-current-contract-preserved`

## Goal

Strengthen the SIGMOD pairwise-preference task by augmenting the shipped, capped pairwise sample with
candidate-side A/B feature columns (joined back to candidate rows), then evaluate feature-based pairwise
baselines. The full quadratic pairwise view is never generated and the release is never rebuilt or modified.

## Verification that this had not already been done

```bash
find paper/sigmod2027/results -iname '*pairwise*' -o -iname '*logistic*' -o -iname '*feature*' -o -iname '*augmented*'
grep -R "candidate_lru_score_a\|candidate_predictor_score_a\|logistic_regression_pairwise\|feature_ready.*true\|augmented_pairwise\|feature_join" \
  scripts hpc paper/sigmod2027/results paper/sigmod2027/technical tests 2>/dev/null
```

Confirmed the feature-based pairwise baseline was **not** done: `scripts/sigmod2027/run_pairwise_baseline.py`,
`paper/sigmod2027/results/baselines/pairwise/plan.json`, and `results.json` all marked the candidate-feature
baselines `blocked_without_feature_join` / `pending_feature_join`.

## Implementation

- `scripts/sigmod2027/build_augmented_pairwise_sample.py`
  - Streams only the candidate partitions referenced by the pairwise sample (partition-pruned; never loads the
    full 277,995,072-row candidate release into memory).
  - Joins candidate-side A/B features using the robust 7-column key: `split`, `trace_family`, `capacity`,
    `horizon`, `trace_name`, `decision_id`, `candidate_page_id`.
  - Includes the required core features (`candidate_lru_score`, `candidate_predictor_score`,
    `candidate_recency_rank`, `candidate_age_norm`, `candidate_is_lru_victim`, `candidate_is_predictor_victim`)
    plus all remaining candidate feature columns (bucket/confidence fields, recent request/hit rates, and gap
    features) so `linear_score_pairwise` can reuse the already-trained `linear_regression_y_loss.json` model
    without a partial-feature approximation.
  - Validates output row count equals input pairwise-sample row count and fails loudly (raises `ValueError`
    listing sample missing keys) if any pairwise row cannot be joined to candidate-side features.
  - Supports `--mode plan|run`, `--resume`, `--overwrite`, `--max-files`, matching the existing runner style.
  - Output: `paper/sigmod2027/results/baselines/pairwise/augmented_pairwise_sample.parquet`.
- `scripts/sigmod2027/run_feature_pairwise_baseline.py`
  - Evaluates non-tie rows only: `random_non_tie`, `majority_non_tie`, `lru_score_pairwise`,
    `predictor_score_pairwise`, `linear_score_pairwise` (using `linear_regression_y_loss.json`), and
    `logistic_regression_pairwise` (a custom pure-numpy Newton-Raphson logistic regression on feature
    differences, L2-regularized — no scikit-learn dependency).
  - Reports tie/non-tie row counts, accuracy, binary log loss, split-level metrics (train/val/test), positive
    rate per split, and class-imbalance notes.
  - Outputs: `feature_pairwise_results.json` (with `status`, `requires_wolverine: true`,
    `safe_for_anonymous_manuscript: true`, release identity/summary, git commit, exact input/output paths,
    limitations), `feature_pairwise_results.csv`, `feature_pairwise_results.md`.
- `tests/test_feature_pairwise_baseline.py`
  - Tiny synthetic release + hand-built bare-schema pairwise sample fixture.
  - `test_augmented_join_row_count_matches_input`, `test_augmented_join_has_ab_feature_suffixes`,
    `test_missing_join_fails_loudly` (corrupts a `candidate_a_page_id` to a nonexistent key and asserts a loud
    `ValueError`), `test_feature_pairwise_baseline_runs_without_crashing` (full build + value-regression +
    feature-pairwise-baseline pipeline, asserts all six baselines report non-null accuracy/log loss).
- `hpc/wulver/sigmod2027/run_feature_pairwise_baseline.sbatch`
  - `20` CPUs, `80G` RAM, `10:00:00`, same guard-rail style as the existing SIGMOD sbatch scripts (rejects
    non-preserved release roots, log dirs outside scratch logs, output/linear-score paths outside the repo).
  - Fails immediately if `linear_regression_y_loss.json` is missing.
  - Runs `build_augmented_pairwise_sample.py --mode run --resume` then
    `run_feature_pairwise_baseline.py` in sequence.
- Documentation updated: `paper/sigmod2027/technical/result_registry.md`,
  `paper/sigmod2027/technical/baseline_jobs.md`, `hpc/wulver/sigmod2027/README.md` (added to submission order).

## Local test results (before submission)

```bash
python -m pytest tests/test_sigmod_result_runners.py -q      # 11 passed
python -m pytest tests/test_feature_pairwise_baseline.py -q  # 4 passed
python -m pytest -q                                           # full suite: 85 passed, 0 failed
```

## Submission

Command:

```bash
sbatch hpc/wulver/sigmod2027/run_feature_pairwise_baseline.sbatch
```

- Job ID: `1087431`
- Queue state at submission: `PENDING`, then `RUNNING` on `n0053`/`n0095` within seconds
- `squeue -u sv96` immediately before submission: empty (no duplicate or conflicting job)
- Initial `.out` log confirmed correct `RELEASE_ROOT`, `OUTPUT_DIR`, and `LINEAR_SCORE_JSON`, and reached
  "=== step 1: build augmented pairwise sample ===" with an empty `.err`.

Expected output files (once the job completes):

- `paper/sigmod2027/results/baselines/pairwise/augmented_pairwise_sample.parquet`
- `paper/sigmod2027/results/baselines/pairwise/feature_pairwise_results.json`
- `paper/sigmod2027/results/baselines/pairwise/feature_pairwise_results.csv`
- `paper/sigmod2027/results/baselines/pairwise/feature_pairwise_results.md`

Candidate-label stats (`1085544`), value regression (`1085545`), and best-candidate (`1085963`/resumed
`1086763`) were **not** resubmitted or modified.

## Completion (2026-07-01, same session)

- Final state: `sacct -j 1087431` reports `COMPLETED`, `ExitCode 0:0`, elapsed `00:07:09`, `MaxRSS 2810620K`, on `n0095`.
- `.err` log: empty. `.out` log: full JSON result payload printed at completion, no tracebacks or warnings.
- Validation performed:
  - `augmented_pairwise_sample.parquet` row count (`1,000,000`) matches the input pairwise sample row count exactly.
  - `augmented_pairwise_sample_report.json` (the build script's own summary): `status: available`, `missing_join_count: 0`, `candidate_partitions_scanned: 168` (all referenced partitions), `feature_columns` count `26` (all core + optional candidate features, enabling `linear_score_pairwise` to reuse `linear_regression_y_loss.json` unmodified).
  - `feature_pairwise_results.json`: `status: available`, all six intended baselines present and non-skipped:
    - `random_non_tie`: accuracy `0.4993`, log loss `0.6931` (sanity-check baseline near chance, as expected).
    - `majority_non_tie`: accuracy `0.9489`, log loss `0.2023` — matches the earlier light-baseline run exactly, confirming label consistency between the two pipelines.
    - `lru_score_pairwise`: accuracy `0.9596`, log loss `0.1326`.
    - `predictor_score_pairwise`: accuracy `0.9489`, log loss `0.2023`.
    - `linear_score_pairwise`: accuracy `0.9530`, log loss `0.1072`.
    - `logistic_regression_pairwise`: accuracy `0.9676`, log loss `0.0774` (best of the six).
  - `tie_row_count`: `879,968`; `non_tie_row_count`: `120,032`; `pairwise_sample_rows_total`: `1,000,000` — consistent with the previously published light-baseline evaluation population.
  - `feature_pairwise_results.csv` and `feature_pairwise_results.md` both present, well-formed, and consistent with the JSON.
- `augmented_pairwise_sample.parquet` (13M) is covered by the repo's existing `.gitignore` rule (`*.parquet`) and is confirmed **not** staged; it is a large intermediate artifact and should not be committed.
- Tests re-run after completion: `tests/test_feature_pairwise_baseline.py` (4 passed); full repo suite `python -m pytest -q` (85 passed, 0 failed).
- Documentation updated to reflect `available` status: `paper/sigmod2027/technical/result_registry.md`, `paper/sigmod2027/technical/baseline_jobs.md`.
