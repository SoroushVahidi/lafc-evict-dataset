# Family / Capacity / Horizon Matrix and Sampling Design

## Families: all 5 required

Each family plays a distinct, non-redundant role already established by
prior analyses — none can be dropped without losing a regime:

| Family | Role | Evidence source |
|---|---|---|
| MetaCDN | Strong-signal / strong-agreement regime | Linkage analysis: all-tied fraction 0.008-0.012 at H16; largest offline+closed-loop MRU-LRU gaps |
| Twemcache | Strong-signal / strong-agreement regime, different reuse structure than MetaCDN | Mechanistic analysis: bimodal hot-set+long-tail reuse, high total reuse volume |
| CloudPhysics | Weak-signal / near-zero-locality-at-capacity-scale regime | Mechanistic analysis: only 9.4%/25.3% of reuses within stack distance 32/128 |
| MetaKV | Residual exception (SIEVE/random beat LRU at cap128) | Linkage + mechanistic analyses: only cell with a closed-loop policy-ordering reversal |
| wiki2018 | Degenerate negative control | Mechanistic analysis: exactly zero reuse events in the scored window |

## Capacities: 32 and 128 (not the full 32/64/128/256 canonical range)

**Recommendation: {32, 128} only**, for the primary design. Justification:

1. Matches Tier 1's own tested capacities exactly, so continuation-sensitivity
   findings can be directly compared, cell-for-cell, against the
   already-validated closed-loop and linkage findings at the *same*
   capacities — the four established regimes (strong/weak/exception/
   degenerate) were characterized at these two capacities specifically.
2. The offline target-discriminativeness audit's own "most discriminative
   regimes" table is dominated by capacity 32 (with one capacity-64 row);
   capacity 256 never appears among the most-discriminative regimes.
   Capacity 128 is the natural second point (MetaKV's exception is
   specifically at cap128).
3. Extending to 64/256 is a valid, clearly-scoped future extension if
   reviewers demand a fuller capacity sweep, but is not necessary to answer
   the core reviewer question with the smallest defensible design.

## Horizons: all three, H ∈ {4, 8, 16}

Recommendation: **test all three**, per the task's own strong scientific
argument (continuation effects may compound with horizon) — verified
feasible below (Section "Runtime feasibility check"). Unlike the linkage
analysis's RQ-CL4 (which had to guard against horizon pseudo-replication
because closed-loop had no horizon dimension), here **every metric is
computed per horizon on the same underlying decision sample**, so no
pseudo-replication concern arises — horizon is a genuine, independently
interesting axis of this experiment, not a repeated measurement of a
horizon-blind quantity.

## Sampling frame (fixed before results; grounded in existing artifacts)

The canonical 277,995,072-row release is not present locally
(`.gitignore`d, per the target-discriminativeness audit). Full enumeration
at that scale is unnecessary for a robustness/sensitivity characterization
and is explicitly not required by the task. Instead:

**Sampling frame** = baseline-LRU eviction decisions produced by replaying
each family's already-verified, hash-checked local 50,000-request processed
trace (`/home/soroush/projects/augmented-caching/repo/data/processed/<family>/trace.jsonl`
— the exact same files Tier 1 used and the audit's `test_source_trace_hashes_recorded_and_match_design`-style
check already validated) through the canonical LRU-prefix logic, at
capacities {32, 128}. This reproduces the same decision-generation process
as the canonical pipeline (same trace, same LRU prefix, same forced-eviction
mechanics) without requiring the multi-hundred-GB full release or HPC
access — a legitimate, artifact-grounded sampling frame, not an invented
substitute dataset.

**Stratification variables** (all computed from baseline-LRU information
only — never from the alternative-continuation results being tested, per
the explicit "do not condition sampling on alternative-continuation
results" constraint):

- family (5 levels)
- capacity (2 levels)
- baseline-LRU discriminativeness at that decision: `all_tied` (regret_max
  under LRU == 0 across all candidates) vs. `discriminative` (regret_max >
  0) — a purely LRU-side computation.
- candidate_count bucket (`== capacity` for cap32 decisions once the cache
  is full; coarse low/mid/high buckets for cap128 to keep strata balanced,
  since candidate_count there can range up to 128).

**Sample size**: **500 decisions per (family, capacity) stratum**, split
proportionally between `all_tied` and `discriminative` sub-strata as they
naturally occur in that (family, capacity) population (not forced to
50/50, to preserve population-representativeness) — 5 × 2 × 500 = **5,000
decisions total**, each evaluated at all 3 horizons and under both
alternative continuations (plus the LRU reproduction check). This is
"small enough to be cheap, large enough to be informative": 500 per
stratum gives a Jaccard-overlap or pairwise-agreement estimate a standard
error on the order of a few percentage points even for a moderately
skewed binary-ish quantity, adequate for a first robustness
characterization (not for detecting subtle sub-1%-level effects, which is
appropriately out of scope for a "smallest defensible" design).

**Additionally**: a **labeled, separate diagnostic oversample** of 100
decisions per (family, capacity) drawn specifically from the highest-regret-
magnitude decile under LRU (the "hard" tail the target-discriminativeness
audit already identified as rare-but-real, e.g. `random regret ≥ 0.5`
cases concentrated in twemcache/cloudphysics at cap32/H16) — reported
**separately**, never pooled into the population-representative 5,000-
decision estimate, exactly as the brief requires.

**Determinism**: exact decision IDs (`trace_name, capacity, request_index`)
and the sampling RNG seed must be recorded and committed alongside any
future run's provenance, before any continuation-policy computation is
performed on them — sampling must be fully reproducible and fixed prior to
seeing any alternative-continuation result.

## Runtime feasibility check (informs Section above, not a promise)

Per decision, per horizon, per continuation policy: `candidate_count`
independent rollouts of ≤`H≤16` steps each. Worst case (cap128,
candidate_count≈128): ~128×16 = 2,048 simple step-operations per
(decision, horizon, continuation). Total for the primary 5,000-decision
sample: `5,000 × 3 horizons × 2 continuations × ~2,048 ≈ 6.1×10^7`
step-operations — comfortably sub-minute in pure Python on a single core
(see `RUNTIME_ESTIMATE.md` for the full estimate including the random
continuation's seed multiplier). This confirms testing all 3 horizons and
5,000 decisions is feasible without needing to trim the matrix for cost
reasons.
