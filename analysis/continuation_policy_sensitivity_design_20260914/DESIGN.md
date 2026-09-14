# Continuation-Policy Sensitivity: Experimental Design

Status: **design only. No experiment was launched, no label was
regenerated, no production data was touched.** This document specifies
what a future, separately-approved implementation task should build and
run.

## 1. Prior work found (do not silently elevate)

A repository-wide, read-only search found **substantial prior continuation
work already exists**, in the secondary repository, none of it canonical
LAFC-Evict evidence:

1. **`src/lafc/evict_value_v2_rollout.py`** (branch `main` /
   `chore/repository-polish`) already implements a generalized,
   pluggable-continuation-policy rollout labeler
   (`EvictValueV2RolloutConfig.reference_policy`, supporting `"lru"`,
   `"blind_oracle"`, `"fifo"`). **This is not the code that produced the
   canonical SIGMOD-scale dataset** (that used
   `evict_value_wulver_v1.py::iter_candidate_rows` /
   `_simulate_lru_misses` — see `POLICY_STATE_AUDIT.md`). It is, however,
   the most natural existing extension point for this design's
   implementation (see Section 9).
2. **`scripts/experiments/exploratory/run_continuation_policy_light_ablation.py`**
   (same branch) already ran a toy-scale ablation comparing
   lru/blind_oracle/fifo continuations — but on `data/example*.json` toy
   traces at **capacity 2-3, capped at 400 requests/trace** — orders of
   magnitude smaller than LAFC-Evict's real 50,000-request traces at
   capacity 32-256. A figure (`figure7_continuation_policy_agreement.png`)
   exists from this in the *secondary* repo's own manuscript materials.
   **This does not constitute canonical LAFC-Evict continuation-sensitivity
   evidence** and must not be cited as such — it is toy-scale exploratory
   work on a different (KBS) manuscript's side track.
3. **Branch `kbs/second-revision-science` only** (not on `main`) has a
   substantially more developed, but frozen-with-no-results, causal
   ablation protocol: `src/lafc/continuation_policy_ablation.py` and
   `configs/continuation_policy_causal_ablation_v1.json`
   (`"status": "PROTOCOL_FROZEN_NO_RESULTS"`). Its scientific question is
   different from this task's: *"Does replacing the fixed LRU continuation
   with an already-learned policy π1 improve the next learned policy π2?"*
   — a policy-iteration/DAgger-style question about downstream learned
   policies, not about whether the raw counterfactual label/ranking itself
   is stable under simple alternative continuations. Relevant context, not
   directly reusable for this narrower question.
4. **The KBS manuscript's own LaTeX text** (`manuscript_source/main.tex`,
   duplicated in `submission_kbs_revision_final/07_LaTeX_Source/main.tex`)
   explicitly states: *"the default continuation rule is a lightweight
   LRU-style replay... Alternative continuation rules are treated as
   exploratory sensitivity directions rather than part of the main
   method"* and separately hypothesizes a **distribution-shift mechanism**
   between the LRU-continuation-constructed label and a deployed policy's
   actual non-LRU trajectory as the leading, unconfirmed explanation for an
   observed capacity-128 regression — explicitly listing "a small
   retraining ablation under an alternative continuation rule" as future
   work never done. This is strong independent motivation for exactly this
   design, from the project's own prior writing.

No hits anywhere (either repository, all branches) for "MRU continuation",
"random continuation", "SIEVE continuation", or `H_CONTINUATION` — those
specific alternatives have never been explored.

## 2. The reviewer question, exactly as it exists in the repository

