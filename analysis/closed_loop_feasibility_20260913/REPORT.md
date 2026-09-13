# Closed-Loop Cache-Policy Evaluation Feasibility Audit

Date: 2026-09-13
Scope: inspection and planning only. No experiments launched, no Wulver jobs, no label regeneration, no canonical data changed, no manuscript edits, nothing published.

## Phase 1 — Repository map

Two repositories are relevant; a third location referenced by the release manifest no longer exists on disk.

- **`lafc-evict-dataset`** (`/home/soroush/projects/lafc-evict-dataset/repo`, branch `analysis/sigmod-target-discriminativeness-20260913`, commit `76d562f`) — dataset/benchmark packaging repo. Confirmed by full-repo grep and `git log --all`: **zero** simulator, cache-state, or eviction-policy code anywhere in its history. It consumes already-generated candidate rows and fits one offline model (`linear_score`, a streaming ridge/normal-equation regression) on them.
- **`Augmented-caching`** (`/home/soroush/projects/augmented-caching/repo`, branch `chore/repository-polish`, commit `ceb3670`) — the actual research codebase. Contains a real, tested closed-loop simulator (`src/lafc/simulator/`, `src/lafc/policies/`, `src/lafc/runner/run_policy.py`), the label-generation pipeline that produced the released candidate rows (`src/lafc/evict_value_dataset_v1.py`, `src/lafc/evict_value_features_v1.py`), and a genuine closed-loop learned policy `evict_value_v1` (HistGradientBoostingRegressor, `models/evict_value_v1_hist_gb.pkl`).
- Three **unmerged worktrees** carry additional baselines not on `chore/repository-polish` or `main`: `worktrees/3l-cache` (`feat/3l-cache-baseline`), `worktrees/cacheus` (`feat/cacheus-baseline`), `worktrees/halp` (`feat/halp-baseline`).
- The release manifest's `source_manifest` field points to `/home/soroush/Augmented-caching/data/derived/evict_value_v1_wulver_heavy_r1/manifest.json` — this exact path **no longer exists** (the repo has since moved to `/home/soroush/projects/augmented-caching/repo`); the specific historical Wulver run directory that generated this release's candidate rows was not recovered. This is a provenance gap worth flagging to whoever owns the label-generation pipeline, independent of this audit.
- `archive/Augmented-caching-preserve-20260808-104203` is a pre-cleanup backup of uncommitted diffs/artifacts, not an alternate/fuller codebase (confirmed by structural diff — no `src/`, `tests/`, or `docs/` tree at all).

Full grep/git-log sweep across both repos for LRU/MRU/random/LFU/SIEVE/S3-FIFO/3L-Cache/CACHEUS/HALP/linear_score/predictor is recorded in `outputs/component_inventory.json`.

## Phase 2 — Closed-loop simulator

**A working closed-loop simulator already exists** in `Augmented-caching`:

