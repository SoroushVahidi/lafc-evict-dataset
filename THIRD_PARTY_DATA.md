# Third-Party Trace Data

LAFC-Evict computes derived cache-eviction supervision (candidate-level
counterfactual labels, decision-level summaries, pairwise samples) from
several third-party production cache traces. This document credits each
upstream source and states the license under which that source's material
is used, as reviewed 2026-09-15. It is not legal advice. See
`dataset_card/LICENSE_DATA.md` and `manifests/source_family_registry.yaml`
for the full governance record this document summarizes.

**Scope note:** this repository's own code is licensed separately under
`LICENSE` (MIT). That license covers this repository's code only -- it
does not relicense any of the third-party trace data described below.
Each family's derived artifacts remain subject to its own upstream
license's attribution/notice requirements.

## Twemcache

- **Provider:** Twitter (via the `twitter/cache-trace` project)
- **Source:** https://github.com/twitter/cache-trace
- **License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Associated publication:** Yang, Yue, and Rashmi, "A Large-Scale
  Analysis of Hundreds of In-Memory Cache Clusters at Twitter," OSDI 2020
  (cited in the Performance Evaluation manuscript as `yang2020twemcache`).

LAFC-Evict's derived supervision under the internal family key `twemcache`
includes transformed information derived from Twitter's own anonymized
production cache traces, used and redistributed here under CC BY 4.0.
Twitter/the paper authors do not endorse this derived work.

## MetaKV

- **Provider:** Meta, via the CacheLib project
- **Primary documentation:** https://cachelib.org/docs/Cache_Library_User_Guides/Cachebench_FB_HW_eval/
- **License:** Apache License 2.0 -- CacheLib's own documentation states
  these traces "are licensed under the same license as CacheLib," and
  `github.com/facebook/CacheLib` is licensed Apache-2.0.
- **Note on mirrors:** `github.com/cacheMon/cache_dataset` separately
  redistributes a copy of this trace and asserts its own blanket CC BY 4.0
  license over its whole collection. That claim is not used as the basis
  here, since it conflicts with CacheLib's own more specific statement for
  this trace; cacheMon is documented only as a known secondary mirror.

LAFC-Evict's derived supervision under the internal family key `metakv`
includes transformed information derived from Meta's own MetaKV production
key-value cache trace, used and redistributed here under Apache License
2.0 (attribution and notice preservation).

## MetaCDN

- **Provider:** Meta, via the CacheLib project
- **Primary documentation:** https://cachelib.org/docs/Cache_Library_User_Guides/Cachebench_FB_HW_eval/
- **License:** Apache License 2.0, same basis and same mirror caveat as
  MetaKV above.

LAFC-Evict's derived supervision under the internal family key `metacdn`
includes transformed information derived from Meta's own MetaCDN
production CDN request trace, used and redistributed here under Apache
License 2.0 (attribution and notice preservation).

## Alibaba Block (internal key: `cloudphysics`)

- **Internal LAFC-Evict key:** `cloudphysics`
- **Actual source:** Alibaba Cloud Elastic Block Storage (EBS) production
  block-storage trace
- **Primary source:** https://github.com/alibaba/block-traces
- **License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
  -- stated directly by the source repository: "The trace data and
  document are licensed under CC-4.0."
- **Associated publication:** the IISWC 2020 paper on Alibaba Cloud block
  storage workloads referenced from the source repository above (exact
  bibliographic metadata not independently re-verified in this pass;
  confirm before citing it formally in the manuscript bibliography).

**Historical naming disclosure (important):** `cloudphysics` is an
internal legacy identifier, embedded throughout this project's committed
manifests, analysis directories, figures, tables, and experiment outputs
for reproducibility, and is not renamed retroactively. **It must not be
interpreted as meaning the data came from VMware/CloudPhysics.** The
actual workload is Alibaba's Cloud EBS block trace, confirmed by this
project's own `docs/V0_3_V1_DATA_INVENTORY.md` (recorded local trace name
`cloudphysics_alibaba_block_head_50k`) and a matching recorded checksum in
`analysis/closed_loop_production_tier1_20260913/scripts/tier1_core.py`.
No VMware/CloudPhysics-specific trace, claim, or characteristic appears
anywhere in this repository. Public-facing prose, figures, and tables
should refer to this workload as "Alibaba Block" (or similar) at first
mention; the internal key `cloudphysics` may remain unchanged in code,
manifests, and evidence paths.

## Wiki2018

- **Provider:** Wikimedia Foundation
- **Source:** https://dumps.wikimedia.org/other/pageviews/
- **License:** CC0 1.0 Universal (public domain dedication)

See `docs/WIKI2018_PROVENANCE_REVIEW.md` for the full, previously-completed
review, attribution wording, and scope caveats for this family (already
approved with attribution and caveat wording; not changed by this
document).
