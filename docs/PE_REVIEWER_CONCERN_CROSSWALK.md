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
| 8 | Related work | PARTIALLY_ADDRESSED | `PE_CITATION_AUDIT.md`, `PE_LITERATURE_SEARCH_GAPS.md` — LeCaR fixed; 5 categories of missing references confirmed still open. | Full related-work rewrite pending a complete literature pass (Section 12 of restructuring plan, not yet done). | None. | NO |
| 9 | Artifact completeness | PARTIALLY_ADDRESSED | Every new evidence artifact (Tier-1, linkage, mechanistic, continuation) is independently gate-validated and byte-verified. | Artifact/reproducibility section (Section 14 of restructuring plan) needs to reference these gates explicitly; not yet written. | Public pairwise-sample promotion decision still deferred (see item 11). | NO |
| 10 | Artifact completeness (release-side) | UNCHANGED | Prior handoff Sections 4/7/8 (public v0.3 wiki2018-only scope, predictor-field issue) unchanged, not re-investigated in this task. | State the public/canonical dataset-scope distinction plainly (carried forward from prior handoff). | Predictor-field issue remains unresolved upstream; out of scope for a manuscript task. | NO |
| 11 | Pairwise view justification | **ADDRESSED in this task** | `PE_PAIRWISE_VIEW_JUSTIFICATION.md` — four concrete reasons, explicitly stated as a derived view carrying no new ground truth. | Insert into methodology section (Section 3 of restructuring plan); not yet inserted into the actual `.tex`. | Canonical regenerated pairwise sample can be cited directly; public-release promotion remains a separate, deferred release decision (see the same document). | NO |
| 12 | y_loss/y_value redundancy | **ADDRESSED in this task** | `PE_YLOSS_YVALUE_DECISION.md` — recommendation B (canonical + documented alias), grounded in an audit of actual code usage. | Apply the recommendation consistently in prose once Sections 3/4 are rewritten; not yet applied beyond the decision document itself. | None; schema compatibility explicitly preserved. | NO |
| 13 | Figures/tables | PARTIALLY_ADDRESSED | `PE_FIGURE_TABLE_PLAN.md` — 5 figures + 3 tables planned, each mapped to an RQ with explicit duplication checks; none of the 8 existing tables answer the new RQs. | Actually build the 5 figures/3 tables from the cited source artifacts; not done in this task (plotting scripts not yet written). | None. | Figure 5 only (continuation robustness) — see item 5. |
| 14 | Citation correctness | PARTIALLY_ADDRESSED | `PE_CITATION_AUDIT.md` — 0 undefined citations, 2 uncited entries flagged, LeCaR error found and fixed against a live authoritative source. | Decide on the 2 uncited entries (cite or remove) during the related-work rewrite; add the still-missing references once `PE_LITERATURE_SEARCH_GAPS.md`'s remaining categories are searched. | None. | NO |

## Summary counts

- ADDRESSED (in this task or already, with only insertion-into-.tex
  remaining): 3 (#7, #11, #12)
- SUBSTANTIALLY_ADDRESSED: 1 (#5)
- PARTIALLY_ADDRESSED: 8 (#1, #2, #3, #4, #8, #9, #13, #14)
- NOT_ADDRESSED: 1 (#6, a genuine scope limitation, not a fixable gap)
- UNCHANGED: 1 (#10, release-side, out of scope for this task)
- Census-dependent: 1 of 14 (#5, and #13's Figure 5 only) — every other
  item is fully resolvable without the population census.
