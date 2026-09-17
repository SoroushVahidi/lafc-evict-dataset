# Problem 7 Phase 7: cross-section contradiction audit

Checked the specific contradiction patterns the Problem-7 spec calls out,
plus a general Abstract/Introduction/Results/Discussion/Limitations/
Conclusion sweep for the headline numbers.

## Specifically checked patterns

1. **"universally useful" vs "regime-conditioned."** No section claims
   universal usefulness. Abstract, Section 8 ("Interpretation"), Section 8f,
   and the Conclusion all consistently use "conditionally, not uniformly,
   discriminative" / "regime-conditioned benchmark" language. **No
   contradiction.**

2. **"LRU best nearly everywhere" vs "LRU best 4/10."** Every occurrence of
   "9 of 10" (`sections/08b_closed_loop.tex` lines 19, 54) is explicitly
   scoped to "this four-policy comparator set" / "the original four," and
   the expanded-comparator subsection immediately states the corrected
   "4 of 10" figure with an explicit "(down from 9 of 10 among the original
   four)." No section presents "9 of 10" as the paper's current headline
   number after the expanded-comparator subsection is introduced. **No
   contradiction** (see CLAIM_LEDGER.csv C08/C09).

3. **"longer horizons remove ties" vs H128 54.3% all-tied.** No sentence
   claims ties are removed or eliminated. `sections/01_introduction.tex:52`
   explicitly says separation "keeps rising with horizon *without
   eliminating* low-information regimes," and Section 8's matched-horizon
   paragraph states the H128 all-tied fraction (0.5434) directly next to the
   monotonicity claim. **No contradiction.**

4. **"continuation robust" without distinguishing MRU census from sampled
   random evidence.** `sections/08e_continuation.tex` keeps these separate
   throughout (sampled MRU/random at capacities 32/128 only, full-population
   MRU census at all capacities/horizons) and Figure 5's caption explicitly
   states "No population-scale random-continuation result is shown or
   implied." **No contradiction.**

## General sweep

- Headline stats (0.9912/0.0088/0.6766/0.0) appear in the Abstract,
  Introduction, Section 8, Limitations, and Conclusion -- checked all five
  occurrences are numerically identical (Problem 6's repetition-reduction
  pass already converted the Limitations/Conclusion instances to
  cross-references rather than restatements, so there is only one place the
  exact digits are stated in full: Section 8).
- Table values vs. prose: `table_matched_long_horizon_sensitivity.tex`,
  `table_problem5_expanded_closed_loop.tex`, `table_tier1_closed_loop.tex`,
  `table_regret_tie_stats.tex`, and `table_dataset_scale.tex` all spot-checked
  against the prose paragraphs that cite them (Section 8/8b) -- consistent.
- One real numeric inconsistency found between prose and its own underlying
  per-cell data (not a cross-*section* contradiction but a cross-check
  failure within Section 8b): the "four of the six cells... <3.2%" claim.
  See CLAIM_LEDGER.csv C10 -- fixed.
- No instance found of a figure/caption disagreeing with its source
  CSV/JSON, and no orphaned or duplicate-numbered table/figure (see
  FIGURE_TABLE_PROVENANCE.csv).

## Net result

One real internal miscount (C10, MODERATE, fixed) and one evidentiary-
strength gap (C13, the 08d correlation caveat, MODERATE, fixed). No
contradiction pattern from the spec's explicit list was found unresolved.
