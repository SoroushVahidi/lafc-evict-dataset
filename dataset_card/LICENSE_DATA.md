# Data Licensing and Redistribution Review

This repository does **not** assume that every upstream trace family can be redistributed in raw or processed form.

The machine-readable source-family registry in `manifests/source_family_registry.yaml` is a release-governance tool for LAFC-Evict. It is **not legal advice**.

## Policy

- Code in this repository is licensed separately under the repository `LICENSE`.
- Data redistribution must follow the upstream source terms for each trace family.
- If redistribution is not clearly permitted, public releases should distribute only generated derivatives that are legally safe, or require users to recreate from locally acquired upstream data.

## Trace-family review checklist

Reviewed 2026-09-15. Full evidence, primary-source URLs, and reasoning for
each row are in `manifests/source_family_registry.yaml` and
`THIRD_PARTY_DATA.md`; this table is a summary, not the authoritative
record.

| Internal family key | Actual upstream source | License | Public status |
| --- | --- | --- | --- |
| `wiki2018` | Wikimedia public pageviews | CC0 1.0 | cleared (see `docs/WIKI2018_PROVENANCE_REVIEW.md`) |
| `twemcache` | Twitter production cache traces (`github.com/twitter/cache-trace`) | CC BY 4.0 | cleared |
| `metakv` | Meta MetaKV production cache trace, via CacheLib | Apache License 2.0 | cleared |
| `metacdn` | Meta MetaCDN production cache trace, via CacheLib | Apache License 2.0 | cleared |
| `cloudphysics` (historical key -- see note) | **Alibaba Cloud EBS block-storage trace** (`github.com/alibaba/block-traces`) | CC BY 4.0 | cleared |
| `citibike` | Citi Bike trip-data | source terms require review | blocked_pending_review |
| `brightkite` | SNAP Brightkite check-ins | source terms and privacy require review | blocked_pending_review |

**Historical-key note on `cloudphysics`:** this project's internal family
key `cloudphysics` is retained for reproducibility -- it is embedded
throughout committed manifests, analysis directories, figures, tables, and
experiment outputs, and is deliberately **not** renamed retroactively. It
does **not** identify the VMware/CloudPhysics trace. The actual workload
behind this key is Alibaba's Cloud EBS block-storage trace (confirmed by
`docs/V0_3_V1_DATA_INVENTORY.md`'s recorded local trace name
`cloudphysics_alibaba_block_head_50k` and a matching checksum in
`analysis/closed_loop_production_tier1_20260913/scripts/tier1_core.py`).
Public-facing prose and figures/tables should identify this workload as
"Alibaba Block" (or similar) at first mention rather than implying it is
VMware/CloudPhysics data; the internal key may remain `cloudphysics` in
code, manifests, and evidence paths.

**Code-license vs. data-license scope:** the repository's `LICENSE` (MIT)
covers this repository's *code* only. It does not, and is not intended to,
relicense the third-party trace data described above. Every trace family's
own upstream license governs redistribution of material derived from it;
LAFC-Evict's derived/transformed artifacts are distributed subject to the
applicable upstream attribution/notice requirements (CC BY 4.0 attribution
for `twemcache`/`cloudphysics`, Apache-2.0 attribution and notice
preservation for `metakv`/`metacdn`; Wiki2018 is CC0-1.0), not under MIT.

**On the `cacheMon/cache_dataset` mirror:** this collection separately
redistributes `metakv`, `metacdn`, and a *different* trace it calls
"CloudPhysics" (the genuine VMware/vscsiStats trace, unrelated to this
project's `cloudphysics` key), all under its own blanket CC BY 4.0 claim.
Where that blanket claim conflicts with a primary source's own stated
license (as it does for `metakv`/`metacdn`, which Meta's CacheLib
documentation states are licensed under Apache-2.0), this document treats
the primary source as authoritative and cacheMon as a documented secondary
mirror path only, not the license basis.

## Release guidance

- The current full public v1.0 release includes `wiki2018`, `cloudphysics`
  (Alibaba Block), `metacdn`, `metakv`, and `twemcache`.
- The published v0.2 Zenodo archival release includes only `wiki2018`.
- The older v0.3 HF-main/AWS release includes only `wiki2018`.
- The v0.1-open trees are historical unpublished local artifacts.
- `cloudphysics` (Alibaba), `metacdn`, `metakv`, and `twemcache` are now
  `cleared_for_public_release` per the 2026-09-15 review recorded above and
  in `manifests/source_family_registry.yaml`.
- `lafc-evict-full-heavy_r1` remains an internal or reproducibility target
  until redistribution questions are resolved for its other constituent
  families (`citibike`, `brightkite`).
- `lafc-evict-sample` may remain fully synthetic and license-clean.
