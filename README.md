# LAFC-Evict Dataset Publication Repository

This is the canonical publication repository for LAFC-Evict.

## Current public release

**LAFC-Evict v1.0** is the current full public release.

- Hugging Face: https://huggingface.co/datasets/SoroushVahidi/lafc-evict
- Hugging Face revision: `v1.0` (commit `37173bc96de2a615455bf9713bb90d846156af29`)
- Scope: Full five-family release containing:
  - Alibaba Block (`cloudphysics`)
  - MetaCDN (`metacdn`)
  - MetaKV (`metakv`)
  - Twemcache (`twemcache`)
  - Wiki2018 (`wiki2018`)
- Size:
  - 277,995,072 candidate-level rows
  - 2,363,286 decision-horizon rows
  - 1,000,000 canonical pairwise-sample rows
- License: Multi-licensed by family -- CC0-1.0 (wiki2018), CC BY 4.0 (Alibaba Block, Twemcache), Apache License 2.0 (MetaCDN, MetaKV). See `THIRD_PARTY_DATA.md` and `dataset_card/LICENSE_DATA.md` for details.

**AWS Open Data and Older Releases:**
- The older wiki2018-only **v0.3** release remains available separately on AWS Open Data (bucket `lafc-evict-open-data`, region `us-west-2`) and on Hugging Face on the `main` revision.
- Zenodo remains on the DOI-backed **v0.2** preview release (version DOI https://doi.org/10.5281/zenodo.21895844, concept DOI https://doi.org/10.5281/zenodo.21895843). No Zenodo version DOI has been minted for v0.3 or v1.0.

See [`docs/LAFC_EVICT_PUBLICATION_STATE.md`](docs/LAFC_EVICT_PUBLICATION_STATE.md) for the detailed release hierarchy.

This repository is a standalone, conservative package for preparing the public release of **LAFC-Evict: Counterfactual Supervision for Learned Cache Eviction**.

It is intentionally limited to release-oriented code, schema definitions, metadata templates, benchmark-view builders, and a tiny synthetic example. It does **not** include raw traces, processed traces, generated large datasets, model artifacts, Slurm logs, or paper-specific research outputs.

LAFC-Evict releases **generated counterfactual supervision labels and benchmark views**. Upstream raw traces remain external source artifacts and should be cited separately using their original provenance and licensing terms.

## Associated Paper / Preprint

This dataset release accompanies the public preprint/manuscript:  
**Decision-aligned eviction-value prediction for robust learning-augmented caching**  
Soroush Vahidi.  
Available at SSRN 6636732.  
Status: public preprint; manuscript under peer review.

The paper describes the learning-augmented caching setting and the experiments
that motivated this dataset release. This repository provides dataset-release
artifacts, schemas, validation tools, benchmark views, and reproducibility
utilities. When using the data artifact, cite the paper/preprint and the
specific host/version used; cite the Zenodo DOI only for DOI-backed Zenodo
versions. As of this handoff, v0.3 has no documented Zenodo DOI.

## Repository boundaries

The publication repository focuses on:

- a canonical candidate-row schema,
- export of existing generated candidate rows into release-ready Parquet partitions,
- derived benchmark views:
  - one-row-per-decision summaries,
  - pairwise candidate comparisons,
- validation and checksum utilities,
- conservative release documentation for provenance, licensing, schema, and limitations.

Large release artifacts remain outside Git history and are represented by
manifests and host records. Scientific/source data and KBS
reviewer-response history are tracked in separate internal working
repositories outside this public release; they are not required to build,
audit, or reproduce anything in this repository, which is self-contained
via the compact validated evidence under `analysis/` and the manifests
above.

## Scientific framing

LAFC-Evict distinguishes five layers:

1. **External raw traces** acquired from upstream providers or public dumps.
2. **Processed traces** produced by preprocessing scripts.
3. **Generated features** computed by this codebase from processed traces and decision state.
4. **Generated counterfactual labels** computed by this codebase.
5. **Benchmark tasks** defined by this repository from those rows.

This repository does **not** claim authorship of upstream raw traces. The main `v1` label is **finite-horizon counterfactual LRU-continuation miss count after forcing one candidate eviction**, not an offline-optimal target.

The published v1.0 public release contains five trace families: alibaba-block (internal key `cloudphysics`), `metacdn`, `metakv`, `twemcache`, and `wiki2018`. Two further families, `brightkite` and `citibike`, remain blocked and are excluded from any public release. The registry is a release-governance tool, not legal advice.

## Repository layout

```text
dataset_card/   Release docs and metadata templates
examples/       Tiny synthetic example and baseline loader
manifests/      Release-manifest and source-trace templates
scripts/        Export, validation, checksum, and benchmark-view builders
src/            Standalone Python package
tests/          Pytest coverage for schema, views, validation, and checksums
publication/    Publication-state records, host manifests, and procedures
release/        Ignored local release payloads and validation artifacts
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

The v0.1-open commands below reproduce historical local staging artifacts;
they do not describe the current public release. Full pairwise materialization
is intentionally not part of the default real release because it can grow
quadratically with decision size.

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
