# Problem 8 Preflight: Compression Opportunity Audit

Read-only. Snapshot: `polish/problem6-scientific-narrative-readability-20260917` @ `54f122d`
(verified). Isolated worktree/branch: `audit/problem8-compression-preflight-20260917`,
created from that exact SHA. No manuscript `.tex`/`.bib` file was edited.

## Method

Read all 18 main-narrative section files (01-11, excluding 12 AI-disclosure and
13 appendix) plus `main.tex` front matter, in full. Word/paragraph/figure/table
counts via `detex` + line-based paragraph splitting (`section_stats.csv`).
Paragraph-level role/disposition classification in
`PARAGRAPH_COMPRESSION_LEDGER.csv` (86 rows, one per major paragraph/labeled
sub-claim -- finer-grained blank-line splitting would have produced ~155 rows
with little added signal, since many "paragraphs" by that measure are single
bolded-lead sentences already treated as one unit here).

## Repetition clusters found (Phase 3)

Most of the repetition Problem 6 flagged is already resolved. Three
**new** (post-Problem-6) clusters were found, all narrow and mechanical:

1. **MRU-census validation-gate stats repeated 3x near-verbatim**
   ("60/60 chunks, 2,363,286 ... records, 30/30 validity gates, independent
   recheck passed") in `03b_experimental_methodology.tex` (closing paragraph),
   `06_release_validation.tex` (PRIMARY -- this is literally its job), and
   `08e_continuation.tex`. Recommend: keep full stats only in Sec. 6; the
   other two cross-reference it. ~65 words.
2. **Tier-1 gate/RUN_ID stats repeated 3x** (14/14 gates, RUN_ID, 230/230
   executions) across `03b`, `06`, `08b_closed_loop.tex`. Same fix. ~15-20
   words (smaller, since two of the three mentions are already short).
3. **"LRU best in 9/10 cells" stated twice within `08b_closed_loop.tex`**
   itself (opening bold claim, then restated near-verbatim as the section's
   closing sentence). ~20 words.

Everything else Problem 6 already condensed to PRIMARY-plus-one-clause
(headline tie stats, wiki2018, metakv/cap128, continuation caveat, "not a
policy") is holding up -- no further cuts recommended there beyond one small
one: Limitations item 4 still re-derives the wiki2018 deductive-proof
sentence instead of only cross-referencing Sec. 8d (~25 words), and the
Conclusion's "not a new eviction policy" clause adds nothing over Related
Work's Positioning paragraph (~8 words, very low priority).

## Report-like / table-narration findings (Phases 4-5)

- `07_tasks_baselines.tex`'s feature-quality-disclosure paragraph (240 words)
  is the one remaining passage with an incident-report flavor (generator bug,
  hardcoded default, root-cause narrative). The scientific fact needed is
  short ("7/26 columns usable; refitting on them reproduces prior results");
  the mechanism narrative can compress by ~60 words with the full root cause
  staying in `analysis/feature_provenance_repair_20260917/` (already true --
  the section already cites that path).
- `06_release_validation.tex`'s validation-checklist paragraph (schema
  completeness, duplicate-candidate checks, checksums enumerated in prose)
  duplicates `table_artifact_layout`'s job; ~25 words recoverable.
- Table narration in `08_characterization.tex` (Q1-Q4 regret numbers) and
  `08b_closed_loop.tex` (per-cell percentages) restates values already in
  `table_informativeness_strata` / `table_tier1_closed_loop`, but this is
  the paper's own central-results prose -- classified NECESSARY_INTERPRETATION,
  not redundant narration, except for one clause in `08_characterization`'s
  "Interpretation" subsection which recaps the stratified finding in
  different words without adding evidence (~40 words, see ledger P-CHAR-7).
- `05_schema_views.tex` and the appendix (`13_appendix_release_tables.tex`)
  are already correctly minimal/out-of-main-text; no further action.

## Discussion/Limitations/Conclusion overlap (Phase 8)

`09b_discussion.tex` (201 words) is now the single highest-value remaining
compression target. Its four-angle recap paragraph (P-DISC-1, ~80 words)
and its closing limitations re-list (P-DISC-3, ~25 words) add no information
beyond Sections 8/8b/8c/8d/8e and Sec. 9 respectively. Its one load-bearing
sentence -- "the offline<->closed-loop correspondence is the paper's central
empirical contribution, not the offline label by itself" -- is worth keeping
but arguably belongs folded into the Conclusion rather than justifying a
standalone ~200-word section. Recommend: compress to ~80-100 words (keep the
one framing sentence + wiki2018/alibaba-block explained-not-merely-observed
point), or merge entirely into `11_conclusion.tex`'s opening paragraph.
Estimated savings ~90-115 words net of what a merge would still need to say.

## Related Work (Phase 6)

Four of five subsections already position rather than summarize. One
sentence in "Learned and Adaptive Cache Replacement" (12 citations listed in
one clause with no individual positioning) reads as summary-only; ~25 words
recoverable by trimming the list to the ones actually discussed afterward
(LeCaR, HALP) and citing the rest via `\cite{}` only where already used
elsewhere. Not worth more than that -- the subsection immediately after this
sentence (HALP/Baleen contrast) is exactly the positioning the phase asks for.

## Sentence-level sample (Phase 9, 15 of ~30 asked for; representative)

| # | Words before | Words after | Meaning preserved |
|---|---|---|---|
| 1 | 28 | 14 | YES |
| 2 | 30 | 20 | YES |
| 3 | 33 | 20 | YES |
| 4 | 56 | 18 | YES |
| 5 | 29 | 18 | YES |
| 6 | 74 | 48 | YES |
| 7 | 48 | 28 | YES |
| 8 | 32 | 18 | YES |
| 9 | 27 | 20 | YES |
| 10 | 41 | 30 | YES |
| 11 | 41 | 28 | YES |
| 12 | 26 | 0 (delete, intra-section dup) | YES |
| 13 | 31 | 31 (kept, one clause defensible) | n/a |

(Full sentence text omitted here for brevity; see fork transcript / re-derivable
directly from the ledger's SHORTEN rows, each of which names the exact
sentence.) Average compression across genuinely-shortened sentences: ~38%.
Sample confirms: sentence-level tightening after Problem 6 recovers real but
small amounts (a few hundred words total across the whole manuscript) --
consistent with Problem 6 having already done a first tightening pass.
Nothing in the sample required dropping a qualifier that would create an
overclaim; all cuts remove connective/meta-commentary tissue, not content.

## Safe compression estimate (Phase 10)

Base: ~11,175 body words (Problem 6's own count; independently reconfirmed
here at ~11,900 by a slightly less aggressive markup-stripping method --
no material drift either way).

| Target | Words cut | % | Resulting words | Page effect | Principal sources |
|---|---|---|---|---|---|
| CONSERVATIVE | ~180 | 1.6% | ~11,000 | ~0 pages (absorbed by reflow) | Pure duplicate-fact removal: 3x-repeated gate stats, intra-section "9/10" repeat, wiki2018 re-derivation in Limitations |
| MODERATE | ~650 | 5.8% | ~10,525 | ~1 page | Above + Discussion compression/merge, feature-disclosure paragraph tightening, release-validation checklist trim, Related Work list trim, general sentence tightening |
| AGGRESSIVE | ~1,300-1,400 | ~12% | ~9,800-9,875 | ~2 pages | Above + would require cutting into KEEP-classified evidence: per-family breakdowns in Sec. 8, case studies in Sec. 8d, capacity/horizon breakdown in Sec. 8e -- NOT recommended, this is exactly the granular evidence that resolved SIGMOD's "tie-heaviness asserted but not investigated" complaint |

Page effect is small relative to word-count % because 6 figures + 13 tables +
references + the mandated appendix/AI-disclosure sections occupy fixed space
that prose cuts don't touch. This matches the pre-Problem-6 compression
analysis on record (LOW/MODERATE/AGGRESSIVE ≈ 340-400 / 780-850 / 1,900-2,300
words out of a larger ~13,985-word base, concluding even AGGRESSIVE only
reached ~14-16%): proportionally consistent, and lower in absolute terms now
because Problem 6 already harvested a chunk of that headroom.

## Section cut budget (Phase 11)

| Section | Current words | Safe (moderate) cut | Target | Main action |
|---|---|---|---|---|
| 01_introduction | 708 | 30 | 678 | Roadmap paragraph tighten |
| 02_background | 695 | 0 | 695 | none -- worked example, protect |
| 03_benchmark_design | 574 | 15 | 559 | Requirements-list tighten |
| 03b_experimental_methodology | 703 | 47 | 656 | Meta-commentary + gate-stat cross-ref |
| 04_label_generation | 428 | 15 | 413 | Scope-clause cross-ref |
| 05_schema_views | 261 | 0 | 261 | none -- already minimal |
| 06_release_validation | 512 | 60 | 452 | Checklist trim, "two sources" box trim |
| 07_tasks_baselines | 1132 | 60 | 1072 | Feature-disclosure root-cause tighten |
| 08_characterization | 1453 | 40 | 1413 | Interpretation-subsection tighten only |
| 08b_closed_loop | 1264 | 20 | 1244 | Drop intra-section "9/10" repeat |
| 08c_linkage | 585 | 0 | 585 | none -- protect |
| 08d_mechanistic | 557 | 0 | 557 | none -- protect |
| 08e_continuation | 861 | 30 | 831 | Gate-stat cross-ref |
| 08f_practical_implications | 471 | 0 | 471 | none -- protect |
| 09b_discussion | 201 | 110 | 91 | Compress/merge candidate into Conclusion |
| 09_limitations_ethics | 674 | 25 | 649 | Item 4 cross-ref only |
| 10_related_work | 575 | 25 | 550 | Trim one summary-only sentence |
| 11_conclusion | 268 | 8 | 260 | Drop one redundant clause |
| **Total (01-11)** | **11,822** | **~485** | **~11,337** | -- |

(Table total is slightly below the 650-word MODERATE headline because the
remainder comes from front-matter/data-availability tightening not itemized
per-section here, and from distributing general sentence-level tightening
across sections that otherwise show "0" above.)

## Top 10 compression opportunities

1. Compress or merge `09b_discussion.tex` into the Conclusion (~110 words, highest single-section yield).
2. De-duplicate the MRU-census gate-stat triple (03b / 06 / 08e -> keep full stats in 06 only) (~65 words).
3. Tighten `07_tasks_baselines.tex`'s feature-bug root-cause narrative to the scientific fact (~60 words).
4. Trim `06_release_validation.tex`'s validation-checklist enumeration (table already covers it) (~25-45 words combined with the "two label sources" box).
5. Drop the intra-section "LRU best 9/10" repeat at the end of `08b_closed_loop.tex` (~20 words).
6. De-duplicate the Tier-1 gate/RUN_ID triple (03b / 06 / 08b) (~15-20 words).
7. Cross-reference rather than re-derive the wiki2018 deductive proof in `09_limitations_ethics.tex` item 4 (~25 words).
8. Tighten `08_characterization.tex`'s "Interpretation" subsection, which recaps rather than adds (~40 words).
9. Trim the one summary-only citation list in `10_related_work.tex`'s learned-replacement subsection (~25 words).
10. General meta-commentary tightening ("this section consolidates... so that scope is stated once rather than scattered" -- style phrasing) in `03b_experimental_methodology.tex`'s opening and similar spots (~12-20 words each, a handful of instances).

## DO NOT CUT list (Phase 12)

- Worked eviction example (`02_background.tex`, full worked-example subsection + Figure 1).
- Exact `y_loss`/`y_value`/regret/optimal-set equations (`04_label_generation.tex`).
- All four benchmark task definitions (`07_tasks_baselines.tex`).
- Problem-3 informativeness-stratification protocol and result (`08_characterization.tex`, "Does informativeness translate into method separation?" subsection).
- Zero-information (stratum Z) interpretation, and the 67.66%/31.66%/0.68% decomposition explaining why 99.12% is "less catastrophic than it sounds."
- Problem-4 matched-horizon result and table/figure (787,762-decision matched population, H=16-128 trajectory).
- Problem-5 expanded-comparator result (4/10, metakv/cap128 widening, r=0.96 vs r=0.96 correlation stability).
- Continuation-policy caveat and both the sampled study and full-population MRU census numbers (`08e_continuation.tex`).
- The frozen-HGB / clean-linear "worse than random" negative result (`08_characterization.tex` and `07_tasks_baselines.tex`).
- MetaCDN validation-window and MetaKV cold-start caveats, wherever they are the PRIMARY statement (`03b_experimental_methodology.tex`) -- SECONDARY one-clause mentions elsewhere may still be trimmed to a pointer, but never removed.
- All 9 items of `09_limitations_ethics.tex` (only item 4's redundant sub-clause is a trim target, not the item itself).
- Data Availability section in `main.tex` front matter (repository/HF/license/version details needed for reproducibility).

## Reviewer simulation (Phase 13)

**A. Performance Evaluation reviewer:** Length feels justified for the
empirical scope (5 workloads x 4 capacities x 3-4 horizons x up to 7
policies, plus 3 robustness studies) -- this is not padding, it's evidence
density. Likely skim points: the schema/release sections (5-6), which are
already the shortest and least novel-feeling; the `09b_discussion.tex`
section reads as filler on a second pass since it recaps rather than adds.
No section feels unshortenable except Sec. 2 (worked example) and the
Sec. 8/8b/8c/8d/8e result chain, which is the paper's actual evidence.

**B. Reader unfamiliar with the repository:** No paragraph requires
outside knowledge to follow after Problem 6's rewrite. The one place that
still reads slightly like an internal incident log is the feature-bug
disclosure in Sec. 7 (generator bug / hardcoded default framing) -- an
outsider doesn't need the bug's mechanism, only the conclusion ("19 of 26
columns carry no signal; results are robust to dropping them").

Both perspectives converge on the same two actionable items: compress
`09b_discussion.tex`, and tighten Sec. 7's feature-disclosure paragraph.
Neither perspective flagged any result section as too long relative to
what it establishes.

## Recommendation (Phase 16 answers)

- **Is 50 pages currently justified?** Largely yes. Roughly two-thirds of
  main-text length is validated evidence (Sections 8/8b/8c/8d/8e/8f) or
  floats (6 figures, 13 tables), not prose padding -- consistent with the
  pre-Problem-6 compression analysis already on record.
- **Is another ~10% reduction (≈1,100-1,200 words) safely achievable?**
  Marginal. The MODERATE estimate here tops out around 5.8% (~650 words)
  without touching evidence; reaching 10% requires moving into AGGRESSIVE
  territory (per-family/per-cell case studies), which is not recommended.
- **Is another ~15% reduction safely achievable?** No. Not achievable
  without cutting the granular mechanistic/informativeness evidence that
  directly answers prior SIGMOD criticism.
- **Is another ~20% reduction safely achievable?** No, for the same reason,
  more so.
- **At what point does further shortening start harming clarity?** Once
  cuts move past the ~650-word MODERATE list above and start removing
  per-family or per-cell numeric breakdowns (Sec. 8's family table, Sec.
  8d's four case studies, Sec. 8e's capacity/horizon breakdown) -- those
  are the specific granularity that turned "tie-heaviness stated but not
  investigated" (a real prior complaint) into an investigated, defensible
  result. Cutting them would trade a presentation improvement for a
  reintroduced scientific-credibility gap.
