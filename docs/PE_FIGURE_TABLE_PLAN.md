# Figure and Table Plan

> **Status update 2026-09-15 (census integration task):** Figures 1-5 and Tables
> 1-3 (dataset scale, Tier-1 closed-loop, linkage+continuation summary)
> are now built and wired into the manuscript, generated reproducibly by
> scripts under `paper/performance_evaluation/scripts/figures/`. Figure 5
> now uses validated population-MRU census evidence while keeping sampled
> random evidence visibly scoped to capacities 32/128.

Status: NOT_PRESENT prior to this task. The manuscript branch
(`manuscript/performance-evaluation-template-20260913`) has 8 tables, all
release/schema-descriptive (dataset scale, decision breakdown, candidate
count stats, pairwise sample stats, artifact layout, split counts, regret/
tie stats, pairwise feature baselines) and no figures beyond a pipeline
overview PNG. None of them answer RQ1-RQ5 directly with the new evidence;
this plan replaces/supplements them rather than assuming they carry over.

Every entry below maps to exactly one RQ from `PE_RESEARCH_QUESTIONS.md`.
No decorative figures. No figure/table pair duplicates the same result
without a stated reason (checked explicitly in the last column).

## Figures

### Figure 1 — Worked cache-decision example

- RQ: RQ5 (practical implications), grounds vocabulary used throughout.
- Source: `PE_WORKED_EXAMPLE.md` (fully specified, hand-verifiable).
- Variables: none (illustrative, not data-driven).
- Visual type: schematic timeline diagram (see worked-example Section 9
  for the exact layout).
- Takeaway: shows what a decision, a candidate, a horizon, `y_loss`, and
  an optimal candidate set concretely are, including a tie.
- Placement: main text, early (Background or Methodology section), so the
  rest of the paper's vocabulary is grounded before any statistics appear.
- Duplication check: none — no other figure or table shows a single
  worked decision.

### Figure 2 — Target discriminativeness across family / capacity / horizon

- RQ: RQ1.
- Source: `analysis/sigmod_target_discriminativeness_20260913/` (per-family
  all-tied fraction table, already summarized in `PE_CLAIM_EVIDENCE_LEDGER.md`
  C1/C2).
- Variables: all-tied fraction (or 1 - all-tied fraction, i.e.
  discriminativeness) on the y-axis; family on the x-axis (or grouped
  bars); separate panels or series per capacity; H=16 as primary, H=4/H=8
  optionally as thin secondary series.
- Visual type: grouped bar chart (5 families x capacities), not a heatmap
  — with only 5 families and 2-4 capacities a bar chart is more precise to
  read than a heatmap and avoids the "decorative figure" risk.
- Takeaway: wiki2018 is exactly at 1.0 (fully degenerate); metacdn is near
  0 (highly discriminative); cloudphysics/metakv sit high (0.66-0.87);
  twemcache is intermediate and capacity-sensitive.
- Placement: main text.
- Duplication check: complements, does not duplicate, the "dataset/
  evaluation scope" table (Table A below), which reports scale, not
  discriminativeness.

### Figure 3 — Offline gap vs. closed-loop gap scatter

