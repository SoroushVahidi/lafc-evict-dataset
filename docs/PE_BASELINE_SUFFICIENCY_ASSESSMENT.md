# Baseline Sufficiency Assessment

Status: NOT_PRESENT prior to this task as a standalone document (the
question was touched on implicitly in the production design's Tier 2
gating language but never assessed against the manuscript's actual RQs).
**No baseline was run, added, or modified by this task.** This is a
classification exercise only.

## Current baselines in the closed-loop evidence chain

LRU, MRU, random (20 CRN seeds), SIEVE — all four already executed at
Tier-1 scale (5 families x 2 capacities, `analysis/closed_loop_tier1_evidence_20260914/`).

## Assessment against RQ1-RQ5

- **RQ1 (informativeness/discriminativeness)**: does not require a
  closed-loop baseline at all — it is an offline-target property. Current
  evidence sufficient. Classification: **NOT_NEEDED_FOR_CURRENT_FRAMING**.
- **RQ2 (offline<->closed-loop correspondence)**: requires policies with
  both an offline counterpart (LRU, MRU, random) and a closed-loop
  replay — exactly what Tier-1 provides. SIEVE is closed-loop-only (no
  offline counterpart) and is correctly excluded from the correspondence
  claim itself (ledger C5), while still being useful as a closed-loop
  reference point (e.g., the MetaKV/cap128 exception, ledger C8).
  Classification: **NOT_NEEDED_FOR_CURRENT_FRAMING** — adding a fifth
  policy would not change what RQ2 is asking.
- **RQ3 (workload/capacity/horizon dependence)**: same four policies,
  applied across the existing 10 cells x 3 horizons, are sufficient to
  characterize dependence; more policies would add breadth but not answer
  the dependence question differently. Classification:
  **NOT_NEEDED_FOR_CURRENT_FRAMING**.
- **RQ4 (continuation-policy robustness)**: this RQ is about label
  robustness to the *continuation* assumption (LRU/MRU/random-mean as
  continuation policies within label construction), which is a distinct
  axis from closed-loop policy baselines. No additional closed-loop
  baseline is relevant here. Classification: **NOT_NEEDED_FOR_CURRENT_FRAMING**.
- **RQ5 (practical guidance)**: synthesis of RQ1-RQ4; no new baseline
  changes what guidance follows from existing results.
  Classification: **NOT_NEEDED_FOR_CURRENT_FRAMING**.

## Learned-policy baseline (`evict_value_v1`, Tier 2)

Explicitly **not** run and **not** authorized by this task ("DO NOT
AUTOMATICALLY ADD BASELINES... No experiment may be launched from this
task"). If a future, separately-approved task decides to pursue it:

- Which exact claim would require it: a claim that LAFC-Evict's learned
  supervision can be *turned into* a closed-loop-competitive policy, not
  merely that the offline labels correspond to closed-loop behavior
  (RQ2, already answered without it).
- Which reviewer concern it would resolve: none of the 14 items in
  `PE_REVIEWER_CONCERN_CROSSWALK.md` require it — item #2 ("insufficient
  meaningful evaluation") is already ADDRESSED by the LRU/MRU/random/SIEVE
  Tier-1 evaluation; no reviewer concern in that crosswalk asks
  specifically for a learned-policy closed-loop result.
- Why current baselines cannot answer that specific (different) claim:
  LRU/MRU/random/SIEVE are all fixed, non-learned heuristics; only a
  trained policy can test whether the offline labels are *actionable* for
  training, as opposed to merely *descriptive* of relative candidate
  quality. This is a genuinely different question from any of RQ1-RQ5 as
  currently scoped.
- Classification: **OPTIONAL** — worth stating in Limitations/Future Work
  as a natural next step (the frozen closed-loop pilot already showed a
  learned Twemcache policy beats random/SIEVE but loses to LRU, and
  MetaCDN learned evaluation remains blocked on independent test chunks —
  carried forward from the prior handoff, not re-investigated here), but
  **not** required before this Performance Evaluation submission given the
  current RQ framing, which is explicitly about the offline-label/
  closed-loop relationship rather than about producing a superior learned
  policy.

## ARC/LIRS or other additional heuristic baselines

Not evaluated against any RQ above because none of RQ1-RQ5 asks a question
that LRU/MRU/random/SIEVE cannot already answer — ARC and LIRS are more
sophisticated recency/frequency heuristics whose addition would broaden
"how good can a heuristic get" (a different, and currently out-of-scope,
question) rather than sharpen the offline/closed-loop correspondence or
continuation-robustness questions this manuscript is organized around.
Classification: **NOT_NEEDED_FOR_CURRENT_FRAMING**. Per instruction, ARC/
LIRS are not run in this task regardless of classification.

## Overall

**ADDITIONAL_BASELINE_REQUIRED: NO**, under the current RQ1-RQ5 framing.
If a future revision of the RQs (e.g., in response to a reviewer round)
explicitly asks whether LAFC-Evict labels can train a closed-loop-superior
policy, Tier 2 becomes REQUIRED_BEFORE_SUBMISSION at that point, but not
before — and even then only as a separately authorized, separately
launched task.
