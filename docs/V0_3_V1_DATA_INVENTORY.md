# V0.3/V1.0 Data Inventory

The original inventory predates the local v0.3 build. The current candidate is
also recorded as DT-14 in `publication/v0_3_v1_asset_inventory.json`: it is a
Wiki2018-only, 22,356,992-row, locally validated, unpublished candidate.

**Status:** INTERNAL planning document. Contains local absolute paths for
engineer usability; do not copy paths verbatim into public-facing metadata.
Read-only audit only -- nothing was moved, deleted, copied, compressed, or
regenerated to produce this document.

**Audit date:** 2026-08-11. **Scope:** local workstation only (this audit did
not contact Wulver). Companion docs:
[`V0_3_V1_RELEASE_DESIGN.md`](V0_3_V1_RELEASE_DESIGN.md),
[`V0_3_V1_PROVENANCE_GAPS.md`](V0_3_V1_PROVENANCE_GAPS.md),
[`V0_3_V1_BUILD_PLAN.md`](V0_3_V1_BUILD_PLAN.md).

---

## 1. Repositories/worktrees inspected

| Path | Role |
|---|---|
| `/home/soroush/lafc-evict-dataset` | Canonical dataset-publication repo (branch `master`, HEAD `04ee3d4` at audit start, clean, 0 ahead/behind `origin/master`) |
| `/home/soroush/Augmented-caching` | Main KBS research repo; holds the original `evict_value_v1_wulver_heavy_r1` generated data |
| `/home/soroush/Augmented-caching-fairness` | Feature worktree; holds `evict_value_v1_cross_family_v1` / `evict_value_v1_fair_v1` generated data |
| `/home/soroush/Augmented-caching-objective-ablation` | Feature worktree; holds `supervision_objective_ablation_v1` generated data |
| `/home/soroush/Augmented-caching-kbs-second-revision` | KBS second-revision worktree; holds a duplicate v0.2-preview staging copy and small processed summaries only, no large raw generated trees |
| `/home/soroush/Augmented-caching-3l-cache`, `-cacheus`, `-halp`, `-kbs-parallel`, `-main` | No substantial local `data/` (~312 KB each: examples + raw README only) |
| `/home/soroush/Augmented-caching-preserve-20260808-104203` | Historical metadata-only backup (manifests/hashes/patches from a prior cleanup pass, no raw candidate data) |
| `/home/soroush/lafc-evict-overnight-logs` | Trivial (12 KB) historical validation-run logs |

`git worktree list` was used to confirm the current Augmented-caching worktree set; `data/` is **not** shared/symlinked between worktrees -- each has its own independent directory, confirmed by direct size inspection.

## 2. Large data trees (bounded `du`/`find`, no full recursive hashing)

| Asset ID | Path | Size | Files/shards | Format |
|---|---|---|---|---|
| DT-1 | `Augmented-caching/data/derived/evict_value_v1_wulver_heavy_r1` | 96 GB | 662 CSV shards, 500K rows/shard | CSV |
| DT-2 | `Augmented-caching-fairness/data/derived/evict_value_v1_cross_family_v1` | 93 GB | per-held-out-family dirs, `shards/` + `_manifests/` | CSV |
| DT-3 | `Augmented-caching-fairness/data/derived/evict_value_v1_fair_v1` | 2.9 GB | -- | CSV |
| DT-4 | `Augmented-caching-objective-ablation/data/derived/supervision_objective_ablation_v1` | 121 GB | per-family `scalar/` + `pairwise/` shards | CSV |
| DT-5 | `Augmented-caching/data/raw` | 799 MB | per-family source dirs | mixed (source-native) |
| DT-6 | `Augmented-caching/data/processed` | 140 MB | -- | processed intermediate |
| DT-7 | `lafc-evict-dataset/release/lafc-evict-v0.1-open` | 1.1 GB | partitioned Parquet (`split=/trace_family=/capacity=/horizon=`) | Parquet |
| DT-8 | `lafc-evict-dataset/release/lafc-evict-v0.1-open-current-contract-preserved` | 2.7 GB | same partitioning as DT-7 plus a much larger `decision_view` | Parquet |
| DT-9 | `lafc-evict-dataset/release/lafc-evict-v0.2-preview` | 134 MB | 2 flat Parquet files | Parquet |
| DT-10 | `lafc-evict-dataset/release/lafc-evict-v0.2-zenodo-flat` | 134 MB | flat mirror of DT-9 for Zenodo's flat file bucket | Parquet |
| DT-11 | `lafc-evict-dataset/release/lafc-evict-sample-v0.1` | 236 KB | tiny synthetic CSV/Parquet | mixed |
| DT-12 | `Augmented-caching-kbs-second-revision/analysis/huggingface_dataset_preview_v0_2` | 134 MB | mirrors DT-9 | Parquet |
| DT-13 | `Augmented-caching-preserve-20260808-104203` | 357 MB | JSON manifests, `.sha256`, git patches | metadata only, no candidate rows |

