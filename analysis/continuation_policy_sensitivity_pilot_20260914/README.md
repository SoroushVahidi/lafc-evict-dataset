# Continuation-Policy Sensitivity: Correctness Pilot

**This is the pre-registered 80-decision correctness pilot only.** It is
**not** the full 5,000-decision scientific study and produces **no
scientific conclusion** about continuation-policy robustness. Its purpose
is solely to determine whether the implementation is correct enough to
authorize the full pre-registered run.

## Duplication audit (performed before any implementation)

A fresh, independent repository-wide search (git grep across every branch
of both repositories, plus inspection of the untracked
`analysis/exploratory/continuation_policy_light/` artifact already on disk)
confirmed: **zero prior instances of MRU or random used as a continuation
policy anywhere.** The only pre-existing continuation-policy work is (a)
`evict_value_v2_rollout.py`'s lru/blind_oracle/fifo support, (b) a toy-scale
ablation (4 traces, capacity 2-3, 300 requests/trace, 3 decisions --
confirmed by inspecting its actual on-disk `summary.json`), and (c) a
frozen-with-no-results causal-ablation protocol on `kbs/second-revision-science`
answering a different question (LRU-vs-learned-π1 continuation for
downstream policy iteration). **Classification: NOT_PREVIOUSLY_RUN** for
the MRU/random candidate-level comparison this pilot performs. New evidence
this pilot provides: MRU/random implemented and tested for the first time,
at real LAFC-Evict scale (not toy), with tie-aware metrics that have never
been computed anywhere before, backed by a candidate-by-candidate exact
equivalence gate against the untouched canonical generator (also never done
before for any rollout variant).

## Implementation (secondary repository)

`src/lafc/evict_value_v2_rollout.py` (branch
`experiment/continuation-sensitivity-pilot-20260914`, secondary repo,
forked from `chore/repository-polish` @ `ceb3670`) gained two additive
branches in `_choose_victim()`: `"mru"` (returns the tail of the same
recency-ordered list LRU already maintains -- zero new state) and
`"random"` (uses an `rng.choice()`, requiring `rng_seed` to be set).
`simulate_rollout_misses()` gained an `rng_seed` parameter implementing the
pre-registered common-random-numbers design (a fresh `random.Random(seed)`
per call, so the same seed value is reused across every candidate within
one decision). **`evict_value_wulver_v1.py` and `_simulate_lru_misses()` --
the canonical generator -- were never touched.** 11 new unit tests added;
12/12 relevant existing + new tests pass (1 pre-existing, unrelated
collection failure confirmed present before this change too, via a
before/after stash comparison).

## LRU equivalence gate: PASS

52,480 candidate/horizon comparisons (4,480 from the 80 frozen pilot
decisions at H=16, plus a broadening audit across all 5 families x 2
capacities x 3 horizons x ~20 additional random decisions each) between the
new `simulate_rollout_misses(..., reference_policy="lru")` path and the
untouched canonical `_simulate_lru_misses()`. **0 mismatches, max absolute
difference 0.** See `outputs/lru_equivalence_gate_result.json`.

**Canonical-release generator provenance: `GENERATOR_PROVENANCE_UNKNOWN`.**
No manifest or provenance record in this repository ties the actual
277,995,072-row historical release to a specific augmented-caching commit
SHA (`dataset_card/PROVENANCE.md` describes provenance *policy*, not a
build record; no historical `candidate_rows.parquet` sample exists locally
to check row-for-row). The equivalence gate above proves the new code path
is self-consistent with the *current* canonical function on the current
codebase -- it does **not** prove the current canonical function is
byte-identical to whatever code actually produced the historical release.
This is reported honestly as a known gap, not glossed over.

## Pilot manifest: frozen before any alternative-continuation result

`PILOT_MANIFEST.json` records the exact 80 decision IDs (20 per cell x 4
cells: twemcache/32, cloudphysics/32, metakv/128, wiki2018/32, all at
H=16), selected using **only** baseline-LRU regret/tie information (never
MRU/random results), via a seeded (`20260914`), stratified (all_tied vs.
discriminative, proportional to a 500-decision random subsample per cell --
documented as a pragmatic approximation appropriate for this small pilot,
not the full population) sampling procedure in `scripts/freeze_pilot_manifest.py`.
The manifest's own content hash is recorded inside itself.

## Results (diagnostic only -- see PILOT_ANALYSIS section of the final report for full numbers)

MRU: mean optimal-set Jaccard 0.992, 0 pairwise reversals out of 192,320
candidate pairs, mean cross-continuation regret 0.0012 misses. Random (mean
over 10 CRN seeds): mean Jaccard 0.936, 2/192,320 reversals, mean
cross-continuation regret 0.0119 misses. Random-seed variance diagnostic:
mean coefficient of variation 0.006, p90 0.030 -- comfortably under the
pre-registered 10% escalation threshold. **These numbers describe 80
decisions and must not be read as evidence about the full population.**

## Files

- `PILOT_MANIFEST.json` -- the 80 frozen decision IDs + selection metadata.
- `IMPLEMENTATION_PROVENANCE.json` -- what was changed, where, and the duplication-audit record.
- `scripts/pilot_lib.py`, `scripts/metrics.py` -- shared library and tie-aware metric implementations.
- `scripts/freeze_pilot_manifest.py` -- decision selection (run first).
- `scripts/lru_equivalence_gate.py` -- the blocking equivalence gate (run second).
- `scripts/run_pilot.py` -- the actual 80-decision MRU/random pilot run (run third).
- `scripts/validate_pilot.py` -- validity gates over a completed run directory.
- `outputs/lru_equivalence_gate_result.json` -- equivalence gate result.
- `outputs/<RUN_ID>/` -- the pilot run's candidate/decision-level results, provenance, and validity-gate outcome.
- `tests/` -- 21 passing unit tests.

## What this pilot does NOT do

Does not run the 5,000-decision primary sample or the 500-decision
diagnostic oversample. Does not escalate random seeds beyond 10 (the
variance diagnostic supports staying at 10 for the full study -- see the
final report). Does not touch Tier 1, Tier 2, the manuscript, or canonical
release semantics. Does not draw a ROBUST/CONDITIONALLY_ROBUST/SENSITIVE
scientific conclusion.
