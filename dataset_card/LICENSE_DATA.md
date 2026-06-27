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
| `twemcache` | eligible_pending_final_review | Candidate for `lafc-evict-v0.1-open`; citation and final review still required. |
| `metakv` | eligible_pending_final_review | Candidate for `lafc-evict-v0.1-open`; citation and final review still required. |
| `metacdn` | eligible_pending_final_review | Candidate for `lafc-evict-v0.1-open`; citation and final review still required. |
| `cloudphysics` | eligible_pending_final_review | Candidate for `lafc-evict-v0.1-open` if the open trace collection provenance is confirmed; citation still required. |
| `wiki2018` | eligible_pending_final_review | Candidate for `lafc-evict-v0.1-open` if derived from Wikimedia public pageviews; cite as a pageview-derived proxy, not a byte-for-byte CDN trace. |
| `citibike` | blocked_pending_review | Excluded from `lafc-evict-v0.1-open` until redistribution and privacy review are complete. |
| `brightkite` | blocked_pending_review | Excluded from `lafc-evict-v0.1-open` until license and privacy review are complete. |

## Release guidance

- `lafc-evict-v0.1-open` should initially include only the license-clean/open-trace families selected by `manifests/source_family_registry.yaml` and `manifests/lafc_evict_v0_1_open_families.json`.
- CitiBike and Brightkite remain excluded from `lafc-evict-v0.1-open` until review is complete.
- `lafc-evict-full-heavy_r1` remains an internal or reproducibility target until redistribution questions are resolved.
- `lafc-evict-sample` may remain fully synthetic and license-clean.
