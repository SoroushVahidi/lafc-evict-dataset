# LAFC-Evict Current Project Status and Handoff (2026-09-14, successor)

> **Pointer added 2026-09-15/16 (Query 2 preservation pass):** for
> current/active PE experiment status (the long-horizon Wulver DAG, the
> publication-grade learned-model retraining attempts, the Tier-2 LFU
> campaign, and the do-not-recompute list), see
> `docs/PE_CURRENT_PROJECT_STATUS_AND_HANDOFF.md` and
> `docs/PE_DO_NOT_RECOMPUTE.md` in the `augmented-caching` repository — that
> is the operational home for experiment/compute status since it hosts the
> actual experiment code and evidence. This document remains the canonical
> handoff for this repository's own scope (manuscript, release, and
> cleanup state) and is not duplicated there.

This document supersedes `docs/CURRENT_PROJECT_STATUS_AND_HANDOFF.md` (the
`polish/final-handoff-20260914` @ `d37d084` version), which predates the
Tier-1 closed-loop evaluation, the offline/closed-loop linkage analysis, the
mechanistic analysis, and the continuation-policy-sensitivity design/pilot/
full study. That document is not deleted (do not discard manuscript or
scientific content) and remains historically accurate for what it covers;
this successor is the canonical starting point for a future agent as of
2026-09-14. Read this document first; consult the prior one only for
release/publication history (Sections 1, 4, 15-17 of the prior document are
still current and are not repeated here in full).

**Permanent project rule (added by this task, applies to all future work):**
Before running any experiment, search the primary repository, all
branches, and registered worktrees for existing equivalent work. Do not
redo work that already exists. This rule was itself validated by this
task's own duplication audit, which found substantial existing evidence
that the naive approach would have silently duplicated or ignored.

## 1. Canonical Scientific Lineage (as of this document)

```text
master / fbbeedb
  -> analysis/sigmod-target-discriminativeness-20260913 / 76d562f
  -> experiment/closed-loop-tier1-harness-20260913 / 8a4cd32
  -> analysis/tier1-offline-closed-loop-linkage-20260914 / c5c8422
  -> analysis/closed-loop-mechanisms-20260914 / 412c47f
  -> design/continuation-policy-sensitivity-20260914 / 79e601b
  -> experiment/continuation-sensitivity-pilot-20260914 / 3b3b6d7
  -> experiment/continuation-sensitivity-full-20260914 / 484417c (VALIDATED)
```

This branch (`manuscript/pe-evidence-restructure-20260914`) and its worktree
(`.claude/worktrees/pe-evidence-restructure-20260914`) were created directly
from `484417c326f3c1af8bd48eb85168fa5f6ae93801`, verified by
`git merge-base --is-ancestor 484417c <this-branch>` returning true at
creation time. This is the latest validated non-census scientific commit
found by inspection at task start; no newer validated non-census commit was
found on any other branch.

**Separately, and NOT an ancestor of the above lineage:**
`experiment/continuation-mru-population-census-20260914` / `1a29e77`
(branches from `484417c`, adds the population census harness on top —
i.e. the census *is* a descendant of the validated lineage, but its own
census *results* are not yet validated; see Section 4).

