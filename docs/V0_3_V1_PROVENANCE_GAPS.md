# V0.3/V1.0 Provenance and Licensing Gaps

**Status:** INTERNAL planning document. Not legal advice -- same caveat as
`dataset_card/LICENSE_DATA.md` and `manifests/source_family_registry.yaml`,
which remain the canonical machine-readable source-family registry. This
document only summarizes what those already say and identifies what
external research is still needed; it does not perform that research
(no data owners were contacted).

---

## 1. Per-family status (as of the existing registry, re-verified this pass)

| Family | Redistribution status (registry) | v0.2-preview status | Privacy risk (registry) | Combined classification for v0.3/v1.0 planning |
|---|---|---|---|---|
| `wiki2018` | `eligible_pending_final_review` (general) | `APPROVED_WITH_ATTRIBUTION_AND_CAVEAT` (real-data-preview-specific, already reviewed 2026-08-11, see `WIKI2018_PROVENANCE_REVIEW.md`) | low | **APPROVED_WITH_ATTRIBUTION_AND_CAVEAT** -- most-cleared family; the caveat is attribution wording + non-endorsement + derived-only distribution, not further legal risk |
| `cloudphysics` | `eligible_pending_final_review` | not recommended for v0.2 preview | low | **PERMISSION_REQUIRED** in the sense that "final review" was never actually closed out -- treat as `LICENSE_UNCLEAR` until someone completes and records that review, even though the registry's working assumption is favorable |
| `metacdn` | `eligible_pending_final_review` | not recommended | low | **LICENSE_UNCLEAR** -- same gap as `cloudphysics` |
| `metakv` | `eligible_pending_final_review` | not recommended | low | **LICENSE_UNCLEAR** -- same gap |
| `twemcache` | `eligible_pending_final_review` | not recommended | low | **LICENSE_UNCLEAR** -- same gap; also has the least-opaque-looking candidate ID format of the four "clean" families (see data-inventory doc section 7), which raises the review's priority slightly |
| `citibike` | `blocked_pending_review` | not recommended, `UNCLEAR` | medium | **DO_NOT_RELEASE** until both source-terms review and privacy review are separately completed and recorded |
| `brightkite` | `blocked_pending_review` | not recommended, `UNCLEAR` | medium | **DO_NOT_RELEASE** until both source-terms review and privacy review are separately completed and recorded; mobility/check-in data carries re-identification risk independent of whatever the license review concludes |

**Important distinction the registry already makes and this document
preserves:** `eligible_pending_final_review` is a *working assumption that
review has not been finalized*, not an approval. `lafc-evict-v0.1-open` (and
its `-preserved` twin) were **built** using the four
`eligible_pending_final_review` families (`cloudphysics`, `metacdn`,
`metakv`, `twemcache`) plus `wiki2018`, but that build predates the
completion of any of those four families' final review and predates the
2026-08-11 `wiki2018`-specific review entirely. **Building a real-data
release is not the same as clearing it for release** -- this is exactly the
gap that makes v0.1-open unpublished today.

## 2. What "final review" concretely still requires, per family

This is a list of the specific external research a future task must do --
this task does not do it:

- **`cloudphysics`, `metacdn`, `metakv`**: identify the exact upstream
  open-cache-trace-collection (`github.com/cacheMon/cache_dataset`) license
  file/terms and confirm they permit redistribution of *derived* supervision
  rows (feature/label pairs computed from the trace), not just permit
  *use* of the trace for research. Record the exact license identifier
  (e.g. an OSI/Creative-Commons name) and URL, the same way
  `WIKI2018_PROVENANCE_REVIEW.md` did for Wikimedia.
- **`twemcache`**: same as above, but for `github.com/twitter/cache-trace`
  specifically (a different upstream than the `cacheMon` collection); this
  repository's own top-level license terms need to be read directly, not
  assumed identical to the other three.
- **`citibike`**: read Citi Bike's system-data terms of use
  (`citibikenyc.com/system-data`) for redistribution language, **and**
  separately assess whether trip-level (not just station-level) supervision
  rows could re-identify individual riders when combined with public
  station data -- this is a privacy question independent of the license
  question.
- **`brightkite`**: read the SNAP dataset's stated terms
  (`snap.stanford.edu/data/loc-brightkite.html`) for redistribution
  language, **and** separately assess check-in/trajectory
  re-identification risk -- this family should be treated as the highest-
  scrutiny of the seven regardless of what the license text says, given the
  well-documented literature on mobility-trace re-identification.

None of this external research was performed in this task (explicitly out
of scope: "do not contact data owners in this task").

## 3. A concrete, previously-undocumented gap found this pass

