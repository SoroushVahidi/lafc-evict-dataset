# LAFC-Evict v0.2 Final Zenodo Prepublication Audit

Audit timestamp: `2026-08-12T00:23:36Z`

Recommendation: `NOT_READY_TO_PUBLISH_ZENODO_V0_2`

## Identity and State

- Repository: `/home/soroush/lafc-evict-dataset`
- Source Git SHA for the archived package: `8fb97e8c68b80c2451dc49e0010b725702c24304`
- Audit repository HEAD: `eb06e15b1ef44b2b8c2e47880e28e3b46197aa2e`
- Branch: `master`, clean and synchronized with `origin/master`
- Zenodo deposition: `21895844`
- Draft URL: https://zenodo.org/deposit/21895844
- Zenodo environment: production (`https://zenodo.org`), authenticated read-only inspection returned HTTP 200
- State: `unsubmitted`; `submitted=false`
- Published DOI: none
- Reserved DOI: `10.5281/zenodo.21895844`, reserved only

## Metadata Audit

The draft metadata is internally consistent for title, v0.2 version, dataset resource type, creator (`Vahidi, Soroush`), New Jersey Institute of Technology affiliation, open access, CC0 license, English language, keywords, publication date, description, and related identifiers. Zenodo's response normalizes `cc0-1.0` to `cc-zero` and adds `scheme=url`; both are expected.

The description accurately identifies a 4,800,000-row derived cache-eviction supervision preview with configurations `cross_family_evict_value_v1` and `objective_ablation_scalar`, Wikimedia pageview-derived `wiki2018` provenance, deterministic pseudonyms, raw-data exclusions, and non-endorsement wording. No ORCID was invented.

Related identifiers were reachable and semantically acceptable for the coordinated dataset/code/preprint context:

- Hugging Face dataset: `isIdenticalTo` for the same v0.2 scientific payload and configurations.
- GitHub repository: `isDocumentedBy`.
- SSRN preprint: `isSupplementTo`.

## Integrity and Scientific Checks

- Exact remote file count: 15.
- Exact remote total: 140,145,059 bytes.
- Every remote MD5 matched the local manifest.
- Local SHA-256 manifest passed for all 15 files.
- `cross_family_evict_value_v1.parquet`: 2,700,000 rows; SHA-256 `38ae87b88bf8367d41f0dc8638eaf12fa5416b559d24c7023f39b9f1c7b6bb8f`.
- `objective_ablation_scalar.parquet`: 2,100,000 rows; SHA-256 `90a2cb7913e234323190810906644e110f5c9ebeaaea47203857f61b822757f9`.
- Combined row count: 4,800,000.
- Schemas, configuration names, provenance columns, pseudonymization fields, and absence of local paths/secrets were verified.

## Cross-Publication and Provenance Checks

The public Hugging Face dataset is reachable, public, at revision `b77413fef197e808aed9cfa708878064a5c00493`. Its Parquet files have matching sizes and the same v0.2 configurations and row counts. The GitHub repository is reachable and documents the learning-augmented caching research code. Wikimedia attribution, CC0 wording, raw-pageview/title exclusions, and non-endorsement wording are consistent across the release and draft metadata.

The `brightkite` values in `source_fold` and `source_relpath` are documented fold-layout labels; released rows have `trace_family=wiki2018` and Wiki2018 source filenames. This is not a scientific payload defect.

## Security and Professionalism

The uploaded textual files and Parquet string columns had no token, credential, private URL, local absolute path, Wulver path, reviewer note, debug material, or accidental internal secret finding. No token was recorded in local audit files.

## Publication Blocker

Zenodo deposition buckets are flat. The remote inventory contains basenames such as `cross_family_evict_value_v1.parquet`, `schema.json`, and `release_manifest.json`; it does not contain `data/` or `metadata/` directories. However:

- `README.md` instructs readers to read `metadata/release_manifest.json`, `metadata/sampling_manifest.json`, and `metadata/provenance_summary.csv`.
- `release_manifest.json` records `data/...` and `metadata/...` paths as its file inventory.

Those references are correct for the canonical local/Hugging Face bundle but false or ambiguous after Zenodo flattening. This violates the archive-structure requirement for publication. No remote file deletion or replacement was attempted. The exact repair is to prepare a flat-safe archive package, update the affected documentation/manifests to use the Zenodo basenames or preserve directory structure in a single archive, then replace the draft package before publication.

No automatic Zenodo metadata correction was made because metadata-only changes cannot repair the uploaded-file path defect.

## Checks Run

- Release validator: passed.
- All 15 SHA-256 checks: passed.
- Remote file count, sizes, and MD5 checks: passed.
- Parquet row count/schema/provenance audit: passed.
- HF/GitHub URL and HF file-size checks: passed.
- JSON validation: passed for tracked JSON records.
- Security/privacy scan: passed.
- Publication test suite previously passed: 28 tests.
- No Zenodo publish endpoint was called.
