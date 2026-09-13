# LAFC-Evict SIGMOD Target-Discriminativeness Audit

Date: 2026-09-13
Scope: evidence audit only. No manuscript claims changed, no new dataset generated, no HPC jobs launched.

## 0. Repository / data provenance (Phase 1)

- **Canonical repo**: `SoroushVahidi/lafc-evict-dataset` (local clone at
  `/home/soroush/projects/lafc-evict-dataset/repo`), **not**
  `SoroushVahidi/Augmented-caching` (that repo hosts a *different* paper — a
  KBS submission about the `evict_value_v1` eviction *policy*, currently at a
  "null result" stage per its own README. LAFC-Evict is the *dataset/
  benchmark* paper and lives in `lafc-evict-dataset`, confirmed by the
  `paper/sigmod2027/` LaTeX tree and `sigmod-*` branches in this repo).
- **Base branch for this audit**: `master` @ `fbbeedb02ffedf571cf6a08a9a7418467d857cea`
  ("Merge AWS Open Data v0.3 release-freeze preparation", 2026-09-12).
- **This audit's branch**: `analysis/sigmod-target-discriminativeness-20260913`.
- **Manuscript**: `paper/sigmod2027/latex/main.tex` (ACM SIGMOD 2027 submission).
- **Canonical SIGMOD-scale dataset** (the one the manuscript's numbers are
  drawn from): `release/lafc-evict-v0.1-open-current-contract-preserved/`
  — 277,995,072 candidate rows, 2,363,286 decision rows, 1,000,000-row
  pairwise sample, 5 trace families (`cloudphysics`, `metacdn`, `metakv`,
  `twemcache`, `wiki2018`), capacities {32, 64, 128, 256}, horizons {4, 8, 16},
  splits {train, val, test}. This matches `table_dataset_scale.tex`,
  `table_candidate_count_stats.tex`, and `table_regret_tie_stats.tex` in the
  manuscript exactly (verified below).
- **Public v0.3 release** (`release/lafc-evict-v0.3-*`, and the AWS/HF-published
  artifact): wiki2018-only, a strict subset of the family list above. **This
  audit analyzes the canonical SIGMOD-scale, multi-family dataset first, as
  instructed** — the wiki2018-only subset is analyzed only as a slice of the
  larger dataset (Section 4/8 below), never substituted for it.
- **Important caveat discovered during this audit**: the entire `release/`
  directory is `.gitignore`d (line 2 of `.gitignore`). The `decision_view.parquet`
  and `candidate_rows/` artifacts used here reproduce the manuscript's
  committed numbers exactly (see Section 1), but `pairwise_sample.parquet`
  does **not** — see the provenance flag in Section 5.

All analysis in this report reads these on-disk artifacts directly; nothing
was regenerated or resampled. Three scripts, `scripts/01-03_*.py`, produce
`outputs/*.json` and `outputs/*.csv`. Every number quoted below is traceable
to one of those files.

## 1. Reproducing the reviewer's core numbers (Phase 2)

| Reviewer claim | Reproduced value | Match |
| --- | --- | --- |
| random-victim optimal probability ≈ 0.9912 | **0.9912418754543462** | exact |
| expected random-victim regret ≈ 0.0088 misses | **0.008826200441884731** | exact |
| pairwise exact ties ≈ 878,262 / 1,000,000 | see Section 5 (provenance flag) | approximate only, from currently on-disk data |

**Methodology** (traced to `paper/sigmod2027/results/baselines/best_candidate/best_candidate_reconciliation_report.json`
and independently re-derived from `decision_view.parquet` in `scripts/01_decision_view_analysis.py`):

- This is a **population statistic over all 2,363,286 decisions**, not a
  sampled estimate — there is no seed because no sampling occurs.
- "Optimal" = membership in the tied argmin set (`regret == 0`); ties count
  as optimal for every member.
- `random_optimal_probability` = the **decision-weighted mean** (every
  decision weighted equally, regardless of candidate count) of the
  per-decision ratio `optimal_candidate_count / candidate_count`.
- `random_expected_regret` = the decision-weighted mean of each decision's
  `regret_mean` field (itself the *candidate*-weighted mean regret **within**
  that one decision).
- Regret is raw miss-count regret (`y_loss - min_y_loss` within the decision),
  not weighted or thresholded.
- We additionally confirmed the **candidate-weighted** (pooled-numerator/
  denominator) version of the same statistics, which is subtly different
  from the decision-weighted figure the reviewer quoted: 0.99438 optimal
  probability and 0.005650 mean regret (Section 2). The two are close here
  but are not the same computation, and future manuscript text should say
  explicitly which one it means.
- Spot-check: two decisions (one fully tied, one with `regret_max=4`) were
  manually recomputed straight from `candidate_rows` and matched
  `decision_view` bit-for-bit (see README "Validation performed").

## 2. Decision-level discriminativeness — population statistics (Phase 3)

All 2,363,286 decisions, both weightings (`outputs/decision_view_report.json`,
key `phase3_discriminativeness`):

