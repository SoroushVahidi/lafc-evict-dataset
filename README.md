# LAFC-Evict Dataset Release Scaffold

This repository is a standalone, conservative package for preparing the public release of **LAFC-Evict: Counterfactual Supervision for Learned Cache Eviction**.

It is intentionally limited to release-oriented code, schema definitions, metadata templates, benchmark-view builders, and a tiny synthetic example. It does **not** include raw traces, processed traces, generated large datasets, model artifacts, Slurm logs, or paper-specific research outputs.

LAFC-Evict releases **generated counterfactual supervision labels and benchmark views**. Upstream raw traces remain external source artifacts and should be cited separately using their original provenance and licensing terms.

## Associated Paper / Preprint

This dataset release accompanies the public preprint/manuscript:  
**Decision-aligned eviction-value prediction for robust learning-augmented caching**  
Soroush Vahidi.  
Available at SSRN 6636732.  
Status: public preprint; manuscript under peer review.

The paper describes the learning-augmented caching setting and the experiments that motivated this dataset release. This repository provides dataset-release artifacts, schemas, validation tools, benchmark views, and reproducibility utilities. When using the data artifact, cite both the paper/preprint and the dataset release DOI once the DOI is available.

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

The first public release should be restricted to **license-clean/open-trace** families only. In particular, **CitiBike** and **Brightkite** require redistribution review before they should appear in any public non-synthetic release.

The intended first real public subset is **`lafc-evict-v0.1-open`**, selected through the machine-readable source-family registry in `manifests/source_family_registry.yaml`. That registry is a release-governance tool, not legal advice.

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
python scripts/build_real_release.py \
  --input-manifest /path/to/generated/candidate_rows/manifest.json \
  --family-selection manifests/lafc_evict_v0_1_open_families.json \
  --output-dir release/lafc-evict-v0.1-open \
  --dataset-id lafc-evict-v0.1-open \
  --dry-run
```

The memory-safe real-release builder defaults to dry-run. Pass `--overwrite` to materialize release artifacts. It uses DuckDB for out-of-core CSV shard ingestion and Parquet export, so it does not load the full selected subset into pandas memory.

`lafc-evict-v0.1-open` is the first real public release target. It includes only the selected open trace families from `manifests/lafc_evict_v0_1_open_families.json` and excludes CitiBike and Brightkite. Full pairwise materialization is intentionally not part of the default real release because it can grow quadratically with decision size; use `--pairwise-sample` for a capped sample or derive pairwise tasks from candidate rows.

Legacy export (loads all shards into pandas memory; not safe for the full real release):

```bash
python scripts/export_lafc_evict_parquet.py \
  --input-path /path/to/generated/candidate_rows_or_manifest \
  --output-dir release/lafc-evict-v0.1-open
```

Install from a fresh clone:

```bash
pip install -e .[dev]
```

Build derived benchmark views:

```bash
python scripts/build_decision_view.py \
  --input-path release/lafc-evict-v0.1-open/data/candidate_rows \
  --output-path release/lafc-evict-v0.1-open/data/decision_view/decision_view.parquet
```

```bash
python scripts/build_pairwise_view.py \
  --input-path release/lafc-evict-v0.1-open/data/candidate_rows \
  --output-path release/lafc-evict-v0.1-open/data/pairwise_view/pairwise_view.parquet
```

Validate the candidate rows:

```bash
python scripts/validate_release_schema.py \
  --input-path release/lafc-evict-v0.1-open/data/candidate_rows
```

Select the intended first real public trace-family subset:

```bash
python scripts/select_release_families.py \
  --registry manifests/source_family_registry.yaml \
  --release-scope v0.1-open \
  --output manifests/lafc_evict_v0_1_open_families.json
```

This selector is a governance aid for `lafc-evict-v0.1-open`. CitiBike and Brightkite remain excluded until review is complete, and `lafc-evict-full-heavy_r1` remains an internal/reproducibility target until redistribution questions are resolved.

Build the real public release (dry-run first):

```bash
python scripts/build_real_release.py \
  --input-manifest /path/to/generated/candidate_rows/manifest.json \
  --family-selection manifests/lafc_evict_v0_1_open_families.json \
  --output-dir release/lafc-evict-v0.1-open \
  --dataset-id lafc-evict-v0.1-open \
  --dry-run
```

Validate a built real release:

```bash
python scripts/validate_real_release.py \
  --release-root release/lafc-evict-v0.1-open
```

## Build a synthetic sample release

```bash
python scripts/build_sample_release.py \
  --input examples/tiny_candidate_rows.csv \
  --output-dir release/lafc-evict-sample-v0.1 \
  --overwrite
```

This command is only a release-workflow smoke test. It builds a fully synthetic dry-run package and is not a scientific benchmark release.

## Development

Run the test suite:

```bash
python -m pytest
```

The tiny synthetic example in [`examples/tiny_candidate_rows.csv`](examples/tiny_candidate_rows.csv) is only for tests and smoke checks.
