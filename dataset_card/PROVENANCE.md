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

## 2. Processed traces

Processed traces are standardized outputs produced by preprocessing scripts from raw inputs. They may normalize record format, identifiers, metadata fields, and paging-view exports.

These processed traces are generated artifacts, but they are still trace-derived and may remain subject to upstream redistribution constraints.

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
