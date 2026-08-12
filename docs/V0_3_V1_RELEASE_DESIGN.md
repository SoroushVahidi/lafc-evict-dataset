# V0.3/V1.0 Release Design

**Status:** INTERNAL planning document. The v0.3 candidate has now been built
and locally validated, but is not uploaded or approved for publication. v1.0
remains planning-only. See `V0_3_V1_DATA_INVENTORY.md` for the evidence this
design is based on and `V0_3_V1_PROVENANCE_GAPS.md` for why the recommended
v0.3 scope is currently limited to `wiki2018`.

---

## 1. Release tiers

### Tier A -- Preview (existing v0.2, published)

- Purpose: minimal real-data proof that the release pipeline and Parquet
  schema work end to end.
- Families: `wiki2018` only.
- Configs: `cross_family_evict_value_v1`, `objective_ablation_scalar`.
- Size: 134 MB, 2 flat Parquet files.
- Status: **done, published** (Hugging Face + Zenodo `10.5281/zenodo.21895844`).

### Tier B -- Expanded curated release (v0.3 candidate)

- Purpose: the first release with enough real, multi-config candidate-level
  data to let an external researcher actually train and evaluate an
  eviction-value model, not just preview the schema.
- Families: **`wiki2018` only**, until `cloudphysics`/`metacdn`/`metakv`/
  `twemcache` clear `LICENSE_UNCLEAR` status (see provenance-gaps doc).
  This is a real constraint on v0.3's scope, not a design preference.
- Configs (see section 4 for detail):
  - `cross_family_evict_value_v1` (expanded: full `wiki2018` candidate rows
    plus decision view, not just a sample)
  - `objective_ablation_scalar` (expanded: full `wiki2018` scalar rows for
    all 4 objectives)
  - `objective_ablation_pairwise` (new: `wiki2018` pairwise comparison rows,
    capped per decision to avoid quadratic blowup, matching the existing
    `RELEASE_SCOPE.md` guidance for pairwise sampling)
- Source: the already-built `lafc-evict-v0.1-open-current-contract-preserved`
  tree (DT-8), filtered to `trace_family=wiki2018` only, **after** the
  pseudonymization gap in section 3 of `V0_3_V1_PROVENANCE_GAPS.md` is
  closed for that filtered subset.
- Expected size: on the order of **150-400 MB** (a `wiki2018`-only filter of
  DT-8's 2.7 GB, which spans 5 families across 4 capacities; `wiki2018` was
  71.7M of DT-1's 323M rows, roughly 22% -- scaled against DT-8's 1.1 GB
  `candidate_rows`, that is roughly 240 MB before Parquet compaction gains
  from single-family partitioning, so revise down after a real build,
  not up).
- Current state: **built locally and validated, not uploaded**.
- Whether v0.3 is worthwhile: **yes** -- it does not require new generation
  compute (DT-1/DT-8 already exist), only pseudonymization + a filtered
  rebuild + provenance sign-off for a family that is already
  `APPROVED_WITH_ATTRIBUTION_AND_CAVEAT`. This is low-risk, high-leverage
  work relative to waiting for the other four families' review.

### Tier C -- Stable/full release (proposed v1.0)

- Purpose: the citable, DOI-stable release the KBS paper and future work
  point to.
- Families: `wiki2018` plus any of `cloudphysics`/`metacdn`/`metakv`/
  `twemcache` that clear `LICENSE_UNCLEAR` by the time v1.0 is built.
  `brightkite`/`citibike` included **only if** their `DO_NOT_RELEASE` status
  is lifted by a completed review; otherwise permanently excluded from
  v1.0 and documented as such (not silently dropped).
- Configs: all of Tier B's configs, expanded to every cleared family, plus
  the `decision_view` and a capped `pairwise` config per family; optionally
  a `cross_family_v1` config built from DT-2 (93 GB source, leave-one-
  family-out folds) if the corresponding families clear review, since that
  data already exists and backs the KBS R2 Major 1 result.
