# Publication Hosting Index

This directory contains host-state records, publication templates, archived bundle metadata, and release-planning artifacts for LAFC-Evict. The authoritative current state is:

- Human-readable: [`../docs/LAFC_EVICT_PUBLICATION_STATE.md`](../docs/LAFC_EVICT_PUBLICATION_STATE.md)
- Machine-readable: [`LAFC_EVICT_PUBLICATION_STATE.json`](LAFC_EVICT_PUBLICATION_STATE.json)

## Current

- **Hugging Face v1.0** is the current full public release.
- Dataset: <https://huggingface.co/datasets/SoroushVahidi/lafc-evict>
- Revision/branch: `v1.0`
- Scope: five families, 277,995,072 candidate rows, 2,363,286 decision-horizon rows, and 1,000,000 canonical pairwise rows.

## Older Active Hosting

- **Hugging Face `main`** retains the older v0.3 Wiki2018-only state.
- **AWS Open Data** hosts the older v0.3 Wiki2018-only payload in bucket `lafc-evict-open-data`, region `us-west-2`.

## Archival

- **Zenodo** currently archives v0.2 only.
- Version DOI: <https://doi.org/10.5281/zenodo.21895844>
- Concept DOI: <https://doi.org/10.5281/zenodo.21895843>
- No v0.3 or v1.0 Zenodo version DOI has been minted.

## Historical Artifacts

Files named `v0_3_*`, `zenodo_v0_*`, `V0_3_*`, and the archived bundle material are retained as historical publication evidence or planning records. They may describe earlier build, upload, or draft states and should not be read as the current release status unless they point back to the publication-state files above.

Publication scripts are dry-run by default. GitHub Releases, tags, and final branch cleanup are intentionally deferred to final release closure.
