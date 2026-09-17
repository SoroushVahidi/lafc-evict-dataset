# Release Scope

## Published `lafc-evict-v1.0` (current public release, as of 2026-09-17)

Full five-family public release. **Published on Hugging Face on the `v1.0` revision.**

- Contains all five evaluated workload families: Alibaba Block (`cloudphysics`), MetaCDN, MetaKV, Twemcache, and Wiki2018.
- Consists of:
  - 277,995,072 candidate-level rows
  - 2,363,286 decision-horizon rows
  - 1,000,000 canonical pairwise-sample rows
- Applicable family-specific licensing: CC0-1.0 (wiki2018), CC BY 4.0 (Alibaba Block, Twemcache), and Apache License 2.0 (MetaCDN, MetaKV). See `THIRD_PARTY_DATA.md` for details.
- Publicly downloadable, checksum-verified, and represents the complete evaluated corpus in the Performance Evaluation manuscript.

## Published `lafc-evict-v0.3-candidate`

Expanded Wiki2018-only candidate. **Published on Hugging Face main revision and AWS Open Data.**

- Same two configurations as v0.2, 22,356,992 total rows, full inclusion of every available wiki2018 shard (no down-sampling).
- Publicly hosted through AWS Open Data in bucket `lafc-evict-open-data` (`us-west-2`).
- `release/lafc-evict-v0.3-candidate/` is the canonical package.

## Published `lafc-evict-v0.2-preview`

- Wiki2018-derived supervision only.
- Two configurations: `cross_family_evict_value_v1` and `objective_ablation_scalar`.
- Pseudonymized derived rows; no raw traces or raw page titles.
- Public on Hugging Face and archived on Zenodo (version DOI https://doi.org/10.5281/zenodo.21895844).

## Historical `lafc-evict-v0.1-open`

Historical unpublished real-data staging generation.

- Included only the license-clean/open-trace families selected by the source-family registry.
- Preserved locally as `lafc-evict-v0.1-open-current-contract-preserved`.

## `lafc-evict-full-heavy_r1`

Internal pre-release baseline family.

- This was the family of internal builds (5 trace families, up to ~278M candidate rows / ~2.36M decisions) used in the research work.
- It has been fully materialized and publicly released under **lafc-evict-v1.0** on Hugging Face.

## `lafc-evict-sample`

Tiny synthetic smoke-test release.

- Safe to host directly in the repository.
- Intended for examples, tests, and format validation only.
- Must not be confused with the full benchmark dataset.