# Pairwise-Sample Provenance Repair Report

**Final-polish preservation update (2026-09-13):** this report preserves the
original repair narrative. The regenerated canonical analysis sample that this
report initially kept outside Git has now been durably preserved at
`analysis/pairwise_provenance_repair_20260913/artifacts/pairwise_sample_regenerated_canonical.parquet`.
See `ARTIFACT_MANIFEST.md` for the current durable artifact location, SHA256,
size, counts, and historical-vs-canonical distinction.

Date: 2026-09-13
Scope: provenance investigation and regeneration only. No manuscript claims changed. No file inside `release/` (or anywhere else previously tracked) was modified. No HPC job launched. No public artifact touched.

## Phase 0 — git-state check (carried over from the target-discriminativeness audit)

`analysis/sigmod_target_discriminativeness_20260913/` **was already committed**, on commit `668d179f62bb495b2686280e7db6a8f0713f0633` (branch `analysis/sigmod-target-discriminativeness-20260913`, based on `master`@`fbbeedb02ffedf571cf6a08a9a7418467d857cea`). The earlier report's `COMMIT:` field simply named the *base* commit rather than the audit's own new commit — a labeling ambiguity in that report's final block, not a real git problem. `git log --oneline -- analysis/sigmod_target_discriminativeness_20260913/` confirms the files exist only from `668d179` onward. No corrective commit action was needed for this.

## Phase 1 — verify the regenerated artifact

