# V0.3/V1.0 Build Plan

**Status:** INTERNAL planning document. Nothing in this document has been
executed. No large data was moved, copied, deleted, compressed, or
regenerated to produce it.

---

## 1. Relation to the KBS paper

| Component | Classification |
|---|---|
| `objective_ablation_scalar` config (backing the `FINAL_VALIDATED`, 84/84-row KBS R2 Major 2 objective-comparison result) | `MUST_RELEASE_FOR_PAPER_REPRODUCIBILITY` -- this is the KBS paper's most complete, fully citable quantitative result; a reviewer or reader reproducing it needs either this data or the exact generation recipe |
| `cross_family_evict_value_v1` config (backing KBS R2 Major 1, currently `EXPERIMENTALLY_COMPLETE_SYNTHESIS_PENDING` pending the Wulver-only 42/42 sync) | `USEFUL_RESEARCH_DATASET_EXTENSION` for now -- the KBS branch's own evidence docs mark this result as synthesis-pending, so publishing the dataset ahead of the paper's own final table risks the dataset and paper numbers disagreeing later; revisit once R2 Major 1 closes |
| A published exact copy of the Wulver-only corrected 42/42 `evict_value_v1` comparison CSV itself | `OPTIONAL_FUTURE_DATA` -- that is a small results table, not training data, and belongs with the paper's reviewer-response artifacts more than with LAFC-Evict |
| `cloudphysics`/`metacdn`/`metakv`/`twemcache`/`brightkite`/`citibike` candidate-level data | `DO_NOT_RELEASE` until each clears provenance review (see provenance-gaps doc) -- **do not let this block the paper**; the paper's citable results (objective ablation, R2 Major 2) do not depend on these families being publicly released, only on the KBS repo's own internal generated data, which already exists independent of this dataset-publication effort |
| The continuation-policy C0/C1/C2 supervision data (currently generating in `analysis/continuation_policy_causal_ablation_production_v1/` on the KBS branch) | `OPTIONAL_FUTURE_DATA` -- not ready in any sense; do not reference it in any release plan until the KBS campaign completes and its own integrity checks pass |

**Bottom line: optional dataset expansion (v0.3/v1.0) should not delay the
KBS paper.** The paper's reproducibility needs are already met by the KBS
repository's own code + internally generated data + the existing v0.2
preview; v0.3/v1.0 is a research-community-facing enhancement, not a paper
blocker.

## 2. What can be prepared locally now (low CPU/RAM/disk-I/O, safe alongside the running C0/C1/C2 campaign)

- Finish this planning-doc pass (done).
- Design/review the schema-v2 changes from `V0_3_V1_RELEASE_DESIGN.md`
  section 6 against `dataset_card/SCHEMA.md` -- pure document editing.
- Write (do not yet run) a small script or checklist to detect the
  `split` column dtype inconsistency found this pass across all of DT-8's
  partitions, so it can be fixed before the next real build -- static code
  review, tiny test data only.
- Draft the per-family "final review" checklist items from
  `V0_3_V1_PROVENANCE_GAPS.md` section 2 into a form ready for whoever does
  that external research next (a checklist is low-cost to prepare now; the
  research itself is out of scope for this task and for "low-compute local
  work" in general, since it requires reading external license pages, not
  local compute).
- Validate (schema/JSON checks only, no data movement) that
  `scripts/validate_release_schema.py` and `scripts/validate_v0_2_preview.py`
  still run cleanly against the existing published v0.2 files, as a smoke
  check that the validation tooling itself is healthy before it is asked to
  gate a v0.3 build.
- Tiny-sample tests of any new pseudonymization-scheme-reuse code, using a
  handful of synthetic rows, never DT-1/DT-8's real data at scale.

## 3. What should wait

- **Any real Parquet (re)build** (filtering DT-8 to `wiki2018`, applying
  pseudonymization, regenerating `decision_view` with narrower dtypes) is a
  nontrivial DuckDB job over gigabytes of data -- explicitly out of scope
  for this read-only audit task, and should not be run casually alongside
  the C0/C1/C2 campaign even though it is a different workstation task,
  simply to avoid competing for CPU/disk I/O while that campaign is active.
  Schedule it for after the campaign completes, per the KBS repo's own
  `NEXT_STEPS.md` "NOW" guidance.