| Statistic | Decision-weighted | Candidate-weighted |
| --- | --- | --- |
| n | 2,363,286 decisions | 277,995,072 candidates |
| all-tied fraction | 0.6766 | — |
| **unique-winner fraction** | **0.0000** | — |
| mean optimal-set fraction / random-optimal probability | 0.9912 | 0.9944 |
| median optimal-set fraction | 1.0 | — |
| mean random regret | 0.008826 | 0.005650 |
| p90 / p95 / p99 random regret (decision-weighted) | 0.0313 / 0.0456 / 0.0939 | — |
| P(regret ≥ 1) | 0.008758 | 0.005620 |
| P(regret ≥ 2) (exact, full candidate scan — `outputs/candidate_level_report.json`) | — | **0.0000285** |
| P(regret ≥ 3) | — | 0.0000010 |
| fraction of decisions with loss range ≥ 1 | 0.3234 | — |
| fraction of decisions with loss range ≥ 2 | 0.001468 | — |
| max observed loss range | 4.0 (out of a max possible horizon of 16) | — |
| mean / std / min / max optimal-set **size** | 116.97 / 85.12 / **16** / 256 | — |

**The single most important number in this table is `unique-winner fraction
= 0.0000`.** Across the entire canonical population of 2,363,286 decisions,
**not one** has a single uniquely-best candidate — every decision's optimal
set has at least 16 tied members. This is a stronger and more concerning
statement than the reviewer's aggregate tie rate: it says the *current*
label, as constructed (unit miss-count regret over a short finite horizon,
integer-valued in a narrow 0–16 range), structurally cannot produce a unique
winner at this scale, because too many candidates realize literally the same
integer miss count.

**Decision-weighted vs. candidate-weighted — why they differ and why it
matters**: decision-weighted statistics give a capacity=256 decision (256
candidates) exactly the same weight as a capacity=32 decision (32
candidates). Candidate-weighted statistics pool all candidate rows, so
larger-capacity decisions contribute proportionally more probability mass.
Averaging per-decision ratios is *not* the same operation as summing
numerators and denominators across decisions and then dividing — the two
happen to be close here (0.9912 vs. 0.9944) because optimal-set fraction does
not vary sharply with capacity in this dataset, but a future analysis must
not silently swap one for the other; we report both throughout.

## 3. Stratified matrix: trace_family × capacity × horizon (Phase 4)

Full 60-row matrix: `outputs/phase4_stratified_family_capacity_horizon.csv`.
Split/candidate-count breakdowns: `outputs/phase4_stratified_split.csv`,
`outputs/phase4_stratified_candidate_count.csv`.

**Most discriminative cells** (lowest mean optimal-set fraction):

| trace_family | capacity | horizon | n_decisions | mean optimal-set frac | all-tied frac | mean random regret |
| --- | --- | --- | --- | --- | --- | --- |
| twemcache | 32 | 16 | 37,849 | 0.9347 | 0.2427 | 0.0670 |
| metacdn | 32 | 16 | 29,348 | 0.9404 | 0.0122 | 0.0601 |
| metacdn | 32 | 8 | 29,348 | 0.9543 | 0.0742 | 0.0459 |
| twemcache | 64 | 16 | 34,748 | 0.9555 | 0.1444 | 0.0450 |
| twemcache | 32 | 8 | 37,849 | 0.9626 | 0.3687 | 0.0378 |

**Least discriminative cells** (all five listed have mean optimal-set
fraction = **1.0**, all-tied fraction = **1.0**, mean random regret = **0**):

All five are **`wiki2018` at every capacity/horizon combination sampled** —
`wiki2018 × {32,64,128}×{4,8,16}`. In fact (confirmed via the Phase 8 script,
Section 4 below) **every one of the 15 wiki2018 (capacity × horizon) cells is
completely non-discriminative**: LRU, MRU, and a uniform-random selector all
achieve exactly 1.0 optimal-selection rate and 0 regret in every single one.

This is the single most important structural finding for the "critical scope
distinction" in the task brief: **wiki2018 is the *only* trace family in the
public v0.3 release.** If a future benchmark claim about "eviction choice
mattering" were evaluated only against the public release, the data would
show *zero* discriminative signal, not "heavily tied but present" signal.
This is categorically different from the SIGMOD-scale, 5-family dataset,
where `metacdn` and `twemcache` at small capacity and long horizon show real,
substantial separation.

## 4. Nontrivial-subset analysis (Phase 5)

Transparent thresholds, not cherry-picked for a favorable outcome (full
numbers: `outputs/decision_view_report.json`, key `phase5_nontrivial_subsets`):

| Threshold | n decisions | % of all decisions | % of candidate rows | mean random regret | dominant strata |
| --- | --- | --- | --- | --- | --- |
| not all tied / loss range ≥ 1 (identical sets) | 764,282 | 32.34% | 33.99% | 0.0273 | metacdn 40%, twemcache 37%, cloudphysics 14%, metakv 8%, **wiki2018 0%** |
| unique optimal victim | **0** | **0%** | 0% | — | (never occurs) |
| optimal-set fraction ≤ 0.5 | 52 | 0.0022% | 0.0006% | 0.549 | cloudphysics/twemcache only, capacity=32, horizon=16 only |
| loss range ≥ 2 | 3,470 | 0.147% | 0.081% | 0.239 | twemcache 69%, metacdn 21%, capacity 32 dominant, horizon 16 dominant |
| random regret ≥ 0.1 | 16,298 | 0.690% | 0.238% | 0.172 | twemcache 76%, capacity 32 (78%), horizon 16 (77%) |
| random regret ≥ 0.5 | 285 | 0.012% | 0.003% | 0.545 | twemcache 83%, capacity 32 almost exclusively, horizon 16 exclusively |
| random regret ≥ 1 | **0** | **0%** | 0% | — | (never occurs) |

