# Reproduce and Export

This repository is designed to export a release from an **existing generated candidate-row dataset**. It does not require committing raw traces to GitHub.

## Associated Paper / Preprint

This dataset release accompanies the public preprint/manuscript:  
**Decision-aligned eviction-value prediction for robust learning-augmented caching**  
Soroush Vahidi.  
Available at SSRN 6636732.  
Status: public preprint; manuscript under peer review.

The paper describes the learning-augmented caching setting and the experiments that motivated this dataset release. This repository provides dataset-release artifacts, schemas, validation tools, benchmark views, and reproducibility utilities. When using the data artifact, cite both the paper/preprint and the dataset release DOI once the DOI is available.

## Inputs

Supported inputs for release export:

- a single candidate-row CSV,
- a single candidate-row Parquet file,
- a directory containing candidate-row CSV or Parquet shards,
- a manifest JSON that lists shard paths.

## Build the real public release (`lafc-evict-v0.1-open`)

Dry-run first:

```bash
python scripts/build_real_release.py \
  --input-manifest /path/to/generated/candidate_rows/manifest.json \
  --family-selection manifests/lafc_evict_v0_1_open_families.json \
  --output-dir release/lafc-evict-v0.1-open \
  --dataset-id lafc-evict-v0.1-open \
  --dry-run
```

Materialize the release:

```bash
python scripts/build_real_release.py \
  --input-manifest /path/to/generated/candidate_rows/manifest.json \
  --family-selection manifests/lafc_evict_v0_1_open_families.json \
  --output-dir release/lafc-evict-v0.1-open \
  --dataset-id lafc-evict-v0.1-open \
  --overwrite
```

Optional capped pairwise sample:

```bash
python scripts/build_real_release.py \
  --input-manifest /path/to/generated/candidate_rows/manifest.json \
  --family-selection manifests/lafc_evict_v0_1_open_families.json \
  --output-dir release/lafc-evict-v0.1-open \
  --dataset-id lafc-evict-v0.1-open \
  --overwrite \
  --pairwise-sample \
  --max-pairwise-rows 1000000 \
  --max-pairs-per-decision 8 \
  --pairwise-seed 7
```

This memory-safe builder:

- filters to the selected open families and hard-fails if blocked families would be included,
- streams CSV shards through DuckDB into partitioned Parquet under `data/candidate_rows/`,
- builds `data/decision_view/decision_view.parquet` out of core,
- writes release metadata, checksums, and governance artifacts,
- does not load the full selected subset into pandas memory.

Full pairwise materialization is intentionally not part of the default real release because it can grow quadratically with decision size. Pairwise tasks can be derived from candidate rows or generated as capped samples.

## Legacy export (small releases only)

```bash
python scripts/export_lafc_evict_parquet.py \
  --input-path /path/to/generated/candidate_rows_or_manifest \
  --output-dir release/lafc-evict-v0.1-open
```

This legacy path loads all shards into pandas memory and is not safe for the full `lafc-evict-v0.1-open` build.

## Build derived views from an existing release

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

## Validate and checksum

```bash
python scripts/validate_real_release.py \
  --release-root release/lafc-evict-v0.1-open
```

```bash
python scripts/validate_release_schema.py \
  --input-path release/lafc-evict-v0.1-open/data/candidate_rows
```

```bash
python scripts/compute_release_checksums.py \
  --input-path release/lafc-evict-v0.1-open \
  --output-path release/lafc-evict-v0.1-open/metadata/checksums.sha256
```

## Upstream regeneration note

If a final release needs to be fully regenerated from raw traces, that regeneration belongs in the original research pipeline or a documented preprocessing workflow. This repository intentionally starts from already generated candidate rows to keep the public package small and conservative.
