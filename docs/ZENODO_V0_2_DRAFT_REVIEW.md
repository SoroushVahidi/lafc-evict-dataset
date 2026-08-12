# Zenodo v0.2 Draft Review

Status: `PUBLISHED_AND_PUBLICLY_VERIFIED`

- Deposition ID: `21895844`
- Draft URL: https://zenodo.org/deposit/21895844
- Public record URL: https://zenodo.org/records/21895844
- Version DOI: `10.5281/zenodo.21895844`
- Concept DOI: `10.5281/zenodo.21895843`
- Concept record ID: `21895843`
- Title: `LAFC-Evict: Learning-Augmented Cache Eviction Dataset`
- Version: `v0.2`
- Creator: Soroush Vahidi
- Affiliation: New Jersey Institute of Technology
- License: CC0 1.0 (`cc-zero` in Zenodo's normalized response)
- Access: open
- Files: 15
- Total size: 140,145,802 bytes after the flat-layout documentation repair
- Checksums: all remote MD5 values match the local manifest; local SHA-256 values remain canonical
- Related identifiers: Hugging Face dataset (`isIdenticalTo`), GitHub repository (`isDocumentedBy`), and SSRN preprint (`isSupplementTo`)
- DOI status: `10.5281/zenodo.21895844` is the published version DOI
- Zenodo state: `done`; `submitted=true`
- Publication state: published; `submitted=true`
- Flat-layout repair: replaced only `README.md`, `release_manifest.json`, and `checksums.sha256` in the existing draft; Parquet files were untouched.

The README and release manifest now use Zenodo-root basenames. Any `data/...` references are explicitly identified as Hugging Face's organized layout, and source provenance paths in `sampling_manifest.json` remain unchanged as provenance values.

## Human Review Checklist

- [ ] Confirm title, version, creator, affiliation, and CC0 license.
- [ ] Confirm the 15-file inventory and the two Parquet files are the intended v0.2 release.
- [ ] Confirm the Hugging Face and GitHub related-identifier relationships.
- [ ] Confirm Wiki2018 attribution and the `source_fold`/`source_relpath` explanation.
- [ ] Confirm the reserved DOI is acceptable for this release.
- [ ] Approve publication separately; publication has not been performed by this task.

Zenodo deposition buckets are flat. Local manifest paths such as `data/foo.parquet` and `metadata/schema.json` are represented remotely by their unique basenames; the local manifest preserves the authoritative relative paths and SHA-256 values.
