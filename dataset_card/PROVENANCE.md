# Provenance

LAFC-Evict must separate upstream data from generated supervision.

## 1. External raw traces

These originate from external providers, public dumps, or upstream workload repositories. Examples of source families referenced in the original research repository include:

- Twemcache,
- MetaKV,
- MetaCDN,
- CloudPhysics,
- Wikimedia pageviews,
- CitiBike,
- Brightkite.

This project does **not** claim authorship of those raw traces.

Release-scope decisions about those families are tracked separately in the machine-readable source-family registry. That registry is a release-governance tool, not legal advice.

## 2. Processed traces

Processed traces are standardized outputs produced by preprocessing scripts from raw inputs. They may normalize record format, identifiers, metadata fields, and paging-view exports.

These processed traces are generated artifacts, but they are still trace-derived and may remain subject to upstream redistribution constraints.

The current public release is the Wiki2018-only v0.2 published preview. The
historical `v0.1-open` trees are unpublished local staging artifacts. Only
families with explicit publication clearance may enter a public release.

## 3. Generated features

Generated features are produced by this codebase from processed traces and current decision state. They include request-context, candidate-context, cache-summary, and disagreement features such as:

- request bucket/confidence,
- candidate recency and predictor/LRU features,
- cache bucket statistics,
- recent candidate request/hit rates.

## 4. Generated labels

Generated labels are counterfactual supervision outputs produced by this codebase. For the main `v1` release path:

- `y_loss` is the finite-horizon counterfactual LRU-continuation miss count after forcing one candidate eviction.
- `y_value = -y_loss`.

This is a generated label family. It should not be described as an upstream annotation, and it should not be described as offline-optimal.

## 5. Benchmark tasks

Benchmark tasks are repository-defined views built from generated candidate rows:

- pointwise candidate-row prediction,
- decision-level summaries,
- pairwise candidate comparison rows.

These benchmark tasks are authored in this project and are distinct from the upstream traces.

## 6. Current release boundary

Wiki2018 is currently cleared for the published derived preview with
attribution and caveat requirements. CloudPhysics, MetaCDN, MetaKV, and
Twemcache remain `eligible_pending_final_review` but are not publication
cleared. CitiBike and Brightkite remain blocked pending license/privacy review.