**Reading this honestly**: the "not all tied" bucket is fairly large (32% of
decisions, 34% of candidate rows) — this is the headline-favorable framing.
But its own mean random regret is still only 0.027 misses, and it never
reaches an optimal-set-fraction below ~0.97 on average. The buckets that
correspond to what a reader would actually call "eviction choice matters a
lot" (optimal-set-fraction ≤ 0.5, random regret ≥ 0.5) are **vanishingly
rare** — 52 and 285 decisions respectively, out of 2,363,286 (0.002% and
0.01%) — and **concentrated almost entirely in `twemcache`/`cloudphysics` at
the smallest capacity (32) and longest horizon (16)**. `wiki2018` and
`metakv` contribute essentially nothing to any nontrivial bucket.

**wiki2018 is entirely absent from the "not all tied" trace-family
distribution above** (0 of 764,282 decisions) — consistent with Section 3's
finding that every wiki2018 cell is perfectly tied.

## 5. Pairwise information content (Phase 7) — with a provenance flag

`outputs/pairwise_report.json`, computed from
`release/.../data/pairwise_sample/pairwise_sample.parquet` (1,000,000 rows)
as currently on disk.

**⚠ PROVENANCE FLAG.** This on-disk file does **not** reproduce the
manuscript's own reported pairwise statistics:

| Statistic | Manuscript (`table_pairwise_sample_label_summary.csv`, committed 2026-07-02) | This audit's on-disk file (mtime 2026-06-27, i.e. pre-dates the fix) |
| --- | --- | --- |
| is_tie | 878,262 (87.83%) | 879,968 (87.997%) |
| label_a_better | 60,673 (49.8% of non-tie) | 6,134 (5.1% of non-tie) |
| label_b_better | 61,065 (50.2% of non-tie) | 113,898 (94.9% of non-tie) |

