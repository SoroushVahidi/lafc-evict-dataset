# LAFC-Evict Publication State

This is the human-readable publication overview. The machine-readable source
of truth is `publication/LAFC_EVICT_PUBLICATION_STATE.json`.

## Current public release

**Publication is currently split across platforms.**

- **Hugging Face** now serves **LAFC-Evict v1.0**:
  <https://huggingface.co/datasets/SoroushVahidi/lafc-evict>
  (revision `v1.0`, commit `37173bc96de2a615455bf9713bb90d846156af29`). This full release
  includes all five evaluated trace families (Alibaba Block / cloudphysics, MetaCDN,
  MetaKV, Twemcache, Wiki2018) and consists of 277,995,072 candidate-level rows,
  2,363,286 decision-horizon rows, and a 1,000,000-row canonical pairwise sample.
  The prior v0.3 revision (`2113cc4d1edee57275d769d8760da77ed67c875d`) remains fully
  accessible on the `main` branch, and the prior v0.2 revision
  (`b77413fef197e808aed9cfa708878064a5c00493`) is also pinnable for reproducibility.
- **AWS Open Data** publicly hosts the older **v0.3 wiki2018-only payload** in
  bucket `lafc-evict-open-data`, region `us-west-2`: 18 objects,
  approximately 106.1 MiB, CC0 1.0, with anonymous public download verified PASS.
  The full five-family v1.0 release is NOT hosted on AWS.
- **Zenodo** still serves **LAFC-Evict v0.2** as the current version:
  version DOI <https://doi.org/10.5281/zenodo.21895844>, concept DOI
  <https://doi.org/10.5281/zenodo.21895843>. A v0.3 or v1.0 Zenodo version has
  **not** been created. No Zenodo version DOI exists yet for v0.3 or v1.0.

v1.0 scope: Full five-family release, deterministic pseudonymization of wiki2018 identifiers. Configs:
`cross_family_evict_value_v1` and `objective_ablation_scalar`. Candidate rows:
277,995,072. Dataset license is multi-licensed by family: CC0-1.0 (wiki2018), CC BY 4.0
(Alibaba Block, Twemcache), and Apache License 2.0 (MetaCDN, MetaKV).

The local package at `release/lafc-evict-v1.0/` is the HF-oriented
source, published on 2026-09-17, and independently re-hash-verified against the live
Hugging Face payload.

## Historical and other releases

- **v0.1 synthetic sample:** historical synthetic workflow sample published
  separately; not the current scientific release.
- **v0.1-open:** historical unpublished real-data staging generation.
- **v0.1-open-current-contract-preserved:** preserved, locally validated,
  unpublished v0.1-open build.
- **v0.2 published preview:** the previous public release (4,800,000 rows, wiki2018-only).
  Remains published and pinnable on both Hugging Face and Zenodo for
  reproducibility.
- **v0.3 published slice:** the older wiki2018-only release (22,356,992 rows) which
  remains on Hugging Face main revision and AWS.

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
of the v0.2 or v1.0 HF or Zenodo packages. Keep manuscript review artifacts and dataset
release bundles conceptually separate.

## Provenance boundary

All five evaluated families (`cloudphysics`, `metacdn`, `metakv`, `twemcache`, `wiki2018`)
are cleared for the published v1.0 release under their applicable upstream licenses (see `THIRD_PARTY_DATA.md`).
`brightkite` and `citibike` remain blocked pending license/privacy review and are excluded from any public release.

## Hosting boundary

HF, AWS Open Data, and Zenodo publication state recorded here is authoritative
for LAFC-Evict. CyVerse, Harvard Dataverse, and other external hosting
exploration is outside this repository's authoritative state unless a concrete
LAFC-Evict publication record is created.