**Separately, and divergent (branches from the OLD `76d562f` SIGMOD-era
commit, not from the Tier-1/linkage/mechanistic/continuation lineage):**
`manuscript/performance-evaluation-template-20260913` / `471b3c4` — the
Performance Evaluation manuscript. Verified by
`git merge-base manuscript/performance-evaluation-template-20260913 experiment/continuation-sensitivity-full-20260914`
returning `76d562f` (not either branch's own tip), and both
`--is-ancestor` checks in each direction returning false. **This means the
current PE manuscript text was written before any of Tier-1, linkage,
mechanistic, or continuation-sensitivity evidence existed.** Do not assume
the manuscript reflects current evidence. See Section 6 and
`docs/PE_MANUSCRIPT_RESTRUCTURING_PLAN.md`.

## 2. What Is Now Validated (in addition to everything in the prior handoff)

| Evidence | Directory | Branch/commit | Validation |
|---|---|---|---|
| Tier-1 closed-loop production evaluation | `analysis/closed_loop_tier1_evidence_20260914/` | `experiment/closed-loop-tier1-harness-20260913` / `8a4cd32`, frozen on `analysis/tier1-offline-closed-loop-linkage-20260914` | `TIER1_VALIDATE: PASS`, 14/14 gates, 230/230 complete, 0 failed; byte-verified evidence freeze (`EVIDENCE_MANIFEST.json`) |
| Offline<->closed-loop linkage | `analysis/closed_loop_offline_linkage_20260914/` | `analysis/tier1-offline-closed-loop-linkage-20260914` / `c5c8422` | Two independent code paths (`compute_rq_analyses.py` + independent recheck), 14 passing consistency tests |
| Mechanistic workload analysis | `analysis/closed_loop_mechanistic_analysis_20260914/` | `analysis/closed-loop-mechanisms-20260914` / `412c47f` | Trace-only, no new simulation; every classification explicitly labeled DIRECTLY_SUPPORTED / PLAUSIBLE_BUT_NOT_ESTABLISHED / NOT_SUPPORTED / CAUSALLY_ESTABLISHED |
| Continuation-policy sensitivity design | `analysis/continuation_policy_sensitivity_design_20260914/` | `design/continuation-policy-sensitivity-20260914` / `79e601b` | Design only, not run; includes its own prior-work duplication audit |
| Continuation-policy sensitivity pilot | `analysis/continuation_policy_sensitivity_pilot_20260914/` | `experiment/continuation-sensitivity-pilot-20260914` / `3b3b6d7` | 80 decisions; 52,480/52,480 LRU-equivalence comparisons passed; 23/23 pilot validity gates |
| **Continuation-policy sensitivity full sampled study** | `analysis/continuation_policy_sensitivity_full_20260914/` | `experiment/continuation-sensitivity-full-20260914` / `484417c` | RUN_ID `20260914T040333Z_1f66342be435`; 16,500 decision-horizon pairs, 0 failed; prelaunch LRU-equivalence 1,271,616/1,271,616; `FULL_EXPERIMENT_VALID: true`; independent recheck script cross-validates headline numbers to 1e-9 |

Exact numbers for every one of these: `docs/PE_CLAIM_EVIDENCE_LEDGER.md`
(new in this task) — every ledger row cites its exact source artifact and
value; do not re-derive numbers from memory or from this table.

## 3. Validated Sampled Continuation Study — Headline Result

At capacities 32 and 128, on the pre-registered discriminative-under-LRU
set (Set C, n=6597 primary-sample decisions):

- MRU continuation: `ROBUST` (median optimal-set Jaccard 1.0 at both
  capacities; mean cross-continuation regret 0.0018 at cap32, 0.0000652 at
  cap128; strict reversal fraction 2.7e-05 at cap32, 0.0 at cap128)
- Mean-random continuation (10 CRN seeds): `ROBUST` (median Jaccard 1.0 at
  both capacities; mean Jaccard is measurably lower than MRU's, 0.725 at
  cap32 / 0.852 at cap128; mean CCR 0.046 at cap32 / 0.020 at cap128;
  strict reversal fraction 1.0e-03 at cap32, 1.5e-06 at cap128)

Classification applied verbatim from the pre-registered `DESIGN.md` Section
3 rule, not re-derived after seeing results. See
`docs/PE_CLAIM_EVIDENCE_LEDGER.md` C10 for full values and required caveats
(sample vs. population, capacities 32/128 only, mean-vs-median Jaccard
nuance).

## 4. Currently Running: Full-Population MRU Continuation Census

- tmux session: `lafc-mru-census-20260914` (exited after successful run)
- Branch: `experiment/continuation-mru-population-census-20260914`
- Harness HEAD: `1a29e77` (worktree at
  `.claude/worktrees/continuation-mru-population-census-20260914`)
- RUN_ID: `20260914T042528Z_1a29e773a113`

**Status: VALIDATED AND INTEGRATED.** Validation branch
`analysis/continuation-mru-census-validation-20260915` commit `95e3a41`
records 60/60 chunks, 2{,}363{,}286/2{,}363{,}286 records, 0 duplicate/
missing/extra keys, 30/30 gates PASS, independent recheck PASS, and
`FULL_CENSUS_VALID: true`. Manuscript integration imports only compact
evidence under
`analysis/continuation_policy_mru_population_census_20260914/validated/20260914T042528Z_1a29e773a113/`;
raw census output remains outside the manuscript branch.

## 5. Hypothesis Map (updated)

| Hypothesis | State (prior handoff) | State (this document) |
|---|---|---|
| H_TARGET | CONDITIONALLY SUPPORTED | Unchanged; see ledger C1/C2 |
| H_OFFLINE_CLOSED_LOOP | SUPPORTED IN PILOT ONLY (2 cells) | **SUPPORTED AT TIER-1 SCALE** (8/9 non-degenerate cells concordant at H=16, r=0.6-0.9 magnitude correlation); two named, characterized exceptions — see ledger C5-C9 |
| H_LEARNED_POLICY | NOT SUPPORTED AS SUPERIOR TO LRU | Unchanged; Tier 2 not run and not authorized by this task |
| H_WIKI | NOT SUPPORTED AS DISCRIMINATIVE TARGET | Unchanged, now mechanistically explained (ledger C3, `CAUSALLY_ESTABLISHED`) |
| H_CONTINUATION | UNKNOWN / NOT TESTED | **ROBUST WITHIN EVALUATED SCOPE**: sampled MRU/random at capacities 32/128; full-population MRU at capacities 32/64/128/256 (ledger C10). Population-scale random and arbitrary deployed policies remain untested. |
| H_PRACTICAL_USE | PARTIALLY SUPPORTED, STRENGTHENED BY PILOT | Further strengthened by Tier-1/linkage/mechanistic evidence chain; see ledger C11 |
| H_PAIRWISE | OLD SHIPPED SAMPLE NOT CANONICAL | Unchanged; see `docs/PE_PAIRWISE_VIEW_JUSTIFICATION.md` (new in this task) for the provenance-remaining-issue assessment |
| H_MECHANISM | (did not exist in prior handoff) | Two of four candidate mechanisms DIRECTLY_SUPPORTED (MetaCDN LRU/MRU separation, wiki2018 degeneracy); two PLAUSIBLE_BUT_NOT_ESTABLISHED (MetaKV cold-start interaction, Twemcache SIEVE-vs-random) — see ledger C8 |

## 6. Performance Evaluation Manuscript State

Branch: `manuscript/performance-evaluation-template-20260913`, HEAD
`471b3c4`. **This branch is scientifically stale** — see Section 1 (it
branches from before any Tier-1/linkage/mechanistic/continuation evidence
existed) and reads, per direct inspection of `01_introduction.tex`, as "we
built a large benchmark release" rather than the intended Performance
Evaluation framing. It was not edited by this task except as documented in
`docs/PE_MANUSCRIPT_RESTRUCTURING_PLAN.md`'s "what was actually changed"
section — read that document for the exact integration decision (safe
copy-forward vs. merge; this task did not merge branches).

New planning/audit documents produced by this task (all in this branch's
`docs/`, none using census data):

- `PE_CLAIM_EVIDENCE_LEDGER.md` — every claim, exact evidence, exact value
- `PE_MANUSCRIPT_RESTRUCTURING_PLAN.md` — old-to-new section mapping, what was and was not edited
- `PE_RESEARCH_QUESTIONS.md` — final ~5 RQ set
- `PE_WORKED_EXAMPLE.md` — publication-quality worked cache-decision example
- `PE_PAIRWISE_VIEW_JUSTIFICATION.md` — pairwise-view rationale + provenance status
- `PE_YLOSS_YVALUE_DECISION.md` — y_loss/y_value redundancy recommendation
- `PE_FIGURE_TABLE_PLAN.md` — figure/table plan mapped to RQs
- `PE_CITATION_AUDIT.md` — bibliography metadata audit, including the LeCaR correction
- `PE_LITERATURE_SEARCH_GAPS.md` — literature positioning audit and gaps
- `PE_REVIEWER_CONCERN_CROSSWALK.md` — updated from the existing `analysis/closed_loop_offline_linkage_20260914/REVIEWER_ISSUE_MATRIX.md`
- `PE_HISTORICAL_REJECTION_RISK_CROSSWALK.md` — updated from `analysis/closed_loop_offline_linkage_20260914/HISTORICAL_REJECTION_RISK_MATRIX.md`

## 7. What Remains Before Performance Evaluation Submission

1. Census validation and integration into the ledger/manuscript (blocked on
   the census finishing; do not force).
2. Full manuscript rewrite following `PE_MANUSCRIPT_RESTRUCTURING_PLAN.md`
   beyond what this task actually edited (see that document's explicit
   "sections rewritten in this task" vs. "sections still pending" split).
3. External literature verification beyond what `PE_LITERATURE_SEARCH_GAPS.md`
   was able to check in this task's time budget.
4. Remaining citation metadata items flagged `NEEDS_EXTERNAL_VERIFICATION`
   in `PE_CITATION_AUDIT.md`.
5. Manuscript build/page-count/warnings verification after the full
   rewrite (only a partial build check was run in this task; see the
   restructuring plan).
6. A submission-readiness pass matching every remaining numerical claim in
   the finished manuscript text against `PE_CLAIM_EVIDENCE_LEDGER.md`.

## 8. Standing Rules (do not violate in any future task)

- Check for existing/equivalent work before running any experiment
  (Section "Permanent project rule" above).
- Never interpret or cite partial/unvalidated census output.
- Do not run Tier 2, add baselines, or rerun prior experiments without an
  explicit, separately authorized task.
- Do not modify the secondary simulator repository or protected
  experimental worktrees from a manuscript/writing task.
- Every strong manuscript claim must trace to a `PE_CLAIM_EVIDENCE_LEDGER.md`
  row; evidence wins over prose if they ever conflict.
