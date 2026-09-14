# Reviewer Concern Crosswalk (Performance Evaluation submission)

Status: PARTIALLY_COMPLETE prior to this task. Built on and updates
`analysis/closed_loop_offline_linkage_20260914/REVIEWER_ISSUE_MATRIX.md`
(13 items, current as of the linkage-analysis task) rather than starting
over. That matrix predates the mechanistic analysis and the full
continuation-sensitivity study; this document reflects both, adds items
#11-#14 explicitly (pairwise view, y_loss/y_value, figures/tables,
citation correctness — present only implicitly or not at all in the prior
matrix), and adds the census-dependency column required for this task.
**A writing problem is never marked resolved merely because evidence now
exists** — the "manuscript action still required" column is non-empty for
every item, including items whose evidence is complete.

| # | Concern | Status | Evidence resolving it | Manuscript action still required | Artifact action still required | Census-dependent |
|---|---|---|---|---|---|---|
| 1 | Unclear contribution / terminology | PARTIALLY_ADDRESSED | Full evidence chain (Tier-1, linkage, mechanistic, continuation) now supports a concrete, evidenced contribution statement (`PE_RESEARCH_QUESTIONS.md` RQ1-RQ5). | Rewrite Introduction/contribution statement using RQ1-RQ5 directly (done for Introduction in this task; see `PE_MANUSCRIPT_RESTRUCTURING_PLAN.md`). Avoid central-narrative jargon ("release-facing provenance fields", "decision-aligned supervision layer") per the writing-style requirement. | None. | NO |
| 2 | Insufficient meaningful evaluation | ADDRESSED | 230 Tier-1 closed-loop replays + linkage analysis (`PE_CLAIM_EVIDENCE_LEDGER.md` C5-C9), not just isolated miss ratios. | Integrate Tier-1/linkage results into main text (Sections 6-7 of the restructuring plan; not yet written). | None. | NO |
| 3 | Target degeneracy | PARTIALLY_ADDRESSED (claim narrowed, not hidden) | `PE_CLAIM_EVIDENCE_LEDGER.md` C1-C3; degeneracy shown to be informative in itself (predicts where closed-loop separation will be small). | Frame as "informative where discriminative, honestly degenerate elsewhere," never as uniform discriminativeness (Section 5 of restructuring plan). | None. | NO |
| 4 | Closed-loop validity | PARTIALLY_ADDRESSED | Directly tested for the first time via linkage analysis; 8/9 non-degenerate cells concordant, r=0.6-0.9 (ledger C5/C6), two named bounded exceptions (C7/C8). | State the bounded finding, name both exceptions explicitly, never claim universal predictive validity (Section 7 of restructuring plan). | None. | NO |
| 5 | Continuation policy | SUBSTANTIALLY_ADDRESSED (sampled scope) | Full sampled study, capacities 32/128, both MRU and mean-random continuation ROBUST (ledger C10). | State sampled scope explicitly every time this result is cited; insert `% TODO-CENSUS` marker (Section 9 of restructuring plan, done for Figure 5 in `PE_FIGURE_TABLE_PLAN.md`). | None now; population census may extend scope later (do not use until validated). | **YES** — population-scale extension pending; sampled result itself is NOT census-dependent for correctness, only for scope-widening. |
| 6 | Narrow cache model | NOT_ADDRESSED | None; unchanged by any task to date. | State explicitly as a limitation (unit-object/count-capacity, unconditional admission, no byte/latency/dirty-write cost) — added to `sections/09_limitations_ethics.tex` in this task. | Would require new label generation to broaden; out of scope for any manuscript task. | NO |
| 7 | Worked example | **ADDRESSED in this task** | `PE_WORKED_EXAMPLE.md` — new, self-contained, hand-verifiable, includes a genuine tie. | Insert as Figure 1 / motivating example (Section 2 of restructuring plan); not yet inserted into the actual `.tex` in this task. | None. | NO |
| 8 | Related work | **SUBSTANTIALLY_ADDRESSED (2026-09-14 literature-positioning task)** | `10_related_work.tex` fully restructured into 6 scientific categories (production workloads, learned cache replacement, modern heuristic/non-learning eviction, learning-augmented caching theory, offline-vs-closed-loop evaluation, positioning); `PE_LITERATURE_CITATION_COVERAGE_AUDIT` (independent, verified) drove 6 new references (LAH/S4-FIFO, HALP, Qiu/Yang/Harchol-Balter, Baleen, HotOS'23 lazy-promotion/quick-demotion, CacheLib), all now cited in-text; explicit HALP-vs-pairwise-view distinction added; explicit learned-from-data-vs-learning-augmented-theory distinction preserved and sharpened. | 4 remaining gap categories (Cache-Coliseum, subsampling paper, DAgger, Park) and the cross-domain (non-caching) offline-vs-closed-loop search are still open — see `PE_LITERATURE_SEARCH_GAPS.md`. Not a blocker for this concern's core ask (current, defensible related-work positioning), which is now met. | None. | NO |
| 9 | Artifact completeness | PARTIALLY_ADDRESSED | Every new evidence artifact (Tier-1, linkage, mechanistic, continuation) is independently gate-validated and byte-verified. | Artifact/reproducibility section (Section 14 of restructuring plan) needs to reference these gates explicitly; not yet written. | Public pairwise-sample promotion decision still deferred (see item 11). | NO |
| 10 | Artifact completeness (release-side) | UNCHANGED | Prior handoff Sections 4/7/8 (public v0.3 wiki2018-only scope, predictor-field issue) unchanged, not re-investigated in this task. | State the public/canonical dataset-scope distinction plainly (carried forward from prior handoff). | Predictor-field issue remains unresolved upstream; out of scope for a manuscript task. | NO |
| 11 | Pairwise view justification | **ADDRESSED in this task** | `PE_PAIRWISE_VIEW_JUSTIFICATION.md` — four concrete reasons, explicitly stated as a derived view carrying no new ground truth. | Insert into methodology section (Section 3 of restructuring plan); not yet inserted into the actual `.tex`. | Canonical regenerated pairwise sample can be cited directly; public-release promotion remains a separate, deferred release decision (see the same document). | NO |
| 12 | y_loss/y_value redundancy | **ADDRESSED in this task** | `PE_YLOSS_YVALUE_DECISION.md` — recommendation B (canonical + documented alias), grounded in an audit of actual code usage. | Apply the recommendation consistently in prose once Sections 3/4 are rewritten; not yet applied beyond the decision document itself. | None; schema compatibility explicitly preserved. | NO |
| 13 | Figures/tables | PARTIALLY_ADDRESSED | `PE_FIGURE_TABLE_PLAN.md` — 5 figures + 3 tables planned, each mapped to an RQ with explicit duplication checks; none of the 8 existing tables answer the new RQs. | Actually build the 5 figures/3 tables from the cited source artifacts; not done in this task (plotting scripts not yet written). | None. | Figure 5 only (continuation robustness) — see item 5. |
| 14 | Citation correctness | **SUBSTANTIALLY_ADDRESSED (2026-09-14)** | `PE_CITATION_AUDIT.md` — 50 entries (44 + 6 new, each independently verified against a primary source before being added), 0 undefined citations confirmed by a clean `latexmk` build (0 `[?]` markers), LeCaR error previously found and fixed. Decision recorded (not deferred) on the 2 uncited entries: both left bibliography-only, with reasoning documented. | None — the decision this row previously deferred has now been made and documented. | None. | NO |

## Summary counts

**Note (2026-09-14):** rows #1-#7, #9, #10, #13 below predate the
`manuscript/pe-evidence-restructure-20260914` full rewrite (commit
`c23b28d`), which substantially advanced most of them (the Introduction,
worked example, Tier-1/linkage/closed-loop results, figures, and tables
this row references are now written into the actual `.tex`, not merely
planned). Those counts were **not** re-audited in this literature-only
follow-on task and are stale; only rows #8 and #14 (both literature/
citation concerns) were re-verified and updated here. A full re-audit of
this table against the current manuscript state is recommended before
submission but is out of this task's scope.

- ADDRESSED (in this task or already, with only insertion-into-.tex
  remaining): 3 (#7, #11, #12) — **stale, see note above**
- SUBSTANTIALLY_ADDRESSED: 3 (#5, #8, #14 — #8/#14 updated 2026-09-14)
- PARTIALLY_ADDRESSED: 6 (#1, #2, #3, #4, #9, #13) — **stale, see note above**
- NOT_ADDRESSED: 1 (#6, a genuine scope limitation, not a fixable gap)
- UNCHANGED: 1 (#10, release-side, out of scope for this task)
- Census-dependent: 1 of 14 (#5, and #13's Figure 5 only) — every other
  item is fully resolvable without the population census.
