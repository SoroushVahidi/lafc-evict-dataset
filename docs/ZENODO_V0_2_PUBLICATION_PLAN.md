# Zenodo v0.2 Publication Plan

Status: deposition `21895844` exists as an unpublished draft. The final flat-layout audit is recorded in `docs/ZENODO_V0_2_FINAL_PREPUBLICATION_AUDIT.md`; publication still requires a separate explicit approval task.

## Scope

KBS reviewer revision remains the main research priority. Zenodo should stay lightweight: archival preservation, DOI/versioning, later safe disk cleanup, and reproducibility. Do not turn this into a separate dataset-paper project.

Recommended architecture:

- GitHub: source code, manifests, validation scripts, reproducibility utilities.
- Hugging Face: interactive and ML-ready dataset distribution.
- Zenodo: frozen archival releases with DOI/versioning.

Use Zenodo first for the public v0.2 preview, then create new Zenodo versions for later curated releases when files change.

## Current Local Release

Release root:

```text
release/lafc-evict-v0.2-preview
```

The staged release contains 15 files and 140,145,059 bytes. Parquet payload bytes are 140,106,094.

Expected Parquet SHA-256 hashes:

```text
38ae87b88bf8367d41f0dc8638eaf12fa5416b559d24c7023f39b9f1c7b6bb8f  data/cross_family_evict_value_v1.parquet
90a2cb7913e234323190810906644e110f5c9ebeaaea47203857f61b822757f9  data/objective_ablation_scalar.parquet
```

## Metadata Draft

Local metadata draft:

```text
publication/zenodo_v0_2_metadata_draft.json
```

Exact file manifest:

```text
publication/zenodo_v0_2_file_manifest.json
```

Planned record identity:

- Title: `LAFC-Evict: Learning-Augmented Cache Eviction Dataset`
- Version: `v0.2`
- Resource type: `dataset`
- Creator: `Vahidi, Soroush`
- Affiliation: `New Jersey Institute of Technology`
- Access: `open`
- License: `cc0-1.0`
- Language: `eng`

No ORCID is included in the local draft because the canonical dataset repository does not contain a confirmed ORCID.

Related identifiers:

- Hugging Face dataset: `isIdenticalTo`, `resource_type=dataset`
- GitHub code/reproducibility repository: `isDocumentedBy`, `resource_type=software`
- Associated SSRN preprint: `isSupplementTo`, `resource_type=publication-preprint`

The Hugging Face relation assumes the Zenodo upload is the exact same v0.2 file payload. If the Zenodo file list changes, downgrade the Hugging Face relation to a less exact relationship before submission.

## Intended Upload Files

Upload the exact 15-file v0.2 preview payload:

```text
README.md
RELEASE_NOTES_v0_2.md
data/cross_family_evict_value_v1.parquet
data/objective_ablation_scalar.parquet
dataset_card.md
metadata/checksums.sha256
metadata/lafc_evict_v0_2_preview_families.json
metadata/provenance_summary.csv
metadata/release_manifest.json
metadata/sampling_manifest.json
metadata/schema.json
metadata/security_scan.json
metadata/source_family_registry.yaml
metadata/statistics.json
metadata/validation_report.md
```

This avoids a repackaging step and keeps Zenodo identical to the Hugging Face preview. The Hugging Face-specific `dataset_card.md` is acceptable as archived release documentation because the Zenodo metadata clearly states that Hugging Face is the interactive distribution endpoint.

The file manifest records, for each file, the release-relative path, byte size, SHA-256, MD5, and role. The future upload helper uploads only manifest-listed files and fails if the release directory has missing, changed, or extra files.

## Final Zenodo Flat Package

Zenodo deposition buckets are flat, so the existing draft uses a Zenodo-specific
copy rather than changing the Hugging Face package:

```text
release/lafc-evict-v0.2-zenodo-flat/
publication/zenodo_v0_2_flat_file_manifest.json
```

The flat package contains 15 root-level files totaling 140,145,802 bytes.
The Parquet files are byte-identical to the canonical release. Only
`README.md`, `release_manifest.json`, and `checksums.sha256` differ from the
Hugging Face-oriented package, to make archive paths valid at the Zenodo root.
The existing draft was repaired in place by replacing only those three files;
it remains `unsubmitted` with `submitted=false`.

## Integrity Plan

Before upload:

```bash
cd /home/soroush/lafc-evict-dataset/release/lafc-evict-v0.2-preview
sha256sum -c metadata/checksums.sha256
find . -type f -printf '%s\t%P\n' | sort -k2
du -sb .
```

After upload but before publication:

1. Read the draft deposition with `GET /api/deposit/depositions/{id}`.
2. Confirm file count is 15.
3. Confirm every uploaded filename matches the intended file list.
4. Confirm Zenodo-reported file sizes match local sizes.
5. Confirm Zenodo-reported checksums match local checksums. Zenodo may report checksums as MD5 for uploaded files; if so, compute local MD5 for comparison and keep SHA-256 as the canonical repository integrity record.
6. Save final `record_id`, version DOI, concept DOI, publication date, file inventory, file sizes, and checksum report in a local follow-up status document after publication.

The draft helper verifies MD5 if Zenodo reports `md5:<digest>` and accepts SHA-256 only if Zenodo exposes that digest. Local SHA-256 remains the canonical repository integrity record.

## DOI And Versioning

Zenodo drafts are mutable until publication. After publication, metadata can be edited, but files and persistent identifiers should be treated as immutable for reproducibility. When files change, create a new version rather than editing the published payload.

Use versioning as:

```text
v0.2   small public preview
v0.3+  expanded curated preview/full-candidate releases
v1.0   stable full release
```

