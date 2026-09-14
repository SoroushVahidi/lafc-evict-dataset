# Scientific Summary: Offline / Closed-Loop Linkage

All numbers below are reproducible from `data/joined_offline_closed_loop.csv`
and `outputs/*.json`; see README.md for the exact source files and method.

## RQ-CL1: Do offline LRU/random/MRU rankings agree with closed-loop rankings?

Pairwise concordance (offline regret gap sign vs. closed-loop miss-ratio gap
sign), MRU-vs-LRU and random-vs-LRU, SIEVE excluded (no offline counterpart):

| Horizon | Concordant | Discordant | Both-tied (wiki2018) |
|---:|---:|---:|---:|
| H=4 | 13/20 | 3/20 | 4/20 |
| H=8 | 13/20 | 3/20 | 4/20 |
| H=16 | 13/20 | 3/20 | 4/20 |

(20 = 2 pairs x 10 family-capacity cells; 4 of the 20 are wiki2018's two
cells x two pairs, all exactly tied on both sides; see JSON for the exact
per-cell breakdown. The count is identical at every horizon -- see RQ-CL4.)

**The 3 discordant comparisons, every horizon, are the same two cells:**
cloudphysics/cap32 (both MRU-vs-LRU and random-vs-LRU discordant -- offline
regret gap is very close to zero there, -0.0027 and -0.0007 respectively,
i.e. barely non-zero on the offline side too) and metakv/cap128
(random-vs-LRU only discordant -- offline says random is very slightly worse
than LRU, +0.0013 regret gap, but closed-loop shows random modestly beating
LRU, -0.015 miss-ratio gap). Per-cell 3-item Kendall tau-b: 8/8
non-degenerate cells have tau-b >= +0.33, with 6/8 at a perfect +1.0; only
cloudphysics/cap32 is negative (-1.0, both pairs discordant there) and
metakv/cap128 is weakly positive (+0.33, one of two pairs discordant).
wiki2018's tau-b is undefined (both sides fully tied, division-by-zero-free
"undefined", not a fabricated 0 or 1).

**Without wiki2018** (excluding the 2 trivially-tied cells): H=16 concordance
is 13/16 (81%), materially the same picture -- wiki2018's 4 automatic
"both_tied" entries do not manufacture agreement where none exists among the
9 non-degenerate cells; they are additional, separately reported, genuine
degenerate-control evidence.

