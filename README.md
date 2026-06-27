# LAFC-Evict Dataset Release Scaffold

This repository is a standalone, conservative package for preparing the public release of **LAFC-Evict: Counterfactual Supervision for Learned Cache Eviction**.

It is intentionally limited to release-oriented code, schema definitions, metadata templates, benchmark-view builders, and a tiny synthetic example. It does **not** include raw traces, processed traces, generated large datasets, model artifacts, Slurm logs, or paper-specific research outputs.

## Scope

The current `v0.1` scaffold focuses on:

- a canonical candidate-row schema,
- export of existing generated candidate rows into release-ready Parquet partitions,
- derived benchmark views:
  - one-row-per-decision summaries,
  - pairwise candidate comparisons,
- validation and checksum utilities,
- conservative release documentation for provenance, licensing, schema, and limitations.

Large release artifacts are expected to be hosted later on a dataset host such as Hugging Face or Zenodo rather than committed to GitHub.

## Scientific framing

LAFC-Evict distinguishes five layers:

1. **External raw traces** acquired from upstream providers or public dumps.
2. **Processed traces** produced by preprocessing scripts.
3. **Generated features** computed by this codebase from processed traces and decision state.
4. **Generated counterfactual labels** computed by this codebase.
5. **Benchmark tasks** defined by this repository from those rows.

This repository does **not** claim authorship of upstream raw traces. The main `v1` label is **finite-horizon counterfactual LRU-continuation miss count after forcing one candidate eviction**, not an offline-optimal target.

## Repository layout

```text
dataset_card/   Release docs and metadata templates
examples/       Tiny synthetic example and baseline loader
manifests/      Release-manifest and source-trace templates
scripts/        Export, validation, checksum, and benchmark-view builders
src/            Standalone Python package
tests/          Pytest coverage for schema, views, validation, and checksums
```

## Quick start

Create a release from an existing generated candidate-row directory or manifest:

```bash
python scripts/export_lafc_evict_parquet.py \
  --input-path /path/to/generated/candidate_rows_or_manifest \
  --output-dir release/lafc-evict-v0.1-open
```

Build derived benchmark views:

```bash
python scripts/build_decision_view.py \
  --input-path release/lafc-evict-v0.1-open/candidate_rows \
  --output-path release/lafc-evict-v0.1-open/decision_view.parquet
```

```bash
python scripts/build_pairwise_view.py \
  --input-path release/lafc-evict-v0.1-open/candidate_rows \
  --output-path release/lafc-evict-v0.1-open/pairwise_view.parquet
```

Validate the candidate rows:

```bash
python scripts/validate_release_schema.py \
  --input-path release/lafc-evict-v0.1-open/candidate_rows
```

## Development

Run the test suite:

```bash
python -m pytest
```

The tiny synthetic example in [`examples/tiny_candidate_rows.csv`](examples/tiny_candidate_rows.csv) is only for tests and smoke checks.
