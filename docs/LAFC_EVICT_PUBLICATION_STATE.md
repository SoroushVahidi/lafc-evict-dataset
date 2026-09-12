# LAFC-Evict Publication State

This is the human-readable publication overview. The machine-readable source
of truth is `publication/LAFC_EVICT_PUBLICATION_STATE.json`.

## Current public release

**Publication is currently split across platforms.**

- **Hugging Face** now serves **LAFC-Evict v0.3**:
  <https://huggingface.co/datasets/SoroushVahidi/lafc-evict>
  (revision `2113cc4d1edee57275d769d8760da77ed67c875d`). The prior v0.2
  revision (`b77413fef197e808aed9cfa708878064a5c00493`) remains fully
  accessible and pinnable for reproducibility.
- **Zenodo** still serves **LAFC-Evict v0.2** as the current version:
  version DOI <https://doi.org/10.5281/zenodo.21895844>, concept DOI
  <https://doi.org/10.5281/zenodo.21895843>. A v0.3 Zenodo version has
  **not** been created — the configured Zenodo credential returned HTTP 403
  on all deposition-management calls. See
  `publication/LAFC_EVICT_PUBLICATION_STATE.json` (`releases[].zenodo_block_detail`
  on the v0.3 entry) for the exact failure evidence. Do not cite a v0.3
  Zenodo DOI until this record is updated with one.

v0.3 scope: Wiki2018-only, pseudonymized derived supervision. Configs:
`cross_family_evict_value_v1` and `objective_ablation_scalar`. Rows:
22,356,992. Dataset license: CC0 1.0. Novelty/documentation gate: passed
(see `reports/v0_3_novelty_audit_20260812/`).

The nested package at `release/lafc-evict-v0.3-candidate/` is the HF-oriented
source, already published, independently re-hash-verified against the live
Hugging Face payload (2026-09-12). `release/lafc-evict-v0.3-zenodo-flat/` is
the same scientific payload in the flat layout required by Zenodo, prepared
locally but not yet uploaded. **Correction (2026-09-12):** the two packages
are NOT byte-identical. Row counts, columns, dtypes, and every scientific/
provenance value are identical (verified via DuckDB `EXCEPT` in both
directions), but the packages differ in the row-level `release_version` tag
(candidate correctly reads `v0.3`; zenodo-flat still reads a stale
pre-finalization `v0.3-candidate` tag) and in Parquet row-group sizing, which
is why their file sizes differ (~111 MB vs. ~70 MB). See
`publication/LAFC_EVICT_PUBLICATION_STATE.json`
(`releases[].zenodo_flat_vs_candidate_reconciliation` on the v0.3 entry) for
full detail. `release/lafc-evict-v0.3-candidate/` remains canonical for any
future publication (AWS or Zenodo); the zenodo-flat package's tag should be
corrected before it is ever uploaded.

## Historical and future releases

- **v0.1 synthetic sample:** historical synthetic workflow sample published
  separately; not the current scientific release.
- **v0.1-open:** historical unpublished real-data staging generation.
- **v0.1-open-current-contract-preserved:** preserved, locally validated,
  unpublished v0.1-open build.
- **v0.2 published preview:** the previous public release (4,800,000 rows).
  Remains published and pinnable on both Hugging Face and Zenodo for
  reproducibility; not deleted or altered by the v0.3 publication.
- **v1.0:** future stable/full release; planning only and conditional on
  explicit provenance clearance for every included family.

## Repository ownership

- Canonical publication repository: `github.com/SoroushVahidi/lafc-evict-dataset` (branch `master`)
- Scientific/source-data repository: `github.com/SoroushVahidi/Augmented-caching` (branch `main`; dataset-generation scripts are in this repository's `scripts/` and `src/`)
- KBS reviewer repository: `github.com/SoroushVahidi/Augmented-caching`, branch `kbs/second-revision-science` (a branch/worktree of the same repository, not a separate GitHub repository)

The publication repository owns release manifests, cards, validation, checksums,
and host records. The source and KBS repositories own research inputs and
scientific/reviewer outputs; they are not publication payload sources of truth.

## SIGMOD separation

The SIGMOD anonymous bundle under `publication/bundles/` is a manuscript
publication artifact only. It is not a dataset-release payload and is not part
of the v0.2 HF or Zenodo packages. Keep manuscript review artifacts and dataset
release bundles conceptually separate.

## Provenance boundary

`wiki2018` is the only family currently cleared for the published derived
release, with attribution and caveat requirements. `cloudphysics`, `metacdn`,
`metakv`, and `twemcache` remain uncleared pending final review. `brightkite`
and `citibike` remain blocked pending license/privacy review. The registry is a
governance record, not legal advice.

## Hosting boundary

HF and Zenodo publication state recorded here is authoritative for LAFC-Evict.
CyVerse, Harvard Dataverse, AWS, and other external hosting exploration is
outside this repository's authoritative state unless a concrete LAFC-Evict
publication record is created.
