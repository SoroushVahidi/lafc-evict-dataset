# Release Scope

## `lafc-evict-v0.1-open`

Recommended first public release.

- Include only the license-clean/open-trace families selected by the source-family registry and selector output.
- Publish candidate rows, decision view, pairwise view, schema docs, manifests, and checksums.
- Do not include ambiguous trace families until upstream review is complete.
- CitiBike and Brightkite remain excluded until review is complete.
- The registry and selector are release-governance tools, not legal advice.

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
