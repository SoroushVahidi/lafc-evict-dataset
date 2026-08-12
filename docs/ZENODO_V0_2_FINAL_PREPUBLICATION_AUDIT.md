# LAFC-Evict v0.2 Final Zenodo Prepublication Audit

Audit timestamp: `2026-08-12T00:36:28Z`

Prepublication recommendation: `READY_TO_PUBLISH_ZENODO_V0_2`

Post-publication result: `ZENODO_V0_2_PUBLISHED_AND_VERIFIED`

Published version DOI: `10.5281/zenodo.21895844`

Concept DOI: `10.5281/zenodo.21895843`

Public record: https://zenodo.org/records/21895844

## Identity and State

- Repository: `/home/soroush/lafc-evict-dataset`
- Canonical scientific source SHA: `8fb97e8c68b80c2451dc49e0010b725702c24304`
- Audit repository HEAD before this record update: `94a3851aedeee214ab9e3bdf10714192c2de448d`
- Zenodo deposition: `21895844`
- Draft URL: https://zenodo.org/deposit/21895844
- Environment: production (`https://zenodo.org`)
- Final state: `done`; `submitted=true`
- Published version DOI: `10.5281/zenodo.21895844`
- Concept DOI: `10.5281/zenodo.21895843`

After the final gate, the record is published with `submitted=true` and the
version DOI above.

## Flat-Layout Repair

The selected strategy was a Zenodo-specific flat 15-file package. The
canonical Hugging Face package was not changed. Only three existing files in
deposition `21895844` were replaced in place:

- `README.md`
- `release_manifest.json`
- `checksums.sha256`

The two Parquet files and the other 12 files were not replaced. Zenodo's
official deposition-file API permits deleting files only from unpublished
depositions and uploading replacements to the same bucket. The draft remained
unsubmitted throughout.

## Integrity and Equivalence

- Final remote file count: 15.
- Final remote total: 140,145,802 bytes.
- Every remote file was read back and matched the local flat manifest's MD5
  and SHA-256.
- `cross_family_evict_value_v1.parquet`: 2,700,000 rows; SHA-256
  `38ae87b88bf8367d41f0dc8638eaf12fa5416b559d24c7023f39b9f1c7b6bb8f`.
- `objective_ablation_scalar.parquet`: 2,100,000 rows; SHA-256
  `90a2cb7913e234323190810906644e110f5c9ebeaaea47203857f61b822757f9`.
- Parquet bytes, schemas, row counts, configuration names, and provenance
  columns are unchanged from the canonical release.
- Local flat manifest: `publication/zenodo_v0_2_flat_file_manifest.json`.

## Path-Reference Audit

All archive-internal paths now resolve as Zenodo-root basenames. The release
manifest declares `archive_layout: zenodo_flat`; its inventory, data files,
and governance artifacts contain no directory separators. The checksum file
also contains only root-level filenames. The README explicitly identifies
the `data/...` paths in its YAML as Hugging Face layout references and uses
Zenodo-root names for its own file references. `sampling_manifest.source_relpath`
values remain unchanged because they are source provenance paths, not archive
references.

## Metadata, Provenance, and Cross-Publication Audit

Title, v0.2 version, dataset resource type, creator (`Vahidi, Soroush`), NJIT
affiliation, open access, English language, CC0 license, publication date,
keywords, and description remain correct. Zenodo's `cc-zero` normalization
and `scheme=url` additions are expected.

The description accurately states the 4,800,000-row derived cache-eviction
supervision preview, both configurations, Wiki2018 pageview-derived scope,
deterministic pseudonyms, raw-data exclusions, Wikimedia attribution, and
non-endorsement. No ORCID was invented.

The Hugging Face dataset is public at revision
`b77413fef197e808aed9cfa708878064a5c00493`; its Parquet sizes, hashes,
configurations, and row counts match. GitHub is reachable and documents the
source code and generation tooling. Related identifiers remain semantically
appropriate: HF `isIdenticalTo`, GitHub `isDocumentedBy`, and SSRN
`isSupplementTo`.

The `brightkite` values in `source_fold` and `source_relpath` remain
documented fold-layout provenance labels; released rows have
`trace_family=wiki2018` and Wiki2018 source filenames.

## Security and Checks

The final flat package and Parquet string columns contain no tokens,
credentials, private URLs, local absolute paths, Wulver paths, reviewer
notes, debug material, or temporary secrets.

Passed checks:

- Release validator.
- Flat-package file-count, path, size, MD5, and SHA-256 validation.
- Canonical Parquet byte/schema/row equivalence.
- Remote read-back of all 15 files.
- JSON validation.
- Security/privacy scan.
- Publication/release test suite: 28 tests.
- `git diff --check` and secret scan.

The publish action was executed exactly once
for deposition `21895844`; no new deposition or version was created.
The next project action should return to the KBS reviewer work.