- Expected size: **2-6 GB** depending on how many families clear review by
  build time (see section 2 for the arithmetic) -- notably smaller than the
  previously-discussed ~12 GB estimate, because DT-1's 96 GB of raw CSV
  compacts to roughly 1.1 GB of partitioned Parquet candidate rows across
  all 5 non-blocked families combined (per DT-7/DT-8's already-built
  numbers), and the 12 GB figure likely assumed less Parquet compaction or
  inclusion of `decision_view` at DT-8's current (oversized, see section 6)
  encoding.
- Stopping condition for calling it v1.0 rather than another v0.x: schema
  frozen (`schema_version` field stable across a released Tier B and Tier
  C), at least one full quality-gate pass (section 8) on the exact files to
  be published, and every included family independently
  `APPROVED_*`/cleared -- not `eligible_pending_final_review`.

## 2. Target size analysis

| Component | Size driver | Estimate |
|---|---|---|
| Payload (candidate rows, Parquet, Snappy/ZSTD-compressed) | row count x ~28 feature columns x compression ratio | ~1.1 GB for 5 families' full candidate rows (already measured in DT-7/DT-8) |
| `decision_view` | currently 1.6 GB in DT-8 for the same 5 families -- **larger than the candidate rows it summarizes**, which is a red flag (see section 6) worth fixing before v0.3, likely via narrower dtypes / dropping redundant columns rather than shipping as-is |
| `pairwise` (capped sample) | capped at `--max-pairs-per-decision` in the existing build script | 5.9 MB at a 1M-row cap (already measured in DT-7/DT-8) |
| Metadata (manifests, schema, checksums, dataset cards) | fixed, small | a few hundred KB, matches v0.2's ~10 metadata files |
| Temporary build space | DuckDB temp dir during `build_real_release.py` | not measured this pass (read-only audit); the existing script already has a `--duckdb-temp-dir` flag, budget headroom equal to at least the input CSV size for the family being filtered |
| Source-data space | DT-1 (96 GB) stays on disk regardless; not part of the release payload | n/a |

Recommendation: **do not ship `decision_view` at its current per-row byte
width for v0.3/v1.0** without first checking whether its columns can be
narrower (float64 -> float32, category-encode `trace_family`/`split`) --
this is a data-quality/schema task, see section 6, not a decision to make
without inspecting the actual column widths first in a future task.

## 3. Parquet sharding design

- Partition by `trace_family` (primary) then `capacity` then `horizon`,
  matching the layout DT-7/DT-8 already use
  (`split=.../trace_family=.../capacity=.../horizon=.../candidate_rows.parquet`).
  This keeps per-partition file sizes in a reasonable single-digit-MB to
  low-hundred-MB range already, based on DT-8's measured sizes, and avoids
  both the "millions of tiny files" and "one giant file" failure modes.
- For Hugging Face: keep the nested directory layout as-is (HF Dataset
  Viewer handles nested Parquet trees; this is what v0.1-open already
  produced, so no new tooling is needed for that target).
- For Zenodo: continue the v0.2 pattern of a **flat** mirror
  (`*-zenodo-flat/`) generated from the nested tree at publish time, since
  Zenodo's file bucket has no folder concept -- this was already solved for
  v0.2 (`ZENODO_V0_2_FLAT_EQUIVALENCE.md`) and the same script/approach
  should be reused, not redesigned.
- Recommended target shard size: **too small to matter yet** at v0.3 scale
  (single-family, ~200-400 MB total) -- keep one Parquet file per
  `capacity x horizon` cell as DT-8 already does. Revisit shard granularity
  only if a future multi-family v1.0 pushes any single partition file past
  ~200-500 MB, which is not expected given the measured per-family
  proportions.
- Avoid train/test leakage in sharding: never split a single `decision_id`
  across two shards or two splits (see section 5).

## 4. Proposed Hugging Face configs

