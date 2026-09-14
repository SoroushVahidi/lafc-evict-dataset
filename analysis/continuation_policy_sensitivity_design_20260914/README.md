# Continuation-Policy Sensitivity: Design Only

**No experiment was launched. No label was regenerated. No frozen evidence
was modified.** This directory is design/feasibility documentation only,
produced from read-only inspection of the label-generator source code
(secondary repository) and the already-frozen offline/closed-loop/linkage/
mechanistic evidence (this repository).

## Files

- `POLICY_STATE_AUDIT.md` — the load-bearing question: for each of
  LRU/MRU/random/SIEVE, is its required continuation state actually
  recoverable from an LRU-generated prefix? (MRU and random: yes,
  trivially. SIEVE: no — excluded from the primary design, not for
  convenience.)
- `DESIGN.md` — exact current generator semantics, prior continuation work
  found (substantial, none of it canonical-scale), the reviewer question
  as it actually exists in this repository (no verbatim quote found),
  pre-registered H_CONTINUATION and success-criterion definitions, primary/
  secondary research questions, tie-aware metric definitions (including the
  cross-continuation regret metric), the mandatory stratified-reporting
  requirement, the random-continuation seed design, the implementation
  approach (a ~6-line additive change to an already-existing, non-canonical
  module), the correctness pilot, and the blocking LRU-reproduction gate.
  (Metric definitions are consolidated here rather than in a separate
  METRICS.md, since `DESIGN.md`'s Sections 6-7 already cover them fully
  without duplication.)
- `MATRIX.md` — family/capacity/horizon scope and justification, and the
  decision-sampling design (stratified, seeded, fixed before results, with
  a separately-reported diagnostic oversample).
- `VALIDITY_GATES.md` — every gate a future implementation must satisfy,
  the blocking LRU-reproduction gate first.
- `RUNTIME_ESTIMATE.md` — analytic runtime/storage estimate grounded in
  this project's own already-measured timing references (Tier-1's ~24s
  full run, the target-discriminativeness audit's >8-hour HPC reference
  point for full-population work) concluding local workstation is
  adequate; Wulver is not needed for this design.

## One-paragraph summary

The canonical LAFC-Evict label generator (`evict_value_wulver_v1.py` /
`_simulate_lru_misses`, in the secondary repository) hardcodes LRU as the
continuation policy via a bespoke inline `OrderedDict` replay. MRU and
random continuations are exactly recoverable from the same LRU-tracked
recency state with zero new tracked state; SIEVE is not, because its
required visited-bit/hand-pointer state never existed in an LRU-generated
prefix. A substantial but non-canonical prior exploration of alternative
continuations already exists in the secondary repository (a generalized,
pluggable-continuation rollout module, a toy-scale ablation script, and a
frozen-with-no-results causal-ablation protocol on a different branch for a
different research question) — none of it constitutes evidence at LAFC-
Evict's actual scale. This design proposes the smallest defensible study:
MRU (primary, deterministic) and random (secondary, CRN-seeded) continuation,
tested against a seeded, stratified sample of 5,000 real baseline-LRU
decisions (all 5 families, capacities {32,128}, horizons {4,8,16}), using
tie-aware metrics (optimal-set Jaccard, tie-aware pairwise concordance,
Kendall tau-b, and a cross-continuation regret measure), reported at four
mandatory stratification levels specifically to prevent wiki2018-style
trivial ties from manufacturing fake robustness. Estimated cost: low
minutes on a local workstation, no HPC required. A blocking LRU-reproduction
gate must pass before any comparison is trusted.
