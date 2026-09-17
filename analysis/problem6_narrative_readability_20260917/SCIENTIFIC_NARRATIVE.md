# Problem 6 Phase 2: intended scientific narrative

Verified against the manuscript as read in Phase 1 (not assumed from the
task's structural guide). Each sentence below is checked against a specific
section/number before being adopted as the target story.

1. Papers on learned cache eviction are hard to compare because each one
   derives its own supervision from raw traces, so a reported improvement
   is often not attributable to the policy alone. *(Section 2, opening
   paragraph — verified as written, not changed.)*

2. LAFC-Evict fixes the label-construction half of that problem: for every
   full-cache-miss decision, it computes, for each candidate victim, how
   many additional misses occur over the next $H$ requests if that
   candidate — and only that candidate — had been evicted. *(Sections 2 and
   4, verified.)*

3. This label is frequently tied: across the full canonical dataset, 67.66%
   of decisions have every candidate exactly tied, and no audited decision
   has a single strictly-best candidate. *(Section 8, verified — the
   manuscript's own number, not an approximation.)*

4. High tie mass does not mean the benchmark is useless, but it does mean
   raw accuracy/optimal-rate is the wrong headline metric: a uniform-random
   guess already lands in the optimal set 99.12% of the time, almost
   entirely because so many decisions are trivially tied. *(Section 8,
   verified.)*

5. An informativeness-stratified re-analysis shows the benchmark is
   conditionally, not uniformly, discriminative: in decisions with positive
   expected random regret, LRU-like and tie-aware selectors clearly separate
   from random and from weaker pointwise learned models; in all-tied
   decisions, correctly, nothing separates. *(Section 8 (Problem 3 result),
   verified.)*

6. Longer horizons reveal more distinctions on the identical population of
   decisions — informativeness rises monotonically for every one of
   787,762 matched decisions from $H=16$ to $H=128$ — but degeneracy
   persists: more than half of decisions are still all-tied at $H=128$.
   *(Section 8 (Problem 4 result), verified.)*

7. Swapping the label's continuation assumption (LRU) for MRU or random
   barely changes which candidate is optimal, at both a sampled and a
   full-population scale; actual closed-loop replay of LRU, MRU, random,
   and SIEVE shows offline and closed-loop policy orderings agree in most,
   not all, informative regimes, with two identified exceptions. *(Sections
   8c and 8e, verified.)*

8. Adding three more real policies (ARC, LIRS, S3-FIFO) under the identical
   closed-loop protocol does not overturn the offline$\leftrightarrow$
   closed-loop correspondence, but it does correct an earlier overstatement:
   LRU no longer wins outright in nearly every cell once the comparator set
   is broadened, though it remains near-best almost everywhere. *(Section
   8b, Problem 5 result, verified.)*

9. LAFC-Evict is therefore useful as a reproducible, regime-aware benchmark
   surface for studying candidate-level eviction supervision — not as a
   universal target, not as evidence that a learned selector will improve
   closed-loop caching, and not as an eviction policy itself. *(Sections 8f,
   9b, 9, and 11 all state variants of this; Phase 5/6 will keep one full
   statement and cross-reference the rest.)*

## Verification notes

- All nine points check out against the manuscript's own numbers; none
  required inventing or approximating a value.
- Point 9 is currently stated three separate times, in three sections, with
  small wording variations (8f "regime-conditioned comparison", 9b "position
  ... is that the correspondence itself ... is the contribution", 11
  "supports concrete, scope-limited guidance"). This is the single largest
  repetition cluster in the paper; see `REPETITION_AUDIT.md`.
- The task's structural guide (steps 1-9 given in the Problem 6 prompt)
  matches this manuscript closely, with two adjustments made after
  verification: (a) the guide's step 3 ("many decisions are genuinely tied
  or weakly informative") is stated more precisely above using the actual
  67.66%/99.12% numbers rather than left qualitative; (b) the guide's step 6
  ("longer horizons monotonically reveal additional distinctions") is
  upgraded from a general claim to the manuscript's actual, stronger,
  literally-monotone-per-decision finding, which is more precise and should
  be used in the rewrite instead of a vaguer paraphrase.
