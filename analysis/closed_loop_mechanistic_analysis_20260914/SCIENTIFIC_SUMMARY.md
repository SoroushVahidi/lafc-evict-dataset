# Scientific Summary: Trace-Only Mechanistic Analysis

All numbers reproducible from `outputs/*.csv`/`*.json` (see README.md for
sources/method).

## Cross-workload trace characteristics (predefined metrics, all 5 families)

| Family | Split | Unique/req ratio | Repeated frac | Reuse-dist median | p75 | Reuse<=32 | Reuse<=128 | n_reuse |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| cloudphysics | test | 0.883 | 0.175 | 869.5 | 3343 | 0.094 | 0.253 | 1432 |
| metacdn | validation | 0.491 | 0.530 | 3 | 14 | 0.796 | 0.852 | 10847 |
| metakv | test | 0.548 | 0.452 | 2 | 285 | 0.574 | 0.600 | 1850 |
| twemcache | test | 0.517 | 0.921 | 490 | 7379 | 0.273 | 0.413 | 7546 |
| wiki2018 | test | **1.000** | **0.000** | -- | -- | -- | -- | **0** |

## Q1: Is cloudphysics/cap32 a meaningful failure or a near-zero-signal sign instability?

**Answer: B -- a near-zero, capacity-scale-irrelevant-locality regime, not a
meaningful contradiction.** Only 17.5% of window requests are reuses at
all; of those, only 9.4% fall within stack distance 32 (75% fall beyond
distance 128). The trace-only predicted LRU hit rate --
`0.175 x 0.094 = 1.6%` at cap32, `0.175 x 0.253 = 4.4%` at cap128 --
**exactly reproduces** the real observed LRU hit rates (134/8192=1.64%,
360/8192=4.39%). Offline H=16 regret gaps there are `MRU-LRU=-0.00266`,
`random-LRU=-0.00066` -- both tiny fractions of the family's own mean
regret scale (LRU offline optimal rate is still ~0.99+ per the target
audit) and tiny relative to the largest gaps observed anywhere in the
matrix (metacdn's MRU-LRU gap is >100x larger). **Classification:
DIRECTLY_OBSERVED** that this is a near-zero-signal regime; the offline/
closed-loop sign disagreement there is exactly what a coin-flip-scale
signal would produce, not evidence the offline supervision is broadly
unreliable.

## Q2: How exceptional is metakv/cap128 compared with the other 9 cells?

It is the only cell (of 10) where a Tier-1 policy other than LRU wins
outright in closed loop (SIEVE, 0.6982 vs. LRU 0.7290), and the only cell
where the offline<->closed-loop sign disagrees for random-vs-LRU
specifically (offline random-LRU gap = +0.00129, i.e. offline says random
is very slightly worse than LRU; closed-loop gap = -0.0151, random
noticeably better). It sits alongside cloudphysics/cap32 as one of 2 (of
10) discordant cells identified by the linkage analysis, but unlike
cloudphysics, metakv's offline signal is NOT weak in aggregate (all-tied
fraction 0.856-0.867, comparable to cloudphysics's 0.66-0.87) while its
reuse structure is markedly different (see Q3).

## Q3: What trace-level properties distinguish MetaKV from MetaCDN/Twemcache?

MetaKV's reuse-distance **median** is very short (2, comparable to
MetaCDN's 3) but its **p75 (285) and p90 (580)** are far longer than
MetaCDN's (14, 494) -- a markedly heavier tail. MetaKV's reuse-within-32
fraction (0.574) is lower than MetaCDN's (0.796), and only rises to 0.600
by distance 128 -- a narrow (2.6 percentage point, ~48 of 1850 reuse
events) "boundary zone" sitting almost exactly at the tested capacities.
Twemcache, by contrast, is bimodal in a different way: very high overall
repeat fraction (0.921) but most of that mass sits at long range (p75=7379),
so its reuse-within-32/128 fractions (0.273/0.413) are actually *lower*
than MetaKV's despite far more total reuse events (7546 vs. 1850).

## Q4: Does MetaKV's cold-start regime measurably differ from other families' warmed windows?

**Structurally, yes** (only MetaKV's window starts at request 0 -- see the
prior audit's `evictions = misses - capacity` identity, reconfirmed here).
**In terms of locality itself, only modestly.** MetaKV's
quarter-by-quarter repeated fraction across the scored window is
0.431 / 0.494 / 0.446 / 0.436 -- essentially flat, and its first repeat
occurs at window-position 1 (the second request), with 16 of the first 32
requests already possible hits under an unbounded cache. Locality is
strong from the very first requests, not something that only develops
after a warm-up period. Twemcache's control quarters (0.906 / 0.892 / 0.934
/ 0.896) are also flat but at a much higher absolute level; cloudphysics's
quarters trend downward (0.279 -> 0.157 -> 0.184). **The cold start changes
which specific window MetaKV is scored on (starting at t=0 rather than
deep in the trace) but does not, by this measure, produce an obviously
different early-vs-late locality signature within that window** -- it is a
different *placement*, not obviously a different *character* of locality.

## Q5/Q6: Is there evidence consistent with SIEVE benefiting from MetaKV's structure? Does this establish causation?

**Q5 -- consistent, not proven:** MetaKV's reuse-distance tail places a
nontrivial (~2.6 percentage point) share of reuse events right at the
32-128 capacity boundary, exactly where a recency-strict policy (LRU) and a
second-chance policy (SIEVE) can plausibly diverge on marginal eviction
decisions. This is `CONSISTENT_WITH_MECHANISM`. **Q6 -- no.** No per-request
SIEVE trajectory data exists (see inventory above), so there is no way to
observe which specific candidates SIEVE actually retained differently from
LRU at the boundary. The cold-start/no-warmup property and the
boundary-zone reuse structure are both real, independently confirmed trace
facts, but existing data cannot isolate which one (or their interaction, or
neither) caused the reversal. **This is explicitly left unresolved rather
than forced.**

## Q7: Can existing data establish why random beats LRU in the MetaKV comparison?

No stronger than Q6's answer: `CONSISTENT_WITH_MECHANISM` at best (the same
boundary-zone reasoning applies -- a policy with no recency bias at all
will, at the margin, sometimes retain a boundary-distance item LRU would
have evicted, or vice versa), but random's stochastic eviction has no
closed-form trace identity the way LRU's does, and no per-seed event log
exists to check which specific evictions differed. `NOT_SUPPORTED` for any
claim that this establishes what random specifically did differently.

