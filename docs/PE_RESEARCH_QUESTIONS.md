# Performance Evaluation Manuscript: Final Research Questions

Status: NOT_PRESENT prior to this task. The prior handoff's Section 11 listed
6 closed-loop-specific "production research questions" (RQ-CL1..CL6) as
internal analysis questions; this document distills them, plus the
continuation-sensitivity and practical-implications material, into the
~5 RQs the manuscript itself should be organized around. RQ-CL5 (learned
policy) and RQ-CL6 (wiki2018-specific) are folded into RQ2 and RQ1
respectively rather than kept as separate top-level RQs, per the
instruction to avoid too many RQs.

## RQ1 — Informativeness: When is the finite-horizon counterfactual target discriminative, and when does it degenerate?

- Maps to: ledger C1, C2, C3.
- Evidence: `analysis/sigmod_target_discriminativeness_20260913/`,
  `analysis/closed_loop_mechanistic_analysis_20260914/` (Q9).
- Planned figures/tables: Figure 2 (discriminativeness across
  family/capacity/horizon), Table "dataset/evaluation scope".

## RQ2 — Correspondence: Does offline candidate ranking correspond to closed-loop cache performance, and how well?

- Maps to: ledger C5, C6, C7, C8, C9.
- Evidence: `analysis/closed_loop_offline_linkage_20260914/`.
- Planned figures/tables: Figure 3 (offline gap vs. closed-loop gap
  scatter), Table "closed-loop results".

## RQ3 — Dependence: How does the offline/closed-loop relationship depend on workload, capacity, and horizon?

- Maps to: ledger C2, C4, C7, C8, C9.
- Evidence: `analysis/closed_loop_offline_linkage_20260914/` (RQ-CL3),
  `analysis/closed_loop_mechanistic_analysis_20260914/`.
- Planned figures/tables: Figure 4 (capacity-scale locality vs.
  discriminativeness / closed-loop separation).

## RQ4 — Robustness: How sensitive are the counterfactual labels to the continuation-policy assumption?

- Maps to: ledger C10.
- Evidence: `analysis/continuation_policy_sensitivity_full_20260914/`
  (sampled study, capacities 32/128; population census pending).
- Planned figures/tables: Figure 5 (continuation-policy robustness), with
  an explicit `% TODO-CENSUS` extension point once the population census
  validates.

## RQ5 — Practical guidance: What does this imply for researchers choosing between offline and closed-loop evaluation?

- Maps to: ledger C11, C12, and the cross-cutting caveats section.
- Evidence: synthesis of RQ1-RQ4; no new artifact of its own.
- Planned figures/tables: none dedicated; this RQ is answered in prose
  (Practical Implications section) using the results already tabulated
  under RQ1-RQ4, plus the worked example (`PE_WORKED_EXAMPLE.md`) as an
  illustrative anchor.

## Explicitly excluded from top-level RQ status

- Learned-policy (`evict_value_v1`) closed-loop competitiveness: Tier 2 was
  never run and is out of scope for this task; do not promote to an RQ
  without new, separately authorized evidence. Mentioned only as a
  limitation/future-work item.
- Pairwise-view and y_loss/y_value questions: these are representation and
  schema-design questions, not empirical RQs; addressed in
  `PE_PAIRWISE_VIEW_JUSTIFICATION.md` and `PE_YLOSS_YVALUE_DECISION.md`
  respectively, referenced from the manuscript's methodology section rather
  than posed as RQs.

## RQ -> experiment -> figure/table coverage check

| RQ | Experiments used | Figures/tables |
|---|---|---|
| RQ1 | target-discriminativeness audit, mechanistic Q9 | Fig 2, scope table |
| RQ2 | Tier-1 closed-loop, linkage RQ-CL1 | Fig 3, closed-loop results table |
| RQ3 | linkage RQ-CL3, mechanistic Q1-Q8/Q10 | Fig 4 |
| RQ4 | continuation pilot + full sampled study | Fig 5, sensitivity summary table |
| RQ5 | synthesis + worked example | Fig 1 (worked example), prose only |

No validated experiment in the current evidence chain lacks an RQ home; no
RQ lacks at least one validated evidential source. Tier-2/learned-policy and
population-census results are the only evidence categories currently
without a place in the main-text RQ structure (by design, per the
constraints of this task).
