# Release Scope

## Published `lafc-evict-v0.2-preview`

- Wiki2018-derived supervision only.
- Two configurations: `cross_family_evict_value_v1` and
  `objective_ablation_scalar`.
- Pseudonymized derived rows; no raw traces or raw page titles.
- Public on Hugging Face and archived on Zenodo.

## Historical `lafc-evict-v0.1-open`

Historical unpublished real-data staging generation.

- Include only the license-clean/open-trace families selected by the source-family registry and selector output.
- Publish candidate rows, decision view, release metadata, schema docs, manifests, and checksums.
- Do not include ambiguous trace families until upstream review is complete.
- CitiBike and Brightkite remain excluded until review is complete.
- The registry and selector are release-governance tools, not legal advice.
- Full pairwise materialization is intentionally not part of the default real release because it can grow quadratically with decision size.
- Pairwise tasks can be derived from candidate rows or generated as capped samples with `scripts/build_real_release.py --pairwise-sample`.

## Published `lafc-evict-v0.3-candidate` (current public release, as of 2026-08-13)

Expanded Wiki2018-only candidate. **Published on Hugging Face and AWS Open
Data** (this section previously said "not uploaded or published" -- corrected
2026-09-12; the AWS public-hosting status was added in the final handoff
documentation). Same two configurations as v0.2, 22,356,992 total rows, full
inclusion of every available wiki2018 shard (no down-sampling).
The `release/lafc-evict-v0.3-candidate/` and `release/lafc-evict-v0.3-zenodo-flat/`
local packages are scientifically identical (verified via DuckDB `EXCEPT`,
2026-09-12); they differ only in an internal `release_version` row tag
(zenodo-flat still carries a stale pre-finalization value) and Parquet
row-group sizing -- see `publication/LAFC_EVICT_PUBLICATION_STATE.json` for
the full reconciliation record. `release/lafc-evict-v0.3-candidate/` is
canonical.

## `lafc-evict-full-heavy_r1`

Internal or pre-release heavy version.

- Intended to reflect the larger generated dataset family used in heavier experiments.
- Requires upstream license review before any public redistribution.
- Remains an internal or reproducibility target until redistribution questions are resolved.
- Must not be treated as automatically publishable just because generated labels were computed locally.
- This is the family of internal builds (5 trace families, up to ~278M
  candidate rows / ~788K decisions) used in the SIGMOD 2027 submission's
  benchmark description. It is **not** part of the public v0.3 release and
  is **not** in scope for the AWS Open Data submission -- do not conflate the
  two when citing or reusing this dataset (added 2026-09-12).

## `lafc-evict-sample`

Tiny synthetic smoke-test release.

- Safe to host directly in the repository.
- Intended for examples, tests, and format validation only.
- Must not be confused with the full benchmark dataset.