## Q8: Can existing data explain Twemcache's random-vs-SIEVE ordering (random beats SIEVE, both capacities)?

Twemcache is exactly the workload with the strongest "small hot set
coexisting with a long scan" bimodal signature in this dataset (p10=3 but
p75=7379, longest_novel_streak=3 -- meaning novel items are never more than
3-in-a-row, i.e. hot references are densely interleaved with a long tail of
far-apart repeats, not clustered "scans"). **A naive reading of SIEVE's
mechanism (second-chance admission is supposed to help exactly this kind of
mixed workload) would predict SIEVE should do well here -- but the actual
Tier-1 result is the opposite (SIEVE loses to random at both capacities).**
Existing trace-only data can describe the structure but **cannot explain
the direction of the outcome**; forcing a "SIEVE benefits from bimodality"
story here would be actively contradicted by the data, not supported by it.
**Classification: NOT_SUPPORTED** for any simple hot-set-plus-scan
explanation of Twemcache's specific random-over-SIEVE ordering.

## Q9: Does wiki2018's trace locality quantitatively explain the exact all-policy tie?

**Yes, exactly and completely.** `n_reuse_events = 0` -- not "rare", zero.
Every one of the 4096 scored-window requests is a first-ever occurrence
across the entire 50,000-request trace (`unique_over_request_ratio=1.0`,
confirmed flat at 0.0 repeated-fraction in every quarter of the window
too). Since a hit requires a repeated reference to an already-resident
item, `miss_ratio=1.0` for every policy at every capacity is a **mathematical
certainty** given zero reuse events, not a statistical tendency.
**Classification: CAUSALLY_ESTABLISHED** -- justified as an exception to
the expectation that this category stay empty, because the argument here is
deductive (an existence proof from a directly counted quantity), not a
correlational inference from small n.

## Q10: "Offline supervision is most informative when the workload exhibits sufficient capacity-scale reuse and nontrivial candidate differentiation" -- supported?

**SUPPORTED**, within the limits of n=10 (5 families x 2 capacities, no
horizon pseudo-replication issue here since trace metrics don't vary by
horizon). The trace-derived LRU hit rate (an exact, capacity-scale reuse
measure) correlates with offline discriminativeness (`1-all_tied_fraction`)
at **r=-0.83 (pooled n=10), r=-0.83/-0.83 (per-capacity n=5)** (negative
because higher exploitable-reuse rate corresponds to lower all-tied
fraction, i.e. more discriminative) and with closed-loop policy separation
(|MRU-LRU| miss-ratio gap) at **r=0.90 (pooled), 0.91/0.89 (per-capacity)**.
Both offline informativeness and closed-loop separation are higher exactly
where trace-level, capacity-scale-relevant reuse is higher -- the same
underlying trace property predicts both, which is direct support for the
proposed generalizable statement. This remains an n=10, exploratory,
non-pre-registered finding (as it was in the linkage analysis), not a
large-sample-validated law.

## Mechanism classification summary

| Explanation | Classification |
|---|---|
| Cloudphysics/cap32 discordance reflects near-zero capacity-scale-relevant locality, not a genuine offline-supervision failure | **DIRECTLY_OBSERVED** (exact LRU-hit-rate match to the trace-derived prediction) |
| Wiki2018's exact all-policy tie is fully explained by zero reuse events in the scored window | **CAUSALLY_ESTABLISHED** (deductive, not statistical) |
| MetaKV/cap128's SIEVE/random advantage over LRU is related to a boundary-zone concentration of reuse distances near the tested capacities | **CONSISTENT_WITH_MECHANISM** |
| MetaKV's cold start (empty cache at t=0) contributed to the reversal | **CONSISTENT_WITH_MECHANISM** at most -- quarter-by-quarter locality is nearly flat, weakening (not ruling out) a strong cold-start-specific story |
| SIEVE benefits from Twemcache's hot-set-plus-long-tail structure | **NOT_SUPPORTED** -- the actual outcome (random beats SIEVE) contradicts the naive mechanistic expectation |
| Offline discriminativeness and closed-loop separation share a common trace-locality cause | **CONSISTENT_WITH_MECHANISM**, exploratory, n=10, both directions r>=0.83 |
| Cold start CAUSED the SIEVE/LRU reversal (isolated causal claim) | **NOT_SUPPORTED** -- no per-request event data exists to isolate this from the boundary-zone reuse explanation, and the two are confounded in this one cell |