**Total inventoried (large trees only): ~318 GB.** The previously-discussed
~121 GB / ~93 GB / ~96 GB figures are each still approximately correct
**today**, but they are three **independent** generated datasets (DT-4,
DT-2, DT-1 respectively), not three copies of the same thing -- see section
5 (duplication).

Confirmed **not** present anywhere on this workstation: any per-family raw
trace tree beyond DT-5 (799 MB); no additional trace families beyond the
seven listed in section 3; no local copy of the corrected/Wulver-only
`evict_value_v1_cross_family_v1` 42/42 replay CSV referenced by the KBS
repo's reviewer docs (confirmed absent by path search during the prior KBS
polish pass).

## 3. Trace families (complete list confirmed across all trees)

Exactly seven families appear in every generated-data tree inspected;
no additional or unexpected families were found:

`wiki2018, brightkite, citibike, cloudphysics, metacdn, metakv, twemcache`

| Family | Original source | Local trace name(s) | Shards in DT-1 (candidate rows) |
|---|---|---|---|
| `wiki2018` | Wikimedia public pageviews | `wiki2018_pageviews_en_50k` | 71,738,880 |
| `brightkite` | SNAP Brightkite check-ins | `brightkite_50k` | 21,928,704 |
| `citibike` | Citi Bike NYC trip data | `citibike_202401_50k` | 23,119,296 |
| `cloudphysics` | Alibaba block-I/O workload (via open cache-trace collection) | `cloudphysics_alibaba_block_head_50k` | 68,193,696 |
| `metacdn` | CDN trace (via open cache-trace collection) | `metacdn_cdn_202303_head_50k` | 39,463,680 |
| `metakv` | KV-cache trace (via open cache-trace collection) | `metakv_kvcache_202206_head_50k` | 54,268,608 |
| `twemcache` | Twitter/Twemcache open trace collection | `twemcache_cluster26_sample100_50k` | 44,330,208 |

DT-1 (`evict_value_v1_wulver_heavy_r1`) generation parameters (from its
`manifest.json`): 7 traces, capacities `{32, 64, 128, 256}`, horizons
`{4, 8, 16}`, `max_requests_per_trace=50000`, 662 shards,
**323,043,072 total candidate rows**. Note `capacity=256` and
`horizon∈{8,16}` appear here but are **not** part of the KBS
`reviewer_fairness_v1` protocol (which uses capacities `{32,64,128}` and
primary horizon `H=4`); they exist for the target-degeneracy/horizon-tie-break
diagnostics documented on the KBS `kbs/second-revision-science` branch.

## 4. Data-asset classification (A-G)

