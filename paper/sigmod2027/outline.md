# Outline

## Proposed title

LAFC-Evict: A Large-Scale Counterfactual Benchmark for Learned Cache Eviction: [Experiments & Analysis]

## Draft abstract

Learned cache-eviction methods are increasingly evaluated on proprietary traces, task-specific preprocessing pipelines, and non-comparable supervision targets, which makes empirical comparison difficult. This paper presents LAFC-Evict, a large-scale benchmark for learned cache eviction built around decision-aligned counterfactual supervision. Each benchmark row represents one candidate victim at one eviction decision and includes release-facing provenance fields, cache-state features, and a finite-horizon counterfactual label defined as the continuation-policy miss count after forcing that eviction. The benchmark also provides decision-level summaries and pairwise preference views to support ranking, classification, and regret-oriented evaluation. The current open release spans multiple trace families and exposes hundreds of millions of candidate rows together with checksums, schema documentation, and validation utilities. Beyond introducing the dataset, the paper characterizes its label structure, tie behavior, decision complexity, and cross-family variation, and it establishes simple baseline tasks for candidate scoring, best-candidate prediction, and pairwise preference modeling. The goal is to provide a reproducible, release-oriented benchmark that makes learned cache-eviction evaluation more comparable, transparent, and extensible.

## 1. Introduction

- Motivate learned cache eviction as an empirical field with fragmented benchmarks.
- State the evaluation problem: inconsistent traces, inconsistent labels, and poor release hygiene.
- State the contribution: a benchmark artifact, not just a method.
- Preview the three task views: candidate, decision, pairwise.

## 2. Background and Motivation: Learned Cache Eviction

- Explain full-cache miss decisions and victim selection.
- Distinguish heuristic, learned, and learning-augmented policies.
- Explain why per-decision candidate supervision is useful.
- Clarify that the benchmark label is finite-horizon, continuation-policy-specific, and not globally optimal.

## 3. Benchmark Design

- Describe the five-layer provenance split:
  raw traces, processed traces, generated features, generated labels, benchmark tasks.
- Explain the release scope for `lafc-evict-v0.1-open`.
- Explain trace-family governance and why some families remain excluded.
- State benchmark desiderata: scale, releaseability, validation, derived tasks.

## 4. Counterfactual Label Generation

- Define `y_loss` and `y_value`.
- Explain one row per candidate victim at one decision.
- Explain capacities, horizons, and split bookkeeping.
- Explain the relationship between candidate labels, decision-optimal candidates, and pairwise preferences.
- Clarify what is inherited from the upstream pipeline versus what is defined in this repository.

## 5. Dataset Schema and Views

- Present the canonical candidate schema.
- Group features into request, candidate, cache-summary, disagreement, and recent-rate families.
- Define the decision view:
  candidate count, best loss, optimal candidates, tie count, regret summaries.
- Define the pairwise view / pairwise sample:
  shared decision metadata, candidate-pair fields, pairwise labels.

## 6. Release Construction and Validation

- Describe the memory-safe release builder and DuckDB-based out-of-core export.
- Describe release manifest, checksums, governance files, and publication bundle.
- Describe validation checks:
  schema completeness, split normalization, family scope, duplicate candidates, metadata consistency, decision-view consistency, checksum validation.
- Explain the current migration/preservation path and why release hardening matters for benchmark papers.

## 7. Benchmark Tasks and Baselines

- Candidate-level regression on `y_loss` or `y_value`.
- Decision-level best-candidate classification or ranking.
- Pairwise preference prediction.
- Baseline families:
  LRU-derived heuristics, predictor-score baseline, linear/logistic models, tree-based baselines, small MLP if practical.
- Evaluation metrics to define later:
  regression error, top-1 decision accuracy, regret-aware ranking metrics, pairwise accuracy/AUC.

## 8. Empirical Characterization

- Scale overview:
  rows, decisions, families, capacities, horizons, files, release size.
- Family and split composition.
- Decision complexity:
  candidate counts and tie behavior.
- Label shape:
  `y_loss`, `y_value`, regret, and pairwise label distributions.
- Cross-family heterogeneity and benchmark difficulty.

## 9. Limitations, Ethics, and Reuse

- Finite-horizon continuation-policy labels are not universal optimality labels.
- Trace redistribution remains family-dependent.
- Some families remain excluded pending review.
- Offline benchmark gains do not automatically imply online deployment gains.
- Reuse guidance for non-public or future extended releases.

## 10. Related Work

- Learned and classical eviction policies.
- Learning-augmented systems.
- Counterfactual supervision and offline evaluation.
- Systems benchmarks and release papers.

## 11. Conclusion

- Reiterate benchmark contribution and intended impact.
- Emphasize release quality, validation, and comparability.
- Point to future extensions:
  additional families, stronger baselines, downstream deployment studies.

## Figures and tables to reserve early

- One benchmark overview table.
- One schema/view figure.
- One release pipeline figure.
- One composition table for family/capacity/horizon counts.
- One or two characterization figures.
- One baseline-results table.

## Page-budget warning

The 12-page SIGMOD submission limit is tight for a benchmark paper. Main text should prioritize:

1. motivation,
2. benchmark design and label definition,
3. release construction and validation,
4. empirical characterization,
5. a compact baseline section.

Detailed ablations, long schema tables, and extra diagnostic plots should be planned for appendix or supplementary artifact material.
