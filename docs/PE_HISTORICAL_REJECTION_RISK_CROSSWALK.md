# Historical Rejection-Risk Crosswalk (Performance Evaluation submission)

Status: PARTIALLY_COMPLETE prior to this task. Builds on and updates
`analysis/closed_loop_offline_linkage_20260914/HISTORICAL_REJECTION_RISK_MATRIX.md`
(10 items, current as of the linkage-analysis task, itself already a
"post-linkage-analysis" update of an earlier version). This document adds
the mechanistic analysis, the full continuation-sensitivity study, and the
required categories from this task's brief (generalizable contribution,
experimental breadth, baseline sufficiency, venue fit, recent literature,
clarity, claims-vs-evidence discipline, mechanistic explanation, actionable
guidance, submission-quality verification) explicitly, mapping each to the
prior matrix's items where they already existed.

| Risk category (this task's required list) | Corresponds to prior matrix # | Status | What the manuscript must do to avoid repeating the pattern |
|---|---|---|---|
| Generalizable contribution | #1 (Insufficient novelty/generalizable insight) | PARTIALLY_REDUCED | State the contribution as the evidenced claim "offline discriminativeness predicts closed-loop separation" (r=0.968, exploratory, n=10 — ledger C4) and the informativeness/robustness characterization (RQ1-RQ4), not as a benchmark-scale claim. Must not overclaim beyond the stated n and exploratory-status caveats. |
| Experimental breadth | #2 (Narrow experimental evidence) | SUBSTANTIALLY_REDUCED | Already reduced by Tier-1 (5 families, 2 capacities, 20 seeds) plus linkage/mechanistic/continuation analyses covering all 10 family-capacity cells at 3 horizons. Manuscript must present this breadth explicitly (Table B, Table A) rather than only summarizing it in prose. |
| Baseline sufficiency | #3 (Weak/outdated baseline comparison) | UNCHANGED | See `PE_BASELINE_SUFFICIENCY_ASSESSMENT.md` — LRU/MRU/random/SIEVE assessed as adequate for the current RQs; no baseline was added by this task (none is authorized to be added without a separately justified, approved task). |
| Venue fit | #4 (Venue/audience mismatch) | UNCHANGED, ADDRESSABLE BY WRITING | The manuscript's current opening (`01_introduction.tex`, pre-edit) reads as a dataset-release paper, which is a SIGMOD/VLDB framing, not a Performance Evaluation framing. Rewritten Introduction in this task (see `PE_MANUSCRIPT_RESTRUCTURING_PLAN.md`) opens with the evaluation-methodology story instead. Remaining sections still need the same treatment. |
| Recent literature | #5 (Incomplete recent literature positioning) | UNCHANGED, PARTIALLY_ADDRESSED THIS TASK | `PE_LITERATURE_SEARCH_GAPS.md` — LeCaR fixed; 5 categories of missing references (Cache-Coliseum, subsampling paper, DAgger, Park, QD-LP) still open; two plausible 2025 arXiv candidates identified but not yet verified/added. |
| Clarity | #6 (Manuscript reads like a report rather than a scientific argument) | PARTIALLY_REDUCED | RQ1-RQ5 now have concrete, numerically answered results — the raw material for an argument-driven presentation exists (`PE_CLAIM_EVIDENCE_LEDGER.md`). Writing-style requirement (avoid "release-facing provenance fields", "decision-aligned supervision layer", "candidate-within-decision" jargon; lead with request/miss/eviction-decision vocabulary) applied to Introduction and Limitations in this task; the other ~9 sections are unchanged and still carry the old style. |
| Claims-vs-evidence discipline | #7 (Claims stronger than evidence) | PARTIALLY_REDUCED (contingent on continued discipline) | Every correlation in the evidence chain (r=0.6-0.97) rests on n=8-10; the source reports already hedge deliberately (no significance claims, exploratory items labeled). `PE_CLAIM_EVIDENCE_LEDGER.md` was built specifically so every manuscript sentence can be checked against it before submission (see item below, "submission-quality verification"). If a future pass strips these hedges, this risk re-emerges as NEW — flagged explicitly so it is not silently lost. |
| Mechanistic/theoretical explanation | #8 (Missing theoretical/mechanistic explanation) | PARTIALLY_REDUCED | 2 of 4 candidate mechanisms DIRECTLY_SUPPORTED (MetaCDN LRU/MRU separation, wiki2018 degeneracy — ledger C3/C8); 2 PLAUSIBLE_BUT_NOT_ESTABLISHED (MetaKV cold-start, Twemcache SIEVE-vs-random), honestly labeled rather than asserted. Manuscript (Section 8 of restructuring plan) must preserve these exact classification labels, not collapse them into a single "explained" narrative. |
| Actionable guidance | #9 (Insufficient actionable guidance) | PARTIALLY_REDUCED | Concrete guidance now exists and is evidenced: trust the offline signal most for twemcache/metacdn-like workloads at H=16; be cautious for cloudphysics-like near-zero-offline-gap regimes; MetaKV's first-window scoring is a known confound. This becomes the content of the new Section 10 (Practical Implications), not yet written. |
| Submission-quality verification | #10 (Inadequate scientific/numerical verification before submission) | SUBSTANTIALLY_REDUCED | Every headline number across Tier-1/linkage/mechanistic/continuation has independent-code-path verification, gate-passing, and byte-verified provenance. The remaining gap is a **manuscript-text-level** verification pass — matching every number that ends up in the finished prose against `PE_CLAIM_EVIDENCE_LEDGER.md` — which has not yet been run because the full manuscript rewrite is not yet done (see `CLAIMS_VERIFIED_AGAINST_EVIDENCE` in the completion report for what was checked for the two sections actually edited in this task). |

## What changed since the prior (`#1-#10`) matrix

- Mechanistic analysis (not reflected in the prior matrix, which predates
  it) resolves 2 of its own 4 candidate mechanisms directly, materially
  strengthening item #8 beyond "PARTIALLY_REDUCED (existing tables only)"
  to "PARTIALLY_REDUCED (existing tables + explicit mechanism
  classification)".
- The full continuation-sensitivity study (not reflected in the prior
  matrix) is new evidence directly relevant to items #1, #2, #7, and #9 —
  it is the single largest evidentiary addition since the prior matrix was
  written, and is reflected above in every relevant row.
- No item moved to fully RESOLVED — every remaining risk still requires
  either a writing action (clarity, venue fit, actionable guidance), a
  literature action (recent literature), or is a genuine, undisputed
  scope boundary (baseline sufficiency, narrow cache model — carried in
  the reviewer crosswalk's #6).