| Config | Purpose | Source | v0.3 | v1.0 |
|---|---|---|---|---|
| `cross_family_evict_value_v1` | primary candidate-level supervision (existing v0.2 config, expanded) | DT-8 filtered/expanded | yes (wiki2018 only) | yes (all cleared families) |
| `objective_ablation_scalar` | 4-objective scalar comparison (existing v0.2 config, expanded) | DT-4 filtered/expanded, once pseudonymized | yes (wiki2018 only) | yes (all cleared families) |
| `objective_ablation_pairwise` | capped pairwise comparison rows | DT-4, pairwise view, capped sample | optional (if size budget allows) | yes |
| `decision_view` | one row per decision, summary stats | DT-8-derived, narrower schema (section 6) | no (keep v0.3 minimal) | yes |

Avoid config explosion: do not create a separate config per capacity or per
horizon -- capacity/horizon are columns/partitions within a config, not
separate configs, matching the existing schema design.

## 5. Split / leakage invariants

- Existing `split` semantics (`train`/`val`/`test` at the trace/decision
  level, per DT-8's `row_counts_by_split`) are already family- and
  decision-grouped, not row-grouped -- preserve this: **all candidate rows
  for one `decision_id` must stay in the same split.**
- For any future `cross_family_v1`-derived config: preserve the leave-one-
  family-out invariant already implemented in DT-2 -- a held-out family's
  data must never appear in another family's training partition. Document
  this explicitly in the dataset card, since it is a different (stronger)
  invariant than the plain train/val/test split above and users could
  otherwise mix them incorrectly.
- Explicit public semantics to state in the v0.3/v1.0 dataset card:
  - "training families" vs. "held-out families" only applies to the
    `cross_family_evict_value_v1` config, not `objective_ablation_*`.
  - `decision_id` is the grouping key that must never be split across
    train/val/test or across a pairwise pair's two members.
  - Source shard pseudonyms (`trace_name`) are stable within a release but
    are release-facing labels, not guaranteed stable across `wiki2018`
    trace-collection dates.

## 6. Proposed stable v1 schema (vs. current v0.1-open/v0.2 schema)

Baseline: `dataset_card/SCHEMA.md`'s existing candidate-row schema (already
well-defined, matches DT-1's actual CSV header exactly -- do not redesign
from scratch).

| Change | Reason |
|---|---|
| Add `schema_version` field (e.g. `"lafc-evict-candidate-v2"`) | Existing `schema_version: "lafc-evict-candidate-v1"` is stamped in the manifest but not in the row data itself; stamping it in-row (or at minimum keeping it manifest-pinned and referenced from the dataset card) lets future consumers detect schema drift without cross-referencing a separate file |
| Rename `candidate_page_id` -> `candidate_object_pseudonym` | The current name is a holdover from the `wiki2018`-first development history; `object` is the general term used elsewhere in the schema/provenance docs, and `_pseudonym` makes the released-value contract explicit (never a raw identifier) |
| Pseudonymize `candidate_object_pseudonym` for every family before release | Currently only true for the published v0.2 preview, not for DT-7/DT-8 (see provenance-gaps doc section 3) |
| Narrow numeric columns | Most feature columns are stored as `float` (implicitly float64 in the CSV source); check whether `float32` is sufficient before the next real build -- not verified this pass, flagged as a build-time task, not decided here |
| Category-encode `trace_family`, `split`, `dataset_source` | Low-cardinality repeated strings; Parquet dictionary encoding already helps here but an explicit `category`/enum-like typing at the config level would make schema validation stricter |
| Add a `release_version` field | Lets a user who has concatenated multiple release versions' Parquet files together tell them apart; currently only available via the separate `release_manifest.json`, not in-row |
| Fix the `split` column dtype inconsistency found this pass | A `pyarrow.parquet.read_table` dataset-level read across DT-7's `wiki2018` partitions raised `ArrowTypeError: Unable to merge: Field split has incompatible types: string vs dictionary<...>` -- some shards store `split` as plain `string`, others as `dictionary<string>`. This does not break single-file reads but **does** break naive `pyarrow.dataset`-style reads across partitions and must be fixed (pin one encoding) before any wider release, not just documented |

