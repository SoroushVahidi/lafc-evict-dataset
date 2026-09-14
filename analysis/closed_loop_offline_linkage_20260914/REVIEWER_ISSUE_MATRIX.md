# Reviewer Issue Matrix (post-linkage-analysis)

Status after this linkage analysis (see SCIENTIFIC_SUMMARY.md for the
numbers backing each classification). No manuscript was edited.

| # | Concern | Status | Evidence | Smallest adequate remedy |
|---|---|---|---|---|
| 1 | Unclear contribution / terminology | PARTIALLY_ADDRESSED | The contribution can now be stated concretely: a reusable offline counterfactual supervision layer whose signal is shown (RQ-CL1/CL2, this analysis) to track closed-loop policy behavior in most, not all, workload/capacity regimes, with the regimes characterized. The wording itself hasn't changed. | MANUSCRIPT_ONLY: state the contribution using the RQ-CL1-CL4 findings directly. |
| 2 | Insufficient meaningful policy evaluation | ADDRESSED | 230 real closed-loop replays, 4 policies, 5 families, 2 capacities, 20 seeds, now linked quantitatively to the offline evidence with concordance/correlation statistics, not just miss ratios in isolation. | -- |
| 3 | Target nearly degenerate | PARTIALLY_ADDRESSED (CLAIM_NARROWED) | Confirmed again by this analysis (all-tied fraction 0.66-0.87 in 3/5 families at H=16), but now also shown that the degeneracy *itself* is informative: it predicts (r=0.968, exploratory) where closed-loop separation will be small, and it is *not* present in twemcache/metacdn, which show the strongest offline-closed-loop agreement. | CLAIM_NARROWING: frame the target as "informative where discriminative, honestly degenerate elsewhere" rather than claiming general discriminativeness. |
| 4 | Offline LRU-continuation labels may not predict deployed behavior | PARTIALLY_ADDRESSED | Directly tested for the first time: predicts well in 8/9 non-degenerate cells (concordance) with real correlation (r=0.6-0.9), fails in 2 identified, small-offline-signal cells (cloudphysics/cap32, metakv/cap128). Not a universal predictor, but not an unfounded assumption either -- now an evidenced, bounded claim. | MANUSCRIPT_ONLY: state the bounded finding, not a universal claim. |
| 5 | Continuation-policy dependence | NOT_ADDRESSED | Explicitly out of scope for this task and for Tier 1 generally; this analysis does not touch the fixed-LRU-continuation assumption in label construction at all. | NEW_EXPERIMENT: the continuation-policy sensitivity experiment remains the only adequate remedy; nothing here substitutes for it. |
| 6 | Narrow cache abstraction (unit-capacity, single-item paging) | NOT_ADDRESSED | Unchanged; this analysis and Tier 1 both use the same abstraction as the canonical dataset. | Out of scope; would require new label generation, not new analysis. |
| 7 | Need for a worked example | NOT_ADDRESSED | This analysis produces tables, not a narrative worked example. | MANUSCRIPT_ONLY: one concrete worked cell (e.g. metacdn/cap32/H16, the strongest-agreement case, or metakv/cap128, the identified reversal) walked through in prose would satisfy this cheaply using data already computed here. |
| 8 | Related work/positioning | NOT_ADDRESSED | Untouched; a citation/writing task. | CITATION_AUDIT: unchanged from the canonical handoff's existing to-do list. |
| 9 | Artifact/reproducibility completeness | ADDRESSED for this analysis specifically | Every number here is reproducible from committed CSV/JSON via two independent code paths (`compute_rq_analyses.py` + `independent_recheck.py`), with 14 passing consistency tests and a byte-verified evidence freeze. | -- |
| 10 | Pairwise representation justification/provenance | NOT_ADDRESSED | Untouched by this task; the known pairwise provenance gap (stale `pairwise_sample.parquet`, documented in the target-discriminativeness REPORT.md Section 5) is unrelated to Tier 1 and was not revisited here. | ARTIFACT/REPRODUCIBILITY: regenerate the pairwise sample from the post-fix pipeline, as already recommended in that report; out of scope here. |
| 11 | y_loss/y_value redundancy | NOT_ADDRESSED | Not investigated by this task. | Out of scope; a separate data-generation-code question. |
| 12 | Weak/unhelpful figures/tables | PARTIALLY_ADDRESSED | This analysis produces new, genuinely informative tables (per-cell concordance, per-horizon correlation, per-family regime characterization) that did not exist before, but none have been turned into manuscript-ready figures. | MANUSCRIPT_ONLY: turn `outputs/rq_cl2_scatter_data.csv` into an actual scatter figure (offline gap vs. closed-loop gap, colored by family) -- the data already exists. |
| 13 | Citation correctness | NOT_ADDRESSED | Untouched; unrelated to this task. | CITATION_AUDIT: unchanged from the canonical handoff's existing to-do list. |

## Remedy summary by type

- **NEW_EXPERIMENT** (genuinely required, not substitutable by analysis): continuation-policy sensitivity (#5).
- **NEW_ANALYSIS** (already done in this task): #2, #4, #9, most of #1/#3.
- **MANUSCRIPT_ONLY** (writing, no new computation needed): #1 (contribution wording), #3/#4 (claim narrowing), #7 (worked example), #12 (turn existing scatter data into a figure).
- **ARTIFACT/REPRODUCIBILITY**: #10 (pairwise regeneration, pre-existing, unrelated to Tier 1).
- **CITATION_AUDIT**: #8, #13 (pre-existing, untouched).
- **Out of scope entirely for any near-term remedy**: #6, #11.

No expensive new experiment is recommended for any item that is really a
writing problem (#1, #7, #12) or a citation problem (#8, #13); the one
genuinely unresolved *experimental* gap is continuation-policy sensitivity
(#5), which cannot be closed by any amount of further analysis of existing
data.
