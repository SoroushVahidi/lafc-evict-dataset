# LAFC-Evict Closed-Loop Production Evaluation Design

Date: 2026-09-13

Scope: design, feasibility, and validity audit only. No production policy run, pilot rerun, model retraining, simulator edit, manuscript edit, merge, push, or publication-system action was performed.

Pilot source: frozen commit `983d7d0204645660e7b683ed30298677c2b42ccf`, `analysis/closed_loop_pilot_20260913/`.

## Objective

Design the smallest scientifically defensible production closed-loop evaluation that can support or falsify this restrained claim:

> LAFC-Evict provides candidate-level counterfactual supervision whose offline signal can be useful for training and diagnosing cache-eviction models, while closed-loop replay remains necessary to evaluate deployed policy performance.

The design is not confirmation-only. It must expose negative cases, split caveats, and learned-policy failures if they occur.

## Key Pilot Evidence

The frozen pilot evaluated MetaCDN and Twemcache at capacity 32 with LRU, MRU, random, SIEVE, and evict_value_v1 where leakage-safe.

Main pilot finding: for LRU, random, and MRU, the offline LAFC-Evict H=16 ordering agreed with the closed-loop miss ordering in both examined families:

- MetaCDN: offline LRU > random > MRU; closed-loop LRU > random > MRU.
- Twemcache: offline LRU > random > MRU; closed-loop LRU > random > MRU.

Constraints exposed by the pilot:

- MetaCDN has no test chunks at capacity 32. Its pilot result is validation-window evidence, not independent test-window evidence.
- evict_value_v1 is expensive: one Twemcache 50k replay at capacity 32 took 2885.189 seconds, about 48 minutes.
- Simple policies are cheap: roughly 0.06-0.12 seconds per 50k replay in the pilot.
- evict_value_v1 beat random and SIEVE on Twemcache but lost to LRU by 162 misses / 2.63%.

## Family Inventory

Split facts use the encoded trace-chunk split with chunk size 4096 and are cross-checked against the released decision view. All processed traces are 50,000 requests and are JSONL with `item_id`; the existing simulator path can replay them through the same request-list construction used in the pilot. Size/object fields vary by source and are not used for occupancy in this unit-capacity evaluation.

| Family | Trace | Train chunks | Val chunks | Test chunks | Test available | Closed-loop test valid | Simulator supported | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cloudphysics | `cloudphysics_alibaba_block_head_50k` | 0,1,2,6,7,8,9,10,11,12 | 3 | 4,5 | YES | YES | YES | Test windows `[16384,24575]`; test is temporal windows within one trace, not an unseen trace. |
| metacdn | `metacdn_cdn_202303_head_50k` | 1,2,3,4,5,8,11,12 | 0,6,7,9,10 | none | NO | NO for test; validation-only evidence possible | YES | No test chunks. Any learned-policy scoring on val is circular because validation participated in model selection. |
| metakv | `metakv_kvcache_202206_head_50k` | 1,2,4,5,7,9,10,11,12 | 3,6,8 | 0 | YES | YES, but first-window test | YES | Test window `[0,4095]`; no prior unscored warmup before scoring, though the full trace still replays continuously. |
| twemcache | `twemcache_cluster26_sample100_50k` | 0,1,2,3,4,5,6,9,11,12 | 7 | 8,10 | YES | YES | YES | Test windows `[32768,36863]` and `[40960,45055]`; strongest pilot learned-policy cell. |
| wiki2018 | `wiki2018_pageviews_en_50k` | 0,1,2,3,4,5,7,8,9,10,12 | 11 | 6 | YES | YES | YES | Offline-degenerate control: all candidates tied in every capacity/horizon cell. |

Trace hashes:

| Family | Processed trace path | SHA256 |
| --- | --- | --- |
| cloudphysics | `/home/soroush/projects/augmented-caching/repo/data/processed/cloudphysics/trace.jsonl` | `fedb3d31ee3c1dd847d25f967392cdf0fdec1e9c1fbb6808772e281bc8d4fb57` |
| metacdn | `/home/soroush/projects/augmented-caching/repo/data/processed/metacdn/trace.jsonl` | `7301f02e1373cb7e06f1ed2c417a8ebe16581319354780f811c8d032391f4e73` |
| metakv | `/home/soroush/projects/augmented-caching/repo/data/processed/metakv/trace.jsonl` | `4c229e841d546cd57a2edb6e3ddc53461ff4dc03d366e9d24e4239a89db7e0de` |
| twemcache | `/home/soroush/projects/augmented-caching/repo/data/processed/twemcache/trace.jsonl` | `62df27062ce2595c843fd91e01d26c9783ff8f165f6b26e983696eda7ada0bb9` |
| wiki2018 | `/home/soroush/projects/augmented-caching/repo/data/processed/wiki2018/trace.jsonl` | `3813084bebfcf463ac22a685494b46aea45aded55d314411c9fbb058b5d67608` |

