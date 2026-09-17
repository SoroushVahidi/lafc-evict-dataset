# LAFC-Evict Publication State

This is the human-readable publication overview. The machine-readable source
of truth is `publication/LAFC_EVICT_PUBLICATION_STATE.json`.

## Current public release

**Publication is currently split across platforms and revisions.**

- **Hugging Face** publishes LAFC-Evict on two revisions of the same
  repository, <https://huggingface.co/datasets/SoroushVahidi/lafc-evict>:
  - **`main` branch/revision** (commit `c8ae80880ecb26d463156051bfef2966d2d6b9a4`
    at the time of this record) continues to serve **v0.3**, wiki2018-only,
    unchanged by the v1.0 publication below. The prior v0.2 revision
    (`b77413fef197e808aed9cfa708878064a5c00493`) and the pre-v1.0 v0.3
    revision (`3b70d882c290201b9efe796ea2b8929878510754`) remain fully
    accessible and pinnable for reproducibility.
  - **`v1.0` branch/revision** (commit `37173bc96de2a615455bf9713bb90d846156af29`)
    publishes the **full five-family release**: `cloudphysics` ("Alibaba
    Block"), `metacdn`, `metakv`, `twemcache`, `wiki2018` -- 277,995,072
    candidate rows, 2,363,286 decisions, 1,000,000 canonical pairwise-sample
    rows. Published 2026-09-17. Independently verified after upload (not
    just "upload succeeded"): anonymous, unauthenticated HTTPS download of
    `metadata/release_manifest.json` and of
    `data/pairwise_sample/pairwise_sample.parquet` both returned HTTP 200;
    the downloaded pairwise-sample file's SHA-256 matched the locally
    recorded checksum exactly; a `wiki2018` and a non-`wiki2018` candidate-row
    partition were each downloaded and checksum-matched; the full 177-file
    remote listing (176 package files plus HF's own `.gitattributes`) was
    diffed against the local package with no unexpected or missing files;
    `main`'s file listing (17 files) was re-checked before and after and is
    unchanged. `brightkite`/`citibike` are not included, per the source
    registry's blocked status.
- **AWS Open Data** publicly hosts the **v0.3 wiki2018-only payload** in
  bucket `lafc-evict-open-data`, region `us-west-2`: 18 objects,
  approximately 106.1 MiB, CC0 1.0, with anonymous public download previously
  verified PASS. AWS Open Data Registry PR #3335 is pending maintainer
  activity unless later local documentation proves it merged. The known fork
  branch is `add-lafc-evict-dataset`; known PR head:
  `e12ac8f90714daf2bc88987725cc2a48b916cd59`. **The five-family v1.0 payload
  is not on AWS Open Data**: no AWS credentials, region configuration, or
  documented/automated publish tooling for this bucket exist in this
  environment or repository (unlike Hugging Face, there is no
  `scripts/publish_to_*_aws*.py` equivalent). This requires a manual
  AWS-account action; see "Next required action" below.
- **Zenodo** still serves **LAFC-Evict v0.2** as the current version:
  version DOI <https://doi.org/10.5281/zenodo.21895844>, concept DOI
  <https://doi.org/10.5281/zenodo.21895843>. Neither a v0.3 nor a v1.0
  Zenodo version has been created. The previously-documented HTTP 403 on
  deposition-management calls no longer reproduces as of 2026-09-17 --
  `GET /api/deposit/depositions` and `GET /api/deposit/depositions/21895844`
  both now return HTTP 200 with the configured token, so the token does have
  at least read access to the correct deposition. Creating and publishing a
  new Zenodo version (a further ~2.8 GB flat-layout upload, then an
  irreversible publish action) was intentionally **not attempted** in this
  pass: it is explicitly not required to consider LAFC-Evict's public-release
  problem resolved, and publishing on Zenodo cannot be undone once done. Do
  not cite a v1.0 Zenodo DOI; none exists.

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
future reuse of the nested package; the zenodo-flat package's tag should be
corrected before it is ever uploaded to Zenodo.

## Historical and future releases

- **v0.1 synthetic sample:** historical synthetic workflow sample published
  separately; not the current scientific release.
- **v0.1-open:** historical unpublished real-data staging generation.
- **v0.1-open-current-contract-preserved:** preserved, locally validated,
  unpublished v0.1-open build.
- **v0.2 published preview:** the previous public release (4,800,000 rows).
  Remains published and pinnable on both Hugging Face and Zenodo for
  reproducibility; not deleted or altered by the v0.3 publication.
- **v1.0 (full five-family release):** built and locally validated on
  2026-09-16 at `release/lafc-evict-v1.0/`, **publicly published on
  Hugging Face on 2026-09-17** as the `v1.0` branch/revision
  (`37173bc96de2a615455bf9713bb90d846156af29`) of
  `SoroushVahidi/lafc-evict`; see "Current public release" above for the
  exact revision and independent verification evidence. It repackages the
  exact corpus behind the manuscript's 277,995,072 candidate rows /
  2,363,286 decisions (source:
  `release/lafc-evict-v0.1-open-current-contract-preserved`, no label
  regeneration), with `wiki2018` identifiers pseudonymized using the same
  scheme already published for v0.2/v0.3, and includes the canonical
  regenerated 1,000,000-row pairwise sample (see
  `analysis/pairwise_provenance_repair_20260913/`). All five included
  families are cleared for public release per the 2026-09-15 registry
  review; `brightkite`/`citibike` remain excluded and blocked. Not yet on
  AWS Open Data or Zenodo -- see "Next required action" below.

### Next required action to make v1.0 fully public across all hosts

Hugging Face publication is done (see above). Remaining:

1. **AWS Open Data**: no automated/documented publish tooling exists in this
   repository for this bucket, and this environment has no AWS credentials
   or region configured. A human needs to either (a) configure AWS
   credentials/region and determine the exact process used for the v0.3
   upload (not scripted anywhere in this repo -- likely done via AWS
   Console or CLI directly against bucket `lafc-evict-open-data`), or
   (b) write and review a new upload script before any agent attempts this.
2. **Zenodo**: create a new version under concept DOI
   `10.5281/zenodo.21895843` using a flat-layout mirror of
   `release/lafc-evict-v1.0/` (same pattern as `*-zenodo-flat` for prior
   versions). The previously-blocking HTTP 403 no longer reproduces (token
   now returns HTTP 200 on both `GET /api/deposit/depositions` and
   `GET /api/deposit/depositions/21895844`), so this is likely achievable,
   but was not attempted in this pass because (a) it requires a further
   ~2.8 GB upload in Zenodo's flat file-bucket format, (b) Zenodo publish
   actions are irreversible once done, and (c) it is not required to
   consider LAFC-Evict's public-release problem resolved. Confirm the exact
   metadata (title, description, family list) before creating the new
   version, and reuse `scripts/create_zenodo_deposit.py` if it already
   supports a "new version" flow -- verify before assuming.
3. After either step, update this document and
   `publication/LAFC_EVICT_PUBLICATION_STATE.json` with the actual
   location/DOI/verification evidence, the same way v0.2/v0.3 were recorded.

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

**Legal/license clearance** (as of the 2026-09-15 review; see
`dataset_card/LICENSE_DATA.md` and `manifests/source_family_registry.yaml`
for full evidence): all five evaluated families are cleared for public
derived-data redistribution under their applicable upstream terms --
`wiki2018` (CC0 1.0), `twemcache` and `cloudphysics` ("Alibaba Block", CC BY
4.0), and `metakv`/`metacdn` (Apache License 2.0). `brightkite` and
`citibike` remain blocked pending license/privacy review; they are not part
of this clearance.

**Current packaging/hosting status** (a separate, operational question from
legal clearance): as of 2026-09-17, all five evaluated families (`wiki2018`,
`twemcache`, `cloudphysics`/"Alibaba Block", `metakv`, `metacdn`) are
**publicly downloadable** from Hugging Face, on the `v1.0` branch/revision
of `SoroushVahidi/lafc-evict` (see "Current public release" above), matching
the manuscript's evaluated corpus exactly (277,995,072 candidate rows,
2,363,286 decisions, plus the 1,000,000-row canonical pairwise sample). They
are not yet on AWS Open Data or Zenodo (see "Next required action" above).
`wiki2018` alone remains additionally available on the `main` branch/revision
(the pre-existing v0.3 release, unchanged).

The registry is a governance record, not legal advice.

**Historical note:** an earlier version of this section (accurate as of
2026-09-13, superseded by the 2026-09-15 review above) stated that
`cloudphysics`, `metacdn`, `metakv`, and `twemcache` "remain uncleared
pending final review." That was correct at the time it was written but is
no longer the current legal-clearance status; it is preserved here only as
historical context, not as current guidance.

## Hosting boundary

HF, AWS Open Data, and Zenodo publication state recorded here is authoritative
for LAFC-Evict. CyVerse, Harvard Dataverse, and other external hosting
exploration is outside this repository's authoritative state unless a concrete
LAFC-Evict publication record is created.
