# LAFC-Evict Publication State

This is the human-readable publication overview. The machine-readable source
of truth is `publication/LAFC_EVICT_PUBLICATION_STATE.json`.

## Current public release

**LAFC-Evict v0.2 published preview** is the current public release.

- Hugging Face: https://huggingface.co/datasets/SoroushVahidi/lafc-evict
- Zenodo version DOI: https://doi.org/10.5281/zenodo.21895844
- Zenodo concept DOI: https://doi.org/10.5281/zenodo.21895843
- Scope: Wiki2018-only, pseudonymized derived supervision
- Configs: `cross_family_evict_value_v1` and `objective_ablation_scalar`
- Rows: 4,800,000
- Dataset license: CC0 1.0

The nested package at `release/lafc-evict-v0.2-preview/` is the HF-oriented
source. `release/lafc-evict-v0.2-zenodo-flat/` is the same scientific payload
in the flat layout required by the Zenodo record. Their Parquet payloads are
byte-identical.

## Historical and future releases

- **v0.1 synthetic sample:** historical synthetic workflow sample published
  separately; not the current scientific release.
- **v0.1-open:** historical unpublished real-data staging generation.
- **v0.1-open-current-contract-preserved:** preserved, locally validated,
  unpublished v0.1-open build.
- **v0.3 candidate:** locally built and validated Wiki2018-only expansion;
  not uploaded or published.
- **v1.0:** future stable/full release; planning only and conditional on
  explicit provenance clearance for every included family.

## Repository ownership

- Canonical publication repository: `/home/soroush/lafc-evict-dataset`
- Scientific/source-data repository: `/home/soroush/Augmented-caching`
- KBS reviewer repository: `/home/soroush/Augmented-caching-kbs-second-revision`

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