- `src/lafc/simulator/cache_state.py` — `CacheState`: `is_full()`, `add()` (raises if called while full), `evict()`. Item-count capacity only; no byte-size/object-size admission modeling in the core state object (a `Page.weight` field supports cost-weighting, not occupancy sizing).
- `src/lafc/policies/base.py` — `BasePolicy` ABC: `reset(capacity, pages)` initializes a fresh `CacheState`; abstract `on_request(request) -> CacheEvent` is the pluggable per-request callback, with the documented contract that eviction happens strictly before insertion on a full-cache miss — exactly the "call the policy on every full-cache miss, let its choice determine subsequent state" pattern required.
- `src/lafc/runner/run_policy.py` — `run_policy(policy, requests, pages, capacity)` is the actual sequential replay loop (`policy.reset(...)`, then `for req in requests: event = policy.on_request(req)`); deterministic for a fixed trace/policy/seed (stochastic policies take an explicit `--seed`). Output is a `SimulationResult` (`src/lafc/types.py`): `total_cost`, `total_hits`, `total_misses`, per-step `events`.
- `src/lafc/simulator/request_trace.py` — loads JSON (`requests`, optional `weights`/`predictions`) or CSV. `load_trace()` dispatches by extension.
- Tests exist and pass: `tests/test_simulator.py`, `tests/test_runner.py`, `tests/test_policies.py`, `tests/test_sieve.py` (55 passed once `PYTHONPATH=src`/editable install is set up — the package is simply not `pip install -e`'d in this ambient shell, not a real defect).
- **Previously used in published experiments**: yes — `scripts/experiments/canonical/run_policy_comparison_wulver_v1.py` already runs the trained `evict_value_v1` model through this same simulator, i.e. this is not a prototype, it is the project's existing closed-loop evaluation path for its own learned policy.

**Object-size assumption**: unit-size / item-count only. All three external baselines (3L-Cache, CACHEUS, HALP) explicitly self-document "unit-size adaptation" as a deliberate simplification from their original byte-size settings — consistent with the released dataset's own capacities (32/64/128/256 objects, unit miss cost), so no adaptation is needed to match the paper's existing capacity semantics.

## Phase 3 — Policy inventory

| Policy | Status | Evidence |
| --- | --- | --- |
| LRU | IMPLEMENTED_AND_READY | `src/lafc/policies/lru.py` — `OrderedDict`-backed, tested |
| MRU | NOT_IMPLEMENTED | zero hits in any branch's history; trivial (LRU with reversed eviction order) |
| Uniform random | NOT_IMPLEMENTED as standalone | `random` used internally in `adaptive_query.py`/`lrb.py` fallback paths only; trivial to add |
| LFU | NOT_IMPLEMENTED standalone | CR-LFU exists only bundled inside the third-party CACHEUS class |
| SIEVE | IMPLEMENTED_AND_READY | `src/lafc/policies/sieve.py` — faithful NSDI'24 Algorithm 1 port with paper-to-code mapping comments, cross-checked against reference C impl; tested |
| S3-FIFO | NOT_IMPLEMENTED | zero matches on any branch |
| 3L-Cache | IMPLEMENTED_BUT_NEEDS_ADAPTER | `worktrees/3l-cache/src/lafc/policies/three_l_cache.py`, 633 lines, faithful reimplementation from FAST'25 paper + pinned reference C++ commit, tested (30 passed); not merged into `main`/HEAD |
| CACHEUS | IMPLEMENTED_BUT_NEEDS_ADAPTER | `worktrees/cacheus/src/lafc/policies/cacheus.py`, wraps the **official** third-party `Cacheus` class (fetched via `scripts/setup/fetch_cacheus_official.py`); adapter isolates the official class's hardcoded `np.random.seed(123)` side effect; known upstream crash at capacity=1 (documented); 21 tests pass; not merged |
| HALP | IMPLEMENTED_BUT_NEEDS_ADAPTER | `worktrees/halp/src/lafc/policies/halp.py`, 270 lines, independent OSDI'23 reimplementation (LRU + Bradley-Terry pairwise model over 8 oldest candidates), has an explicit `test_no_future_leakage_from_next_arrival` test (passes); not merged |
| `evict_value_v1` (learned) | IMPLEMENTED_AND_READY | `src/lafc/policies/evict_value_v1.py` + `models/evict_value_v1_hist_gb.pkl` — genuinely closed-loop, plugs into the same registry/loop as LRU/SIEVE |
| manuscript `linear_score` | IMPLEMENTED_BUT_NEEDS_ADAPTER | exists only as an offline candidate-ranking model in `lafc-evict-dataset`; never wired into the simulator; needs a thin `BasePolicy` adapter that scores the current cache's resident pages using the model's coefficients |

Also present (not requested but closed-loop-ready): `marker`, `fifo_reinsertion`, `blind_oracle`, `predictive_marker`, `trust_and_doubt`, `weighted_lru`, `offline_belady` (offline-optimal oracle, for comparison only), `lrb` (external NSDI'20 baseline, needs optional `lightgbm`), and several experimental `atlas_*`/`sentinel_*`/`rest_v1` policies.

## Phase 4 — Tracing the manuscript's `linear_score` baseline

- **Training script**: `scripts/sigmod2027/run_value_regression_baseline.py` in `lafc-evict-dataset` (NOT in Augmented-caching). Fits a streaming closed-form normal-equations regression of `y_loss` on `FEATURE_COLUMNS` (26 columns, `src/lafc_evict_dataset/schema.py:22-49`) over the **released candidate_rows parquet directly** — three streaming passes (feature means, normal equations, evaluation).
- **Training data**: `release/lafc-evict-v0.1-open-current-contract-preserved/data/candidate_rows/**/*.parquet`, train split only (205,726,368 rows).
- **Model artifact**: `paper/sigmod2027/results/baselines/value_regression/linear_regression_y_loss.json` — full coefficient dump, verified directly (see below).
- **Evaluation**: split-level regression metrics only (`mae`, `rmse`, `r2`) plus a decision-level induced ranking (`best_candidate_from_linear_score.json`, argmin over the fitted score within each decision) and a pairwise reuse (`linear_score_pairwise`). **This is candidate-ranking-only, never real replay.**
- **Fit quality**: test R² = 0.0026, val R² = −0.0506 — the manuscript's own text calls this "intentionally weak," consistent with what was found.

**Critical direct finding (verified by reading the coefficient JSON, not inferred):** of the 26 `FEATURE_COLUMNS` fed into the fit, the fitted coefficients confirm quantitatively that far more of them are degenerate than the prior predictor audit enumerated:

- Exactly **zero** coefficient (0.0, to float precision) on: `bucket_gap_to_lru_victim`, `bucket_gap_to_predictor_best`, `cache_bucket_max/mean/min/std`, `confidence_gap_to_lru_victim`, `confidence_gap_to_predictor_best`, `predictor_lru_disagree`, `score_gap_to_predictor_best`, `candidate_bucket` (~1e-16), `request_bucket` (~1e-11) — 11 features contribute nothing.
- A **shared, identical, non-zero "phantom" coefficient** (1.0719685890848...) on four *different* feature names — `cache_confidence_mean`, `candidate_confidence`, `candidate_predictor_score`, `request_confidence` — which is the signature of perfectly-collinear identical-constant columns (all four are hard-coded at 0.5 everywhere) being split evenly by a minimum-norm pseudoinverse solve on a rank-deficient design matrix. This is a numerical artifact, not learned signal, and it is further duplicated by `cache_unique_bucket_count`'s coefficient (2.1439...) which is numerically indistinguishable from the model's own intercept (2.1439...) — i.e. this constant column's "coefficient" is really just re-absorbing part of the intercept.
- `candidate_is_lru_victim` and `candidate_is_predictor_victim` get the **exact same coefficient** (−0.02584...), for the same reason (identical columns).
- The only features carrying real, non-degenerate signal are: `candidate_lru_score` (1.503, the largest genuine coefficient), `candidate_age_norm` (0.641), `score_gap_to_lru_victim` (−0.641, its near-exact negative), `candidate_recency_rank` (−0.000245), `recent_candidate_request_rate` (19.34), `recent_candidate_hit_rate` (−15.20), and the LRU-victim indicator (−0.026, shared with the predictor alias).

**Interpretation**: `linear_score` is a real, independently-fitted 26-feature model — it is **not** the same object as the broken `candidate_predictor_score` field, and it is not invalidated by the predictor bug. But of its 26 nominal input features, roughly **14 are inert** (either exactly zero or absorbed as a spurious shared/intercept-like constant) as a direct consequence of the same upstream constant-feature problem the predictor audit found. Effectively, `linear_score`'s real predictive content reduces to LRU-recency-family features plus two request/hit-rate features — which also explains why the manuscript's plain LRU-derived heuristic baseline (pairwise accuracy 0.9596) already beats `linear_score` (0.9530), and why a plain logistic regression on feature differences (0.9676) beats both: `linear_score` is close to a noisy reparameterization of LRU, not a materially richer learned model, given this release's candidate rows.

**Can `linear_score` make a valid closed-loop eviction choice at every event?** Only in principle, and only after the adapter work in Phase 3. Its genuinely load-bearing features (recency rank, age, LRU score, request/hit rate) are all computable online from cache/request history. Its degenerate features are harmless (they'd contribute ~0 or a constant offset at every request, changing nothing about ranking). So `linear_score` *could* be deployed closed-loop without leaking anything — but doing so would mostly reproduce LRU with cosmetic differences, which is scientifically underwhelming as "the learned baseline" the reviewers are asking to see compared against SIEVE/S3-FIFO/etc. **The real, substantially different learned baseline for a closed-loop comparison is `evict_value_v1` (HistGradientBoostingRegressor), not `linear_score`.**

### Online-feature audit (for the features that matter)

| Feature | Classification | Basis |
| --- | --- | --- |
| `candidate_recency_rank`, `candidate_age_norm` | ONLINE_AVAILABLE | position in recency order within the resident cache (`dataset_card/SCHEMA.md`), purely a function of past requests |
| `candidate_lru_score`, `candidate_is_lru_victim`, `score_gap_to_lru_victim` | ONLINE_AVAILABLE | derived from the same recency ordering |
| `recent_candidate_request_rate`, `recent_candidate_hit_rate` | ONLINE_AVAILABLE | "recent ... frequency ... over the configured history window" — backward-looking by construction |
| `candidate_predictor_score` and the 13 other constant bucket/confidence/gap fields | UNKNOWN / MOOT | never varies in this release, so their *intended* online-availability can't be assessed from this data; they contribute ~0 to `linear_score` regardless |
| `y_loss`/`y_value` (target, not a feature) | COUNTERFACTUAL_ONLY, correctly excluded from `FEATURE_COLUMNS` | confirmed not present in the feature list fit by the regression — no target leakage into the model's inputs |

No feature actually used by the manuscript's `linear_score` requires future information. The main risk is not leakage into `linear_score`'s inputs; it is that ~half its nominal feature space is dead weight, which the manuscript does not currently disclose.

## Phase 5 — Predictor vs. `linear_score` vs. `evict_value_v1`

Three distinct objects, now traced separately as instructed:

1. **The released `candidate_predictor_score`/bucket/confidence fields** — hard-coded constants across all 277,995,072 rows (re-confirmed directly on a fresh partition scan in this session: `COUNT(DISTINCT ...)` = 1 for every predictor/bucket/confidence column, exactly matching the prior audit). `candidate_is_predictor_victim` is bit-identical to `candidate_is_lru_victim`.
2. **The manuscript's `linear_score`** — a separate, freshly-fit ridge regression computed downstream, in `lafc-evict-dataset`, directly on the released (partially degenerate) candidate rows. It is a real model, distinct from (1); it merely inherits (1)'s degeneracy as unusable inputs.
3. **`Augmented-caching`'s `evict_value_v1`** — the actual, currently-maintained closed-loop learned policy (HistGradientBoostingRegressor, `models/evict_value_v1_hist_gb.pkl`), trained via `scripts/experiments/canonical/train_evict_value_wulver_v1.py` on features defined in `src/lafc/evict_value_features_v1.py` (the same 26-name schema, non-degenerate in that repo's own feature-extraction code — no evidence found that `evict_value_features_v1.py`'s computation is itself broken).

**What code populates the released constant fields?** No code in either inspected repository currently computes them as constants — `lafc-evict-dataset` only reads a `split` column and candidate-row columns that arrive already baked in; `Augmented-caching`'s own feature-extraction code (`evict_value_features_v1.py`) does not look structurally broken. The most likely explanation, consistent with all evidence gathered, is that the **specific historical data-generation run that produced this release's candidate rows** (`evict_value_v1_wulver_heavy_r1`, per the release manifest's `source_manifest`) ran its predictor-scoring step against a placeholder/untrained fallback scorer (e.g. `src/lafc/learned_gate/lightweight_estimator.py`'s dependency-free `_linear_score` sigmoid fallback, which — with zero/degenerate weights — would output a constant 0.5 and default its argmin tie-break to LRU order) rather than a real trained `evict_value_v1` checkpoint. **This could not be confirmed further without either the missing `evict_value_v1_wulver_heavy_r1` run directory (path no longer exists on this machine) or the pipeline owner's direct confirmation — flagged as instructed, not resolved.**

**Classification: UNFINISHED_FEATURE (bug-adjacent), not INTENTIONAL_PLACEHOLDER.** `dataset_card/SCHEMA.md` documents `predictor_lru_disagree` as "Indicator that predictor and LRU would evict different candidates" — a field permanently at its floor value across 278M rows is inconsistent with that being a deliberately-shipped, meaningful feature.

**Does the manuscript ever imply this predictor is an independent learned policy, or compare LRU against an alias of itself?** No manuscript sentence found asserts the predictor field is an independently-functioning trained model. The one place it appears as a headline number — `predictor_score_pairwise`: accuracy 0.9489, log loss 0.2023 (`paper/sigmod2027/results/baselines/pairwise/feature_pairwise_results.md`) — is numerically consistent with, and silently explained by, the constant-field finding (it is not a random/chance number; it matches `majority_non_tie` almost exactly, 0.9489, because a constant predictor score degenerates the "predictor's choice" to whatever the tie-break defaults to). **`PREDICTOR_LRU_ALIAS_INVALIDATES_EXISTING_RESULT: NO`** — no published claim states or relies on the predictor being materially different from LRU; the number is silently explained, not falsified. It is, however, a disclosure gap: a future reader could easily misread 0.9489 as "an independent learned predictor nearly matches LRU," when it is actually "LRU compared against a constant."

## Phase 6 — Data split / leakage audit

Two independent split mechanisms exist, one in each repo, and they are **not the same** — this needs to be tracked carefully in any closed-loop pilot design.

**In the released data (`lafc-evict-dataset`)**: verified directly by querying the canonical release —

```
trace_name                          n_splits  min_t/max_t per split
cloudphysics_alibaba_block_head_50k   3       train spans t=32..49999 (nearly the whole trace);
                                                val is the window t=12288..16383; test is t=16384..24575
                                                (both windows nested INSIDE train's overall time range)
metacdn / metakv / twemcache / wiki2018: same pattern — every trace_name appears in 2-3 splits, with
                                                val/test occupying carved-out interior chunks, not a
                                                trailing holdout and not a separate trace file
```

**There are only 5 traces total (one per family).** Trace-level holdout (an unseen trace) is therefore **not possible** with the current release composition — "held-out" can only mean a held-out *time-chunk* within the same 5 continuously-replayed traces already used for `train`. This is a materially different (weaker) notion of "held out" than the audit's own Phase 7 instructions implicitly assumed, and it must be stated explicitly in any pilot/production writeup.

**In `Augmented-caching`'s label-generation code**: `src/lafc/evict_value_dataset_v1.py:33-44` (`_split_by_trace_and_capacity`) assigns split by a deterministic hash of `f"{trace}|cap={capacity}"` — i.e. by (trace, capacity) pair, not by time. The Wulver-scale builder (`scripts/experiments/canonical/build_evict_value_dataset_wulver_v1.py:34`) additionally supports `--split-mode source_family`, which **would give a genuine held-out-family split** (train on 4 families, test on the 5th) — this mode exists and is usable, but it is not what produced the currently-released candidate rows (whose split pattern, confirmed above, is a within-trace time/chunk split, not a family split).

**Leakage findings**:

- No raw future-leakage found in `evict_value_features_v1.py`'s feature set or in `EVICT_VALUE_V1_FEATURE_COLUMNS` — none of them read `actual_next` or any raw future-trace value; `y_loss`/`y_value` (the future-horizon rollout labels) are used strictly as regression targets, never as inputs, in both repos.
- `HALP` (the OSDI'23 baseline) trains online using `actual_next`-derived pairwise comparisons, but only for already-elapsed, matured events — it has its own explicit `test_no_future_leakage_from_next_arrival` test, which passes. This is a real, disclosed design choice, not a leak.
- **Genuine open risk, not previously documented**: because `train`'s time range in the released data surrounds/overlaps `val`/`test`'s carved-out windows within the same continuous trace, any rolling/windowed statistic (`recent_candidate_request_rate`, `recent_candidate_hit_rate`, `cache_bucket_*` aggregates) computed without respecting split boundaries could summarize history that spans across a split boundary. This does not leak future information (the window is still backward-looking in wall-clock/request-index time), but it means `train` and `test` are **not statistically independent** the way an unseen-trace holdout would be — a policy "fit on train" for these five traces has already seen most of each trace's overall statistical character before ever touching its own `test` chunk. This should be disclosed as a limitation of any offline-vs-closed-loop comparison that uses this release's `split` column, and argues for including the `source_family`-mode split as an additional, stronger validity check in the pilot.

## Phase 7 — Minimum convincing closed-loop pilot

Given the evidence above (simulator ready, LRU/SIEVE ready, raw 50k-request traces present, no trace-level holdout available), the following minimal pilot is feasible **today** with only small implementation work (adding trivial MRU/random/LFU policies), not new research:

- **Families**: metacdn, twemcache (the two regimes the prior audits already found most discriminative offline — metacdn/twemcache at capacity 32, horizon 16).
- **Capacity**: 32 (the regime where the offline target is least tie-dominated).
- **Trace usage**: replay the full 50,000-request processed trace per family (`data/processed/{metacdn,twemcache}/trace.jsonl`); report metrics separately on the request range corresponding to the release's `test` split window as the closest available approximation to "held-out," explicitly caveated per Phase 6 (it is a held-out *time-chunk of the same trace*, not an unseen trace).
- **Policies**: LRU (ready), SIEVE (ready), MRU (trivial, ~20 lines, mirrors `lru.py`), uniform random (trivial, ~20 lines), `evict_value_v1` if its trained checkpoint (`models/evict_value_v1_hist_gb.pkl`) still loads correctly against the current feature code (not verified in this audit — a 5-minute check before the pilot). Do **not** include LFU/S3-FIFO/3L-Cache/CACHEUS/HALP in the *minimal* pilot — they either need net-new implementation (LFU, S3-FIFO) or a branch merge plus adapter validation (3L-Cache, CACHEUS, HALP) that is better scheduled for the production run once the minimal pilot has already answered the reviewers' core question.
- **linear_score**: include only as a stretch goal behind a thin adapter (Phase 4) — expect it to track LRU closely, which is itself a useful (if unflattering) result to report.
- **Metrics**: total requests, hits, misses, miss ratio, eviction count, relative miss-ratio change vs. LRU. For random: fixed seeds (e.g. 5 seeds) and report mean ± spread.
- **Runtime**: trivially fast — replaying 50,000 requests through a Python `OrderedDict`-based LRU/SIEVE loop is sub-second per (trace, policy) run; even a slow pure-Python `evict_value_v1` inference path (HistGradientBoostingRegressor scoring per decision) would be seconds, not minutes, at this scale.

## Phase 8 — Offline vs. closed-loop validity test

The scientific question: do policies that score better on the counterfactual benchmark also perform better in true replay? Defensible comparisons, and their limits:

- **Policy-level ranking correlation**: compute each policy's closed-loop miss ratio (Phase 7) and separately compute an offline proxy score for the same policy family where one exists (e.g., LRU's offline mean regret ≈ 0.003057, MRU's ≈ 0.065965, random's ≈ 0.008826, already computed in the prior discriminativeness audit). Spearman-correlate policy rank under offline mean regret vs. closed-loop miss ratio, per family/capacity cell. **This is valid** only for the small set of policies (LRU, MRU, random) that exist both as an offline "counterfactual choice" and as a closed-loop policy — it cannot be extended to SIEVE/S3-FIFO/CACHEUS/etc. without first generating offline counterfactual labels *for those policies' choices*, which the current release does not contain.
- **Offline optimal-choice rate vs. closed-loop miss ratio**: same caveat — only meaningful for policies whose victim choice coincides with a candidate actually present in the offline decision's candidate set (LRU does, by construction; MRU and random can be scored against the same candidate set; SIEVE/S3-FIFO/CACHEUS do not necessarily choose among the same candidate set at all, since their internal state — visited bits, FIFO queues, LFU counters — is not represented in the released decision snapshots).
- **Family/capacity-specific correlations**: worth computing, but sample size is a real constraint — only 5 families × 4 capacities = 20 cells, several of which (all of wiki2018) are already known to be fully non-discriminative offline, so those cells will trivially show zero offline variance to correlate against.

**What this comparison can support**: whether the offline counterfactual target is *directionally* informative about closed-loop quality for the policies it was constructed around (LRU/MRU/random). **What it cannot support**: a claim that the offline benchmark validates or predicts closed-loop performance for policies (SIEVE, S3-FIFO, 3L-Cache, CACHEUS, HALP, evict_value_v1) whose eviction logic depends on state never captured in the offline decision snapshots. The offline dataset's candidate rows were generated under one specific state-distribution (a particular LRU-continuation trajectory); a different policy visits a different sequence of cache states, so individual offline decisions do not map one-to-one onto the states any other policy actually visits. This is exactly the reviewers' criticism, and closed-loop replay is the direct answer to it — the offline-vs-closed-loop correlation is a secondary, supporting analysis, not a substitute.

## Phase 9 — Continuation-policy sensitivity vs. closed-loop replay

These are two different experiments and answer different questions:

- **(A) Closed-loop evaluation of policies** — replay a full trace, let each policy's own choices determine its own future cache states. Answers: "how good is policy P, evaluated honestly, on this trace?" This is what Phases 2–8 describe.
- **(B) Continuation-policy sensitivity of the offline counterfactual labels** — keep the existing forced-eviction-then-continue design, but regenerate `y_loss`/`y_value` using MRU or LFU (instead of LRU) as the *continuation* policy after the forced eviction, and see how much the resulting labels/rankings change. Answers: "how much does the benchmark's offline target itself depend on an arbitrary modeling choice (LRU continuation)?" This does not evaluate any policy in true closed loop; it is a robustness/sensitivity check on the existing offline construction.

**A does not make B unnecessary**, but A is strictly higher-value for answering the reviewers directly, since the reviewers' stated objection is about closed-loop validity, not about continuation-policy sensitivity per se. **Recommendation: B remains worth doing eventually** (it is comparatively cheap — it reuses `evict_value_dataset_v1.py`'s existing `_simulate_lru_misses`-style rollout with the continuation policy swapped, requiring re-scanning the 277M candidate-row-equivalent generation pipeline, i.e. Wulver-scale, not free) but is **not a prerequisite for, or a substitute for, A**, and should be sequenced after A given the current review cycle's priorities.

## Phase 10 — Compute cost

Historical evidence from this project's own Wulver logs (`internal/wulver_job_logs/`, `hpc/wulver/sigmod2027/README.md`, `reports/.../best_candidate_reconciliation_report.md`) gives real numbers for the *offline* candidate-row-scale jobs, for contrast:

- Candidate-label stats over 277,995,072 rows: budgeted 16 CPU / 64G / 4h.
- Value-regression fit over the same rows: budgeted 24 CPU / 96G / 8h.
- Best-candidate full evaluation: **exceeded 8h**, required a checkpoint/resume, total wall clock >8h (up to the 24h resubmission ceiling) on a 24 CPU / 96G node.
- Feature-pairwise baseline (only the 1M-row pairwise sample, partition-pruned): 7m09s, 2.8GB RAM — this is the closest existing analogue in scale to what closed-loop replay needs.

**Closed-loop replay operates over raw request traces (50,000 requests × 5 families = 250,000 total events), not the 277M-row candidate table** — a completely different, dramatically smaller compute regime:

- **Pilot** (2 families × 1 capacity × ~4-5 policies × a few random seeds): on the order of 10-20 (trace, policy) replay runs, each processing 50,000 sequential requests. In pure Python with `OrderedDict`/heap-based policies this is well under a second per run; even `evict_value_v1`'s per-decision model inference adds at most low seconds per run. **Total pilot wall clock: well under 5 minutes on a laptop.**
- **Full production** (5 families × 4 capacities × ~8-9 policies × a few seeds for stochastic ones ≈ 150-200 runs of 50,000 requests each): still on the order of minutes to low tens of minutes total, not hours — several orders of magnitude cheaper than any of the existing offline Wulver jobs above.

**Classification: LOCAL_WORKSTATION_SUFFICIENT** for both the pilot and the full production closed-loop experiment, contingent on `evict_value_v1`'s checkpoint loading cleanly and on 3L-Cache/CACHEUS/HALP's per-request inference cost not being pathological (CACHEUS/HALP involve small per-request model updates; nothing in the fork's reading suggested anything beyond seconds-per-50k-trace territory). Merging the three unmerged worktree branches and validating their adapters is an engineering task, not a compute-cost problem. This is a stark contrast with H=32/64 label generation (Phase 12), which requires re-deriving values from the full 277M-row candidate structure at Wulver scale.

## Phase 11 — Full production design

If the pilot succeeds (policies rank sensibly, no crashes, `evict_value_v1` loads):

- **Families**: all 5. wiki2018 is fully non-discriminative in the *offline* target, but that says nothing about whether policies actually differ in true closed-loop replay on it (a purely-recency-driven access pattern could still separate LRU from MRU from random in real replay even though the offline forced-eviction-then-LRU-continuation label collapses to ties). **Recommend including wiki2018 as an explicit negative-control regime**: report it, and if closed-loop policies genuinely also don't separate on it, that is itself a useful, publishable confirmation that the offline non-discriminativeness reflects a real property of the workload rather than an artifact of the label construction. Given the low marginal compute cost (Phase 10), there is no efficiency reason to exclude it.
- **Capacities**: all 4 (32/64/128/256) — cheap to include given the compute picture.
- **Split usage**: report on both (a) the release's own `test` time-chunk (for direct comparability with existing offline numbers, with the Phase 6 caveat stated explicitly every time) and (b) a `source_family`-mode held-out-family replay for at least the learned policies (`evict_value_v1`, `linear_score` adapter), since that is the only genuinely unseen-data holdout available in this project's code.
- **Policies**: LRU, MRU, random, SIEVE (all cheap/ready) plus `evict_value_v1`; add LFU and a genuine standalone random-eviction policy (small implementation effort); merge and validate 3L-Cache, CACHEUS, HALP from their worktrees (moderate effort — CACHEUS's capacity=1 crash and its global RNG side-effect need explicit handling in a multi-run harness); include the `linear_score` adapter as a secondary, expected-to-underperform reference given Phase 4's finding.

## Phase 12 — Priority decision

1. **A. Closed-loop replay** — **CRITICAL**. Directly answers the reviewers' central, explicitly-stated objection; simulator, traces, and two ready policies already exist; compute cost is trivial (Phase 10); no data regeneration or manuscript risk. Nothing in the code or data makes this infeasible — if anything, feasibility is stronger than the task's own framing assumed (a trace-level held-out split does not exist, but a time-chunk holdout and a `source_family`-mode holdout both do).
2. **C. Continuation-policy sensitivity labels (B in Phase 9's lettering)** — **MEDIUM**. A real, complementary robustness check on the existing offline construction; reuses existing rollout code (`_simulate_lru_misses`-style) with the continuation policy swapped, but requires Wulver-scale regeneration over the full candidate structure (not free), and does not by itself answer the reviewers' closed-loop objection.
3. **B. H=32/64 horizon extension** — **LOW**, for this review cycle. Extends an axis of the *offline* benchmark that is not what either reviewer asked about, requires full-scale regeneration (Wulver, hours), and does not touch the closed-loop question at all. Consistent with the task's framing that this is now lower priority than closed-loop work.

## Optional-artifact note

This directory (`analysis/closed_loop_feasibility_20260913/`) contains only this report, its README, and a lightweight JSON inventory — no generated simulation data, per instructions.

---

LAFC_EVICT_CLOSED_LOOP_FEASIBILITY_REPORT

REPOSITORIES_INSPECTED:
- SoroushVahidi/lafc-evict-dataset — /home/soroush/projects/lafc-evict-dataset/repo, branch analysis/sigmod-target-discriminativeness-20260913, commit 76d562f90cc2bdd5bcb89b6e4eb44e305f430615
- SoroushVahidi/Augmented-caching — /home/soroush/projects/augmented-caching/repo, branch chore/repository-polish, commit ceb36705b59d0d16db55d0fc0bfb63a5c7a2a6a1
- Augmented-caching unmerged worktrees: worktrees/3l-cache (feat/3l-cache-baseline @ e351e70), worktrees/cacheus (feat/cacheus-baseline @ 5a54b33), worktrees/halp (feat/halp-baseline @ b32cb68)

SIMULATOR_EXISTS:
YES

PRIMARY_SIMULATOR:
SIMULATOR_PATH: /home/soroush/projects/augmented-caching/repo/src/lafc/simulator/ (cache_state.py, request_trace.py) + src/lafc/policies/base.py + src/lafc/runner/run_policy.py
SIMULATOR_CAPABILITIES:
- Replays a full request trace sequentially (JSON or CSV input, request_trace.py)
- Maintains real cache occupancy state across requests (CacheState.add/evict)
- Calls the pluggable policy's on_request() exactly on a full-cache miss, before insertion
- Chosen victim determines all subsequent state (genuinely closed-loop, not scored independently)
- Records hits/misses/evictions/per-step events into a SimulationResult
- Item-count capacity only (32/64/128/256 objects matches the paper's existing capacity semantics; no byte-size modeling)
- Deterministic for fixed trace/policy/seed; stochastic policies take an explicit --seed
- Tests exist and pass (test_simulator.py, test_runner.py, test_policies.py, test_sieve.py)
- Already used in a published-style experiment: run_policy_comparison_wulver_v1.py runs evict_value_v1 through this same loop

POLICY_STATUS:
- LRU: IMPLEMENTED_AND_READY (src/lafc/policies/lru.py)
- MRU: NOT_IMPLEMENTED (trivial to add)
- random: NOT_IMPLEMENTED as standalone (trivial to add)
- LFU: NOT_IMPLEMENTED standalone (CR-LFU exists only bundled inside third-party CACHEUS)
- SIEVE: IMPLEMENTED_AND_READY (src/lafc/policies/sieve.py)
- S3-FIFO: NOT_IMPLEMENTED
- 3L-Cache: IMPLEMENTED_BUT_NEEDS_ADAPTER (complete + tested, worktrees/3l-cache, unmerged)
- CACHEUS: IMPLEMENTED_BUT_NEEDS_ADAPTER (official-source wrapper, complete + tested, worktrees/cacheus, unmerged; capacity=1 crash documented)
- HALP: IMPLEMENTED_BUT_NEEDS_ADAPTER (complete + tested incl. no-leakage test, worktrees/halp, unmerged)
- linear_score (manuscript): IMPLEMENTED_BUT_NEEDS_ADAPTER (offline-only today; would need a thin BasePolicy wrapper)
- other learned policy (evict_value_v1): IMPLEMENTED_AND_READY (src/lafc/policies/evict_value_v1.py + models/evict_value_v1_hist_gb.pkl; genuinely closed-loop already)

LINEAR_SCORE_TRAINING_PATH: lafc-evict-dataset/scripts/sigmod2027/run_value_regression_baseline.py
LINEAR_SCORE_MODEL_ARTIFACT: lafc-evict-dataset/paper/sigmod2027/results/baselines/value_regression/linear_regression_y_loss.json
LINEAR_SCORE_FEATURES:
- 26 columns from src/lafc_evict_dataset/schema.py FEATURE_COLUMNS; verified directly from the fitted coefficient JSON that ~14 of the 26 are degenerate (exact zero coefficient, or a spurious shared/intercept-absorbing constant from perfectly-collinear constant columns)
- The only features with genuine, non-degenerate fitted signal: candidate_lru_score, candidate_age_norm, score_gap_to_lru_victim, candidate_recency_rank, candidate_is_lru_victim (== is_predictor_victim), recent_candidate_request_rate, recent_candidate_hit_rate

LINEAR_SCORE_DEPLOYABLE_CLOSED_LOOP:
PARTIALLY — technically deployable after a thin adapter (its real features are all online-available), but its real information content is close to a noisy reparameterization of LRU (its LRU-derived features dominate; plain LRU already beats it on the manuscript's own pairwise numbers, 0.9596 vs 0.9530). Augmented-caching's evict_value_v1 (HistGradientBoostingRegressor) is the more scientifically meaningful "learned baseline" for a closed-loop comparison.

ONLINE_FEATURE_AUDIT:
- candidate_recency_rank, candidate_age_norm, candidate_lru_score, candidate_is_lru_victim, score_gap_to_lru_victim: ONLINE_AVAILABLE (recency-order/cache-state derived)
- recent_candidate_request_rate, recent_candidate_hit_rate: ONLINE_AVAILABLE (backward-looking history window, per dataset_card/SCHEMA.md)
- candidate_predictor_score + 13 constant bucket/confidence/gap fields: UNKNOWN/MOOT (never vary in this release; contribute ~0 to the fitted model regardless)
- y_loss / y_value (target): COUNTERFACTUAL_ONLY, confirmed excluded from the feature list — no leakage into linear_score's inputs

PREDICTOR_FIELD_CLASSIFICATION:
UNFINISHED_FEATURE (bug-adjacent) — not confirmed with the pipeline owner

PREDICTOR_RELATION_TO_LINEAR_SCORE:
Independent. candidate_predictor_score is one of linear_score's 26 nominal input features, but because it (and its correlated bucket/confidence siblings) is constant across the entire release, it is functionally inert in the fitted model (folded into a shared, intercept-like coefficient, contributing no real signal). linear_score is not an alias of the predictor field, and the predictor bug does not invalidate linear_score's reported R² (already near zero) — but it does mean linear_score has effectively fewer real input dimensions than its 26-feature listing implies. Both the predictor field and linear_score are also distinct from Augmented-caching's evict_value_v1 (a real, separately-trained HistGradientBoostingRegressor); the released predictor field most likely reflects a placeholder/fallback scorer used in the specific historical data-generation run, not evict_value_v1's own feature-extraction code (which was not found to be broken).

PREDICTOR_LRU_ALIAS_INVALIDATES_EXISTING_RESULT:
NO — no manuscript claim asserts or depends on the predictor being independent of LRU; the one headline number affected (predictor_score_pairwise, 0.9489/0.2023) is silently explained by, not contradicted by, the constant-field finding. It is a disclosure gap, not a false claim.

HELD_OUT_REPLAY_POSSIBLE:
YES, with an important caveat: there is no held-out TRACE (only 5 traces total, one per family, so trace-level holdout is impossible in this project's current data). "Held out" is available in two weaker/different forms: (a) the release's existing test split, which is a carved-out interior time-chunk of the same continuously-replayed trace (not a trailing forward holdout, and not statistically independent of train, since train's time range surrounds it); (b) Augmented-caching's --split-mode source_family, a genuine held-out-family split, available in the upstream builder but not what produced this release's actual split column.

TRAIN_TEST_SPLIT:
Released data: per-trace time-chunk split (train/val/test windows carved out of one continuous 50k-request trace per family; verified directly by querying decision_t ranges per trace_name/split). Augmented-caching code: hash(trace, capacity) split by default, or --split-mode source_family for a held-out-family split.

DATA_LEAKAGE_FINDINGS:
- No raw future-value leakage into any feature used by linear_score or evict_value_v1's feature set (y_loss/y_value confirmed target-only, never a feature)
- HALP's online training uses only already-elapsed actual_next comparisons, with its own passing no-leakage test
- Train and test are not statistically independent under the release's own split (time-chunk carved out of the same trace, surrounded by train on both sides) — a real, previously-undocumented finding; this weakens (without invalidating) any "held-out" claim made using the release's existing split column
- The three-way predictor/linear_score/evict_value_v1 confusion itself is a provenance risk if not disclosed — a reader could mistake the constant predictor field for evict_value_v1's actual output

MINIMAL_PILOT:
Replay the full 50,000-request processed traces for metacdn and twemcache at capacity=32 through the existing Augmented-caching simulator, comparing LRU, SIEVE, MRU (new, trivial), uniform random (new, trivial, seeded), and evict_value_v1 if its checkpoint loads; report metrics on the full trace and separately on the release's test-window request range, with the time-chunk-not-trace-holdout caveat stated explicitly.

PILOT_POLICIES:
- LRU (ready)
- SIEVE (ready)
- MRU (needs ~20 lines, mirrors lru.py)
- uniform random (needs ~20 lines, seeded)
- evict_value_v1 (ready, pending a 5-minute checkpoint-load sanity check)

PILOT_RUN_COUNT: on the order of 10-20 (trace × policy × seed) replay runs of 50,000 requests each
PILOT_ESTIMATED_RUNTIME: well under 5 minutes total
PILOT_COMPUTE_LOCATION: LOCAL_WORKSTATION_SUFFICIENT

OFFLINE_VS_CLOSED_LOOP_TEST:
Correlate each policy's closed-loop miss ratio against its offline mean-regret/optimal-selection-rate proxy, but only for the policies that exist in both worlds today (LRU, MRU, random — all three already have offline regret numbers from the prior discriminativeness audit). This validates whether the offline label is directionally informative for the policies it was built around; it cannot, by itself, validate or predict closed-loop performance for SIEVE/S3-FIFO/CACHEUS/HALP/evict_value_v1, whose state (visited bits, FIFO queues, LFU counters, model internals) is not represented in the offline decision snapshots at all — closed-loop replay is the direct test for those, not a substitute analysis.

FULL_PRODUCTION_DESIGN:
All 5 families (including wiki2018 as a deliberate negative control, given near-zero marginal compute cost), all 4 capacities, LRU/MRU/random/SIEVE/evict_value_v1 immediately, LFU and standalone-random added with small effort, 3L-Cache/CACHEUS/HALP merged from their worktrees with adapter validation, linear_score included as a secondary reference expected to track LRU closely. Report both the release's existing test-window metrics (for comparability) and a source_family-mode held-out-family replay for the learned policies (the only genuine unseen-data holdout available).

FULL_PRODUCTION_RUN_COUNT: roughly 150-200 (family × capacity × policy × seed) runs of 50,000 requests each
FULL_PRODUCTION_ESTIMATED_COMPUTE: LOCAL_WORKSTATION_SUFFICIENT (minutes to low tens of minutes total; contrast with the >8-hour Wulver-scale offline candidate-row jobs this project has already run)

ALTERNATIVE_CONTINUATION_LABELS_STILL_NEEDED:
MAYBE

WHY:
Closed-loop replay (A) directly answers the reviewers' stated objection about deployed-policy evaluation and is cheap and ready now. Continuation-policy sensitivity (an MRU/LFU-continuation relabeling, "B" in Phase 9) answers a different, complementary question — how much the existing offline target itself depends on the LRU-continuation modeling choice — and remains scientifically worth doing, but requires Wulver-scale regeneration (not free) and does not resolve the reviewers' core criticism by itself. It should follow, not precede or substitute for, closed-loop replay.

SCIENTIFIC_PRIORITY:
1. Closed-loop replay (A) — CRITICAL
2. Continuation-policy sensitivity relabeling (C) — MEDIUM
3. H=32/64 horizon extension (B) — LOW for this review cycle

CLOSED_LOOP_SCIENTIFIC_VALUE:
CRITICAL

GO_FOR_CLOSED_LOOP_PILOT:
YES

BLOCKERS_BEFORE_PILOT:
- None structural. Two small implementation tasks first: add MRU and standalone uniform-random policy classes (~20 lines each, mirroring lru.py); verify models/evict_value_v1_hist_gb.pkl still loads against current feature-extraction code (5-minute check).
- Editorial-only: confirm with the pipeline owner whether evict_value_v1_wulver_heavy_r1's predictor placeholder was intentional or a bug, and disclose the linear_score degenerate-feature finding (Phase 4/5) in the manuscript before or alongside any closed-loop results, so reviewers don't need to independently discover it.
- Package/environment: run `pip install -e .` (or set PYTHONPATH=src) in whatever environment executes the pilot — the "ModuleNotFoundError" seen in ambient shells during this audit was an environment setup gap, not a code defect.

REPOSITORY_MODIFIED:
YES — this audit's own artifacts only (analysis/closed_loop_feasibility_20260913/ in lafc-evict-dataset, committed in an isolated worktree branch; see NEXT_SINGLE_ACTION). No other files in either repository were modified. No generated/canonical data, manuscript, or public artifact was touched.

EXPERIMENTS_LAUNCHED:
NO

MANUSCRIPT_EDITED:
NO

NEXT_SINGLE_ACTION:
Merge or cherry-pick this audit's commit (branch worktree-closed-loop-feasibility-20260913 in the isolated worktree at .claude/worktrees/closed-loop-feasibility-20260913, based on master@fbbeedb since analysis/sigmod-target-discriminativeness-20260913 was already checked out elsewhere and could not be safely branched from directly) onto analysis/sigmod-target-discriminativeness-20260913, then implement the two trivial MRU/uniform-random policy classes and run the minimal pilot (metacdn + twemcache, capacity 32, LRU/SIEVE/MRU/random/evict_value_v1) locally before deciding on the full production design.
