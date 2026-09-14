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

## What was actually changed (updated 2026-09-14, follow-on rewrite pass)

**Pass 1** (original task, HEAD `edc7607`): rewrote `01_introduction.tex`
and `09_limitations_ethics.tex`; fixed the LeCaR citation.

**Pass 2** (this follow-on task) added substantially more:

1. New `sections/03b_experimental_methodology.tex` (families/capacities/
   horizons/splits/policies/seeds/metrics, consolidated in one place).
2. Rewrote `sections/02_background.tex` to integrate the worked example
   (`docs/PE_WORKED_EXAMPLE.md`) as Figure 1, and added early citations
   (LRU/ARC/LIRS/SIEVE/S3-FIFO/LeCaR/LRB/Parrot/GL-Cache) so prior work is
   discussed by page 2, not only in Related Work.
3. Rewrote `sections/03_benchmark_design.tex` to lead with the scientific
   abstraction (trace/access/cache-state/eviction-decision/candidate-victim)
   before release mechanics.
4. Edited `sections/04_label_generation.tex` to add the y\_loss/y\_value
   dual-interface explanation (recommendation B, canonical + alias).
5. Fully rewrote `sections/08_characterization.tex` around target
   discriminativeness (RQ1), with Figure 2.
6. Added four new results sections: `08b_closed_loop.tex` (RQ2 part 1,
   Table 2), `08c_linkage.tex` (RQ2 part 2/RQ3, Figure 3),
   `08d_mechanistic.tex` (RQ3 part 2), `08e_continuation.tex` (RQ4, with
   one `% TODO-CENSUS` marker, no final Figure 5).
7. Added `08f_practical_implications.tex` (RQ5) and `09b_discussion.tex`
   (Discussion).
8. Extended `sections/06_release_validation.tex` with a provenance
   subsection (analysis-artifact chain, canonical-vs-sensitivity label
   distinction, census-not-validated statement, generator-provenance
   limitation).
9. Edited `sections/07_tasks_baselines.tex` to state explicitly that the
   shipped pairwise sample used is the canonical regenerated sample (not
   the historical stale one), and trimmed stale internal bug-fix
   narration.
10. Added `sections/13_appendix_release_tables.tex` (appendix) and moved
    3 orphaned schema/release tables into it, as planned but not executed
    in Pass 1.
11. Added new tables `table_tier1_closed_loop.tex` (Table 2) and
    `table_linkage_continuation_summary.tex` (Table 3).
12. Generated 4 figures via reproducible Python scripts under
    `paper/performance_evaluation/scripts/figures/` (Figures 1-4, wired
    into the manuscript) plus one explicitly-labeled preliminary,
    sampled-only Figure 5 draft (NOT wired into the manuscript, per the
    task's constraint against presenting census-adjacent evidence as
    final).
13. Rewrote the abstract to match the new RQ-organized framing.
14. Updated `09_limitations_ethics.tex`'s forward pointers from plain
    text to real `\ref{}`s now that the target sections exist.
15. Added `\usepackage{graphicx}` and reordered `main.tex`'s `\input`
    list.
16. Added a new Related Work subsection ("Offline Surrogate Evaluation
    and Closed-Loop Correspondence") for early positioning against the
    cross-domain offline/online-evaluation-correspondence literature.

Not yet done: Section 10 (Related Work)'s existing five subsections were
not otherwise rewritten (only the one new subsection was added); Section
5 (schema views) and Section 12 (AI-use disclosure) were left unedited;
no section was physically renamed/relabeled (new content used new files
instead, to avoid breaking existing `\ref{}`s under time pressure).

## Build/integration blocker check

No blocker was found. `pdflatex`/`latexmk` built the full manuscript
cleanly after both passes (see the final report's
`MANUSCRIPT_BUILD_RESULT`). All further restructuring is deferred by
choice, not because of a technical blocker.