Root cause, traced via git history: commit `3b49189` ("Fix pairwise
orientation and reconcile baseline counts", 2026-07-02 18:28) corrected the
pairwise A/B orientation logic and regenerated the manuscript's result
tables. But `release/` is gitignored, so the actual `pairwise_sample.parquet`
data artifact was never re-committed anywhere — and the local copy under
`release/lafc-evict-v0.1-open-current-contract-preserved/` still has an
mtime of **2026-06-27 20:20**, i.e. it **predates the fix by five days** and
was evidently never regenerated locally after the fix landed (the fix and
its result regeneration most plausibly ran on the HPC cluster referenced in
`hpc/wulver/sigmod2027/*.sbatch`, with only the small result CSV/JSON files
pulled back and committed). The tie-fraction is close (0.19% relative
difference — plausibly just a different sampling draw over an unchanged
population, since the A/B swap does not itself change which pairs are tied),
but the direction-balance claim in the manuscript text (Section
`07_tasks_baselines.tex`: "the non-tie label_a_better/label_b_better split is
balanced (about 49.8%/50.2%)... not... a construction-induced directional
imbalance") is **flatly contradicted** by the file currently on disk, which
is 95% skewed toward `label_b_better`.

**This is a real, previously-undetected reproducibility gap** that this
audit surfaces as a byproduct of Phase 12 validation, not something the
audit was specifically asked to find. It does not change the audit's central
conclusion (the tie-heavy characterization is still qualitatively correct
either way), but it means: **do not regenerate pairwise-orientation-sensitive
tables from the current local `release/` checkout without first re-running
the release build (or restoring a checksummed frozen copy) to match the
post-fix pipeline.** Recommended as a concrete follow-up action, not
attempted here (out of scope: "do not modify AWS/HF/Zenodo", and this predates
any of those publications anyway — it is purely a local-build staleness
issue).

**With that caveat stated, the information-content findings from the current
file** (population statistics over its 1,000,000 rows):

- 118,635 unique decisions are represented in the sample (of 2,363,286 total
  — the sample is itself a small, capped slice of the decision population).
- Only **15.9%** of represented decisions (18,847 / 118,635) contribute *any*
  strict (non-tie) pair; the remaining **84.1%** (99,788 decisions)
  contribute *only* tied pairs in this sample.
- Among decisions that do contribute a strict pair, they contribute 6.4
  strict pairs on average (out of 8.4 sampled pairs per decision on average).
- Strict-pair density is highly concentrated: the top-5 (family, capacity,
  horizon) cells by strict fraction are all `metacdn` at horizon=16 (density
  0.82–0.93); the bottom-5 are all `wiki2018` (density **exactly 0.0** in
  every one).
- **Quadratic pairwise-expansion weighting effect** (computed from
  `decision_view` population `candidate_count`, independent of the
  provenance issue above): the *full* pairwise universe, if ever
  materialized instead of using a capped sample, would contain
  24,791,643,360 pairs — a candidate_count=256 decision would contribute
  32,640 pairs vs. 496 for a candidate_count=32 decision, a **65.8×**
  weighting disparity purely from candidate-pool size (which correlates with
  capacity). The shipped 1,000,000-row sample avoids materializing this, and
  its capacity mix (23.9–26.1% per capacity) tracks the decision-level
  population mix (24.0–26.0%) closely, so the *shipped sample itself* is not
  visibly capacity-skewed — but any future move to a larger or full pairwise
  artifact must actively guard against this quadratic effect.

## 6. Horizon effect (Phase 6)

`outputs/phase6_horizon_effect.csv`, all three existing horizons (4, 8, 16),
787,762 decisions each (the same underlying full-cache-miss events relabeled
at each horizon, confirmed against `08_characterization.tex`):

| horizon | all-tied frac | mean optimal-set frac | unique-winner frac | mean random regret | mean loss range | max loss range | distinct optimal-set sizes seen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | 0.7399 | 0.99501 | 0.0 | 0.00500 | 0.260 | 3.0 | 20 |
| 8 | 0.6707 | 0.99177 | 0.0 | 0.00827 | 0.330 | 3.0 | 36 |
| 16 | 0.6193 | 0.98694 | 0.0 | 0.01322 | 0.384 | 4.0 | 68 |

**Longer horizons help, monotonically, but only modestly, and do not fix the
core problem.** Going from H=4 to H=16: the all-tied fraction drops 12
points (74%→62%), mean regret roughly triples (0.005→0.013), and the number
of distinct optimal-set sizes seen more than triples (20→68, i.e. more
varied tie structure). But mean optimal-set fraction only drops from 0.995
to 0.987, and **unique-winner fraction stays at exactly 0.0 at every
horizon** — H=16 is not remotely long enough to break the fundamental
tie-density problem, which comes from unit miss-count regret being a very
coarse, small-integer-range signal, not primarily from a too-short horizon.
Longer horizons (32, 64, ...) were not evaluated (no such data exists in the
current release; see Section 8/Phase 10 for the cost estimate of generating
them).

## 7. Simple-victim diagnostics (Phase 8) — single-decision counterfactual only

**Labeled explicitly, per instructions, as a single-decision counterfactual
diagnostic — not a closed-loop policy evaluation.** Computed by joining the
full 277,995,072-row `candidate_rows` table to `decision_view` on the
canonical 9-column decision key (`outputs/candidate_level_report.json`,
`outputs/phase8_lru_mru_stratified.csv`); one selection per decision for each
method, so these are directly decision-weighted (2,363,286 decisions each).

| Selector | Optimal-selection rate | Mean regret |
| --- | --- | --- |
| uniform random (Section 2) | 0.9912 | 0.008826 |
| **LRU** (evict least-recently-used) | **0.9970** | **0.003057** |
| **MRU** (evict most-recently-used) | **0.9342** | **0.065965** |
| predictor-victim column | 0.9970 | 0.003057 |

Two findings worth flagging:

1. **LRU clearly and consistently beats uniform random, and MRU clearly and
   consistently loses to it**, across nearly every stratum (full breakdown in
   `phase8_lru_mru_stratified.csv`). This is a real, useful sanity result:
   *despite* the heavy tie density documented above, the label surface does
   discriminate between a sensible heuristic (LRU) and a deliberately bad one
   (MRU) — MRU's mean regret (0.066) is ~21× LRU's (0.0031) and ~7.5× random's
   (0.0088). The gap is largest exactly where Sections 3–4 already identified
   the most discriminative regime: `metacdn`/`twemcache` at small capacity —
   e.g. `metacdn, capacity=32, horizon=16`: LRU optimal rate 0.986 vs. MRU
   0.685 (mean regret 0.014 vs. 0.318, a 22× gap). In `wiki2018`, LRU and MRU
   are **identical** (both exactly 1.0 / 0 regret) — consistent with Section
   3's finding that wiki2018 is fully degenerate.
2. **`candidate_is_predictor_victim` is bit-identical to `candidate_is_lru_victim`
   everywhere** in this release (verified both by an aggregate match across
   the full 278M-row scan — identical sums, identical optimal-selection rate
   to 16 significant figures — and by a row-level equality check on one
   partition file, 0 mismatches out of 4,613,504 rows). This means the
   "predictor" score baked into this release's candidate features is, in
   effect, just a copy of the LRU signal, not an independent learned scorer.
   This is stated as an observation for the label-generation code to confirm
   deliberately (it may be an intentional placeholder default), not asserted
   as a bug — but it means any manuscript claim that treats
   `candidate_predictor_score`/`candidate_is_predictor_victim` as evidence of
   a *distinct* predictive signal is currently unsupported by this release's
   data.
3. **Comparison to the manuscript's reported `linear_score` baseline**
   (0.8753 decision-weighted optimal-selection rate, 0.1251 mean regret, from
   `table_regret_tie_stats.tex`): the trivial **LRU** heuristic (0.9970,
   0.0031) substantially *outperforms* the manuscript's regression-based
   `linear_score` selector on this same decision-weighted metric. This is an
   apples-to-apples comparison (same metric, same decision population) and is
   a materially important context for how "weak" baselines should be framed
   in the revision — a hand-coded LRU rule currently beats the paper's
   learned pointwise regressor at this task.

## 8. Scientific classification (Phase 9)

**Classification: B — CONDITIONALLY DISCRIMINATIVE.**

Justification, weighing all phases above:

- **Not A (discriminative overall)**: the aggregate picture the reviewer
  criticized is confirmed, not an artifact — 67.7% of decisions are fully
  tied, unique-winner fraction is exactly 0.0 across all 2,363,286 decisions
  at every horizon tested, and P(regret ≥ 1) candidate-weighted is only
  0.56%. This is not a measurement error or a sampling artifact; it
  reproduces exactly and is confirmed by independent manual spot-checks.
- **Not C/D (only a small minority of decisions carry signal, or none do)**:
  a genuinely large, non-cherry-picked subset — 32.3% of all decisions,
  concentrated in `metacdn`/`twemcache`/`cloudphysics` at smaller capacities
  and longer horizons — is not all-tied, and within that subset the simple
  LRU-vs-MRU diagnostic shows a clear, large (7–22×), monotonic-with-horizon
  separation that a trivial heuristic can exploit. This is real signal, not
  noise, and it is not confined to a handful of decisions (764,282 of them
  qualify under the "not all tied" threshold alone).
- **B fits because** the signal is real but **structurally concentrated**: it
  is essentially absent from `wiki2018` (0% of any nontrivial bucket, 15/15
  capacity×horizon cells perfectly tied) and thin in `metakv`, while
  `twemcache` and `metacdn` at capacity=32 and horizon=16 carry a
  disproportionate share of it. The truly "hard" regime — optimal-set
  fraction ≤ 0.5, or random regret ≥ 0.5 — exists (it is not empty, unlike
  "regret ≥ 1" which never occurs) but is extremely rare (0.002%–0.01% of
  decisions) and confined to two families at one capacity and one horizon.

## 9. Was the reviewer's concern resolved? Implications for the revision (Phase 10)

**REVIEWER_CONCERN_RESOLVED: PARTIALLY.** The reviewer's numbers are
confirmed accurate, not overturned — but this audit shows the aggregate
statistic hides a real, identifiable, non-trivial discriminative regime, which
directly answers the reviewer's own framing ("either demonstrate meaningful
nontrivial regions... or substantially narrow/revise the benchmark claims").
Meaningful regions exist and are now characterized; the benchmark claims
still need to be narrowed to match what the data actually supports.

Recommendations, each scoped against existing vs. new data:

1. **Add an explicit filtered/nontrivial benchmark track**, defined
   transparently (e.g. "not all tied" or "loss range ≥ 1", covering 32.3% of
   decisions / 34.0% of candidate rows) alongside the full-population
   numbers, rather than reporting only the aggregate. *Addresses*: the core
   reviewer criticism directly. *Data sufficiency*: existing data suffice —
   this is a re-slicing of `decision_view.parquet`, already computed in this
   audit (`outputs/phase5_nontrivial_subsets` inside
   `decision_view_report.json`). *Cost*: negligible (seconds). *Post-hoc bias
   risk*: low if the threshold is stated in the methods section *before*
   headline numbers are reported and is not tuned to a target result — this
   audit deliberately swept eight thresholds, not just favorable ones.
2. **Report family-stratified results, and be explicit that `wiki2018` (=
   the entire public v0.3 release) is structurally non-discriminative for
   this target.** *Addresses*: the "critical scope distinction" risk called
   out in the task brief — if reviewers or future users evaluate claims
   against the public release alone, they will find zero signal, which could
   look like the benchmark doesn't work at all rather than like a
   family-specific property. *Data sufficiency*: existing (Section 3/4/7
   above). *Cost*: none. *Bias risk*: none — this is disclosure, not method
   change.
3. **Retain the current target but add a graded/weighted regret framing**
   (e.g., report P(regret≥1) and P(regret≥2) as thresholds, not just mean
   regret) so that the rare-but-real high-regret tail (0.15% of decisions
   have loss range ≥ 2, up to regret ≈ 4) is visible instead of averaged
   away. *Addresses*: reviewer's "regret is too small on average" framing.
   *Data sufficiency*: existing (this audit computed the exact P(regret≥2)
   via one candidate_rows scan; see `candidate_level_report.json`). *Cost*:
   the one heavy scan already run here (~6–10 seconds on this machine for
   the full 278M-row join). *Bias risk*: low.
4. **Investigate increasing the horizon beyond 16**, since Section 6 shows a
   real, monotonic, not-yet-saturated trend (mean regret triples from H=4 to
   H=16 with no sign of plateauing) — but this is the one recommendation that
   requires **new data generation**, not just new analysis. *Addresses*: "can
   longer horizons resolve the tie problem" directly. *Existing data
   sufficient*: **NO** — no horizon beyond 16 exists in the current release.
   *Estimated scale*: the current three horizons (4, 8, 16) together produced
   787,762×3 ≈ 2.36M decisions from replaying the same underlying full-cache-
   miss events; adding e.g. H=32 and H=64 would mean re-running the label
   generator's continuation-policy rollout for 787,762 base events at two
   additional (longer, hence more expensive per-event) horizons across all
   candidates (256 max per decision) — a multi-hour-to-day-scale HPC job on
   the same order as the `run_best_candidate_baseline.py` full-release
   evaluation the reconciliation report already logged as ">8 hours wall
   clock" on Wulver's general partition for one linear pass over 168 files;
   a fresh horizon requires regenerating the underlying `candidate_rows`
   values (label generation), which is a materially larger job than that
   evaluation pass. **This audit stops here and does not launch that job**,
   per the phase-11 stop condition — see the HPC job sketch in the final
   block below.
5. **Do not currently claim `candidate_predictor_score`/
   `candidate_is_predictor_victim` provides signal independent of LRU** in
   this release, per Section 7 finding #2, until the label-generation code
   confirms whether this is intentional. *Addresses*: an unforced accuracy
   risk this audit surfaced as a byproduct, not a reviewer criticism.
   *Data sufficiency*: existing. *Cost*: none (it's a claim-scoping change,
   not an experiment). *Bias risk*: none.
6. **Fix the pairwise-sample provenance gap** (Section 5) before relying on
   any *new* pairwise-orientation-sensitive analysis: regenerate
   `release/.../pairwise_sample.parquet` from the current (post-`3b49189`)
   pipeline, or restore/checksum a frozen copy matching the committed
   manuscript tables, so future audits and revisions don't silently draw
   conclusions from a stale artifact. *Addresses*: a reproducibility risk,
   not a reviewer criticism directly, but directly relevant to any journal
   revision claiming reproducibility. *Data sufficiency*: the release-build
   pipeline exists; this is a re-run, not new generation. *Cost*: unknown
   without timing the current pipeline end-to-end; likely comparable to or
   less than the >8-hour best-candidate evaluation job, since sample
   construction reads the same 168 partitions once. *Bias risk*: none.
7. **Do not redesign the target from scratch** based on this evidence alone.
   Classification B (conditionally discriminative, not non-discriminative)
   does not support the most drastic option (D → full redesign); a
   narrowed/stratified reporting approach (recommendations 1–3) is
   proportionate to what the data show.

## 10. Validation status (Phase 12)

- All decision/candidate row counts cross-checked against
  `table_dataset_scale.tex` / `table_candidate_count_stats.tex` / the
  manifest-backed counts already in the manuscript: **match exactly**
  (2,363,286 decisions; 277,995,072 candidates; 168 partitions; 5 families;
  capacities {32,64,128,256}; horizons {4,8,16}).
- `tie_count == optimal_candidate_count` verified for **all** 2,363,286
  decisions (population check, 0 mismatches) — confirms these are the same
  quantity in this schema, not two independent measurements.
- `regret_sum` confirmed integer-valued for all decisions (population check,
  0 non-integer rows) — this is what licenses the exact
  `P(regret≥1) = 1 - optimal_set_fraction` shortcut used in Phase 3.
- Two decisions (one fully-tied, one non-trivial with loss range 4) manually
  recomputed from raw `candidate_rows` and matched `decision_view` exactly.
- `candidate_is_predictor_victim ≡ candidate_is_lru_victim` checked both in
  aggregate (full 278M-row scan) and row-level (one partition file, 0/4.6M
  mismatches).
- **Public-v0.3 / SIGMOD-scale conflation check**: this report analyzes only
  `release/lafc-evict-v0.1-open-current-contract-preserved/` (the 5-family,
  277,995,072-row dataset) as primary; `wiki2018`-only figures are reported
  strictly as *strata within* that dataset, never substituted for it. No
  numbers from `release/lafc-evict-v0.3-*` were used anywhere in this report.
- **Known unresolved discrepancy**: `pairwise_sample.parquet` on-disk does
  not match the manuscript's committed pairwise statistics (Section 5) — this
  is reported, not silently reconciled or hidden.
- Git working tree: this audit's branch adds only new files under
  `analysis/sigmod_target_discriminativeness_20260913/`; no existing tracked
  file was modified; no manuscript file was touched.

---

LAFC_EVICT_SIGMOD_TARGET_AUDIT_REPORT

CANONICAL_REPO: SoroushVahidi/lafc-evict-dataset (local: /home/soroush/projects/lafc-evict-dataset/repo)
BRANCH: analysis/sigmod-target-discriminativeness-20260913 (base: master)
COMMIT: fbbeedb02ffedf571cf6a08a9a7418467d857cea

CANONICAL_SIGMOD_DATASET: release/lafc-evict-v0.1-open-current-contract-preserved
CANDIDATE_ROWS: 277,995,072
DECISIONS: 2,363,286
TRACE_FAMILIES: cloudphysics, metacdn, metakv, twemcache, wiki2018 (public v0.3 = wiki2018 only, analyzed only as a stratum, not substituted)
CAPACITIES: 32, 64, 128, 256
HORIZONS: 4, 8, 16 (no longer horizon exists in current data)

REVIEWER_RANDOM_OPTIMAL_0_9912:
- reproduced: YES, exact
- exact_value: 0.9912418754543462
- methodology: decision-weighted mean over all 2,363,286 decisions of (optimal_candidate_count / candidate_count); population statistic, no sampling; candidate-weighted alternative = 0.9943795298644719

REVIEWER_RANDOM_REGRET_0_0088:
- reproduced: YES, exact
- exact_value: 0.008826200441884731
- methodology: decision-weighted mean over all 2,363,286 decisions of each decision's regret_mean (y_loss - min_y_loss, averaged over that decision's candidates); candidate-weighted alternative = 0.005650017421891565

REVIEWER_PAIR_TIES_878262_OF_1M:
- reproduced: PARTIALLY (tie fraction close: 879,968/1,000,000 = 0.8800 vs reported 0.8783; but the on-disk pairwise_sample.parquet is a stale, pre-orientation-fix artifact — see Section 5 provenance flag — and does NOT reproduce the manuscript's committed 60,673/61,065/878,262 label split or its balanced-orientation claim)
- exact_value: manuscript-committed ground truth = 878,262 (from paper/sigmod2027/results/metadata_tables/table_pairwise_sample_label_summary.csv, git-tracked, dated 2026-07-02); current on-disk file = 879,968
- methodology: exact count over the full 1,000,000-row shipped pairwise sample (population, not further sampled); manuscript figure and current on-disk figure come from two different builds of the same pipeline (pre- vs post- commit 3b49189's orientation fix)

OVERALL_TARGET_STATISTICS:
- all_tied_fraction: 0.676601985540472
- unique_winner_fraction: 0.0
- mean_optimal_set_fraction: 0.9912418754543462 (decision-weighted); 0.9943795298644719 (candidate-weighted)
- median_optimal_set_fraction: 1.0
- random_optimal_probability: 0.9912418754543462 (decision-weighted); 0.9943795298644719 (candidate-weighted)
- mean_random_regret: 0.008826200441884731 (decision-weighted); 0.005650017421891565 (candidate-weighted)
- p95_random_regret: 0.04564901822684992 (decision-weighted, per-decision regret_mean distribution)
- fraction_loss_range_ge_1: 0.323398014459528
- fraction_loss_range_ge_2: 0.001468294569510419

MOST_DISCRIMINATIVE_REGIMES:
- twemcache, capacity=32, horizon=16: mean optimal-set fraction 0.9347, all-tied fraction 0.2427, mean random regret 0.0670 (n=37,849 decisions)
- metacdn, capacity=32, horizon=16: mean optimal-set fraction 0.9404, all-tied fraction 0.0122, mean random regret 0.0601 (n=29,348)
- metacdn, capacity=32, horizon=8: mean optimal-set fraction 0.9543 (n=29,348)
- LRU-vs-MRU diagnostic gap is largest in exactly these same cells (metacdn/twemcache, capacity=32, horizon=16): MRU mean regret up to 22x LRU's

LEAST_DISCRIMINATIVE_REGIMES:
- wiki2018 at every one of its 15 capacity x horizon cells: mean optimal-set fraction = 1.0, all-tied fraction = 1.0, mean random regret = 0.0 exactly — LRU, MRU, and random are all indistinguishable and all perfect
- metakv is a distant second-least-discriminative family (LRU optimal rate 0.9994-1.0 across all cells; MRU still clearly worse at 0.929-0.937, so metakv is degenerate but not fully so, unlike wiki2018)

NONTRIVIAL_SUBSET_RESULTS:
- "not all tied" / "loss range >= 1": 764,282 decisions (32.34% of all decisions, 33.99% of candidate rows); mean random regret 0.0273; wiki2018 contributes 0 decisions to this bucket
- "unique optimal victim": 0 decisions (never occurs anywhere in the population)
- "optimal-set fraction <= 0.5": 52 decisions (0.0022%); cloudphysics/twemcache only, capacity=32 only, horizon=16 only
- "loss range >= 2": 3,470 decisions (0.147%); twemcache 69%, capacity 32 and horizon 16 dominant
- "random regret >= 0.1": 16,298 decisions (0.69%); twemcache 76%, capacity 32 (78%), horizon 16 (77%)
- "random regret >= 0.5": 285 decisions (0.012%); twemcache 83%, capacity 32 almost exclusively, horizon 16 exclusively
- "random regret >= 1": 0 decisions (never occurs)
- Conclusion: a broad-but-shallow nontrivial region (~32% of decisions) coexists with a vanishingly rare but real "hard" tail (~0.01%), both concentrated away from wiki2018 and toward twemcache/metacdn at small capacity and long horizon

HORIZON_EFFECT:
- H=4: all-tied 0.7399, mean optimal-set fraction 0.99501, mean random regret 0.00500, mean loss range 0.260, max loss range 3.0
- H=8: all-tied 0.6707, mean optimal-set fraction 0.99177, mean random regret 0.00827, mean loss range 0.330, max loss range 3.0
- H=16: all-tied 0.6193, mean optimal-set fraction 0.98694, mean random regret 0.01322, mean loss range 0.384, max loss range 4.0
- Trend: monotonic and real (regret roughly triples H4->H16, all-tied fraction drops 12 points) but not saturated and not sufficient on its own — unique-winner fraction remains exactly 0.0 at every tested horizon
- Longer horizons (32, 64, ...) do not exist in current data; generating them requires new label-generation runs, not just new analysis (see recommendation 4 / HPC sketch below)

PAIRWISE_INFORMATION_CONTENT:
- Tie fraction (current on-disk file): 87.997% (see provenance flag above for why this is not an exact manuscript match)
- Only 15.9% of decisions represented in the pairwise sample (18,847 / 118,635) contribute >=1 strict pair; 84.1% contribute only tied pairs
- Strict-pair density ranges from ~0.93 (metacdn, horizon=16 cells) down to exactly 0.0 (every wiki2018 cell)
- Full pairwise universe would be 24,791,643,360 pairs with up to 65.8x per-decision weighting disparity by candidate_count/capacity if ever fully materialized (the shipped 1,000,000-row sample avoids this and is not itself capacity-skewed)

SIMPLE_VICTIM_DIAGNOSTICS:
- random: optimal-selection rate 0.9912 (decision-weighted) / 0.9944 (candidate-weighted); mean regret 0.008826 / 0.005650
- LRU: optimal-selection rate 0.9970; mean regret 0.003057 (beats both random and the manuscript's reported linear_score baseline of 0.8753/0.1251)
- MRU: optimal-selection rate 0.9342; mean regret 0.065965 (clearly and consistently worse than random and LRU, confirming the target CAN separate a bad heuristic from a good one)
- other: candidate_is_predictor_victim is bit-identical to candidate_is_lru_victim throughout this release (0/4.6M-row mismatch spot check, exact match in full 278M-row aggregate) — flagged as a data-generation question, not assumed to be a bug

SCIENTIFIC_CLASSIFICATION:
B

CLASSIFICATION_JUSTIFICATION:
The aggregate reviewer statistics are confirmed exactly (not an artifact of aggregation methodology) and the dataset is genuinely tie-dominated overall (unique-winner fraction is exactly 0.0 across all 2,363,286 decisions at every tested horizon). But a large (32.3% of decisions), non-cherry-picked, family/capacity/horizon-identifiable subset shows real signal, and a simple LRU-vs-MRU diagnostic shows the target can separate a good heuristic from a bad one by 7-22x in mean regret within that subset. The signal is structurally concentrated (present in metacdn/twemcache at small capacity and long horizon; essentially absent in wiki2018 and thin in metakv) rather than either broadly strong (ruling out A) or vanishingly rare everywhere (ruling out C/D, since C/D would understate how large and well-defined the "not all tied" bucket is).

REVIEWER_CONCERN_RESOLVED:
PARTIALLY

EXISTING_DATA_SUFFICIENT_FOR_NEXT_STEP:
YES for recommendations 1-3, 5-6 (re-slicing, re-reporting, and one provenance fix using data/pipelines that already exist). NO for recommendation 4 (testing whether horizons beyond 16 further reduce tie density requires new label generation).

RECOMMENDED_NEXT_EXPERIMENT:
Re-report benchmark headline numbers stratified by trace_family x capacity x horizon (not just pooled), add an explicit "nontrivial" filtered track (loss range >= 1, ~32% of decisions) alongside the full-population numbers, and explicitly disclose that the public wiki2018-only v0.3 release is structurally non-discriminative for this target so it is not mistaken for a representative slice of the benchmark's difficulty. This is a re-analysis and re-reporting exercise, not a new data-generation campaign.

NEW_DATA_GENERATION_REQUIRED:
YES, but only for one specific follow-up: testing horizons beyond 16 (recommendation 4). Not required for the core reviewer-response narrowing described above.

HPC_REQUIRED:
YES, for the horizon-extension experiment only (recommendation 4) — not for anything else in this report. Job sketch if pursued: re-run the label-generation/continuation-policy rollout for the existing 787,762 base full-cache-miss events at 1-2 new horizons (e.g. 32, 64), across up to 256 candidates per decision per the existing candidate_count range; the closest existing timing reference is the best-candidate evaluator's full-release pass, logged in best_candidate_reconciliation_report.json as requiring ">8 hours wall clock" on Wulver's general partition for one linear scoring pass over the existing 168 partitions -- label generation for new horizons is a larger job than that (it produces new candidate_rows content, not just a scoring pass over existing rows), so budget at least that much, likely more, per new horizon. Exact required input paths, node/hour budget, and output schema should be scoped as a dedicated follow-up plan before submission to Wolverine/HPC; this audit does not submit that job.

ARTIFACTS_CREATED:
- analysis/sigmod_target_discriminativeness_20260913/README.md
- analysis/sigmod_target_discriminativeness_20260913/REPORT.md (this file)
- analysis/sigmod_target_discriminativeness_20260913/scripts/01_decision_view_analysis.py
- analysis/sigmod_target_discriminativeness_20260913/scripts/02_candidate_level_analysis.py
- analysis/sigmod_target_discriminativeness_20260913/scripts/03_pairwise_analysis.py
- analysis/sigmod_target_discriminativeness_20260913/outputs/decision_view_report.json
- analysis/sigmod_target_discriminativeness_20260913/outputs/candidate_level_report.json
- analysis/sigmod_target_discriminativeness_20260913/outputs/pairwise_report.json
- analysis/sigmod_target_discriminativeness_20260913/outputs/phase4_stratified_family_capacity_horizon.csv
- analysis/sigmod_target_discriminativeness_20260913/outputs/phase4_stratified_split.csv
- analysis/sigmod_target_discriminativeness_20260913/outputs/phase4_stratified_candidate_count.csv
- analysis/sigmod_target_discriminativeness_20260913/outputs/phase6_horizon_effect.csv
- analysis/sigmod_target_discriminativeness_20260913/outputs/phase7_pairwise_strict_density.csv
- analysis/sigmod_target_discriminativeness_20260913/outputs/phase8_lru_mru_stratified.csv

VALIDATION_STATUS:
All row/decision counts cross-checked against manuscript tables (exact match); tie_count==optimal_candidate_count and regret_sum-integer-valued confirmed as population checks (0 exceptions each); two decisions manually recomputed from raw candidate_rows and matched decision_view exactly; candidate_is_predictor_victim===candidate_is_lru_victim checked at both row level (one partition, 0/4.6M mismatches) and full-population aggregate level; no public-v0.3/SIGMOD-scale conflation (wiki2018 reported only as a stratum of the 5-family dataset); one unresolved discrepancy documented rather than hidden (pairwise_sample.parquet provenance gap, Section 5); git working tree clean except this audit's own new files on its own branch.

MANUSCRIPT_EDITED:
NO

NEXT_SINGLE_ACTION:
Regenerate (or restore a checksummed frozen copy of) release/lafc-evict-v0.1-open-current-contract-preserved/data/pairwise_sample/pairwise_sample.parquet from the current post-orientation-fix pipeline, so that the pairwise-view artifact backing future manuscript revisions matches what is actually committed in table_pairwise_sample_label_summary.csv -- before any further pairwise-based analysis or manuscript editing proceeds.
