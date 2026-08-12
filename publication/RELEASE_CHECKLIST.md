# Publication Checklist

## Build

- Confirm the release version, scope, lineage, and family-selection manifest.
- Build only from approved local source data and record source provenance.
- Do not regenerate or modify an already published scientific payload.

## Local validation

- Validate schema, row counts, uniqueness, split/family consistency, and target semantics.
- Generate and verify the SHA-256 checksum manifest.
- Confirm the exact files and bytes intended for publication.

## Security, privacy, and provenance

- Run local-path, secret/token, and privacy scans.
- Fail closed on any raw identifier leakage or security finding.
- Fail closed unless every included family has explicit publication clearance.
- Review attribution, license, and dataset-card wording.

## Hugging Face

- Run the dry-run plan and review the exact file inventory.
- Obtain separate approval before any upload.
- Record the resulting repository revision and verified payload hashes.

## Zenodo new version

- Use the existing concept DOI's new-version workflow.
- Run flat-layout manifest and metadata checks.
- Create or update a draft only with separate approval.
- Verify file count, bytes, checksums, metadata, and related identifiers.
- Do not publish the record without separate approval.

## Post-publication record

- Record public DOIs, host revision, file inventory, total bytes, and scientific hashes.
- Update human-readable release notes and citation metadata.

No upload, Zenodo publication, or external-service modification is authorized
by this checklist alone.
