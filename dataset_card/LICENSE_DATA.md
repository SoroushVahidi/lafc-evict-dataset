# Data Licensing and Redistribution Review

This repository does **not** assume that every upstream trace family can be redistributed in raw or processed form.

The machine-readable source-family registry in `manifests/source_family_registry.yaml` is a release-governance tool for LAFC-Evict. It is **not legal advice**.

## Policy

- Code in this repository is licensed separately under the repository `LICENSE`.
- Data redistribution must follow the upstream source terms for each trace family.
- If redistribution is not clearly permitted, public releases should distribute only generated derivatives that are legally safe, or require users to recreate from locally acquired upstream data.

## Trace-family review checklist

| Trace family | Current status | Redistribution note |
| --- | --- | --- |
| `twemcache` | eligible_pending_final_review; not publication-cleared | Internal candidate only; citation and final review still required. |
| `metakv` | eligible_pending_final_review; not publication-cleared | Internal candidate only; citation and final review still required. |
| `metacdn` | eligible_pending_final_review; not publication-cleared | Internal candidate only; citation and final review still required. |
| `cloudphysics` | eligible_pending_final_review; not publication-cleared | Internal candidate only; provenance and attribution review still required. |
| `wiki2018` | cleared for v0.2 published preview | Wikimedia pageview-derived proxy; attribution and caveat wording required. |
| `citibike` | blocked_pending_review | Excluded from `lafc-evict-v0.1-open` until redistribution and privacy review are complete. |
| `brightkite` | blocked_pending_review | Excluded from `lafc-evict-v0.1-open` until license and privacy review are complete. |

## Release guidance

- The published v0.2 release includes only `wiki2018`.
- The v0.1-open trees are historical unpublished local artifacts.
- `cloudphysics`, `metacdn`, `metakv`, and `twemcache` remain excluded from public releases until final review and explicit clearance.
- `lafc-evict-full-heavy_r1` remains an internal or reproducibility target until redistribution questions are resolved.
- `lafc-evict-sample` may remain fully synthetic and license-clean.