| Asset ID | Path | Class | Rationale |
|---|---|---|---|
| DT-5 | `data/raw` | A/B (original + normalized source) | Per-family raw/normalized trace inputs, has its own `README.md` |
| DT-6 | `data/processed` | B | Normalized intermediate, small |
| DT-1 | `evict_value_v1_wulver_heavy_r1` | C (generated supervision, intermediate) | Candidate-level `eviction_loss`/`y_value` rows, CSV, **contains raw (non-pseudonymized) candidate identifiers**, all 7 families incl. license-blocked ones -- not release-ready as-is |
| DT-2, DT-3 | `evict_value_v1_cross_family_v1`, `_fair_v1` | C/D | Leave-one-family-out generated supervision + intermediate models feeding the KBS R2 Major 1 baseline comparison |
| DT-4 | `supervision_objective_ablation_v1` | C | 4-objective (eviction_loss/next_arrival/reuse_distance/pairwise) generated supervision feeding the KBS R2 Major 2 result (`FINAL_VALIDATED`, 84/84) |
| DT-7 | `lafc-evict-v0.1-open` | F (superseded duplicate of DT-8's `candidate_rows`) | See section 5 |
| DT-8 | `lafc-evict-v0.1-open-current-contract-preserved` | E (final-candidate, unpublished) | Built via `scripts/build_real_release.py` from DT-1; validated locally 2026-06-29; **never published**; still contains raw wiki2018 titles (see `V0_3_V1_PROVENANCE_GAPS.md`) |
| DT-9, DT-10 | v0.2-preview / v0.2-zenodo-flat | E (final, published) | Live on Hugging Face + Zenodo; hashes verified against known-good values (section 6) |
| DT-11 | `lafc-evict-sample-v0.1` | E (final, published-adjacent) | Tiny synthetic smoke sample |
| DT-12 | KBS repo's `huggingface_dataset_preview_v0_2` | F (exact duplicate of DT-9/DT-10) | See section 5 |
| DT-13 | preserve-20260808 dir | G (historical backup, metadata only) | No candidate rows; JSON manifests + hashes + git patches from a past cleanup pass |

## 5. Duplication findings (cheap methods only -- filenames/sizes/manifests/spot hashes)

| Pair | Classification | Evidence | Reclaimable (est.) |
|---|---|---|---|
| DT-7 `candidate_rows/` vs DT-8 `candidate_rows/` | **EXACT_CONFIRMED** | Identical row counts in both `release_manifest.json` files (277,995,072 candidate rows); spot-checked one partition file (`split=train/trace_family=cloudphysics/capacity=32/horizon=8/candidate_rows.parquet`) -- SHA-256 `70a69a2158...` identical in both trees | ~1.1 GB (DT-7's `candidate_rows` share) |
| DT-7 `decision_view` vs DT-8 `decision_view` | **INDEPENDENT** (not a duplicate) | DT-7's `decision_view` is 15 MB, DT-8's is 1.6 GB -- `docs/current_release_status_v0_1_open.md` identifies DT-7 as the "stale repo-local release" and DT-8 as the validated "preserved current-contract release"; DT-7's decision_view is an incomplete/earlier build | n/a (not safe to treat as duplicate; DT-7 as a whole is superseded, see below) |
| DT-12 vs DT-9/DT-10 | **EXACT_CONFIRMED** | `cross_family_evict_value_v1.parquet` SHA-256 `38ae87b88b...` identical across all three copies | 134 MB (DT-12, in the KBS repo -- already gitignored there as of the prior KBS-repo polish pass, not deleted) |
| DT-1 vs DT-2 vs DT-4 (the three ~100 GB+ trees) | **INDEPENDENT** | Different directory structure, different manifests, different scientific purpose (single-target full generation vs. leave-one-family-out folds vs. 4-objective ablation); no shared filenames found in a `find`-based structural comparison | 0 (not duplicates) |
| DT-13 (preserve dir) vs DT-1 | **INDEPENDENT** | DT-13 contains only `.done.json` / `.sha256` / manifest files matching DT-1's shard names, not the shard data itself | 0 (not duplicates) |

**Total confirmed reclaimable via exact duplication: ~1.25 GB**, all of it
low-value historical/staging copies, not the ~300 GB of large generated
trees (which are independent and each still actively referenced by KBS
reviewer documentation). **No deletion was performed** -- see
`V0_3_V1_BUILD_PLAN.md` section "Later cleanup candidates" for the
authorization-gated list.

## 6. v0.2 published-state verification (read-only; nothing modified)

Confirmed against the task's known-good values, all matching exactly:

- Zenodo flat package (DT-10): **15 files**, **140,145,802 bytes** total (`du -cb`).
- `cross_family_evict_value_v1.parquet` SHA-256: `38ae87b88bf8367d41f0dc8638eaf12fa5416b559d24c7023f39b9f1c7b6bb8f`
- `objective_ablation_scalar.parquet` SHA-256: `90a2cb7913e234323190810906644e110f5c9ebeaaea47203857f61b822757f9`

No modification was made to DT-9 or DT-10.

## 7. Privacy/sensitivity spot-checks (structural only -- no sensitive values printed)

Object-identifier format was checked structurally (length/character-class
pattern) without printing raw values for any family except `wiki2018`
(public, CC0-licensed page titles, non-sensitive):

| Family | `candidate_page_id` format in DT-1 | Risk classification |
|---|---|---|
| `wiki2018` | Raw human-readable page title (e.g. `en:<Page_Title>`) | `LOW_RISK` content-wise (public CC0 text) but **not currently pseudonymized** in DT-1/DT-7/DT-8 -- `PSEUDONYMIZATION_REQUIRED` before any release reuses this tree (the *published* v0.2 preview already applied pseudonymization via a separate, already-completed transform) |
| `cloudphysics` | Short numeric/hash-like token | `LOW_RISK` -- workload/block-I/O identifiers, already opaque |
| `metacdn` | Long numeric/hash-like token | `LOW_RISK` -- already opaque |
| `metakv` | Short numeric/hash-like token | `LOW_RISK` -- already opaque |
| `twemcache` | Longer non-numeric, non-hash-pattern token | `AGGREGATION_REQUIRED` caution -- format not confirmed opaque; needs a direct (non-printing) format check before release even though the registry rates this family `privacy_risk: low` |
| `citibike` | Short non-numeric, non-hash-pattern token | `PSEUDONYMIZATION_REQUIRED` -- combined with `blocked_pending_review` license status; do not inspect further until license clears |
| `brightkite` | 32-character hash-like token | `PSEUDONYMIZATION_REQUIRED` + `AGGREGATION_REQUIRED` -- already opaque at the ID level, but mobility/check-in traces carry well-known trajectory re-identification risk independent of ID opacity; combined with `blocked_pending_review` license status, treat as `DO_NOT_RELEASE_PENDING_REVIEW` |

Full per-family provenance/redistribution classification is in
`V0_3_V1_PROVENANCE_GAPS.md`.

## 8. Existing generated supervision datasets (section 9 of the task)

| Dataset | Target(s) | Rows (approx) | Families | Capacities | Horizons | Splits | Feeds |
|---|---|---|---|---|---|---|---|
| DT-1 `evict_value_v1_wulver_heavy_r1` | `y_loss`/`y_value` (`eviction_loss`, H primary=4) | 323,043,072 | all 7 | 32/64/128/256 | 4/8/16 | none pre-assigned (per-decision) | source for DT-7/DT-8 real-release build |
| DT-2 `evict_value_v1_cross_family_v1` | `eviction_loss`, leave-one-family-out | not counted (93 GB, per-family shards) | all 7 (as held-out folds) | 32/64/128 | 4 | cross-family train/held-out | KBS R2 Major 1 (`evict_value_v1` corrected comparison) |
| DT-4 `supervision_objective_ablation_v1` | `eviction_loss`, `next_arrival`, `reuse_distance`, `pairwise` | not counted (121 GB, scalar+pairwise per family) | all 7 | 32/64/128 | 4 | scalar/pairwise views | KBS R2 Major 2 (`FINAL_VALIDATED`, 84/84 rows) |
| DT-7/DT-8 `lafc-evict-v0.1-open*` | same as DT-1, Parquet-compacted | 277,995,072 candidate rows, 2,363,286 decisions, 1,000,000 pairwise sample | 5 (excludes brightkite/citibike) | 32/64/128/256 | (per DT-1 selection) | train/val/test (205.7M/44.1M/28.2M) | unpublished v0.1-open candidate real release |
| DT-9/DT-10 v0.2-preview | `eviction_loss` (cross-family) + objective-ablation scalar | small (preview-scale) | `wiki2018` only | -- | -- | -- | published HF/Zenodo preview |

Exact row/column counts for DT-2 and DT-4 were not fully enumerated (would
require summing across hundreds of CSV shards); their manifests and
per-family `provenance.json`/`label_statistics.json` files already record
this and are cheap to re-read if needed for the build plan.

## 9. What should wait for Wulver

- No v0.3/v1.0 data component was found to exist **only** on Wulver among
  the trees inspected -- everything discovered locally (DT-1, DT-2, DT-4,
  DT-7, DT-8) is already present on this workstation.
- The KBS branch's `CROSS_ENVIRONMENT_EVIDENCE_MATRIX.md` separately
  documents a **Wulver-only** corrected `evict_value_v1` cross-family 42/42
  replay (SHA-256 `982bfdffdb...`) that is *not* present locally under any
  path searched. That artifact is KBS reviewer evidence, not itself a
  dataset-release asset, but if a future release wants to publish the exact
  scored comparison table (not just the training rows), that specific CSV
  would need to be synced from Wulver first -- not done in this task.
- The C0/C1/C2 continuation-policy campaign currently running locally
  (`analysis/continuation_policy_causal_ablation_production_v1/` in the KBS
  repo) is a candidate **future** dataset component (see
  `V0_3_V1_RELEASE_DESIGN.md` versioning plan) once it completes and passes
  integrity checks -- not ready for inclusion in any release now.
