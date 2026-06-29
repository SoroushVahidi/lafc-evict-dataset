# Metadata-Backed Paper Results

This directory holds lightweight benchmark tables for the SIGMOD/PACMMOD 2027 paper draft.

- Source scope is intentionally limited to the preserved release manifest, checksums file, decision view, and shipped pairwise sample.
- No candidate-row parquet contents are scanned here.
- Full real-release validation passed on the preserved release on 2026-06-29; manuscript-facing tables should reflect that pass while keeping candidate-row scans and public hosting claims pending.
- Generated Markdown and CSV outputs live under `metadata_tables/`.
- Generated LaTeX table files live under `../latex/tables/`.

Regeneration command:

```bash
python paper/sigmod2027/technical/extract_metadata_tables.py \
  --release-root release/lafc-evict-v0.1-open-current-contract-preserved \
  --results-dir paper/sigmod2027/results/metadata_tables \
  --latex-tables-dir paper/sigmod2027/latex/tables
```