## evict_value_v1 Leakage Audit

Model: `/home/soroush/projects/augmented-caching/repo/models/evict_value_wulver_v1_best_heavy_r1.pkl`

SHA256: `0c9e8a48066f8bb80bfab31b023c9785ca5b955f408d50c18008dbcc314ea61b`

Identifier: `wulver_h4_random_forest`

Selection: validation mean regret across horizon/model candidates. Loading during pilot freeze emitted scikit-learn 1.9.0 vs 1.8.0 version warnings.

The model was trained on trace-chunk train rows from all seven Wulver families, including the five SIGMOD-scale families. This is not family-independent evaluation. It is temporal test-window evaluation within the same family/trace where test chunks exist.

| Family | Used in training? | Validation/model-selection chunks | Isolated test chunks | Classification | Learned-policy production action |
| --- | --- | --- | --- | --- | --- |
| cloudphysics | YES, train chunks 0,1,2,6,7,8,9,10,11,12 | chunk 3 | 4,5 | LEARNED_POLICY_SAFE_TEST | Safe in principle; consider one new learned cell at cap32 after Tier 1. |
| metacdn | YES, train chunks 1,2,3,4,5,8,11,12 | chunks 0,6,7,9,10 | none | BLOCKED_LEAKAGE_RISK | Do not run evict_value_v1 for production claims. Report baseline-only validation-window evidence separately if needed. |
| metakv | YES, train chunks 1,2,4,5,7,9,10,11,12 | chunks 3,6,8 | 0 | LEARNED_POLICY_SAFE_TEST | Safe in principle, but test starts at request 0 and offline signal is weak; not a first learned cell. |
| twemcache | YES, train chunks 0,1,2,3,4,5,6,9,11,12 | chunk 7 | 8,10 | LEARNED_POLICY_SAFE_TEST | Use frozen pilot cap32 result as the first learned-policy cell; rerun only if a unified production artifact is explicitly required. |
| wiki2018 | YES, train chunks 0,1,2,3,4,5,7,8,9,10,12 | chunk 11 | 6 | LEARNED_POLICY_SAFE_TEST | Safe but low value for learned-policy scoring; include as Tier 1 negative control instead. |

## Policy Readiness

| Policy | Classification | Basis | Production recommendation |
| --- | --- | --- | --- |
| LRU | READY_CURRENT_BRANCH | `src/lafc/policies/lru.py`, existing simulator registry/tests, pilot validated. | Include Tier 1. |
| MRU | NEEDS_ADAPTER | Not an Augmented-caching current-branch policy; pilot-local implementation is tiny and validated. | Include Tier 1 by carrying pilot-local adapter in the production analysis script, not by editing simulator code. |
| random | NEEDS_ADAPTER | Not an Augmented-caching current-branch standalone policy; pilot-local seeded implementation is validated. | Include Tier 1 with seeds 0..19. |
| SIEVE | READY_CURRENT_BRANCH | `src/lafc/policies/sieve.py`, tested, pilot validated. | Include Tier 1. |
| evict_value_v1 | READY_CURRENT_BRANCH_WITH_GATES | Implemented and artifact-backed, but expensive and has model-version warning. | Tier 2 only, leakage-safe cells only, deterministic one run per cell. |
| CACHEUS | IMPLEMENTED_OTHER_BRANCH / NEEDS_ADAPTER | Existing `feat/cacheus-baseline` worktree, not current branch. | Exclude from primary production matrix. |
| LeCaR | NOT_READY | No trustworthy current implementation found in inspected inventory. | Exclude. |
| 3L-Cache | IMPLEMENTED_OTHER_BRANCH / NEEDS_ADAPTER | Existing `feat/3l-cache-baseline` worktree, not current branch. | Exclude from primary production matrix. |
| FIFO-Reinsertion | READY_CURRENT_BRANCH | Current branch has `fifo_reinsertion.py`; prior canonical outputs exist. | Optional cheap extension only after Tier 1, not required for the primary matrix. |
| HALP | IMPLEMENTED_OTHER_BRANCH / NEEDS_ADAPTER | Existing `feat/halp-baseline` worktree, not current branch. | Exclude from primary production matrix. |
| LRB | READY_CURRENT_BRANCH_WITH_OPTIONAL_DEPENDENCY | Current branch has `lrb.py`, but optional LightGBM dependency and tuning concerns apply. | Exclude from primary production matrix. |

## Capacity Design

Candidate scopes:

- A. cap32 only: strongest offline signal and cheapest to interpret, but cannot address capacity sensitivity.
- B. cap32 + cap128: smallest useful capacity-sensitivity design. It contrasts the most discriminative regime with a larger cache where offline random regret and tie structure weaken.
- C. cap32 + cap64 + cap128 + cap256: complete but unnecessary for the first production answer, especially if learned-policy cells are included.
- D. cap32 + cap64: lower-risk incremental design, but less informative about whether agreement persists at a substantially larger capacity.

Recommendation: B, capacities 32 and 128.

Rationale: cap32 is essential because prior audits show the strongest signal there. cap128 gives a meaningful larger-cache contrast while keeping the cheap tier very small and avoiding a mechanical all-capacity sweep. The offline matrix shows reduced but nonzero signal at cap128 for MetaCDN and Twemcache; wiki2018 remains fully degenerate at all capacities.

## Offline Horizon Relationship

Closed-loop replay has no finite LAFC-Evict horizon. Production reporting should treat horizons as offline label variants compared against one observed closed-loop ranking per family/capacity.

Recommendation:

- Use H=16 as the primary offline comparison because the pilot used it and the audit shows it has the strongest existing discriminativeness.
- Include H=4, H=8, and H=16 as secondary comparisons for the Tier 1 matrix.
- For each family/capacity, compare offline LRU/random/MRU ordering and regret gaps at each H against the closed-loop LRU/random/MRU ordering and miss gaps.
- Across the small 10-cell Tier 1 matrix, report descriptive alignment only: rank agreement counts, gap-direction checks, and scatter plots/tables of offline regret gap versus closed-loop miss gap. Avoid p-value claims.

This directly addresses horizon limitations by asking whether H=16 is actually the best aligned existing target. It does not test alternative continuation policies.

## Random-Seed Design

Retain 20 random seeds, 0..19.

Pilot precision:

- MetaCDN random misses: std 27.53, standard error 6.16, approximate 95% CI half-width 12.1 misses. The LRU-vs-random gap was 638.15 misses.
- Twemcache random misses: std 20.26, standard error 4.53, approximate 95% CI half-width 8.9 misses. The LRU-vs-random gap was 257.90 misses.

Increasing to 50 or 100 seeds would be cheap but not scientifically necessary for the production question. The observed uncertainty is already much smaller than the policy gaps of interest.

## Two-Tier Production Design

Tier 1: broad cheap closed-loop baseline evaluation.

- Families: cloudphysics, metacdn, metakv, twemcache, wiki2018.
- Capacities: 32, 128.
- Policies: LRU, MRU, random, SIEVE.
- Random seeds: 0..19.
- Purpose: test whether offline LAFC-Evict rankings/regret structure correspond to actual closed-loop policy separation, including a negative/control family.

Tier 2: narrow learned-policy demonstration.

- Model: evict_value_v1 `wulver_h4_random_forest`, SHA256 above.
- Cells: reuse frozen Twemcache cap32 result as the first learned-policy evidence cell; add at most cloudphysics cap32 as one new learned-policy production cell after Tier 1 validates trace/scoring machinery.
- Exclusions: no MetaCDN learned-policy run for production claims; no wiki2018 learned-policy run unless specifically needed after Tier 1; no all-family/all-capacity learned sweep.
- Purpose: demonstrate an offline-model-to-deployed-policy workflow without spending days on redundant or weak cells.

This two-tier design is scientifically preferable because it separates the core dataset-usefulness question from the expensive learned-policy demonstration.

## wiki2018 Negative Control

Include wiki2018 in Tier 1.

Reason: prior offline audit says wiki2018 is completely non-discriminative under the current LAFC-Evict target: all candidates tied, random regret 0, and no unique winner in every capacity/horizon cell. A closed-loop production result on wiki2018 can falsify a too-simple interpretation. If LRU/random/MRU also remain indistinguishable, that supports the offline degeneracy diagnosis. If closed-loop policies separate substantially, that exposes a limitation of the finite-horizon candidate labels or their state distribution.

## Pre-Registered Questions

RQ-CL1: Do offline LAFC-Evict policy rankings among LRU, random, and MRU agree with closed-loop miss rankings?

Metrics: per family/capacity/H offline optimal rate and mean regret for LRU/random/MRU; per family/capacity closed-loop misses and miss ratios; exact rank-agreement count.

RQ-CL2: Does the strength of offline counterfactual separation predict the magnitude of closed-loop policy separation?

Metrics: offline mean-regret gap between MRU and LRU and between random and LRU; closed-loop miss gap and relative miss-ratio gap for the same policy pairs. Use descriptive comparisons across 10 cells only.

RQ-CL3: How does agreement vary by workload and cache capacity?

Metrics: rank agreement and gap magnitude by family at capacities 32 and 128; no pooled claim that hides family-specific behavior.

