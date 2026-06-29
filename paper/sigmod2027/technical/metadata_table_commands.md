# Metadata Table Commands

Use these commands to regenerate the lightweight paper tables without scanning candidate-row parquet contents.

## Extract metadata-backed tables

```bash
python paper/sigmod2027/technical/extract_metadata_tables.py \
  --release-root release/lafc-evict-v0.1-open-current-contract-preserved \
  --results-dir paper/sigmod2027/results/metadata_tables \
  --latex-tables-dir paper/sigmod2027/latex/tables
```

## Run normal tests

```bash
python -m pytest
```

## Compile the LaTeX draft

```bash
cd paper/sigmod2027/latex
latexmk -pdf main.tex
```

## Validate the existing local publication bundle

```bash
python scripts/validate_publication_bundle.py \
  --bundle-dir /tmp/lafc-evict-v0.1-open-current-contract-preserved-publication-bundle
```
