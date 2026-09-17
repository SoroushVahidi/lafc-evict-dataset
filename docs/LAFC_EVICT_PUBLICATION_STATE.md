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
- **AWS Open Data** publicly hosts the **v0.3 wiki2018-only payload** in
  bucket `lafc-evict-open-data`, region `us-west-2`: 18 objects,
  approximately 106.1 MiB, CC0 1.0, with anonymous public download previously
  verified PASS. AWS Open Data Registry PR #3335 is pending maintainer
  activity unless later local documentation proves it merged. The known fork
  branch is `add-lafc-evict-dataset`; known PR head:
  `e12ac8f90714daf2bc88987725cc2a48b916cd59`.
- **Zenodo** still serves **LAFC-Evict v0.2** as the current version:
  version DOI <https://doi.org/10.5281/zenodo.21895844>, concept DOI
  <https://doi.org/10.5281/zenodo.21895843>. A v0.3 Zenodo version has
  **not** been created -- the configured Zenodo credential returned HTTP 403
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
  2026-09-16 at `release/lafc-evict-v1.0/` -- **not yet uploaded to any
  public host.** It repackages the exact corpus behind the manuscript's
  277,995,072 candidate rows / 2,363,286 decisions (source:
  `release/lafc-evict-v0.1-open-current-contract-preserved`, no label
  regeneration), with `wiki2018` identifiers pseudonymized using the same
  scheme already published for v0.2/v0.3. All five included families
  (`cloudphysics`/"Alibaba Block", `metacdn`, `metakv`, `twemcache`,
  `wiki2018`) are cleared for public release per the 2026-09-15 registry
  review; `brightkite`/`citibike` remain excluded and blocked. See
  `release/lafc-evict-v1.0/README.md` and
  `release/lafc-evict-v1.0/metadata/validation_report.md`. Uploading this
  package to Hugging Face / AWS Open Data / Zenodo requires an explicit,
  user-approved publish step (see "Next required action" below) -- it was
  not performed automatically, since publishing this much newly-redistributed
  third-party production trace data to permanent public hosts is a
  significant, hard-to-reverse, externally-visible action.

### Next required action to make v1.0 actually public

1. Review `release/lafc-evict-v1.0/` (README, manifest, validation report,
   checksums) and confirm the packaging decisions are acceptable: wiki2018
   pseudonymization, and the inclusion of the *canonical regenerated*
   pairwise sample (not the stale one shipped in
   `lafc-evict-v0.1-open-current-contract-preserved`) -- see
   `release/lafc-evict-v1.0/README.md`'s "Pairwise sample" section and
   `analysis/pairwise_provenance_repair_20260913/REPORT.md` for why.
2. Upload to Hugging Face: `python scripts/publish_to_huggingface.py
   --release-root release/lafc-evict-v1.0 --repo-id
   SoroushVahidi/lafc-evict-v1.0` (or the existing dataset repo, as a new
   revision -- confirm which before running; this repository's own
   `publish_to_huggingface.py` requires `HF_TOKEN`/`HUGGINGFACE_HUB_TOKEN` to
   be set).
3. Upload to AWS Open Data bucket `lafc-evict-open-data` following the same
   procedure used for the v0.3 wiki2018-only payload (see
   `publication/RELEASE_CHECKLIST.md`).
4. Create a new Zenodo version under concept DOI
   `10.5281/zenodo.21895843` using a flat-layout mirror of
   `release/lafc-evict-v1.0/` (same pattern as `*-zenodo-flat` for prior
   versions) -- note the v0.3 Zenodo upload is separately blocked by an
   HTTP 403 on the configured token (see the v0.3 entry above); confirm
   token scope before attempting v1.0.
5. After upload, update this document and
   `publication/LAFC_EVICT_PUBLICATION_STATE.json` with the actual
   revision/DOI/verification evidence, the same way v0.2/v0.3 were recorded.

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
legal clearance): `wiki2018` is the only family actually **publicly hosted**
today, in the v0.3 release (Hugging Face and AWS Open Data, see above). As of
2026-09-16, all five evaluated families (`wiki2018`, `twemcache`,
`cloudphysics`/"Alibaba Block", `metakv`, `metacdn`) have been **packaged and
locally validated** together in `release/lafc-evict-v1.0/`, matching the
manuscript's evaluated corpus exactly (277,995,072 candidate rows,
2,363,286 decisions). That package is **not yet uploaded** to Hugging Face,
AWS Open Data, or Zenodo -- packaging is done, hosting is the remaining
step. Do not describe `twemcache`/`cloudphysics`/`metakv`/`metacdn` derived
rows as currently publicly downloadable; they are not, until the upload step
in "Next required action" above is completed.

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
