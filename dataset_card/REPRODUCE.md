# Reproduce and Export

This repository is designed to export a release from an **existing generated candidate-row dataset**. It does not require committing raw traces to GitHub.

## Inputs

Supported inputs for release export:

- a single candidate-row CSV,
- a single candidate-row Parquet file,
- a directory containing candidate-row CSV or Parquet shards,
- a manifest JSON that lists shard paths.

## Export candidate rows to release Parquet

```bash
python scripts/export_lafc_evict_parquet.py \
  --input-path /path/to/generated/candidate_rows_or_manifest \
  --output-dir release/lafc-evict-v0.1-open
```

This script:

- reads the existing generated candidate rows,
- validates the canonical schema,
- normalizes split aliases to `train` / `val` / `test`,
- writes Parquet partitions by split, trace family, capacity, and horizon,
- writes a release manifest with row counts and SHA256 checksums.

## Build derived views

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

## Validate and checksum

```bash
python scripts/validate_release_schema.py \
  --input-path release/lafc-evict-v0.1-open/candidate_rows
```

```bash
python scripts/compute_release_checksums.py \
  --input-path release/lafc-evict-v0.1-open \
  --output-path release/lafc-evict-v0.1-open/checksums.sha256
```

## Upstream regeneration note

If a final release needs to be fully regenerated from raw traces, that regeneration belongs in the original research pipeline or a documented preprocessing workflow. This repository intentionally starts from already generated candidate rows to keep the public package small and conservative.
