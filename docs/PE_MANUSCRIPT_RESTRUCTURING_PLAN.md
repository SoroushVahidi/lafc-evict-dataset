# Performance Evaluation Manuscript Restructuring Plan

Status: NOT_PRESENT prior to this task. `paper/performance_evaluation/`
(branch `manuscript/performance-evaluation-template-20260913` @ `471b3c4`)
is a **verbatim Elsevier/elsarticle template migration of the SIGMOD
manuscript** — `TEMPLATE_MIGRATION_REPORT.md` confirms this, and the
section files are byte-identical in name and near-identical in content to
`paper/sigmod2027/latex/sections/01_introduction.tex` through
`12_ai_use_disclosure.tex`. Direct inspection of `01_introduction.tex`
confirms it still opens with "277,995,072 candidate rows... a shipped
pairwise sample" framing and never mentions Tier-1, linkage, mechanistic,
or continuation-sensitivity evidence — i.e. exactly the "reads like a
dataset schema report" failure mode this task is meant to fix. **No
restructuring toward a Performance Evaluation journal argument has
happened yet.** This plan is new.

## Branch/lineage note (why this had to be a plan, not a merge)

`manuscript/performance-evaluation-template-20260913` branches from
`analysis/sigmod-target-discriminativeness-20260913` @ `76d562f` — the
*old* SIGMOD-era commit — not from the validated
Tier-1/linkage/mechanistic/continuation lineage this task's branch
(`manuscript/pe-evidence-restructure-20260914`, off `484417c`) is built on.
`git merge-base` between the two branches returns `76d562f`, and neither is
an ancestor of the other. **This task does not merge the two branches** (per
instruction: "Do not merge existing branches"). Instead: the manuscript
LaTeX sources were **copied forward** (not merged) into this branch's
`paper/performance_evaluation/` tree — a plain `git show
manuscript/performance-evaluation-template-20260913:<path>` extraction per
file, preserving the original template/Elsevier structure and
acknowledgments, so that editing happens on top of the validated evidence
lineage rather than the reverse. This is documented explicitly here so a
future integration (reconciling this branch's edits back with any further
work done directly on `manuscript/performance-evaluation-template-20260913`)
is a deliberate, visible decision rather than a silent divergence. See
Section "What was actually changed" below for the exact copy performed.

## Old section -> new section mapping