- **External provenance research** (reading upstream license terms for
  `cloudphysics`/`metacdn`/`metakv`/`twemcache`/`citibike`/`brightkite`) --
  not a Wulver dependency, but a human/external-research dependency not
  satisfiable by local compute or by this task.
- **Any data believed to exist only on Wulver**: per the data-inventory
  doc section 9, nothing found in this audit is Wulver-only among dataset-
  release assets specifically. The one Wulver-only artifact relevant to a
  future release (the corrected 42/42 `evict_value_v1` comparison CSV) is
  KBS reviewer evidence, not itself a release building block, and should
  not be contacted for in this task (per explicit instruction not to
  contact Wulver).

## 4. Later cleanup candidates (NOT deleted -- authorization-gated list only)

| Path | Size | Why likely redundant | Confidence | Prerequisite before any deletion |
|---|---|---|---|---|
| `lafc-evict-dataset/release/lafc-evict-v0.1-open/data/candidate_rows/` | ~1.1 GB | `docs/current_release_status_v0_1_open.md` already documents this as the "stale repo-local release", byte-identical (spot-checked, SHA-256 match) to the `-preserved` copy's `candidate_rows` | High | Confirm no other file/script references `lafc-evict-v0.1-open` (non-`-preserved`) by exact path before removing; keep the `-preserved` copy regardless |
| `lafc-evict-dataset/release/lafc-evict-v0.1-open/data/decision_view/` and rest of that tree | remainder of the 1.1 GB | Superseded as a whole build by `-preserved`, per the same status doc, even though `decision_view` itself is not byte-identical (it is an earlier/incomplete build, not a duplicate) | Medium (this is "superseded", not "duplicate" -- verify nothing depends on its specific, different `decision_view` before removing) | Same as above |
| `Augmented-caching-kbs-second-revision/analysis/huggingface_dataset_preview_v0_2/` | 134 MB | Exact byte-for-byte duplicate (SHA-256 match) of `lafc-evict-dataset/release/lafc-evict-v0.2-preview/`; already flagged and gitignored (not deleted) in a prior KBS-repo polish pass | High | This is in a different repo than this one; any deletion decision belongs to that repo's own cleanup task, not this one -- listed here for completeness only |
| `Augmented-caching-preserve-20260808-104203/` | 357 MB | Historical backup metadata (manifests/hashes/patches) from a prior cleanup pass; likely no longer needed once its contents are confirmed superseded by current repo state | Low-Medium (needs a human check of what it was preserving and whether that context is still needed) | Read `preservation_manifest.txt` and confirm the preserved dirty/untracked state it captured has since been committed or is otherwise no longer needed |
| `lafc-evict-overnight-logs/` | 12 KB | Trivial historical validation-run log from the 2026-06-29 v0.1 validation pass | Low priority (trivial size, not worth the review overhead) | n/a -- too small to matter; listed only for completeness |

**Total identified for later cleanup: ~1.25-1.6 GB**, none of it acted on in
this task. The ~310 GB of large generated-data trees (DT-1, DT-2+DT-3, DT-4)
are **not** cleanup candidates -- they are independent, still-referenced
generated datasets, not duplication.

## 5. Exact next recommended dataset task

Given the provenance gaps are the binding constraint (not compute, not
missing data), the highest-leverage next task is: **complete the `wiki2018`-
only v0.3 build** (filter DT-8 to `trace_family=wiki2018`, apply the
existing v0.2-style pseudonymization to that filtered subset, fix the
`split`-column dtype inconsistency, narrow `decision_view`'s columns,
re-run the existing validation scripts, then stop -- no upload) since it
requires zero new external license research and reuses data and tooling
that already exist. In parallel (no compute conflict), begin the external
license-terms research for `cloudphysics`/`metacdn`/`metakv`/`twemcache`
from `V0_3_V1_PROVENANCE_GAPS.md` section 2, since that is the actual
bottleneck for v1.0's family count, not local compute or data availability.
