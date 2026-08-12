# Zenodo v0.2 Draft Review

Status: `UNPUBLISHED_DRAFT_NOT_READY_TO_PUBLISH`

- Deposition ID: `21895844`
- Draft URL: https://zenodo.org/deposit/21895844
- Concept record ID: `21895843`
- Title: `LAFC-Evict: Learning-Augmented Cache Eviction Dataset`
- Version: `v0.2`
- Creator: Soroush Vahidi
- Affiliation: New Jersey Institute of Technology
- License: CC0 1.0 (`cc-zero` in Zenodo's normalized response)
- Access: open
- Files: 15
- Total size: 140,145,059 bytes
- Checksums: all remote MD5 values match the local manifest; local SHA-256 values remain canonical
- Related identifiers: Hugging Face dataset (`isIdenticalTo`), GitHub repository (`isDocumentedBy`), and SSRN preprint (`isSupplementTo`)
- DOI status: `10.5281/zenodo.21895844` is reserved in the unpublished draft metadata; it is not published
- Zenodo state: `unsubmitted`; `submitted=false`

Publication hold: Zenodo stores these files with flat basenames. The uploaded `README.md` and `release_manifest.json` refer to local bundle paths such as `metadata/release_manifest.json` and `data/cross_family_evict_value_v1.parquet`; those paths do not exist in the Zenodo draft. Repair requires replacing the affected uploaded text files or rebuilding the package. No remote file deletion or replacement was attempted.

## Human Review Checklist

- [ ] Confirm title, version, creator, affiliation, and CC0 license.
- [ ] Confirm the 15-file inventory and the two Parquet files are the intended v0.2 release.
- [ ] Confirm the Hugging Face and GitHub related-identifier relationships.
- [ ] Confirm Wiki2018 attribution and the `source_fold`/`source_relpath` explanation.
- [ ] Confirm the reserved DOI is acceptable for this release.
- [ ] Approve publication separately; publication has not been performed by this task.

Zenodo deposition buckets are flat. Local manifest paths such as `data/foo.parquet` and `metadata/schema.json` are represented remotely by their unique basenames; the local manifest preserves the authoritative relative paths and SHA-256 values.