| Old (SIGMOD-template, `01`-`12`) | New (PE, ~14-part) | Action |
|---|---|---|
| `01_introduction.tex` | 1. Introduction | REWRITE — remove dataset-scale-first opening; open with the scientific story (see `PE_CLAIM_EVIDENCE_LEDGER.md`/`PE_RESEARCH_QUESTIONS.md`); state RQ1-RQ5 explicitly. |
| `02_background.tex` | 2. Background and motivating example | REWRITE + MERGE — keep the learned-eviction background, insert the worked example (`PE_WORKED_EXAMPLE.md`) as the motivating example (new content, addresses reviewer concern #8). |
| `03_benchmark_design.tex` | 3. Evaluation methodology / LAFC-Evict construction | REWRITE — retitle away from "benchmark design"; keep label-definition content but lead with counterfactual-label semantics, not release packaging. |
| `04_label_generation.tex` | 3 (merged into above) | MERGE — label generation mechanics belong inside Section 3, not a standalone section; avoid the schema-report feel of two adjacent sections both about label construction. |
| `05_schema_views.tex` | Appendix / artifact reproducibility | MOVE TO APPENDIX — column-level schema detail is artifact documentation, not main-narrative content, per the "avoid a paper that reads like a dataset schema report" instruction. Candidate/decision/pairwise *view relationships* (not full column lists) stay in Section 3 as a short paragraph; full schema moves out. |
| `06_release_validation.tex` | 14. Artifact/reproducibility information | MOVE TO END — release/validation mechanics belong with reproducibility material, not mid-paper. |
| `07_tasks_baselines.tex` | 4. Experimental methodology | REWRITE — keep task definitions (value regression, best-candidate selection, pairwise preference) but reframe as the experimental design that RQ1-RQ5 are answered with, and add the new evaluations (Tier-1 closed-loop, linkage, mechanistic, continuation) that did not exist when this section was written. |
| `08_characterization.tex` | 5. Target discriminativeness + 8. Mechanistic workload analysis | SPLIT — the existing target-discriminativeness content becomes Section 5; the new mechanistic-analysis evidence (not present in this section at all currently) becomes Section 8. |
| (none — did not exist) | 6. Closed-loop policy evaluation | NEW — Tier-1 results (`analysis/closed_loop_tier1_evidence_20260914/`); no prior manuscript section covers this. |
| (none — did not exist) | 7. Offline<->closed-loop correspondence | NEW — linkage results (`analysis/closed_loop_offline_linkage_20260914/`); no prior manuscript section covers this. |
| (none — did not exist) | 9. Continuation-policy sensitivity | NEW — sampled full-study results (`analysis/continuation_policy_sensitivity_full_20260914/`), with the single `% TODO-CENSUS` marker for future population-scale extension. |
| (none — did not exist) | 10. Practical implications / guidance | NEW — synthesis section answering RQ5; did not exist in the SIGMOD-derived draft. |
| `09_limitations_ethics.tex` | 11. Limitations | REWRITE — the existing limitations section predates every caveat in `PE_CLAIM_EVIDENCE_LEDGER.md`'s cross-cutting-caveats block (finite-horizon labels, LRU-canonical continuation, tie-dominated target, wiki2018 degeneracy, unit-capacity/unconditional-admission abstraction, MetaCDN validation-window caveat, MetaKV cold-start caveat, sampled-continuation-scope caveat); every one of those must be added. Ethics content, if still applicable, stays merged here or splits to artifact info. |
| `10_related_work.tex` | 12. Related work | REWRITE per `PE_LITERATURE_SEARCH_GAPS.md` and `PE_CITATION_AUDIT.md`; fix the LeCaR author-metadata error identified in this task. |
| `11_conclusion.tex` | 13. Conclusion | REWRITE — align with the restated RQ1-RQ5 and their actual (bounded, honestly-caveated) answers rather than the old benchmark-release framing. |
| `12_ai_use_disclosure.tex` | 14 (folded into Artifact/reproducibility, or kept standalone if the venue requires it) | KEEP — venue-required disclosure content; not a scientific-content section, lowest priority to touch. |
| (none) | Figure/table set | NEW — see `PE_FIGURE_TABLE_PLAN.md`; none of the 8 existing tables directly answer RQ1-RQ5 (they are release/schema descriptive) and none of the 5 new figures currently exist. |

## Material that belongs in appendix/artifact rather than main narrative

- Full column-by-column schema (`05_schema_views.tex` content).
- Release validation mechanics and checksums (`06_release_validation.tex`
  content) — belongs with reproducibility info (new Section 14), not
  mid-paper.
- The full 230-row Tier-1 results table (Table B in
  `PE_FIGURE_TABLE_PLAN.md`) if page budget is tight; keep only H=16/
  primary rows in the main text.
- `artifact_layout` and `split_counts` tables — pure release bookkeeping,
  appendix/artifact only.

## Exact RQs

See `PE_RESEARCH_QUESTIONS.md` (RQ1-RQ5, each mapped to evidence and to a
figure/table).

## Planned figures/tables

See `PE_FIGURE_TABLE_PLAN.md` (5 figures, 3 main-text tables, explicit
duplication checks, explicit appendix candidates).

## What was actually changed in this task (see also `FINAL_HEAD` in the
completion report)

This task performed the following concrete, committed edits (not merely
planning) on `paper/performance_evaluation/` in this branch, copied forward
from `manuscript/performance-evaluation-template-20260913` as described
above:

1. Rewrote `sections/01_introduction.tex` to open with the scientific
   story (per the required framing) instead of dataset-scale numbers, and
   to state RQ1-RQ5 explicitly.
2. Rewrote `sections/09_limitations_ethics.tex` to add every cross-cutting
   caveat from `PE_CLAIM_EVIDENCE_LEDGER.md`.
3. Fixed the LeCaR citation author-metadata error in
   `latex/refs.bib` (see `PE_CITATION_AUDIT.md`).
4. Did **not** rewrite Sections 2-8, 10, 12-13 in this task — that is the
   largest remaining piece of manuscript work (see
   `docs/CURRENT_PROJECT_STATUS_AND_HANDOFF_20260914B.md` Section 7 and the
   final report's `REMAINING_MANUSCRIPT_WORK`). Rewriting all eleven
   remaining content sections to publication quality in one pass was judged
   higher-risk than doing the two highest-leverage, most reviewer-visible
   sections (Introduction, Limitations) correctly and leaving the rest as
   an explicit, planned to-do rather than a rushed, unverified rewrite.
5. Did not move any section to appendix in this task (the file moves
   themselves are mechanical LaTeX restructuring that should happen
   together with the full section rewrite, not split across two passes).

## Build/integration blocker check

No blocker was found preventing the above four edits from being made
directly and built (`pdflatex`/`latexmk` are available in this
environment; see the final report's `MANUSCRIPT_BUILD_RESULT`). The
remaining, larger restructuring (full section rewrite + file moves) is
deferred by choice (Section "What was actually changed", item 4), not
because of a technical blocker.
