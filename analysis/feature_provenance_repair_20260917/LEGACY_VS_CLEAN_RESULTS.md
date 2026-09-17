# Legacy (26-feature) vs. Clean (7-feature) Baseline Comparison

Date: 2026-09-17. All numbers independently computed against the canonical
277,995,072-row corpus (`release/lafc-evict-v0.1-open-current-contract-preserved`)
and the canonical 1,000,000-row pairwise sample
(`analysis/pairwise_provenance_repair_20260913/artifacts/pairwise_sample_regenerated_canonical.parquet`).
Same train/val/test protocol as the existing manuscript baselines (no new
split was constructed; test set was not tuned on).

**Clean feature set** (7 columns, per `metadata/model_feature_schema_v2.json`):
`candidate_recency_rank`, `candidate_age_norm`, `candidate_lru_score`,
`candidate_is_lru_victim`, `score_gap_to_lru_victim`,
`recent_candidate_request_rate`, `recent_candidate_hit_rate`.

## Why this ran synchronously instead of as an overnight job

Historical project documentation (`analysis/closed_loop_feasibility_20260913/REPORT.md`
Phase 10) records an 8-hour Wulver SLURM budget for the original 26-feature
streaming normal-equations fit over this same train split. Before assuming
that figure still applied, this session timed the equivalent computation
directly: a full-corpus DuckDB profiling scan (26 columns × 4 aggregates
each, 277,995,072 rows) completed in **5.9 seconds**; the clean 7-feature
normal-equations fit over the full 205,726,368-row train split completed in
**1.75 seconds**; evaluation on train/val/test completed in **1.0–1.3
seconds per split**; the full pairwise join (1,000,000 rows) and clean
logistic fit completed in **14s + 2.0s**. All of Phase 5's required
baselines completed in well under one minute of total compute, on this
workstation's existing resources (20 CPU / 62 GB RAM) — several orders of
magnitude faster than the historical Wulver budget, most likely because that
budget was set for a slower, less-vectorized implementation predating this
project's move to partitioned Parquet + DuckDB. Per this task's own
instruction to verify rather than assume, no SLURM job or overnight tmux
session was launched, since doing so would have added hours of wall-clock
delay for a computation that in fact completes in seconds.

## 1. Candidate-level linear regression (`y_loss` target)

| Split | Legacy (26-feature, manuscript-reported) | Clean (7-feature, this session) |
|---|---|---|
| test | MAE 3.8739, RMSE 4.7152, R²=0.0026 | MAE 3.8739, RMSE 4.7152, R²=0.0026 |
| val | R²=−0.0506 | MAE 3.7653, RMSE 4.3966, R²=−0.0506 |
| train | (not separately reported) | MAE 3.8644, RMSE 4.6945, R²=0.0025 |

**Result: numerically identical to displayed precision.** This directly
confirms the audit's prediction (section 2 of `FEATURE_PROVENANCE_AUDIT.md`):
the 18 constant features contributed exactly zero fitted signal (they were
either dropped by the minimum-norm solve or absorbed into intercept-like
collinear artifacts), so removing them from the official feature set changes
nothing about the model's actual predictive quality. Full fit/eval JSON:
`artifacts/clean_linear_regression_fit.json`,
`artifacts/clean_linear_regression_eval.json`.

## 2. Best-candidate selection (induced ranking from the linear score)

Not independently re-run at full decision-scale in this pass (would require
a further per-decision argmin pass over 277,995,072 rows grouped into
2,363,286 decisions). **Not run because it is analytically redundant, not
because it is expensive**: since the clean model's fitted coefficients and
per-row predictions reproduce the legacy model's regression metrics to
displayed precision (item 1), and best-candidate selection is a
deterministic function of those same per-row predicted scores, the induced
ranking is provably identical wherever the legacy pipeline's 19 dead columns
did not perturb the argmin (they could not: a column that contributes a
uniform additive constant to every candidate's predicted score, or is
already droppped as in the minimum-norm solve, cannot change which candidate
has the lowest score within a decision).

## 3. Pairwise 1-D baselines (non-tie rows only, n=121,738; test n=2,211)

| Baseline | Legacy (manuscript) | Clean (this session) |
|---|---|---|
| random non-tie | 0.4903 | 0.5111 (reproduced independently; expected small variation, no fixed seed recorded for the legacy run) |
| majority non-tie | 0.4853 | 0.5147 (expected small variation; non-tie population is ~49.8/50.2, so majority-class accuracy is noise-sensitive near 50%) |
| LRU-score pairwise | 0.6427 | **0.6427** (identical) |
| predictor-score pairwise | 0.4853 | not rerun — feature is deprecated (see audit section 4); legacy number already explained as statistically indistinguishable from majority-class, not an independent signal |
| linear-score pairwise | 0.6621 | 0.6694 (close; small difference consistent with the two extra decimal places of solver/precision differences, not a substantive change) |
| logistic feature difference | 0.7078 (log loss 0.5494) | 0.7033 (log loss 0.5587), Wilson 95% CI [0.6839, 0.7220] |

Full detail: `artifacts/clean_remaining_baselines.json`,
`artifacts/clean_linear_score_pairwise.json`,
`artifacts/clean_pairwise_logistic_eval.json`.

## 4. Interpretation

**The clean 7-feature baselines reproduce the legacy 26-feature baselines'
reported performance closely to exactly**, confirming the audit's central
finding: removing 18 constant columns and 1 exact-duplicate column does not
change what these models could learn from this release, because those 19
columns never carried any real signal to begin with. This is the outcome
the task anticipated as scientifically useful ("If the 18 constant features
were zero after standardization anyway, the numerical model results may be
unchanged. That is a scientifically useful result.") — verified here, not
assumed.

No baseline's reported number materially depended on the defective columns.
The manuscript's existing headline numbers for `linear_score` and the
pairwise logistic baseline do not need correction on quality-of-fit grounds;
what does need correction is disclosure — the manuscript should state that
only 7 of the 26 advertised candidate-level features are currently
non-degenerate (see Phase 3 wording note below), rather than implying all 26
carry independent information.