- RQ: RQ2.
- Source: `analysis/closed_loop_offline_linkage_20260914/outputs/rq_cl2_scatter_data.csv`
  (already computed; explicitly named as a "turn existing scatter data
  into a figure" remedy in `REVIEWER_ISSUE_MATRIX.md` item #12).
- Variables: offline regret-gap (x-axis) vs. closed-loop miss-ratio gap
  (y-axis), one point per (family, capacity, pair) at H=16; color by
  family; marker shape by pair (MRU-vs-LRU / random-vs-LRU); the two named
  discordant cells (cloudphysics/cap32, metakv/cap128) annotated directly
  on the plot.
- Visual type: scatter plot with a fitted trend line (r=0.835/0.755 per
  ledger C6) and the two discordant points labeled, not hidden.
- Takeaway: real, positive correspondence (RQ2's headline finding),
  honestly showing where it breaks down.
- Placement: main text.
- Duplication check: this is the *only* place the raw offline/closed-loop
  correlation is shown graphically; the correlation coefficients also
  appear in prose (Section on RQ2) but not as a redundant table, since the
  scatter already conveys the same numbers more informatively.

### Figure 4 — Capacity-scale locality vs. discriminativeness / closed-loop separation

- RQ: RQ3.
- Source: `analysis/closed_loop_mechanistic_analysis_20260914/` (trace-derived
  LRU hit rate) joined with discriminativeness (Figure 2's data) and
  closed-loop |MRU-LRU| separation (Tier-1 summary.csv).
- Variables: trace-derived LRU hit rate (x-axis) vs. two y-series across
  two small panels: (a) offline discriminativeness, (b) closed-loop
  |MRU-LRU| miss-ratio gap; one point per (family, capacity), n=10.
- Visual type: two side-by-side scatter panels sharing the x-axis.
- Takeaway: r=-0.83 (panel a) and r=0.90 (panel b) — the same trace
  property predicts both, explicitly the mechanistic story of RQ3/RQ1
  jointly.
- Placement: main text.
- Duplication check: distinct from Figure 3 — Figure 3 relates offline gap
  directly to closed-loop gap; Figure 4 relates an independent trace
  property to each of them separately, which is the mechanistic
  explanation, not the correspondence claim itself.

### Figure 5 — Continuation-policy robustness

- RQ: RQ4.
- Source: `analysis/continuation_policy_mru_population_census_20260914/validated/20260914T042528Z_1a29e773a113/figure5_mru_continuation_data.csv`,
  companion validated population summaries, and
  `analysis/continuation_policy_sensitivity_full_20260914/outputs/20260914T040333Z_1f66342be435/scientific_analysis.json`
  for sampled mean-random values.
- Variables: capacity on x-axis; Set-C mean Jaccard, mean
  cross-continuation regret, and fraction of LRU-optimal candidates still
  MRU/random-optimal. Population MRU appears at capacities 32/64/128/256;
  sampled MRU and sampled mean-random appear only at capacities 32/128.
- Visual type: three-panel line/marker plot generated by
  `paper/performance_evaluation/scripts/figures/make_figure5_continuation_robustness.py`.
- Takeaway: population MRU is near-identical to LRU across all four
  capacities; sampled random is more perturbing but remains formally
  ROBUST at capacities 32/128. The plot must not imply population random
  evidence.
- Placement: main text.
- LaTeX marker: none; the validated population census is now integrated.
- Duplication check: none — this is the only continuation-sensitivity
  figure; the underlying numbers also appear in
  `PE_CLAIM_EVIDENCE_LEDGER.md` C10 but that is a ledger, not manuscript
  prose or a manuscript table.

## Tables

### Table A — Dataset / evaluation scope

- RQ: supports all RQs (methodology grounding, not itself an RQ answer).
- Source: existing `table_dataset_scale.tex`/`table_decision_breakdown.tex`
  content (candidate rows 277,995,072; decisions 2,363,286; 5 families;
  capacities 32/64/128/256; horizons 4/8/16), reused, not recomputed.
- Placement: main text (Experimental Methodology section).
- Duplication check: this table is scale/scope only; it does not repeat
  any discriminativeness or closed-loop number (those are Figures 2-5).

### Table B — Tier-1 closed-loop results

- RQ: RQ2 (supporting detail for Figure 3), RQ3.
- Source: `analysis/closed_loop_tier1_evidence_20260914/run/*/summary.csv`,
  reused verbatim from the validated freeze (do not recompute).
- Content: per family/capacity/policy miss_ratio, misses,
  relative_miss_diff_vs_lru, for LRU/MRU/SIEVE/random-mean.
- Placement: main text or appendix depending on final page budget — this
  is the one candidate for appendix relocation, since its content is
  already visualized in Figures 2-4; if kept in the main text, trim to the
  H=16/primary-capacity rows and move the full 230-row table to the
  artifact/appendix.
- Duplication check: overlaps in *content* with Figures 3-4 (which plot
  derived quantities from this same table) — kept because reviewers
  specifically asked for "insufficient meaningful policy evaluation" (item
  #2 in `PE_REVIEWER_CONCERN_CROSSWALK.md`) to be answered with concrete
  numbers, not only a plot; if a page-budget cut is needed, this table
  should move to the appendix before any figure is cut.

### Table C — Continuation-policy sensitivity / robustness summary

- RQ: RQ4.
- Source: sampled-study `scientific_analysis.json` plus validated
  population-census summaries under
  `analysis/continuation_policy_mru_population_census_20260914/validated/20260914T042528Z_1a29e773a113/`.
- Content: sampled MRU/random capacity-32/128 values plus compact
  population-MRU Set-C values, including new capacities 64/256 and
  robustness classification.
- Placement: main text, directly beside Figure 5 (the table gives exact
  values; the figure gives the visual mean/median contrast).
- Duplication check: complements Figure 5 rather than duplicating it — the
  figure is for the visual mean-vs-median story, the table is for the
  exact citable numbers a reader would otherwise have to read off the
  figure.

## Deliberately not planned as main-text figures/tables

- Any table restating `y_loss`/`y_value` statistics twice (see
  `PE_YLOSS_YVALUE_DECISION.md`) — one column suffices.
- A predictor-feature table — the predictor-field issue
  (`candidate_is_predictor_victim == candidate_is_lru_victim`) is a
  limitation to state in prose, not a result to tabulate.
- Any Tier-2/learned-policy table — Tier 2 was never run; do not create a
  placeholder table for it.
- Any table implying population-scale random continuation or arbitrary
  deployed-policy robustness.
