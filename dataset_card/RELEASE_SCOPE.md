# Release Scope

## `lafc-evict-v0.1-open`

Recommended first public release.

- Include only license-clean or clearly redistributable trace families.
- Publish candidate rows, decision view, pairwise view, schema docs, manifests, and checksums.
- Do not include ambiguous trace families until upstream review is complete.

## `lafc-evict-full-heavy_r1`

Internal or pre-release heavy version.

- Intended to reflect the larger generated dataset family used in heavier experiments.
- Requires upstream license review before any public redistribution.
- Must not be treated as automatically publishable just because generated labels were computed locally.

## `lafc-evict-sample`

Tiny synthetic smoke-test release.

- Safe to host directly in the repository.
- Intended for examples, tests, and format validation only.
- Must not be confused with the full benchmark dataset.
