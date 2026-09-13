# SIGMOD target-discriminativeness audit (2026-09-13)

Evidence audit responding to the strongest SIGMOD reviewer criticism of
LAFC-Evict: is the counterfactual eviction target dominated by ties to the
point of being non-discriminative? This directory contains the analysis
scripts, machine-readable outputs, and full report. **No manuscript claims
were changed as part of this audit.**

See `REPORT.md` for the full write-up. Key inputs analyzed:

- `release/lafc-evict-v0.1-open-current-contract-preserved/data/decision_view/decision_view.parquet`
  (2,363,286 rows — the canonical SIGMOD-scale decision population)
- `release/lafc-evict-v0.1-open-current-contract-preserved/data/candidate_rows/**/*.parquet`
  (277,995,072 rows, 168 partitions)
- `release/lafc-evict-v0.1-open-current-contract-preserved/data/pairwise_sample/pairwise_sample.parquet`
  (1,000,000 rows — see REPORT.md provenance flag; this on-disk copy is stale
  relative to the manuscript's committed pairwise numbers)

All three parquet artifacts live under the gitignored `release/` directory
and are NOT checked into this branch (per instructions: no giant generated
data files in git). Only the small machine-readable summaries this analysis
produced are committed, under `outputs/`.

## Reproduce

Requires the release artifacts above to exist locally (they are produced by
the repo's existing release-build pipeline, e.g. `scripts/build_real_release.py`
against `release/lafc-evict-v0.1-open-current-contract-preserved`). No RNG,
no sampling, no seeds — every statistic is an exact population aggregate over
whatever is on disk at run time.

```bash
cd analysis/sigmod_target_discriminativeness_20260913/scripts
python3 01_decision_view_analysis.py     # Phases 2-6: decision_view population stats (~1s)
python3 02_candidate_level_analysis.py   # Phases 3/7/8: full 277.995M-row candidate_rows scan (~10-15s on this machine)
python3 03_pairwise_analysis.py          # Phase 7: pairwise_sample information content (~1s)
```

Outputs land in `../outputs/`. Dependencies: `duckdb`, `pandas` (both already
in this repo's environment; no new dependency was added).

## What each script computes

| Script | Phases | Source data | Notes |
| --- | --- | --- | --- |
| `01_decision_view_analysis.py` | 2, 3, 4, 5, 6 | `decision_view.parquet` only | Reproduces reviewer's 0.9912 / 0.0088 exactly; decision-weighted + candidate-weighted stats; trace_family×capacity×horizon matrix; nontrivial-subset thresholds; horizon trend |
| `02_candidate_level_analysis.py` | 3 (regret≥2 exact), 7 (quadratic-weighting cross-check), 8 | Full `candidate_rows` scan joined to `decision_view` | Only script that touches the full 278M-row table; needed because decision_view stores mean/std/max/sum of regret but not the full per-candidate histogram; also computes LRU/MRU/predictor-victim diagnostics |
| `03_pairwise_analysis.py` | 7 | `pairwise_sample.parquet` | Tie/strict-preference breakdown, per-decision strict-pair contribution, quadratic pairwise-expansion weighting effect; **carries an explicit provenance flag** — see REPORT.md |

## Validation performed

- Manually recomputed `candidate_count`, `min_y_loss`, `optimal_candidate_count`,
  `regret_mean`, `regret_sum`, and `regret_max` from raw `candidate_rows` for
  two spot-checked decisions (one all-tied, one non-trivial) — exact match
  against `decision_view` in both cases.
- Confirmed `tie_count == optimal_candidate_count` for all 2,363,286 decisions
  (population check, not a sample).
- Confirmed `regret_sum` is integer-valued for all decisions (population
  check), which is what licenses the exact `P(regret>=1) = (candidate_count -
  optimal_candidate_count) / candidate_count` shortcut in `01_...py` instead
  of requiring a full candidate_rows scan for that one threshold.
- Cross-checked `candidate_is_predictor_victim` against `candidate_is_lru_victim`
  row-by-row on one partition file: identical on every row in that file, and
  aggregate predictor/LRU regret statistics are bit-identical across the full
  278M-row scan — flagged in REPORT.md as a real property of this release
  worth confirming with the label-generation code, not assumed to be a bug.
