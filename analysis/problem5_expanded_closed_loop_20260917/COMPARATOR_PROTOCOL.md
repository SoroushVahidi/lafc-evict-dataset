# Problem 5 Phase 2: pre-specified expanded comparator set

Date: 2026-09-17, written and committed BEFORE any expanded-policy execution
or outcome is observed (no results exist yet at commit time; see git log for
this file's commit relative to the results commit).

## Objective

Add a small, principled, representative set of stronger cache-replacement
baselines to the existing Tier-1 closed-loop protocol
(`analysis/closed_loop_production_tier1_20260913/`), to test whether the
manuscript's closed-loop conclusions (LRU best in 9/10 cells, MRU worst
everywhere, metakv/cap128 the one exception) are an artifact of a narrow
LRU/MRU/random/SIEVE comparator set.

## Pre-specified policy set (chosen before seeing any expanded-policy result)

1. **ARC** (Adaptive Replacement Cache) -- adaptive recency/frequency
   representative. Self-tuning balance between recency and frequency lists;
   no hyperparameters to choose.
2. **LIRS** (Low Inter-reference Recency Set) -- reuse-distance /
   inter-reference-recency representative. No hyperparameters to choose.
3. **S3-FIFO** -- modern lightweight FIFO-family representative. Uses the
   algorithm's own published default ratios
   (`small_size_ratio=0.1`, `ghost_size_ratio=0.9`, `move_to_main_threshold=2`);
   these are NOT fit to any LAFC-Evict trace.
4. **W-TinyLFU** (optional fourth, included) -- modern frequency-sketch
   admission representative, paired with a segmented-LRU main cache. Its
   admission logic is fully bundled inside the library's own `WTinyLFU`
   class, so it can be evaluated fairly under the exact same protocol as the
   others without ad hoc admission wiring.

All four are implemented via `libcachesim` (see `IMPLEMENTATION_INVENTORY.md`
for the reuse-vs-reimplement decision) and are **deterministic** -- none use
randomness in their eviction/admission decisions, so no seed averaging is
required for them (unlike the existing `random` Tier-1 policy).

Rejected candidates and why (decided now, not after seeing results):

- **CLOCK / CLOCK-Pro**: available in the same library, but rejected from
  this *small* set because it is primarily a low-overhead approximation of
  LRU/LIRS-like recency; with ARC (adaptive) and LIRS (recency-distance)
  already included, CLOCK would add limited new qualitative signal for one
  more policy slot. Documented here, not silently dropped.
- **Plain TinyLFU (no admission-only variant)**: not exposed as a
  standalone class in `libcachesim` distinct from `WTinyLFU`; W-TinyLFU is
  the form the library validates, so it is used instead of assembling an ad
  hoc admission-only wrapper.
- **LFU**: already implemented and tested in the `augmented-caching` repo
  (`lafc.policies.lfu.LFUPolicy`) for the Tier-2/learned-closed-loop work,
  but deliberately NOT added here -- it is a frequency-only baseline with no
  adaptive or recency-distance mechanism, and adding it would grow the set
  past "approximately three (+1)" without adding a qualitatively distinct
  policy family beyond what ARC/LIRS/S3-FIFO/W-TinyLFU already cover.

This is a small, non-exhaustive set by design (per the task's explicit
instruction not to turn this into an exhaustive cache-algorithm benchmark).

## Exact protocol re-used unchanged from Tier 1

Every value below is copied verbatim from
`analysis/closed_loop_production_tier1_20260913/scripts/tier1_core.py`
(`FAMILY_CONFIG`, `FAMILIES`, `CAPACITIES`) -- Problem 5 does not redefine or
re-derive any of it:

- Families: cloudphysics, metacdn, metakv, twemcache, wiki2018 (same 5).
- Capacities: 32, 128 (same 2; Tier 1's capacities only -- Problem 5 does not
  add capacity 64/256, which are long-horizon-only in this manuscript).
- Same trace files, same expected SHA256 hashes, same scored windows per
  family (including the metacdn validation-window caveat and the metakv
  no-leading-warmup caveat), same 50,000-request full-trace replay per
  family with only the scored window's requests counted.
- Existing LRU/MRU/random/SIEVE numbers are **not** recomputed; the frozen
  `analysis/closed_loop_tier1_evidence_20260914/` evidence is reused
  byte-for-byte as the basis for comparison.

## New executions

4 new deterministic policies x 5 families x 2 capacities = 40 new executions
(no seeds needed; see above). This is added to, not merged destructively
with, the existing 230-execution Tier-1 run.

## Runtime expectation

Each new policy replay is a single 50,000-request sequential pass per family
(same trace length as existing Tier-1 policies, which completed all 230 runs
in well under a minute end-to-end per `tier1_run.log`). 40 additional
executions of the same trace length are expected to complete in well under
Phase 5's "few minutes" synchronous-execution threshold; if Phase 3 smoke
timing contradicts this, Problem 5 will move production to Wulver per Phase 5
instead of silently running it on a login node for hours (not expected).

## Change log discipline

This file is committed before the production run in Phase 4 and is not
edited afterward to match observed results. Any post hoc protocol change
would be recorded as a new dated addendum, not a silent edit.