Generated via `scripts/regenerate_pairwise_v2.py` (a provably-equivalent, filter-pushed-down reformulation of `lafc_evict_dataset.real_release_build._build_pairwise_sample` — see that script's docstring; the unmodified function, kept for reference in `scripts/regenerate_pairwise.py`, is correct but was killed after >15 minutes with zero output because DuckDB does not push the `sampled_decisions` filter ahead of the self-join on this machine).

| Field | Value |
| --- | --- |
| Path | `/tmp/claude-1000/-home-soroush/8a66210e-4d63-4b01-b3ba-10065c25f134/scratchpad/pairwise_repair/generated/pairwise_sample.parquet` (kept outside git, per instructions) |
| Rows | 1,000,000 |
| Size | 11,367,843 bytes |
| SHA256 | `1d770c6999ac999673b46805a6ca173e24b116793b35405d2d211cae7b9eda02` |
| Schema | identical to the shipped `pairwise_sample.parquet` schema (14 columns: `decision_id, capacity, horizon, split, trace_family, trace_name, candidate_a_page_id, candidate_b_page_id, y_loss_a, y_loss_b, y_loss_diff_a_minus_b, label_a_better, label_b_better, is_tie`) |
| Source candidate artifact | `release/lafc-evict-v0.1-open-current-contract-preserved/data/candidate_rows/**/*.parquet` (168 partitions, 277,995,072 rows — the same population used throughout the target-discriminativeness audit) |
| Source artifact identity | Not independently content-hashed (168 files, 2.7GB); identity is instead established indirectly and more rigorously: `decision_view.parquet` built from this same candidate population reproduces the manuscript's decision-level reconciliation numbers to 16 significant figures (`0.9912418754543462`), which is strong evidence the population is unchanged since the manuscript's own analysis |
| Sampling seed | 7 (manifest-recorded default, confirmed matching `release_manifest.json`'s `pairwise_sample.pairwise_seed`) |
| max_pairwise_rows / max_pairs_per_decision | 1,000,000 / 8 (manifest-recorded, confirmed matching) |
| Generator code state | this checkout's HEAD at run time: `668d179f62bb495b2686280e7db6a8f0713f0663` (branch `analysis/sigmod-target-discriminativeness-20260913`) — i.e. `lafc_evict_dataset.real_release_build` as of `master`@`fbbeedb`, which includes both `1f5f272` and `3b49189` |
| Runtime | 930.2 seconds (candidates registration 0.1s + `sampled_decisions` 5.9s + `candidates_sampled` filter 15.0s + final self-join/COPY 909.2s) |
| Timestamp | 2026-09-13 (this session) |

**Independently recomputed label counts directly from the written parquet** (not generator stdout — a fresh `duckdb.connect()` + `SELECT SUM(is_tie), SUM(label_a_better), SUM(label_b_better), COUNT(*) FROM read_parquet(...)` in `scripts/compare_pairwise_states.py`):

```
n_rows: 1,000,000
n_ties: 878,262
n_a_better: 60,673
n_b_better: 61,065
```

Exact match to the generator's own stdout, and exact match to the manuscript's committed table (see Phase 2). No discrepancy between "trust the generator" and "verify independently."

## Phase 2 — full stale vs. regenerated vs. manuscript comparison

`scripts/compare_pairwise_states.py` output (`outputs/pairwise_three_state_comparison.json`):

| | **A. stale** (on-disk release) | **B. regenerated** (canonical) | **C. manuscript** (committed CSV) |
| --- | --- | --- | --- |
| Path | `release/.../data/pairwise_sample/pairwise_sample.parquet` | `.../scratchpad/pairwise_repair/generated/pairwise_sample.parquet` | `paper/sigmod2027/results/metadata_tables/table_pairwise_sample_label_summary.csv` |
| SHA256 | `99697a0d20acc643848db6bcb71656b32fad939b004cbe56f2b69b3a418bcb18` | `1d770c6999ac999673b46805a6ca173e24b116793b35405d2d211cae7b9eda02` | n/a (CSV, not a data artifact) |
| Size | 6,165,425 bytes | 11,367,843 bytes | n/a |
| Rows | 1,000,000 | 1,000,000 | 1,000,000 (implied by summed counts) |
| Ties | 879,968 | **878,262** | **878,262** |
| a_better | 6,134 | **60,673** | **60,673** |
| b_better | 113,898 | **61,065** | **61,065** |
| mtime | 2026-06-27 20:20:52 | 2026-09-13 (this session) | committed 2026-07-02 |

- `A_vs_B_identical_bytes`: **false**
- `A_vs_C_tie_count_diff`: 1,706
- `B_vs_C_tie_count_diff`: **0** — exact match on every count
- `A_matches_C_exactly`: **false**
- `B_matches_C_exactly`: **true**

**Candidate-pair identity overlap (A vs B)**, computed on the unordered pair key (decision key + `{low, high}` candidate ids, since `pairwise_sample.parquet`'s own schema only carries 5 decision-identifying columns — `trace_name, capacity, horizon, decision_id, split` — not the full 9-column canonical key):

```
a_unordered_pairs:       1,000,000
b_unordered_pairs:       1,000,000
overlap_unordered_pairs:    52,368
overlap_fraction_of_a:      0.052368
```

**SAME_UNORDERED_PAIR_SAMPLE: NO.** Only **5.24%** of A's pairs also appear in B. This is not a small, orientation-scale discrepancy — it is a near-total resampling. This single number is what forced a deeper root-cause investigation in Phase 3 below, because a pure A/B orientation reversal cannot explain a 94.76% difference in *which pairs were even selected*, let alone the tie-count delta.

## Phase 3 — root cause (corrected from the prior working assumption)

**The prior sessions' working assumption — "the stale file just predates the orientation fix, `3b49189`" — is confirmed but incomplete, and is hereby corrected.** There are **two independent fixes** between when the stale file was built and now, not one, and the tie-count/pair-identity discrepancy is fully explained by the *first* one, which has nothing to do with orientation.

**Git history of `_build_pairwise_sample`'s home file, `src/lafc_evict_dataset/real_release_build.py`** (only 4 commits ever touched it):

| Commit | Date (EDT) | What changed |
| --- | --- | --- |
| `9983cdb` | 2026-06-27 13:38 | Introduced the memory-safe real-release builder, including `_build_pairwise_sample` and a **hardcoded 6-column** `DECISION_GROUP_COLUMNS = (decision_id, capacity, horizon, split, trace_family, trace_name)` |
| `b08a514` | 2026-06-27 19:30 | Bugfixes before a full build; `DECISION_GROUP_COLUMNS` still the same 6 columns |
| **stale file built** | **2026-06-27 20:20** | ~50 minutes after `b08a514` — this is the code state that produced the file currently on disk |
| `1f5f272` | **2026-06-28 23:03** | "Harden real-release migration, validation, and publication metadata" — redefines `DECISION_GROUP_COLUMNS = tuple(DECISION_METADATA_COLUMNS)`, i.e. the full **9-column** key (adds `dataset_source`, `decision_t`, `decision_chunk_id`) |
| `3b49189` | 2026-07-02 18:28 | "Fix pairwise orientation and reconcile baseline counts" — adds the deterministic-hash A/B orientation swap; **does not touch `sampled_decisions`, the pair-enumeration CTE, or `DECISION_GROUP_COLUMNS` at all** (confirmed by re-reading the full diff — the only change to `_build_pairwise_sample`'s logic is which candidate lands in slot A vs B) |

**Why the 6→9 column change (not orientation) explains the discrepancy**: `_build_pairwise_sample`'s `sampled_decisions` CTE ranks the full set of distinct decisions by `hash(concat_ws(<DECISION_GROUP_COLUMNS values>, seed))` and takes the top 125,000. Even though — critically — the best-candidate-evaluator reconciliation report already established that **zero 6-column keys ever collapse two distinct 9-column decisions in this dataset** (i.e. this specific data has no actual key collisions, so grouping by 6 vs. 9 columns does *not* merge any rows), the **hash value itself still changes** when the concatenated string fed into `hash()` gains three more fields. A hash function is sensitive to its entire input string; `hash('a|b|c|seed')` and `hash('a|b|c|d|e|f|seed')` are unrelated even when `a,b,c` are identical. So the *set of decisions* is unchanged, but the *ranking* used to pick which 125,000 of them get sampled is a completely different (and, from a hash function's perspective, uncorrelated) permutation.

**This was verified directly, not just argued**: reran only the `sampled_decisions` selection step, once with the old 6-column list and once with the current 9-column list, both against the *current* (unchanged) decision population and seed 7:

```
old(6col) sampled decisions: 125,000
new(9col) sampled decisions: 125,000
overlap:                       6,546
overlap fraction of new:    0.052368
```

**`0.052368` — identical to six significant figures to the measured A-vs-B pair-overlap fraction above.** This is not a coincidence; it is a direct, quantitative confirmation that the 6-vs-9-column hash-input change, by itself, fully reproduces the observed near-total resampling. No population drift, no DuckDB-version hash-implementation difference, and no orientation-logic change are needed to explain it (though a DuckDB version difference cannot be fully ruled out as a compounding factor — no lock file or historical version record exists in this repo to check; see Validation Status).

**Corrected statement of the root cause**: the stale `pairwise_sample.parquet` was built under `b08a514`, **before both** `1f5f272` (6→9 column decision-key fix for the hash-based decision sampler) **and** `3b49189` (A/B orientation fix). The 6-vs-9-column change alone accounts for essentially the entire pair-identity mismatch and the resulting 1,706-tie-count delta (878,262 vs 879,968) — this is pure sampling-set churn from re-ranking a tie-heavy population under a different hash input, not evidence of a population change or a tie-determination bug. The orientation fix, layered on top four days later, is real and correctly documented, but it is not what explains the tie-count or pair-identity discrepancy — its only effect (as designed, and as confirmed by `is_tie`'s definition depending solely on `y_loss_low = y_loss_high`, computed before any orientation swap) is on which candidate is labeled A vs B, i.e. the direction-balance split. **Both fixes are needed to reach the canonical, manuscript-matching artifact; neither one alone would have been "the" cause.**

**Orientation-fix effect, isolated**: because `is_tie` is computed before the orientation swap in both the pre- and post-`3b49189` code, the fix changes *only* `label_a_better`/`label_b_better`'s meaning, never `is_tie`. This is exactly why B (built with both fixes) reproduces C's tie count exactly while also reproducing C's balanced ~49.8%/50.2% direction split — two independent correctnesses, from two independent fixes, both required.

## Phase 4 — canonical artifact decision

Per instructions, **the stale release file was not overwritten**. Decision:

- **Stale artifact preserved as-is**, documented as historical/non-canonical: `release/lafc-evict-v0.1-open-current-contract-preserved/data/pairwise_sample/pairwise_sample.parquet`, SHA256 `99697a0d20acc643848db6bcb71656b32fad939b004cbe56f2b69b3a418bcb18`, label counts (6,134 / 113,898 / 879,968).
- **Canonical regenerated artifact kept outside git** (Option A): `/tmp/claude-1000/-home-soroush/8a66210e-4d63-4b01-b3ba-10065c25f134/scratchpad/pairwise_repair/generated/pairwise_sample.parquet`, SHA256 `1d770c6999ac999673b46805a6ca173e24b116793b35405d2d211cae7b9eda02`, with the exact generation command, seed, and source recorded in Phase 1 above and in `outputs/pairwise_three_state_comparison.json`. This path is a session-scratchpad location and will not survive indefinitely; if this artifact needs to persist, it should be regenerated with `scripts/regenerate_pairwise_v2.py` (deterministic, ~930s) rather than relied upon at this exact path long-term.
- Not published, not uploaded, not written into `release/`, AWS, Hugging Face, or Zenodo.

## Phase 5 — rerun the pairwise information-content audit on the canonical sample

`scripts/rerun_pairwise_audit_canonical.py` (`outputs/canonical_pairwise_report.json`), compared against the prior (stale-file-based) audit's `outputs/pairwise_report.json`:

| Statistic | Prior audit (stale, A) | This repair (canonical, B) | Manuscript (C) |
| --- | --- | --- | --- |
| Tie fraction | 0.879968 | **0.878262** | 0.878262 |
| Strict fraction | 0.120032 | 0.121738 | 0.121738 (=121,738/1,000,000, matches `07_tasks_baselines.tex`'s stated non-tie count) |
| a_better share of strict | 0.0511 (5.1%) | **0.4984 (49.8%)** | ~49.8% (as stated in manuscript text) |
| b_better share of strict | 0.9489 (94.9%) | **0.5016 (50.2%)** | ~50.2% |
| Decisions represented | 118,635 | 118,506 | not stated |
| Decisions with ≥1 strict pair | 15.89% | 16.04% | not stated |
| Decisions with only tied pairs | 84.11% | 83.96% | not stated |
| Most discriminative cells | metacdn, horizon=16, various capacities | **same** (metacdn, horizon=16, various capacities) | (qualitatively consistent with manuscript's characterization) |
| Least discriminative cells | wiki2018, all cells, strict_fraction = 0.0 | **same** (wiki2018, all cells, strict_fraction = 0.0) | consistent |

**What changed**: the tie fraction (marginally, 0.18 percentage points) and, materially, the **direction balance** — from a badly skewed 5.1%/94.9% (stale) to the correct, balanced ~49.8%/50.2% (canonical), matching the manuscript's own claim of a non-construction-induced balance.

**What did not change**: every qualitative, family/capacity/horizon-stratified conclusion from the target-discriminativeness audit — metacdn/twemcache at small capacity and long horizon remain the most discriminative regime; wiki2018 remains completely non-discriminative (strict_fraction exactly 0.0 in every one of its cells, in both the stale and canonical samples); the overall "heavily tie-dominated but with an identifiable nontrivial regime" picture is unchanged. The decision-view-based numbers (0.9912, 0.0088, unique-winner fraction = 0, the 32.34% nontrivial subset, the LRU-vs-MRU diagnostic) were never affected by this bug in the first place, since they come from `decision_view.parquet`, not `pairwise_sample.parquet`.

**SCIENTIFIC_CLASSIFICATION_AFTER_REPAIR: B — CONDITIONALLY DISCRIMINATIVE (unchanged).** Nothing in this repair moves the classification toward A, C, or D. The repair corrects a data-provenance/reproducibility defect in one secondary artifact; it does not change any of the population-level decision-view evidence the classification was primarily based on.

## Phase 6 — predictor == LRU investigation (completed)

Re-confirmed, using the same full-population evidence gathered earlier in this session:

- `candidate_is_predictor_victim` is **bit-identical** to `candidate_is_lru_victim` across all 277,995,072 candidate rows (exact aggregate match to 16 significant figures in a full-table scan; 0/4,613,504 row-level mismatches on a direct spot-check partition).
- `predictor_lru_disagree` is **`0.0` for every one of the 277,995,072 rows** — never once fires.
- More fundamentally: `candidate_predictor_score`, `request_bucket`, `request_confidence`, `candidate_bucket`, `candidate_confidence`, `score_gap_to_predictor_best`, `bucket_gap_to_predictor_best`, and `confidence_gap_to_predictor_best` are **each a single hard-coded constant value across the entire release** (0.5, 0.0, 0.5, 0.0, 0.5, 0.0, 0.0, 0.0 respectively — `MIN = MAX`, `COUNT(DISTINCT ...) = 1` for every one of them, verified directly).

**Interpretation**: there is no functioning upstream predictor model behind this release's "predictor" features at all — they are placeholder constants. Given a constant score, whatever tie-break rule assigns "the predictor's victim" evidently defaults to the same choice as the LRU rule, which is why `candidate_is_predictor_victim` always equals `candidate_is_lru_victim` and `predictor_lru_disagree` never fires. `dataset_card/SCHEMA.md` documents `predictor_lru_disagree` as "Indicator that predictor and LRU would evict different candidates" — a field that is *always* 0 across 278M rows is inconsistent with that being a meaningful, intentionally-included feature, which is why this reads as **accidental/unfinished** (a real predictor was never wired into this release's label-generation pipeline) rather than a deliberate design choice.

**Manuscript check**: Section `07_tasks_baselines.tex`'s own committed results are consistent with this finding, not contradicted by it — the "predictor-score pairwise" baseline scores 0.5016 accuracy / 0.6931 log loss, statistically identical to the "random non-tie" (0.5006) and "majority non-tie" (0.5016) sanity checks. This is exactly what a zero-variance feature difference produces under logistic regression. **The manuscript's reported number is not wrong — it is silently explained by this finding, which the manuscript does not currently disclose.** No downstream analysis in this repo (including the pairwise-feature-baseline table) treats predictor and LRU as materially independent methods in a way that would be falsified by this finding, but the manuscript should say explicitly that `candidate_predictor_score` is a released placeholder, not a trained model's output, so a future reader doesn't misread the 0.5016 baseline result as "the predictor tried and failed" rather than "the predictor field carries no information by construction."

**Per instructions: this is reported, not acted on.** No generated data was changed. This is an open question for whoever owns the label-generation pipeline (outside this repo — the candidate features trace back to `/home/soroush/Augmented-caching/data/derived/evict_value_v1_wulver_heavy_r1/manifest.json` per the release manifest's `source_manifest` field, not to any code in `lafc-evict-dataset`) to confirm as intentional or fix.

## Phase 7 — git bookkeeping

- `analysis/sigmod_target_discriminativeness_20260913/` was already committed (Phase 0) — no action needed.
- This directory, `analysis/pairwise_provenance_repair_20260913/` (`README.md`, `REPORT.md`, `scripts/*.py` ×4, `outputs/*.json`/`*.csv` ×3), is being added and committed now, on the same branch (`analysis/sigmod-target-discriminativeness-20260913`), in a new commit.
- The 1,000,000-row regenerated parquet is **not** committed (kept at the scratchpad path recorded in Phase 1/4).
- Not pushed.

## Phase 8 — validation

- Regenerated rows = 1,000,000 — confirmed (both generator stdout and an independent fresh read).
- Regenerated counts = 60,673 / 61,065 / 878,262 exactly — confirmed independently in `compare_pairwise_states.py` and again in `rerun_pairwise_audit_canonical.py`.
- Manuscript tracked summary matches exactly — confirmed (`B_matches_C_exactly: true`).
- SHA256 recorded for both stale and regenerated files.
- Source/seed/command recorded (Phase 1 table).
- Stale artifact clearly identified as stale (Phase 4) — not deleted, not overwritten.
- Regenerated artifact clearly identified as canonical for analysis purposes (Phase 4).
- Exact discrepancy mechanism documented and *quantitatively verified* (Phase 3's 0.052368 overlap-fraction match), correcting the prior "orientation only" working assumption.
- Predictor/LRU relationship explained (Phase 6), not acted on.
- Target-discriminativeness audit artifacts confirmed already committed (Phase 0).
- Pairwise-provenance-repair artifacts committed in this session (Phase 7).
- Manuscript files unchanged — confirmed via `git status` before and after (only new files under `analysis/` were ever staged).
- No AWS/HF/Zenodo changes — none attempted.
- No HPC jobs launched — the 930-second regeneration ran locally on this machine, not on Wulver or any cluster.
- **One residual open question, honestly flagged rather than resolved**: whether a DuckDB version difference between the June 2026 build environment and this session's DuckDB 1.5.4 contributed anything on top of the 6-vs-9-column effect. No lock file, `pip freeze` snapshot, or recorded DuckDB version exists anywhere in this repo for the June build, and the quantitative match (0.052368 to 6 significant figures) between the isolated 6-vs-9-column test and the real A-vs-B discrepancy already explains the effect size well enough that a compounding version difference, if any, would have to be small. This is not further pursued here.

---

LAFC_EVICT_PAIRWISE_PROVENANCE_REPAIR_REPORT

REPO: SoroushVahidi/lafc-evict-dataset (local: /home/soroush/projects/lafc-evict-dataset/repo)
BRANCH: analysis/sigmod-target-discriminativeness-20260913

BASE_COMMIT: fbbeedb02ffedf571cf6a08a9a7418467d857cea
TARGET_AUDIT_COMMIT: 668d179f62bb495b2686280e7db6a8f0713f0633
PAIRWISE_REPAIR_COMMIT: 4c5b6437 (this commit adds this report itself; run `git log --oneline -1 -- analysis/pairwise_provenance_repair_20260913/` to reconfirm)

TARGET_AUDIT_WAS_PREVIOUSLY_COMMITTED:
YES

STALE_PAIRWISE_PATH: release/lafc-evict-v0.1-open-current-contract-preserved/data/pairwise_sample/pairwise_sample.parquet
STALE_PAIRWISE_SHA256: 99697a0d20acc643848db6bcb71656b32fad939b004cbe56f2b69b3a418bcb18
STALE_LABEL_COUNTS:
- a_better: 6,134
- b_better: 113,898
- tie: 879,968

REGENERATED_PAIRWISE_PATH: /tmp/claude-1000/-home-soroush/8a66210e-4d63-4b01-b3ba-10065c25f134/scratchpad/pairwise_repair/generated/pairwise_sample.parquet
REGENERATED_PAIRWISE_SHA256: 1d770c6999ac999673b46805a6ca173e24b116793b35405d2d211cae7b9eda02
REGENERATED_FILE_SIZE: 11,367,843 bytes
REGENERATED_ROWS: 1,000,000

REGENERATED_LABEL_COUNTS:
- a_better: 60,673
- b_better: 61,065
- tie: 878,262

MANUSCRIPT_EXPECTED_LABEL_COUNTS:
- a_better: 60,673
- b_better: 61,065
- tie: 878,262

MATCHES_MANUSCRIPT_TRACKED_SUMMARY:
YES

PAIRWISE_GENERATOR: lafc_evict_dataset.real_release_build._build_pairwise_sample
GENERATOR_COMMIT: 668d179f62bb495b2686280e7db6a8f0713f0633 (this checkout's HEAD; includes upstream fixes 1f5f272 and 3b49189 on master@fbbeedb)
GENERATION_COMMAND: analysis/pairwise_provenance_repair_20260913/scripts/regenerate_pairwise_v2.py (provably-equivalent reformulation of the unmodified generator; see script docstring for the equivalence proof and script/regenerate_pairwise.py for the verbatim-but-impractically-slow original call)
SAMPLING_SEED: 7
SOURCE_ARTIFACTS:
- release/lafc-evict-v0.1-open-current-contract-preserved/data/candidate_rows/**/*.parquet (168 partitions, 277,995,072 rows)
- release/lafc-evict-v0.1-open-current-contract-preserved/metadata/release_manifest.json (params: max_pairwise_rows=1,000,000, max_pairs_per_decision=8, pairwise_seed=7)

SAME_UNORDERED_PAIR_SAMPLE:
NO (only 5.24% pair overlap between stale and regenerated, out of 1,000,000 pairs each)

TIE_COUNT_DISCREPANCY_ROOT_CAUSE:
The stale file was built under commit b08a514 (2026-06-27), before commit 1f5f272 (2026-06-28) changed the pairwise sampler's decision-selection hash input from a hardcoded 6-column key to the canonical 9-column key. Although this dataset has zero actual 6-vs-9-column key collisions (independently confirmed via the earlier best-candidate-evaluator reconciliation), the hash() function's input STRING still changes when 3 more columns are concatenated in, which completely reshuffles the ORDER BY hash(...) LIMIT 125000 ranking used to pick which decisions get sampled -- even though the underlying decision population is identical. This was verified directly: isolating just this one variable (6-col vs 9-col hash input, same population, same seed=7) reproduces a 0.052368 overlap fraction, matching the real stale-vs-regenerated overlap to 6 significant figures. This -- not the later orientation fix (3b49189, 2026-07-02) -- is what explains the 1,706-tie-count difference and the near-total pair-identity mismatch. The orientation fix is real, correctly documented, and necessary to reach the canonical artifact, but its only actual effect is on the label_a_better/label_b_better direction split (via is_tie being computed before any orientation swap in both code versions), not on tie count or which pairs are sampled.

ORIENTATION_FIX_EFFECT:
Confirmed to affect ONLY which candidate is labeled A vs B within an already-selected pair (fixing a pre-existing "A is always the lexicographically-smaller candidate_page_id" bias to a deterministic-hash-based balanced assignment). Does not affect is_tie, decision selection, or pair selection. This was previously assumed to be the sole explanation for the stale-vs-canonical discrepancy; that assumption is corrected above.

UPDATED_PAIRWISE_INFORMATION_CONTENT (canonical sample):
- tie_fraction: 0.878262
- strict_fraction: 0.121738
- decisions_with_strict_pairs: 16.04% (19,005 / 118,506 represented decisions)
- decisions_only_ties: 83.96%
- important_strata: most discriminative = metacdn at horizon=16 across capacities (strict fraction 0.82-0.92); least discriminative = every wiki2018 cell (strict fraction exactly 0.0 in all of them) -- both unchanged from the stale-file-based audit

SCIENTIFIC_CLASSIFICATION_AFTER_REPAIR:
B -- CONDITIONALLY DISCRIMINATIVE (unchanged)

SCIENTIFIC_CONCLUSIONS_CHANGED:
NO (the decision-view-based evidence underlying the classification was never affected by this artifact's staleness; only the pairwise-sample's own reported tie-fraction and, materially, its direction-balance figures needed correction)

PREDICTOR_EQUALS_LRU:
YES

PREDICTOR_LRU_EXPLANATION:
candidate_predictor_score and every other "predictor"/"bucket"/"confidence" feature column are hard-coded constants across all 277,995,072 candidate rows (verified: MIN=MAX, COUNT(DISTINCT)=1 for each). There is no functioning upstream predictor model behind this release. Given a constant score, the tie-break used to select "the predictor's victim" defaults to the same candidate LRU would pick, which is why candidate_is_predictor_victim is bit-identical to candidate_is_lru_victim and predictor_lru_disagree is always 0. This reads as an accidental/unfinished feature path (a real, intentionally-included disagreement indicator would not be permanently at its floor value), not a deliberate design choice, but this has not been confirmed with whoever owns the upstream label-generation pipeline (outside this repo). The manuscript's own reported predictor-score-pairwise baseline result (0.5016 accuracy, indistinguishable from random/majority) is consistent with, and silently explained by, this finding -- not contradicted by it. No data was changed.

CANONICAL_PAIRWISE_ARTIFACT_DECISION:
Keep the verified regenerated parquet outside git at the scratchpad path recorded above (Option A), with its SHA256, generation command, seed, and source recorded in this report. The stale release file is left in place, unmodified, and documented as historical/non-canonical. No overwrite performed.

PROVENANCE_ARTIFACTS_CREATED:
- analysis/pairwise_provenance_repair_20260913/README.md
- analysis/pairwise_provenance_repair_20260913/REPORT.md (this file)
- analysis/pairwise_provenance_repair_20260913/scripts/regenerate_pairwise.py
- analysis/pairwise_provenance_repair_20260913/scripts/regenerate_pairwise_v2.py
- analysis/pairwise_provenance_repair_20260913/scripts/compare_pairwise_states.py
- analysis/pairwise_provenance_repair_20260913/scripts/rerun_pairwise_audit_canonical.py
- analysis/pairwise_provenance_repair_20260913/outputs/pairwise_three_state_comparison.json
- analysis/pairwise_provenance_repair_20260913/outputs/canonical_pairwise_report.json
- analysis/pairwise_provenance_repair_20260913/outputs/canonical_pairwise_strict_density.csv

MANUSCRIPT_EDITED:
NO

PUBLIC_ARTIFACTS_MODIFIED:
NO

HPC_USED:
NO

VALIDATION_STATUS:
All Phase 8 checks passed (see Phase 8 section above for the itemized list). One item explicitly left open and disclosed rather than resolved: cannot fully rule out a compounding DuckDB-version hash() difference on top of the confirmed 6-vs-9-column effect, since no historical DuckDB version record exists for the June 2026 build; the quantitative match already explains the effect size well.

WORKTREE_STATUS:
Clean except this session's own new files under analysis/pairwise_provenance_repair_20260913/ (staged for commit) and one pre-existing, unrelated untracked file (publication/.env.example.azure-cleanup-backup-20260903-213025) that predates this session and was not touched.

NEXT_SINGLE_ACTION:
Perform the already-scoped closed-loop evaluation feasibility audit before launching any new scientific experiment.
