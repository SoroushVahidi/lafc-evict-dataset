# Zenodo v0.2 Flat-Package Equivalence

The Zenodo-specific staging package is `release/lafc-evict-v0.2-zenodo-flat/`.
It contains the same 15 logical release files as the canonical v0.2 package,
stored at one directory level for Zenodo's flat file bucket.

- Flat package file count: 15
- Flat package total: 140,145,802 bytes
- Canonical Parquet payloads: byte-identical
- `cross_family_evict_value_v1.parquet`: 2,700,000 rows; SHA-256 `38ae87b88bf8367d41f0dc8638eaf12fa5416b559d24c7023f39b9f1c7b6bb8f`
- `objective_ablation_scalar.parquet`: 2,100,000 rows; SHA-256 `90a2cb7913e234323190810906644e110f5c9ebeaaea47203857f61b822757f9`
- Both Parquet schemas are unchanged.

Only these textual files differ from the canonical Hugging Face-oriented
package:

- `README.md`: explains the Zenodo flat layout and distinguishes it from the
  organized Hugging Face layout.
- `release_manifest.json`: uses flat basenames and declares
  `archive_layout: zenodo_flat`.
- `checksums.sha256`: uses flat basenames and was regenerated accordingly.

All other release files are byte-identical. The differences contain no
scientific, row-count, schema, provenance, licensing, or checksum-value
changes. The canonical Hugging Face package was not modified.
