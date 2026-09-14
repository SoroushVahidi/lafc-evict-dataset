# Full-Population Deterministic MRU Continuation Census

An unattended overnight job: exact/full-population LRU-vs-MRU
continuation-sensitivity census over the canonical LAFC-Evict decision
population (no sampling), extending the validated 5,000-decision sampled
study to (a) the complete decision population and (b) capacities 64/256
(never tested by the sampled study). **Random continuation is out of scope
for this census** -- it remains the sampled study's job.

## Duplication audit

A fresh search (both repositories, all branches, tracked/untracked
artifacts) found no prior full-population continuation census anywhere.
**Classification: NOT_PREVIOUSLY_RUN.** The completed 5,000-decision sampled
study (`experiment/continuation-sensitivity-full-20260914` @ `484417c`,
validated: `FULL_EXPERIMENT_VALID: true`, independent recheck passed)
already found both MRU and mean-random continuation **ROBUST** (median
optimal-set Jaccard 1.0, mean cross-continuation regret <0.04 misses,
reversal fraction <6e-5) at capacities 32/128 -- this census's incremental
value is removing sampling uncertainty entirely (full population: 787,762
decisions, exactly matching the canonical dataset's documented decision
count) and extending coverage to capacities 64 and 256, which have never
been tested under any continuation policy.

## Population

787,762 total decisions (verified by cheap O(n) enumeration, matching the
canonical SIGMOD-scale dataset's documented `787,762 decisions` per
horizon exactly) x 3 horizons = 2,363,286 decision-horizon units, each
evaluated under LRU (baseline) and MRU (the only alternative -- no random,
SIEVE, FIFO, or blind_oracle).

## Streaming design (never materializes candidate-level rows)

`census_lib.compute_compact_decision_record()` computes LRU and MRU
candidate losses in local variables, derives the compact tie-aware summary
(optimal-set sizes/intersection/union/Jaccard, pairwise taxonomy, Kendall
tau-b, cross-continuation regret, all-tied flags), and returns only that
summary -- the per-candidate loss dictionaries go out of scope and are
never written to disk. One compact JSON line per decision-horizon, not one
line per candidate.

## Checkpointing

One file per (family, capacity, horizon) chunk under `outputs/<RUN_ID>/chunks/`.
A chunk is marked complete only via a `.done` sidecar (expected count +
SHA256) written after every decision in that chunk succeeds. On resume,
any malformed/truncated trailing line (e.g. from a killed process) is
detected, the file is rewritten to drop it (never left as permanent
garbage), and only the specific missing decisions are recomputed -- never
a blind full-chunk retry, never a silently-skipped failure.

## Validation before launch

- 19 unit/integration tests pass, including a synthetic checkpoint/resume/
  malformed-line-repair smoke test that caught and fixed a real bug (a
  naive resume would have left a truncated line permanently embedded in
  the output file).
- LRU-equivalence gate: **180,000 candidate/horizon comparisons across all
  20 (family, capacity) cells, including the never-before-audited 64 and
  256 capacities. 0 mismatches.**

## Benchmark and runtime estimate

50-decision timing samples at cap32 (~75 decisions/sec) and cap256
(~8.5 decisions/sec) confirm throughput scales ~linearly with capacity
(more candidates per decision). Extrapolated total wall time: **~11.3
hours** (population-weighted across all 20 cells) -- within the
scientifically-useful, operationally-reasonable overnight window.
Estimated compact output: **~1-1.5 GB** total (2,363,286 compact JSON
lines, no candidate-level data) -- well under any storage concern.

## What is committed vs. kept local-only

Committed: harness scripts, tests, this README, and (once available)
compact analysis/summary outputs. **Not committed**: the raw
`chunks/*.jsonl` files (git-ignored) -- kept immutable locally, referenced
by exact path/size/SHA256 once the census completes.