Recommendation: v0.2 can receive its own DOI once the next task explicitly approves creating and publishing a Zenodo record. This is reasonable because the Hugging Face v0.2 preview is already public, small, validated, and intended to be citeable as a frozen snapshot. Do not reserve or publish a DOI during planning.

Gate separation:

- Gate A: `CREATE_ZENODO_DRAFT` creates an unpublished draft, submits metadata, uploads the exact manifest files, verifies the draft, and stops.
- Gate B: `PUBLISH_ZENODO_RECORD` is a separate future action after draft review. It must record the specific version DOI, concept DOI, record ID, publication timestamp, and version after publication.

The draft helper rejects `--publish` and requires `--no-publish` for actual draft creation.

## Storage Strategy

Zenodo default storage is 50 GB per record, with an additional 150 GB account allowance that can be allocated to records needing more capacity.

Implications:

- The current v0.2 preview is about 140 MB and fits easily.
- The estimated curated full release is about 12 GB and fits comfortably under the default 50 GB per-record quota.
- Reserve the 150 GB additional allowance for an exceptional future record that genuinely exceeds 50 GB.
- Do not upload raw or intermediate CSV trees by default.
- Do not archive the historical 96 GB heavy corpus on Zenodo unless licensing, provenance, privacy, and reproducibility value are explicitly re-reviewed and extra quota use is approved.
- Keep raw/intermediate local or private until licensing and reproducibility are finalized.

## Safety Notes

Observed v0.2 checks:

- Existing `metadata/security_scan.json` reports passed with no findings.
- Release metadata says no machine paths, no raw trace rows, and pseudonymized object IDs.
- Local SHA-256 verification passed for all 15 files.
- A read-only Parquet string-column scan found no local absolute paths, token markers, or Wulver markers.

Known caveat:

- `source_fold` and `source_relpath` values contain `brightkite/...` fold-layout labels even though `trace_family` is `wiki2018`. The v0.2 builder defaults `cross_family_fold` and `objective_fold` to `brightkite` and selects CSV files named `wiki2018_pageviews_en_50k__...` under that fold directory. This is a held-out/fold naming artifact, not evidence that Brightkite rows are included. The actual release manifest includes only `wiki2018`, the sampling manifest source filenames are Wiki2018 pageview shards, and preview validation enforces `trace_family=wiki2018`.

No Parquet payload change is needed for DOI preparation. A future schema polish release should rename or document these columns more clearly, for example `source_fold` as `generation_fold_label`.

## Existing Tooling Assessment

- `scripts/create_zenodo_deposit.py`: READY_TO_CREATE_DRAFT. The legacy bundle workflow remains dry-run-first, and the v0.2 path now consumes explicit metadata and file-manifest inputs. The v0.2 draft path rejects `--publish` and requires `--create-draft --upload --verify --no-publish` before any write.
- `src/lafc_evict_dataset/publication.py`: READY_TO_CREATE_DRAFT. The v0.2 path validates metadata, exact 15-file inventory, byte sizes, SHA-256, MD5, release security scan, Wiki2018 attribution, CC0 metadata, preview validation, and post-upload draft state/files/metadata.
- `publication/ZENODO_METADATA_TEMPLATE.json`: STALE for v0.2 because it uses `MIT`, version `0.1`, and generic draft text.
- `tests/test_publication_dry_runs.py`: READY_TO_REUSE for no-network dry-run safety.
- `tests/test_publication_bundle.py`: READY_TO_REUSE for the older publication-bundle path.
- New-version support: MISSING.
- Post-upload checksum/size verification: READY_FOR_DRAFT. The draft verifier compares file names, sizes, and Zenodo-reported MD5/SHA-256 where exposed.
- Concept DOI/version DOI local recording: DOCUMENTED_FOR_FUTURE_PUBLISH. Do not record DOI fields until a separate publish gate has completed.

## Historical Gate A Command Sequence

These commands document the already-completed draft workflow. Do not run the
creation command again. The next separately approved task is the publication
gate after reviewing the final audit.

Dry-run:

```bash
cd /home/soroush/lafc-evict-dataset
python scripts/create_zenodo_deposit.py \
  --metadata publication/zenodo_v0_2_metadata_draft.json \
  --release-dir release/lafc-evict-v0.2-preview \
  --manifest publication/zenodo_v0_2_file_manifest.json \
  --dry-run
```

Approved Gate A draft creation:

```bash
cd /home/soroush/lafc-evict-dataset
source ~/.config/zenodo/env
python scripts/create_zenodo_deposit.py \
  --metadata publication/zenodo_v0_2_metadata_draft.json \
  --release-dir release/lafc-evict-v0.2-preview \
  --manifest publication/zenodo_v0_2_file_manifest.json \
  --create-draft \
  --upload \
  --verify \
  --no-publish
```

Gate A API sequence:

```text
GET  /api/deposit/depositions?size=100&all_versions=1
POST /api/deposit/depositions
PUT  /api/deposit/depositions/{id}                      metadata only
PUT  {bucket_url}/{release_relative_filename}           one per intended file
GET  /api/deposit/depositions/{id}                      inspect draft files/metadata
```

Gate B API sequence, only after separate explicit approval:

```text
POST /api/deposit/depositions/{id}/actions/publish
GET  /api/records/{record_id}
```

Future draft state format, to be written only after an actual draft exists:

```text
publication/zenodo_v0_2_draft_state.json
```

Fields: `deposition_id`, `draft_url`, `api_self_url`, `created_at_utc`, `metadata_version`, `file_manifest_sha256`, `source_git_sha`, `zenodo_state`, and `published=false`. Do not store tokens, credentials, or private bearer URLs.

Future publish status format should record `record_id`, `version_doi`, `concept_doi`, `published_at_utc`, `version`, `file_manifest_sha256`, and `source_git_sha`.
