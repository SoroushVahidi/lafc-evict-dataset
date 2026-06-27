# Datasheet for LAFC-Evict

## Motivation

LAFC-Evict is intended to support supervised learning and benchmarking for cache-eviction decisions using counterfactual labels derived from generated candidate rows.

## Composition

Each canonical row represents one candidate eviction at one eviction decision. A release may also provide derived decision-level and pairwise benchmark views.

## Collection process

LAFC-Evict does not originate the upstream raw traces. Instead, the pipeline starts from externally sourced traces, preprocesses them into a common format, then generates features and labels.

Those upstream raw traces must be cited separately and may have their own licensing or attribution obligations.

## Preprocessing

The release pipeline assumes existing generated candidate rows are already available. This repository converts those rows into release-ready Parquet partitions and benchmark views without requiring raw traces in the release repository.

## Recommended uses

- supervised scoring of candidate victims,
- ranking and regret analysis,
- pairwise comparison tasks,
- decision-level benchmark evaluation.

## Out-of-scope uses

- claims of raw-trace ownership,
- claims that the default `v1` labels are globally optimal,
- redistribution of upstream traces without trace-family review.

The first public release should therefore be restricted to license-clean/open-trace families only. CitiBike and Brightkite require review before redistribution.

## Distribution

GitHub hosts only the lightweight release scaffold. Large release artifacts should be distributed through a dataset host with checksums and manifest metadata.

## Maintenance

The repository should version:

- schema changes,
- release-manifest format,
- trace-license status,
- benchmark-view definitions.