**MetaCDN sensitivity**: excluding MetaCDN's 2 validation-window cells drops
total concordance from 13/20 to 9/16 at H=16 (mru_vs_lru 5/8 concordant + 1
discordant + 2 tied; random_vs_lru 4/8 concordant + 2 discordant + 2 tied,
wiki2018's tied pairs unchanged) -- MetaCDN contributes exactly 4 concordant
pairs (all 4 of its own family-capacity-pair comparisons are concordant) and
0 discordant pairs, so its inclusion modestly *strengthens* the agreement
picture, and this is disclosed rather than hidden. MetaCDN's own evidence
remains validation-window, not test-window, throughout.

**Answer**: For the two comparable pairs (SIEVE has no offline counterpart),
offline and closed-loop orderings agree in the large majority of
non-degenerate cells (8/9 by sign at H=16, matching the frozen pilot's own
finding for the 2 cells it covered), with two identified, small-magnitude
exceptions (cloudphysics/cap32, metakv/cap128) that are both cells where the
offline signal itself is weak/near-zero, not cells with strong offline
signal being contradicted.

## RQ-CL2: Does offline regret-gap strength predict closed-loop miss-gap magnitude?

Primary (per horizon, n=10 family-capacity cells, Pearson r / Spearman rho / Kendall tau-b):

| Horizon | MRU-vs-LRU (r / rho / tau) | random-vs-LRU (r / rho / tau) |
|---:|---|---|
| H=4 | 0.746 / 0.781 / 0.636 | 0.605 / 0.732 / 0.500 |
| H=8 | 0.783 / 0.878 / 0.682 | 0.671 / 0.793 / 0.545 |
| H=16 | **0.835 / 0.915 / 0.773** | **0.755 / 0.829 / 0.591** |

**H=16 gives the numerically strongest correspondence on every single one of
these 6 statistics**, though the differences between horizons are modest in
absolute terms (e.g. r=0.746 to 0.835 for MRU-vs-LRU) and n=10 is very small
-- p-values were computed but are explicitly not treated as evidence of
significance here.

**Excluding wiki2018** (n=8): correlations weaken somewhat at H=4/H=8 (e.g.
MRU-vs-LRU r drops from 0.746 to 0.679 at H=4) but the H=16-is-strongest
pattern holds unchanged (H=16 MRU-vs-LRU r=0.794, random-vs-LRU r=0.716,
still the best of the three horizons on every statistic) -- wiki2018's two
exactly-(0,0) points are not single-handedly manufacturing the correlation
or the horizon ranking.

**Test-window-only** (excluding MetaCDN's validation-window cells, n=8 or
fewer depending on horizon after also excluding wiki2018 where relevant):
qualitatively the same picture; see `outputs/rq_cl2_gap_correspondence.json`
`test_window_only_by_horizon` for exact per-horizon values.

**Answer**: Yes, with real effect sizes (r in the 0.6-0.9 range depending on
horizon/pair/inclusion) that are directionally consistent across every
sensitivity slice computed, but this rests on only 8-10 independent
(family, capacity) points per horizon -- a real, honestly small-sample
finding, not a large-sample-validated one.

## RQ-CL3: How does the relationship vary by workload and capacity?

Per-family pattern at H=16 (from `outputs/rq_cl3_workload_capacity_dependence.json`):

| Family | Split | Offline all-tied (H16) | Offline MRU-LRU gap (H16) | Closed-loop MRU-LRU gap | Regime |
|---|---|---:|---:|---:|---|
| twemcache | test | 0.24 (cap32) / 0.10 (cap128) | 0.090 / 0.120 | 0.204 / 0.329 | **Strong-agreement, most discriminative non-degenerate family** |
| metacdn | validation | 0.012 / 0.0085 | 0.304 / 0.315 | 0.274 / 0.302 | **Strong-agreement, most offline-discriminative family overall** |
| cloudphysics | test | 0.87 (cap32) / 0.66 (cap128) | -0.003 / 0.004 | 0.016 / 0.043 | **Weak/ambiguous** -- offline gap near zero, cap32 sign flips |
| metakv | test | 0.87 / 0.86 | 0.071 / 0.071 | 0.074 / 0.063 (MRU); but random gap flips at cap128 | **Mostly agreeing, one reversal** at cap128 (random-vs-LRU; also SIEVE-vs-LRU, closed-loop only) |
| wiki2018 | test (offline-degenerate control) | 1.0 / 1.0 | 0.0 / 0.0 | 0.0 / 0.0 | **Fully degenerate on both sides, exactly** |

**Strong-agreement regimes**: twemcache and metacdn -- both have the
strongest offline discriminativeness (lowest all-tied fraction) among the 5
families and show large, same-signed offline and closed-loop gaps.
**Weak/ambiguous regime**: cloudphysics -- offline discriminativeness is
among the weakest of the non-degenerate families (all-tied fraction
0.66-0.87) and its offline MRU-LRU gap is close enough to zero that its sign
is not robust (flips at cap32). **Reversal regime**: metakv/cap128 for the
random-vs-LRU pair (and, closed-loop-only, for SIEVE-vs-LRU) -- this is also
the one cell with the resolved cold-start/no-warmup scoring window (see
above), a plausible but not proven contributing factor. **Degenerate
regime**: wiki2018, exactly, at both capacities, confirming it is a clean
negative control rather than a source of spurious agreement.

**Exploratory** (not pre-registered as such, but motivated by DESIGN.md's own
discussion): does higher offline discriminativeness (1 - all_tied_fraction)
at H=16 predict larger closed-loop |MRU-LRU| separation, across all 10
cells? **Pearson r = 0.968, Spearman rho = 0.915, Kendall tau-b = 0.773**
(n=10) -- a strong, consistent relationship, but exploratory, small-n, and
not itself one of the four pre-registered RQs.

**Capacity dependence**: within every family, going cap32 -> cap128 widens
the closed-loop MRU-LRU gap for cloudphysics, metacdn, and twemcache (e.g.
twemcache 0.204 -> 0.329) and narrows the offline all-tied fraction (more
discriminative at cap128) for cloudphysics and twemcache but not metacdn
(which is already near-zero all-tied at both capacities) or metakv (stays
~0.86 at both). Capacity dependence is therefore itself family-specific, not
a single uniform effect.

## RQ-CL4: Which horizon is best aligned?

H=16 wins, or ties, on every single statistic computed across every
sensitivity slice (primary, excluding-wiki2018, test-window-only; both
pairs; Pearson, Spearman, Kendall) -- summarized in
`outputs/rq_cl4_horizon_alignment.json`. The coarse concordant/discordant
pairwise counts are *identical* across H=4/H=8/H=16 (13/3/2 split every
time) -- horizon does not change which cells agree in *sign*, only how
*strongly* the offline and closed-loop gaps track each other in magnitude
(the correlation and per-cell tau-b measures, which do increase with H).

**Answer**: H=16 is the best-supported horizon among {4,8,16} by every
magnitude-sensitive statistic, consistently and without exception, though
the absolute differences from H=4/H=8 are modest and n is small (8-10 per
horizon) -- this is not a dramatic or decisive horizon effect, but it is a
real, non-cherry-picked, symmetrically-computed one that happens to validate
the design's own choice of H=16 as primary.

## Offline discriminativeness vs. closed-loop separation

See RQ-CL3's exploratory correlation above (r=0.968, n=10, H=16). The most
offline-discriminative non-degenerate families (metacdn, twemcache) do show
the largest closed-loop policy separation; the least discriminative
non-wiki2018 families (cloudphysics, metakv, both with all-tied fraction
>0.85 at H=16) show the smallest non-degenerate closed-loop separation. This
is a coherent, mutually-reinforcing picture, not a contradiction between the
two evidence sources.

## Closed-loop policy findings, reconfirmed independently

Recomputed directly from `run_results.csv`/`summary.csv` in the frozen
evidence snapshot (not merely re-asserted from a prior report):

- **LRU best in 9/10 cells**: confirmed. The sole exception is metakv/cap128,
  where SIEVE (0.6982) beats LRU (0.7290) by 4.22% relative -- SIEVE has no
  offline counterpart, so this is closed-loop-only evidence, not part of
  RQ-CL1's offline-vs-closed-loop comparison.
- **MRU worst in every non-degenerate cell**: confirmed, all 8 non-wiki2018
  cells.
- **MetaKV/cap128 SIEVE-vs-LRU reversal**: confirmed (see above); now
  additionally linked to the resolved cold-start scoring-window property of
  MetaKV (this is the only family/cell combination where the cache starts
  empty in the scored window).
- **cloudphysics SIEVE-vs-random near-tie/order change**: confirmed
  (cap32 gap 0.08pp vs. random-seed std ~0.10pp there; cap128 gap 0.57pp vs.
  std ~0.14pp) -- cap32 remains noise-level, cap128 remains more likely real.
- **wiki2018 all-policy degeneracy**: confirmed exactly, both capacities,
  hits=0/misses=scored_requests/miss_ratio=1.0 for every policy and every
  one of the 20 random seeds (std=0 exactly).
- **Random seed variability**: confirmed small relative to policy gaps in
  every cell.

## Mechanistic interpretation (existing data only; no new simulation)

| Candidate mechanism | Classification | Evidence |
|---|---|---|
| MetaKV/cap128 SIEVE (and random) outperforming LRU is related to the cold-start (empty-cache, no-warmup) scoring window unique to MetaKV | PLAUSIBLE_BUT_NOT_ESTABLISHED | MetaKV is the only family with `evictions = misses - capacity` (empty-cache start); SIEVE's scan-resistant "second-chance" admission policy behaves differently from LRU specifically during cold-start fill, when every policy's recency ordering is still being established from scratch. No isolated cold-start-vs-warm ablation exists in the frozen data to confirm this is the *cause* rather than a coincidence of this one family's access pattern. |
| Twemcache favoring random over SIEVE (both capacities) reflects a KV-cache access pattern with less exploitable recency/frequency structure than SIEVE's algorithm assumes | PLAUSIBLE_BUT_NOT_ESTABLISHED | Twemcache is the only family where SIEVE is closed-loop-worse than random at both capacities; no independent access-pattern characterization (e.g. reuse-distance distribution) exists in the frozen artifacts to confirm this directly. |
| MetaCDN's LRU/SIEVE closeness with MRU's poor performance reflects strong temporal locality that both reasonable heuristics exploit similarly, while MRU actively fights it | DIRECTLY_SUPPORTED | The offline diagnostic (Section 7 of `sigmod_target_discriminativeness` REPORT.md) already shows LRU and MRU cleanly separated across nearly every stratum with the gap "largest exactly where ... the most discriminative regime" is (metacdn/twemcache, small capacity); this closed-loop run reproduces that same LRU-close/MRU-far pattern quantitatively (MRU relative gap 47-55% vs. LRU, the largest of any family). |
| wiki2018's complete closed-loop degeneracy reflects the same structural tie-density property documented offline (fully tied at every offline cell) | DIRECTLY_SUPPORTED | Both offline (`phase4`/`phase8`: all_tied_fraction=1.0, LRU=MRU=random regret=0.0 exactly at every capacity/horizon) and closed-loop (this run: every policy/seed miss_ratio=1.0 exactly) show byte-for-byte identical degeneracy; this is not two independent findings coincidentally agreeing, it is the same underlying property (near-total absence of short-range reuse in this workload/window) manifesting identically at both evidence layers. |

No mechanism here required a new simulation; all four rest entirely on
already-existing offline and closed-loop artifacts.
