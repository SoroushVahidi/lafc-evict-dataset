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

## Local `lafc-evict-v0.3-candidate`

Expanded Wiki2018-only candidate, locally built and validated, not uploaded or
published.

## `lafc-evict-full-heavy_r1`

Internal or pre-release heavy version.

- Intended to reflect the larger generated dataset family used in heavier experiments.
- Requires upstream license review before any public redistribution.
- Remains an internal or reproducibility target until redistribution questions are resolved.
- Must not be treated as automatically publishable just because generated labels were computed locally.

## `lafc-evict-sample`

Tiny synthetic smoke-test release.

- Safe to host directly in the repository.
- Intended for examples, tests, and format validation only.
- Must not be confused with the full benchmark dataset.