RQ-CL4: Which offline horizon H in {4,8,16} is most aligned with closed-loop behavior?

Metrics: for each H, count rank agreements and compare offline regret-gap ordering with closed-loop miss-gap ordering across Tier 1 cells.

RQ-CL5: Can a model trained using LAFC-Evict supervision produce a closed-loop policy competitive with classical baselines on leakage-safe temporal test windows?

Metrics: learned-policy misses, miss ratio, difference versus LRU, SIEVE, and random; runtime; leakage status. Evaluate only gated Tier 2 cells.

RQ-CL6: What happens in an offline-degenerate workload such as wiki2018?

Metrics: wiki2018 closed-loop LRU/random/MRU/SIEVE miss ratios at capacities 32 and 128; compare against all-tied fraction 1.0 and mean random regret 0.0 for H=4/8/16.

## Metrics

Closed-loop metrics:

- scored requests
- hits
- misses
- miss ratio
- evictions
- absolute miss difference versus LRU
- relative miss difference versus LRU
- runtime

Random aggregate metrics:

- mean
- standard deviation
- min
- max
- approximate confidence interval
- number of seeds

Offline comparison metrics:

- optimal-choice rate
- mean regret
- all-tied fraction
- mean optimal-set fraction
- max observed loss range
- relevant discriminativeness thresholds where already available

Cross-analysis:

- rank agreement counts
- descriptive Kendall/Spearman-style rank agreement only when the policy set is large enough to be meaningful
- offline regret gap versus closed-loop miss gap tables/scatter data
- no inferential correlation claims from tiny samples

## Continuation-Policy Limitation

This production closed-loop evaluation is not the same as a continuation-policy sensitivity experiment.

Closed-loop replay answers: how do deployed policies perform when each policy controls its own state trajectory?

Continuation-policy sensitivity answers: how much do LAFC-Evict labels change if the forced-eviction counterfactual continues with a policy other than LRU?

A separate continuation-policy-sensitivity experiment remains necessary if the reviewer concern is specifically about the fixed LRU continuation used to generate labels. The production closed-loop evaluation strengthens practical validation, but it does not replace that label-construction sensitivity check.

## Primary Production Matrix

Primary Tier 1 matrix:

- Families: cloudphysics, metacdn, metakv, twemcache, wiki2018.
- Capacities: 32, 128.
- Policies: LRU, MRU, random, SIEVE.
- Random seeds: 0..19.
- Offline horizons for comparison: 4, 8, 16.
- Scoring restriction: use test windows where nonempty; report MetaCDN as validation-window evidence only.

Tier 2 learned-policy matrix:

- Model: evict_value_v1 `wulver_h4_random_forest`, SHA256 `0c9e8a48066f8bb80bfab31b023c9785ca5b955f408d50c18008dbcc314ea61b`.
- Reuse frozen Twemcache cap32 pilot result.
- Add cloudphysics cap32 only after Tier 1 validation and explicit approval.
- Do not run MetaCDN learned-policy cells for production claims.
- Do not run all safe families/capacities by default.

Estimated run counts:

- Simple deterministic Tier 1 runs: 30 (5 families x 2 capacities x 3 deterministic policies: LRU, MRU, SIEVE).
- Random Tier 1 runs: 200 (5 families x 2 capacities x 20 seeds).
- Learned Tier 2 new runs: 1 recommended new run (cloudphysics cap32), plus 1 frozen pilot result reused for Twemcache cap32.

Estimated runtime:

- Simple Tier 1: less than 5 minutes locally including startup/IO overhead; raw replay time should be well under 1 minute.
- Learned Tier 2: at least 48 minutes per 50k replay at cap32 based on the Twemcache pilot; budget 1-2 hours for one new learned cell and validation.
- Total recommended new runtime: less than 5 minutes for Tier 1 plus 1-2 hours only if the single new learned cell is approved.

Local workstation feasibility: Tier 1 yes. Tier 2 partially: one learned cell is feasible; a full learned matrix is not attractive locally.

Wulver need: optional for Tier 1; recommended for any multi-cell learned-policy sweep.

## Expected Journal Value

Expected evidentiary value: HIGH if the production matrix is executed with the gates above.

The design directly tests whether LAFC-Evict's offline candidate-level signal is associated with closed-loop behavior for policies that can be scored both ways, includes a negative/control workload, and keeps learned-policy claims narrow and leakage-gated.

Falsification or weakening conditions:

- systematic offline/closed-loop rank disagreement for LRU/random/MRU
- no meaningful closed-loop policy separation
- offline-regret structure unrelated to closed-loop miss gaps
- wiki2018 showing large closed-loop separation despite offline all-tie labels, without a clear explanation
- learned-policy evaluation proving too slow or too provenance-uncertain to support even a narrow workflow demonstration
