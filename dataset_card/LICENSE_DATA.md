# Data Licensing and Redistribution Review

This repository does **not** assume that every upstream trace family can be redistributed in raw or processed form.

## Policy

- Code in this repository is licensed separately under the repository `LICENSE`.
- Data redistribution must follow the upstream source terms for each trace family.
- If redistribution is not clearly permitted, public releases should distribute only generated derivatives that are legally safe, or require users to recreate from locally acquired upstream data.

## Trace-family review checklist

| Trace family | Current status | Redistribution note |
| --- | --- | --- |
| `twemcache` | TODO upstream license review | Confirm whether processed or derived request traces may be mirrored. |
| `metakv` | TODO upstream license review | Confirm whether processed or derived trace redistribution is permitted. |
| `metacdn` | TODO upstream license review | Confirm whether processed or derived trace redistribution is permitted. |
| `cloudphysics` | TODO upstream license review | Confirm whether processed traces and generated derivatives are publicly redistributable. |
| `wikimedia/pageviews` | TODO source attribution review | Public source family, but release should document the exact dump source, transformation, and attribution obligations. |
| `citibike` | TODO license and privacy review | Do not assume public redistribution of processed traces without review. |
| `brightkite` | TODO license and privacy review | Do not assume public redistribution of processed traces without review. |

## Release guidance

- `lafc-evict-v0.1-open` should include only trace families with clean redistribution status.
- `lafc-evict-full-heavy_r1` must not be published until upstream review is complete.
- `lafc-evict-sample` may remain fully synthetic and license-clean.
