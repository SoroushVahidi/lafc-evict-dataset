# Mechanism Classification

Using exactly the four categories specified: `DIRECTLY_OBSERVED`,
`CONSISTENT_WITH_MECHANISM`, `CAUSALLY_ESTABLISHED`, `NOT_SUPPORTED`. No
category-2 finding is upgraded to category 3 rhetorically.

## DIRECTLY_OBSERVED

1. **Cloudphysics/cap32 (and cap128) is a near-zero capacity-scale-relevant
   locality regime.** Directly measured: 17.5% of window requests are
   reuses; of those, only 9.4%/25.3% fall within stack distance 32/128. The
   trace-derived predicted LRU hit rate matches the actual observed LRU hit
   rate exactly (134/8192 at cap32, 360/8192 at cap128) via the closed-form
   stack-distance identity -- this is a fact about the trace, directly
   computed, not an inference.
2. **MetaKV's scored window begins at request 0 with an empty cache and no
   leading warmup** -- re-confirmed here independently of the prior audit's
   `evictions = misses - capacity` finding, via `pre_window_history_requests
   == 0` for MetaKV and `> 0` for every other family.
3. **Wiki2018's scored window contains exactly zero reuse events.**
   Directly counted (`n_reuse_events = 0`), not estimated.
4. **The exact LRU closed-form identity holds in all 10 tested cells**
   (`mechanism_comparison.csv`, `exact_match=True` throughout) -- this is
   itself a directly observed, exactly reproducible fact, not a
   correlation.
5. **MetaKV's reuse-distance distribution has a short median (2) but a
   markedly heavy tail (p75=285, p90=580)**, distinct from MetaCDN's
   short-and-light-tailed distribution (median 3, p75 14) and Twemcache's
   long-median-heavy-tail distribution (median 490, p75 7379).

## CONSISTENT_WITH_MECHANISM

6. **MetaKV's boundary-zone reuse concentration (a ~2.6-percentage-point
   band of reuse events with stack distance between 32 and 128) is
   consistent with a policy-choice-sensitive regime** where LRU's strict
   recency ordering, SIEVE's second-chance/visited-bit ordering, and
   random's memorylessness can plausibly diverge on which marginal items
   survive -- without isolating which one actually diverged, since no
   per-request policy trajectory exists.
7. **Offline discriminativeness and closed-loop policy separation are both
   explained, to a similar degree, by the same trace-derived
   capacity-scale reuse measure** (Pearson r = -0.83 with all-tied
   fraction, +0.90 with closed-loop MRU-LRU gap, pooled n=10). Consistent
   with a common underlying cause (exploitable locality at the tested
   capacity), not proof of one, given the small n and the exploratory,
   non-pre-registered nature of this check.

## CAUSALLY_ESTABLISHED

8. **Wiki2018's exact all-policy, all-seed tie is caused by zero reuse
   events in the scored window.** This is the one item placed in this
   category, and it is justified narrowly: the argument is *deductive* (a
   hit requires a repeated reference; there are exactly zero repeated
   references; therefore hits=0 for every possible policy, not just the
   four tested), not a statistical inference drawn from correlating small
   samples. It is not being used here as a general license to claim
   causation elsewhere in this analysis -- every other finding above and
   below is intentionally kept at `DIRECTLY_OBSERVED` or
   `CONSISTENT_WITH_MECHANISM`.

## NOT_SUPPORTED

9. **"Cold start caused the MetaKV SIEVE/LRU reversal" as an isolated
   causal claim.** The cold-start property and the boundary-zone reuse
   structure are both real and both present in this one cell, but they are
   confounded -- no per-request event log exists to separate their
   individual contributions, and Q4's quarter-by-quarter analysis shows
   locality is nearly flat across the window (not obviously different
   early vs. late), which weakens rather than supports a strong
   cold-start-specific story.
10. **"SIEVE benefits from Twemcache's hot-set-plus-long-tail structure."**
    Twemcache does have the most pronounced version of this structure in
    the dataset (short `longest_novel_streak=3`, heavy-tailed reuse
    distances), but the actual outcome is the opposite of what this
    mechanism would predict (random beats SIEVE at both capacities, not
    the reverse). The data structurally has the property; the outcome
    contradicts the naive story built on it.
11. **"Random specifically retains different items than LRU at MetaKV's
    boundary zone, causing its closed-loop advantage."** No per-seed
    eviction event log exists to check this; it is indistinguishable, with
    current data, from the same generic boundary-zone argument applied to
    SIEVE (finding 6), which itself only reaches `CONSISTENT_WITH_MECHANISM`.

## Note on reviewer-facing framing

Per the task's explicit instruction, none of the following are marked
addressed by this analysis: continuation-policy dependence, citation/
related-work completeness, or manuscript presentation quality. The
mechanistic findings above bear only on: offline-labels-vs-deployed-behavior
(now characterized cell-by-cell, not just aggregate), target
discriminativeness (now linked to an independent trace-locality measure),
practical usefulness (bounded, workload-dependent guidance now exists), and
scope/limitations (the two exceptions are now characterized, one fully
explained, one honestly left as unresolved).