Backward compatibility with v0.2: v0.2's two configs used the v1 schema
already (per `schema.json` in DT-9/DT-10); a `schema_version` bump to v2
should be purely additive (new optional columns, renamed-with-alias where
cheap) so that code written against v0.2 does not silently break, but this
was not verified column-by-column in this pass -- do that check when the
schema change is actually implemented, not before.

## 7. Data quality gates (mandatory before any future publish)

At minimum, reusing/extending the validation already implemented in
`scripts/validate_real_release.py` / `validate_release_schema.py` /
`validate_v0_2_preview.py` (all present in this repo already -- do not
reimplement):

- schema validation (column names/types match the declared `schema_version`)
- row-count validation against the build manifest
- uniqueness constraints on `decision_id x candidate_object_pseudonym`
- decision/candidate consistency (every candidate row's decision exists in
  `decision_view`; every `decision_view` row's candidate count matches the
  candidate rows present)
- no train/test/held-out-family leakage (section 5's invariants)
- no `NaN`/`Inf` in `y_loss`/`y_value` or any feature column not explicitly
  documented as nullable
- target-domain validation (`y_loss >= 0`, `y_value = -y_loss` exactly)
- capacity/candidate-count consistency (candidate count per decision should
  not exceed `capacity`)
- family consistency (`trace_family` matches the partition path)
- source-provenance completeness (`provenance_summary.csv` covers every
  included family with a redistribution status, not `UNCLEAR`)
- license status gate: **fail closed** if any included family's
  `redistribution_status` in `manifests/source_family_registry.yaml` is
  anything other than an explicit `APPROVED_*` value -- this is the gate
  that currently blocks a straight rebuild of DT-8 into v0.3/v1.0
- privacy scan (reuse `security_scan.json`'s existing approach from v0.2)
- local-path scan (no `/home/`, `/tmp/`, `/mmfs1` absolute paths in any
  public-facing file -- already checked for v0.1-open's publication bundle
  per `current_release_status_v0_1_open.md`; re-run for any new build)
- token/secret scan
- duplicate detection (re-run the section-5-style spot checks from the
  data-inventory doc, not a full byte-for-byte hash of the whole release)
- deterministic build manifest (already implemented -- `release_manifest.json`)
- SHA-256 manifest (already implemented -- `checksums.sha256`)

**Fail-closed conditions:** any family with a non-`APPROVED_*`
redistribution status must be excluded from the build entirely (not
included-with-a-warning); any row failing the leakage/uniqueness/NaN checks
must fail the whole build, not be silently dropped; any local absolute path
found in a public-facing file must block publish.

## 8. Reproducibility manifest design

Extend the existing `release_manifest.json` structure (already covers
`dataset_id`, `version`, `schema_version`, `source_manifest`,
`family_selection_manifest`, row counts) to also explicitly record, per
release:

- source trace family list with each family's provenance/license
  classification **inline** (not just by reference to the registry file,
  so the manifest is self-describing even if the registry changes later)
- generation code SHA (git commit of the KBS repo that produced the source
  CSV/Parquet -- DT-1's manifest does not currently record this; add it)
- generation config SHA (hash of whatever config drove the DT-1/DT-2/DT-4
  build)
- transformation pipeline version (`build_real_release.py`'s own version/SHA)
- schema hash (hash of the column-name/type list, not just a version string,
  so silent schema drift is detectable even under an unchanged version
  string)
- pseudonymization method identifier (see section 9) and namespace
- split construction method reference
- release version and prior-version lineage (`supersedes: "v0.2"` etc.)

**Must not** include local absolute filesystem paths in the public-facing
copy -- DT-8's `release_manifest.json` currently stores
`source_manifest: "/home/<username>/Augmented-caching/data/derived/..."`,
which is fine for the *internal* build record but must be stripped/relativized
for the version actually published (v0.1-open was never published, so this
has not yet been tested end-to-end against a real publish -- flag for the
build plan, not fixed here).

## 9. Pseudonymization design

- Requirement recap: deterministic within scope, no secret key needed by
  downstream users, no reversible leakage of raw identifiers, stable across
  reproducibility runs, namespace-separated per family.
- The already-published v0.2 preview's pseudonymization scheme (referenced
  in its `manifest.json` as `object_ids_pseudonymized: true`, "deterministic
  release pseudonyms") already satisfies these requirements **for the one
  family it was applied to**. Reuse the same scheme/implementation for
  `wiki2018` in v0.3 rather than designing a new one.
- **Not yet verified this pass**: whether that same scheme, applied to the
  other six families' identifier formats (numeric/hash-like for
  cloudphysics/metacdn/metakv, longer non-hash for twemcache, short
  non-hash for citibike, 32-char hash for brightkite), needs any per-family
  adjustment -- e.g. a family whose raw ID is already a 32-character hash
  (brightkite) may not need the same transform as a family with raw
  human-readable text (wiki2018). This is a concrete task for whoever
  extends pseudonymization beyond `wiki2018`, not resolved here.
- Namespace separation: confirm (in a future task, by reading the
  pseudonymization code, not assumed here) that the same raw ID in two
  different families cannot collide to the same pseudonym -- likely already
  true if the scheme salts by `trace_family`, but verify before extending
  beyond one family.

## 10. Storage / hosting plan

| Target | Role | v0.3 fit | v1.0 fit |
|---|---|---|---|
| Hugging Face | primary interactive/ML-ready host | Well within normal free-tier dataset storage at ~150-400 MB | Likely still within normal storage at 2-6 GB; the existing `HUGGINGFACE_STORAGE_REQUEST_DRAFT.md` in this repo suggests storage was already anticipated as a possible future need -- re-evaluate against the actual v1.0 build size once families are finalized, don't request storage speculatively |
| Zenodo | DOI-backed archival snapshot | Well within Zenodo's standard per-record allowance (v0.2 used 140 MB of a much larger allowance) | Should remain within standard allowance at the 2-6 GB estimate; Zenodo's default limit is generously above that, but confirm the exact current limit before v1.0 build (not re-verified this pass) |
| GitHub (`lafc-evict-dataset` repo) | code/manifests/docs only | No change -- continue keeping the `release/` directory's large Parquet payloads out of git (already the case; `release/` is not fully git-tracked today per the `.gitignore`, verify pattern coverage for any new v0.3 directory name before building it) | Same |

No storage was requested or allocated in this task, per instructions.

## 11. Versioning plan

- **v0.2** (done): `wiki2018`-only preview, proof of pipeline.
- **v0.3** (proposed): justified by (a) `wiki2018` expanding from a small
  preview sample to the full candidate-row set already built in DT-8, (b)
  adding the `objective_ablation_pairwise` config, (c) fixing the schema
  issues in section 6 -- all achievable without new provenance clearance
  beyond what `wiki2018` already has.
- **v1.0** (proposed): justified only once (a) at least one additional
  family clears `LICENSE_UNCLEAR` -> an explicit `APPROVED_*` status, (b)
  the schema is frozen as `schema_version=v2` with no further planned
  breaking changes, (c) a full quality-gate pass (section 7) succeeds on
  the exact files to be published.
- **Future versions**: schema/data changes should bump `schema_version`
  (breaking) or add optional columns under the same `schema_version`
  (non-breaking); family-set expansions alone (e.g. adding `cloudphysics`
  once cleared) can be a minor version bump (`v1.1`) without a schema
  change, if the schema is already stable by then.
- **Zenodo mechanics**: future releases must use the existing concept DOI
  `10.5281/zenodo.21895843`'s "new version" workflow (as v0.2 already did,
  landing at version DOI `10.5281/zenodo.21895844`), never a new unrelated
  Zenodo record -- this is already established practice, just carrying it
  forward.
