# Closed-Loop Mechanistic Analysis (Trace-Only)

Investigates whether the two offline<->closed-loop discordances identified
by the linkage analysis (`analysis/closed_loop_offline_linkage_20260914/`)
-- cloudphysics/cap32 and metakv/cap128 -- can be explained using
already-existing artifacts. **No new cache-policy replay, no Tier-1/Tier-2
run, no continuation-policy experiment, no new baseline, and no simulator
invocation of any kind was performed.** Everything here is computed from
the raw processed request traces (`item_id` sequences,
`/home/soroush/projects/augmented-caching/repo/data/processed/<family>/trace.jsonl`,
read-only) and the already-frozen offline/closed-loop evidence.

## What data actually exists (inventory, answered before any calculation)

- **Per-request policy events, cache-state trajectories, eviction
  identities, candidate-choice records**: **do not exist anywhere.** The
  Tier-1 evidence (`analysis/closed_loop_tier1_evidence_20260914/`) and the
  frozen pilot (`analysis/closed_loop_pilot_20260913/`) both contain only
  aggregate per-(family, capacity, policy[, seed]) summary rows
  (`scored_requests, hits, misses, miss_ratio, evictions, runtime_sec`) --
  never a per-request hit/miss/eviction log. This was confirmed by
  inspecting every file under both directories.
- **Raw processed request traces**: exist, one 50,000-line JSONL per family,
  each line carrying `item_id` (the exact field the harness/pilot use as
  `page_id`). These ARE analyzed here, extensively -- reading a trace file
  is not a policy simulation.
- **Reuse-distance / stack-distance / working-set / frequency statistics**:
  did not exist before this task; computed here from the raw traces.
- **Because no per-request policy trajectory exists, this analysis cannot
  and does not attempt to reconstruct "what SIEVE/random actually did at
  step N"** -- it characterizes the trace itself and, for LRU only, derives
  an exact closed-form prediction (see below), which is mathematically
  possible for LRU specifically (see Section "The LRU closed-form
  identity") but not for SIEVE (visited-bit/hand state) or random
  (stochastic eviction).

## The LRU closed-form identity (the analysis's central tool)

By a classical result (Mattson et al. 1970): under an LRU cache of capacity
C that starts empty and runs continuously (exactly how Tier 1 replays each
50,000-request trace), a reference is a **hit if and only if its stack
distance is less than C**, where stack distance = the number of *distinct*
items referenced since the item's previous reference (0 if referenced
back-to-back). This is computed here via a Fenwick-tree algorithm
(`scripts/reuse_distance.py`) that never allocates a cache and never decides
a hit/miss itself -- it only counts distinct intervening items.

**This closed-form prediction was computed for all 10 Tier-1 (family,
capacity) cells and matched the actual frozen Tier-1 LRU hit counts
EXACTLY, all 10/10** (`outputs/mechanism_comparison.csv`,
`exact_match=True` throughout; enforced by
`test_mechanism_comparison_lru_prediction_matches_tier1_exactly`). This
simultaneously (a) proves the reuse-distance implementation is correct
beyond a synthetic-example sanity check, and (b) gives a rigorous,
non-simulated tool for explaining *why* LRU's hit rate is what it is in any
given cell, in terms of the trace's own reference pattern. No equivalent
closed-form exists for SIEVE or random, so those two policies are
discussed only via CONSISTENT_WITH_MECHANISM-level trace correlations, never
via an exact identity.

## Predefined metric set

Fixed and documented in `scripts/predefined_metrics.py` **before** any
result was interpreted, applied identically to all 5 families (no metric
was added or dropped after seeing which cells looked interesting): window
request count, unique-object count and ratio, compulsory/repeated fraction
(relative to the full 50,000-request trace history, not just the window),
top-1%/5%/10% frequency concentration, Shannon entropy, the full
reuse-distance distribution (median/mean/p10/p25/p75/p90) restricted to
in-window reuse events, reuse-within-32/128/beyond-128 fractions,
working-set size at scales 32/128, longest novel-reference streak,
pre-window history length, plus a cold-start-specific block (max-possible
hits in the first 32/128 requests under an unbounded cache, first-repeat
position, cumulative unique-count curve, and quarter-by-quarter repeated
fraction within the window).

## Files

- `outputs/trace_characteristics.csv` -- the full predefined metric set, one row per family.
- `outputs/reuse_distance_summary.csv` -- the reuse-distance-specific subset, standalone.
- `outputs/early_window_characteristics.csv` -- the cold-start-specific block, one row per family (all 5, for comparability, not just MetaKV).
- `outputs/mechanism_comparison.csv` -- the 10-row (family x capacity) LRU closed-form prediction vs. actual Tier-1 evidence, plus offline all-tied fraction (H=16) and closed-loop MRU-LRU gap, for the exploratory correlation.
- `outputs/correlation_summary.{csv,json}` -- Pearson r / Spearman rho of the trace-derived LRU hit rate against offline discriminativeness and closed-loop separation (pooled n=10 and per-capacity n=5).
- `outputs/cloudphysics_cap32_diagnosis.json`, `outputs/metakv_cap128_diagnosis.json`, `outputs/wiki2018_diagnosis.json` -- per-cell narrative diagnosis grounded in the tables above.
- `scripts/reuse_distance.py` -- the stack-distance algorithm (Fenwick + brute-force reference implementation).
- `scripts/predefined_metrics.py` -- the frozen metric list (documentation-as-code).
- `scripts/analyze_trace_mechanisms.py` -- primary analysis; run first.
- `scripts/independent_recheck.py` -- three independent cross-checks (Fenwick-vs-brute-force spot check on real traces, a from-scratch brute-force LRU-hit recomputation avoiding `reuse_distance.py` entirely, and a hand-rolled Pearson-r recheck).
- `tests/test_mechanistic_analysis.py` -- 17 assertions covering no-simulator-use, frozen-evidence integrity, exact window/capacity/label correctness, reuse-distance correctness on analytically known sequences, the exact-match LRU identity, wiki2018's zero-reuse-events fact, source trace hash integrity, determinism, and the independent recheck.

Reproduce with:
```sh
cd analysis/closed_loop_mechanistic_analysis_20260914
python3 scripts/analyze_trace_mechanisms.py
python3 scripts/independent_recheck.py
python3 -m pytest tests/ -v
```