`lafc-evict-v0.1-open` and `lafc-evict-v0.1-open-current-contract-preserved`
(both built from `wiki2018` among other families) **still contain raw,
non-pseudonymized Wikipedia page titles** in the `candidate_page_id` column
today, e.g. values shaped like `en:<Page_Title>` rather than a deterministic
pseudonym. This is different from the *published* v0.2 preview, which
explicitly applied a pseudonymization transform before release
(`object_ids_pseudonymized: true` in its manifest, confirmed by a separate
byte-level check in this pass).

This means: even for the one family (`wiki2018`) that already has a
completed, favorable provenance review, **the existing v0.1-open build is
not itself release-ready** -- it needs the same pseudonymization step
applied to it that the v0.2 preview already went through, before its
`wiki2018` rows (or any other family's rows) could be published. This is a
data-processing gap, not a licensing gap, but it blocks release exactly the
same way. See `V0_3_V1_BUILD_PLAN.md` for where this fits in the build
sequence.

## 4. Redistribution-status summary (task's requested vocabulary)

| Family | Status |
|---|---|
| `wiki2018` | `APPROVED_WITH_ATTRIBUTION_AND_CAVEAT` |
| `cloudphysics` | `LICENSE_UNCLEAR` |
| `metacdn` | `LICENSE_UNCLEAR` |
| `metakv` | `LICENSE_UNCLEAR` |
| `twemcache` | `LICENSE_UNCLEAR` |
| `citibike` | `DO_NOT_RELEASE` (pending review) |
| `brightkite` | `DO_NOT_RELEASE` (pending review) |

Given four of seven families are `LICENSE_UNCLEAR` and two are
`DO_NOT_RELEASE`, **only `wiki2018` is currently clear enough to publish
candidate-level real-data rows for**, exactly matching what the already-
published v0.2 preview did. This is the primary input to this task's final
classification (`PROVENANCE_REVIEW_REQUIRED_BEFORE_BUILD`).

## 5. Resolution (2026-09-15): the external research this document flagged has now been performed

This section records the outcome of the "final review" this document said
a future task would need to do. The external research (primary-source
license lookups, not just intent) was performed on 2026-09-15 as part of
the Performance Evaluation public-release audit. Findings, in full, live
in `manifests/source_family_registry.yaml`, `dataset_card/LICENSE_DATA.md`,
and `THIRD_PARTY_DATA.md`; summarized here for continuity with the gap
this document originally flagged:

| Family | Prior status (this doc) | Resolved status (2026-09-15) | Basis |
|---|---|---|---|
| `twemcache` | `LICENSE_UNCLEAR` | Cleared, CC BY 4.0 | `github.com/twitter/cache-trace`'s own repo (GitHub license API + LICENSE file text) |
| `metakv` | `LICENSE_UNCLEAR` | Cleared, Apache License 2.0 | Meta's own CacheLib documentation ("licensed under the same license as CacheLib") + `facebook/CacheLib`'s Apache-2.0 license |
| `metacdn` | `LICENSE_UNCLEAR` | Cleared, Apache License 2.0 | Same basis as `metakv` |
| `cloudphysics` (historical key) | `LICENSE_UNCLEAR` | Cleared, CC BY 4.0 -- **but see the important correction below** | `github.com/alibaba/block-traces`'s own repo ("The trace data and document are licensed under CC-4.0") |

**Important correction found during this review, not merely a licensing
answer:** the internal family key `cloudphysics` does **not** identify the
VMware/CloudPhysics dataset this document's own earlier table implied by
using that name. Per Section 3 of `docs/V0_3_V1_DATA_INVENTORY.md` (local
trace name `cloudphysics_alibaba_block_head_50k`) and a matching recorded
checksum in
`analysis/closed_loop_production_tier1_20260913/scripts/tier1_core.py`,
the actual workload behind this key is Alibaba Cloud's Elastic Block
Storage production block-storage trace. The key `cloudphysics` is
preserved unchanged in all manifests, evidence directories, figures,
tables, and experiment outputs for reproducibility -- it was **not**
renamed retroactively, and no raw data, hash, or experiment output was
regenerated or altered by this correction. Only source-registry
provenance/attribution metadata (`manifests/source_family_registry.yaml`,
`dataset_card/LICENSE_DATA.md`) and reader-facing display labels in the
Performance Evaluation manuscript (prose, figures, tables -- not internal
keys or evidence paths) were updated, to display "alibaba-block" instead
of "cloudphysics" from the first defining occurrence onward, with a
footnote explaining the historical key at first mention. No scientific
number changed as part of this correction.

`citibike` and `brightkite` were out of scope for this review and remain
`DO_NOT_RELEASE` / `LICENSE_UNCLEAR` exactly as this document originally
recorded.