**No verbatim reviewer letter was found in either repository.** The only
review-related archive present
(`publication/bundles/archives/sigmod2027_anonymous_review.zip`) contains
submission supplementary results, not received review text. The
"reviewer concern" as documented is the project's own internal,
repeatedly-stated articulation (`docs/CURRENT_PROJECT_STATUS_AND_HANDOFF.md`
§12, `docs/SCIENTIFIC_EVIDENCE_INDEX.md`'s `H_CONTINUATION` row), reading:
*"Continuation-policy sensitivity asks: how do the counterfactual labels
themselves change if the continuation policy after a forced eviction
changes?"* This is corroborated, independently, by the KBS manuscript's own
distribution-shift hypothesis (Section 1.4 above) — two independent
internal sources converge on the same concern, even though neither is a
literal external reviewer quote. This should be reported honestly in any
future manuscript text: the concern is well-motivated internally, not
sourced from an external review this repository has a record of.

Of the five possible readings offered in the task brief, the repository
evidence most directly supports **(2) sensitivity of candidate rankings**
and **(3) sensitivity of the optimal candidate set** as primary — this is
exactly the wording of the internal H_CONTINUATION concern ("how do the
labels themselves change") and of this task's own framing ("are candidate
values/rankings materially dependent..."). **(1) absolute-loss
sensitivity** falls out as a natural byproduct metric. **(4) target
discriminativeness** and **(5) downstream learned-policy conclusions** are
secondary/exploratory — (5) in particular is the *kbs/second-revision*
branch's question, not this one's, and is explicitly out of scope here.

## 3. Pre-registered hypothesis

**H_CONTINUATION**: *Candidate-level finite-horizon counterfactual
supervision (regret ranking and optimal-candidate-set membership) is
materially stable under a change of continuation policy (LRU → MRU;
LRU → random) in workload/capacity regimes where the target is already
discriminative under LRU, and is not expected to be informative one way or
the other in regimes that are already tie-dominated or degenerate under
LRU (since there is little ranking structure to disturb there).*

Pre-specified evidence categories (defined **before** any data is
collected, per instruction):

- **ROBUST**: median optimal-set Jaccard overlap ≥ 0.8 AND cross-continuation
  regret (Section 6) ≤ 1 miss for ≥ 80% of LRU-optimal candidates, **within
  the discriminative-under-LRU stratum** (see Section 7 — degenerate
  decisions are excluded from this judgment by design, not by cherry-picking
  after the fact).
- **CONDITIONALLY ROBUST**: the above holds in some but not all
  family/capacity strata, with the pattern of where it holds vs. fails
  itself explainable by already-established regime characteristics
  (strong-signal vs. weak-signal vs. exception vs. degenerate, from the
  linkage/mechanistic analyses).
- **MATERIAL SENSITIVITY**: median Jaccard < 0.5 OR cross-continuation
  regret > 2 misses for a majority of LRU-optimal candidates in a majority
  of discriminative strata.
- **INCONCLUSIVE**: metrics disagree in direction across the primary
  tie-aware measures (Section 6), or sample size proves inadequate (pilot
  will check this before any full run).

These thresholds are illustrative anchors fixed now, before data
collection, precisely so a future implementer cannot adjust them after
seeing results; they should be reviewed (not silently changed) by a human
before the full experiment runs, but must not be tuned to the pilot's own
outcome.

## 4. Primary and secondary research questions

**Primary** (directly answers the reviewer concern):
- **P1.** How stable are optimal candidate sets under continuation change?
- **P2.** How stable are tie-aware candidate rankings/regret orderings under
  continuation change?
- **P3.** Does continuation sensitivity vary systematically by
  workload/capacity/horizon (using the regimes already established by the
  linkage and mechanistic analyses: strong-signal, weak-signal, MetaKV
  exception, degenerate control)?

**Secondary** (exploratory, clearly separated from primary in reporting):
- **S1.** Does target discriminativeness itself (all-tied fraction,
  optimal-set-fraction) change under the alternative continuation?
- **S2.** Are the strong-signal regimes (MetaCDN, Twemcache) more
  continuation-robust than the weak-signal regime (cloudphysics)?
- **S3.** Does sensitivity grow with horizon H?
- **S4.** What happens in wiki2018 (expected: nothing informative, since
  zero reuse events in the mechanistic analysis's trace-only
  characterization already implies near-total ties regardless of
  continuation — a negative-control expectation stated in advance)?
- **S5.** Does MetaKV show unusual continuation dependence, consistent with
  its already-flagged closed-loop exception?

## 5. Continuation policies to test

**Primary**: **MRU** (deterministic, WELL_DEFINED_FROM_PREFIX, maximally
different eviction behavior from LRU, already a familiar reference point
from Tier 1). **Random** (WELL_DEFINED_FROM_PREFIX, secondary stochastic
stress test — see Section 8 for the seed design). **SIEVE excluded**
(NOT_WELL_DEFINED_FOR_COUNTERFACTUAL_SUBSTITUTION — see
`POLICY_STATE_AUDIT.md`; not excluded "merely because it wasn't used in
Tier 1" but because its state genuinely does not exist in an LRU-generated
prefix). FIFO and blind_oracle remain available (already coded in
`evict_value_v2_rollout.py`) as clearly-labeled optional secondary checks
if reviewers want more than the two primary alternatives — not part of the
primary design, to avoid a policy zoo.

## 6. Tie-aware primary metrics (minimal set, justified)

The target is heavily tied (global all-tied fraction ≈0.68, unique-winner
fraction = 0). Metrics that assume a single well-defined argmin are
inappropriate as primary measures. Primary set (redundancy-checked, not
all ten candidate metrics from the brief):

1. **Optimal-set Jaccard overlap** per decision:
   `|OptSet_LRU ∩ OptSet_C| / |OptSet_LRU ∪ OptSet_C|`. Directly answers
   P1. Reported as a distribution (median, IQR), not just a mean.
2. **Pairwise preference-agreement table** per decision (for all candidate
   pairs, or a bounded random subsample of pairs for large candidate
   counts): classify each pair into `{concordant, discordant, LRU_tie/C_strict,
   LRU_strict/C_tie, both_tied}` — the exact tie-aware taxonomy requested,
   directly answering P2 without forcing a strict ranking.
3. **Kendall tau-b** on candidate regret values, per decision (tie-capable
   by construction, `scipy.stats.kendalltau`) — a single summary number per
   decision to complement the categorical pairwise table.
4. **Cross-continuation regret** (Section 6-bis below) — the single most
   reviewer-facing number: "if I trust the LRU-continuation label, how much
   do I lose under the alternative continuation?"

Secondary/diagnostic (reported, not primary):
- Change in all-tied-decision fraction and optimal-set fraction
  (population-level, answers S1).
- Absolute/relative change in candidate regret scale (mean/median regret
  under C vs. under LRU).
- Fraction of decisions where the *practical* selected candidate (e.g. the
  argmin a downstream consumer would pick, tie-broken by a fixed
  deterministic rule stated once) changes.

Redundant metrics explicitly **not** computed as primary: raw
optimal-set-size difference (subsumed by Jaccard), a single arbitrary
argmin comparison (explicitly rejected per the brief's own warning), and
per-candidate absolute loss without pairing against LRU (not a stability
measure by itself).

## 6-bis. Cross-continuation regret (the headline practical metric)

For decision `d`, let `OptSet_LRU(d)` be the (possibly multi-element) set
of LRU-continuation-optimal candidates. For alternative continuation `C`:

```
R_C(d, e) = L_C(d, e) - min_e' L_C(d, e')     for e in OptSet_LRU(d)
```

Because `OptSet_LRU(d)` may have many members (tie-heavy target), report
**all** of the following rather than picking one arbitrary tie-break:

- `mean_over_LRU_optimal`: average of `R_C(d, e)` over `e ∈ OptSet_LRU(d)`
  — "if a uniformly random LRU-optimal candidate were followed, what's the
  expected extra C-continuation loss?"
- `best_case`: `min_{e ∈ OptSet_LRU(d)} R_C(d, e)` — best-case if the
  *luckiest* LRU-optimal candidate happens to also be chosen.
- `worst_case`: `max_{e ∈ OptSet_LRU(d)} R_C(d, e)` — worst-case exposure.
- `prob_still_optimal`: fraction of `OptSet_LRU(d)` that is also in
  `OptSet_C(d)` (equivalently, `P(uniformly sampled LRU-optimal candidate
  is C-optimal)`).

`mean_over_LRU_optimal` is recommended as the primary reported number
(robust to tie-set size, directly interpretable, matches the brief's
"mean over LRU-optimal candidates" suggestion); best/worst-case are
reported as bounds, never dropped silently.

## 7. Tie-aware stratified reporting (mandatory, not optional)

Every metric above is reported **at least** at these four strata, to
prevent trivial ties from manufacturing fake robustness:

1. All sampled decisions (population-representative).
2. Excluding decisions all-tied under **both** LRU and the alternative
   continuation (removes the wiki2018-style trivial-tie inflation risk).
3. Restricted to decisions discriminative under LRU (`regret_max > 0`
   under LRU) — the stratum the reviewer actually cares about.
4. Restricted to decisions discriminative under **at least one** of LRU or
   the alternative continuation.

Additionally reported by family (using the linkage/mechanistic analyses'
already-established regime labels): strong-signal (MetaCDN, Twemcache),
weak-signal (cloudphysics), exception (MetaKV), degenerate control
(wiki2018) — **wiki2018 is expected, and required to be reported, as a
near-100%-both-tied stratum that contributes essentially no information to
the robustness claim**, exactly as it did in the closed-loop and linkage
analyses; it must never be pooled into an aggregate robustness number
without the stratified breakdown alongside it.

## 8. Random continuation: seed design (not run here)

Common-random-numbers (CRN) is scientifically appropriate here: within one
decision, initialize a **fresh `random.Random(seed)` with the identical
seed value for every candidate's independent rollout**. This does not make
the draws literally identical across candidates (each candidate's forced
cache differs, so the RNG stream advances differently), but it is the
standard, defensible CRN application for reducing between-candidate
variance in a paired comparison, and costs nothing extra to implement.

**Seed count**: not fixed at an arbitrary 20 by convention. Proposed rule:
start with **10 seeds** per decision (analytic justification: raw per-decision
rollout losses are bounded integers in `[0, H]` with `H≤16`, a much smaller
and more constrained range than Tier-1's full-trace miss ratios which
already showed <0.3-percentage-point cross-seed std at 20 seeds over
thousands of scored requests — a per-decision rollout over ≤16 steps has
proportionally less room for variance to accumulate). The **pilot**
(Section 10) must report the empirical coefficient of variation of the
primary cross-continuation regret metric at 10 seeds; if relative SE
exceeds a pre-specified 10% threshold, escalate to 20 seeds for the full
run. This is a seed-count *decision rule*, fixed now, not a result-driven
adjustment.

## 9. Implementation approach (not performed in this task)

Smallest clean approach: extend
`src/lafc/evict_value_v2_rollout.py::_choose_victim()` (already a small,
isolated `if/elif` dispatch) with two new branches:

```python
if policy == "mru":
    return candidates[-1]          # same recency-ordered list, opposite end
if policy == "random":
    return rng.choice(candidates)  # rng threaded through from the caller, CRN-seeded per Section 8
```

This is a **~6-line change**, entirely additive, to a module that is
**not** the canonical dataset builder (`evict_value_wulver_v1.py`) — the
canonical LRU-generation semantics for the released dataset are
**untouched** by this change. Alternative-continuation outputs must be
written to a clearly separate sensitivity-analysis directory (e.g.
`analysis/continuation_policy_sensitivity_20260914/outputs/`, mirroring
the Tier-1 evidence-freeze pattern already established in this project),
never mixed into or silently substituted for the canonical `candidate_rows`
release artifacts. **No change to the secondary repository is made in this
task**; this is a specification for a future, separately-approved change.

## 10. Correctness pilot (design only; not run)

Before any full sample is collected, a tiny pilot must verify semantics,
not produce scientific claims:

- **Cells**: one clearly discriminative regime (twemcache/cap32, H=16 —
  the pilot's own frozen evidence already shows this is highly
  discriminative); one weak-signal regime (cloudphysics/cap32, H=16); the
  MetaKV exception (metakv/cap128, H=16); wiki2018 as a cheap control
  (wiki2018/cap32, H=16) — 4 cells total, reusing exactly the regimes this
  design's own strata are built around.
- **Decision count**: 20 baseline-LRU eviction decisions per cell (80
  total), fixed and recorded by exact `(trace, capacity, request_index)`
  triple — small enough to hand-inspect every row if needed.
- **Purpose**: (a) verify the LRU-reproduction gate (Section 11) on this
  tiny sample; (b) confirm MRU/random substitution runs without error and
  produces sane (non-negative, ≤H, hits+misses-consistent) losses; (c)
  empirically check the 10-seed CoV rule from Section 8; (d) get a real
  wall-clock timing number to replace the analytic estimate in
  `RUNTIME_ESTIMATE.md`. **The pilot's own numbers must not be used for
  any ROBUST/CONDITIONALLY_ROBUST/SENSITIVE claim** — it exists to
  validate the harness, not to answer H_CONTINUATION.

## 11. LRU reproduction gate (critical, blocking)

**Before trusting any MRU/random comparison, the newly extended
`_choose_victim(..., policy="lru")` path must reproduce
`_simulate_lru_misses`'s (the canonical generator's) `y_loss` exactly on
an audit sample.** These are two independently-written LRU
implementations in the same codebase (Section 1 of `POLICY_STATE_AUDIT.md`)
— a silent divergence between them (e.g. in exactly when `move_to_end` is
called, or off-by-one in the horizon slice) would invalidate every
downstream comparison. Because `release/` is not present locally, this
gate cannot be checked from canonical row-level data in this environment;
the future implementation task must either (a) obtain a small, hash-
verified audit slice of real canonical `candidate_rows` for exact
comparison, or (b) at minimum, cross-check the two "LRU" code paths
against each other and against the aggregate offline statistics already
frozen in `analysis/sigmod_target_discriminativeness_20260913/outputs/`
(`phase8_lru_mru_stratified.csv`'s `lru_mean_regret`/`lru_optimal_rate`
per family/capacity/horizon, computed from the real canonical data) as an
aggregate-level consistency check. **If this gate cannot be passed, the
continuation experiment must not proceed** — this is a blocking
precondition, not a nice-to-have.

## 12. Performance Evaluation framing

The deliverable this design aims at is not "we tried another policy and
numbers were similar" but: *how robust is a finite-horizon counterfactual
performance label to the rollout policy used after the intervention, and
in which workload regimes should a systems researcher trust vs. distrust
this class of label?* The stratified reporting (Section 7) and the
cross-continuation regret metric (Section 6-bis) are designed specifically
to produce that kind of actionable, regime-conditioned guidance, which is
the right shape of claim for a Performance Evaluation methodology
contribution.
