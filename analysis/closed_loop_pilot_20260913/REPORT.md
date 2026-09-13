# LAFC-Evict Closed-Loop Pilot Report

## 1. Objective

This pilot tests whether offline candidate-level counterfactual signals correspond to meaningful closed-loop cache-policy differences. It is a narrow bridge between LAFC-Evict's reusable counterfactual supervision layer and true policy replay, not a production-scale evaluation.

## 2. Protocol

Families: MetaCDN and Twemcache.

Capacity: 32.

Policies: LRU, MRU, uniform random, SIEVE, and evict_value_v1 where leakage-safe.

Random seeds: 0..19.

Execution: each policy replays the full 50,000-request processed JSONL trace through the existing Augmented-caching simulator. The policy updates its own cache state after each request. This is genuine closed-loop execution and not a replay of the 277M candidate table.

Scoring: requests outside the scored windows still affect cache state but do not contribute to metrics. There is no separate leading warmup; scoring is window-restricted after full-trace state evolution.

MetaCDN scored validation windows `[0,4095]`, `[24576,32767]`, and `[36864,45055]`, for 20,480 scored requests. MetaCDN has no test chunks at capacity 32.

Twemcache scored temporally held-out test windows `[32768,36863]` and `[40960,45055]`, for 8,192 scored requests.

Learned-policy leakage gate: evict_value_v1 is blocked on MetaCDN because the available scored windows are validation chunks that participated in model selection. evict_value_v1 is evaluated on Twemcache test chunks 8 and 10.

## 3. Validity Checks

| Check | Status |
| --- | --- |
| hits + misses = scored_requests | PASS |
| same scored interval per policy within each family | PASS |
| capacity consistency | PASS |
| full 50k trace processing | PASS |
| NaN / invalid numeric output | none found |
| genuine raw-trace closed-loop replay | PASS |
| LRU deterministic duplicate check | PASS |
| random seed=0 duplicate check | PASS |

Result file hashes:

| File | SHA256 |
| --- | --- |
| `outputs/run_results.csv` | `81bd86d0550f6db2a03836bb899bc3c3026cc210f1f49be981dca317e2725428` |
| `outputs/summary.csv` | `fd5ab07aa565d3af5d198600f527513d8cbc8a95ffeab8a4e1db14219aa76279` |
| `outputs/sanity_checks.json` | `f1abe70549cdf88d5a7b29256c050bc80da06ffd6831a4ce558d65c69f957c11` |

## 4. Closed-Loop Results

Lower misses and lower miss ratio are better.

### MetaCDN

| Policy | Scored requests | Hits | Misses | Miss ratio | Evictions | Difference vs LRU | Runtime |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LRU | 20,480 | 8,619 | 11,861 | 0.579150 | 11,829 | 0 / 0.00% | 0.061 s |
| SIEVE | 20,480 | 8,523 | 11,957 | 0.583838 | 11,925 | +96 / +0.81% | 0.105 s |
| random, mean over 20 seeds | 20,480 | 7,980.85 | 12,499.15 | 0.610310 | 12,467.15 | +638.15 / +5.38% | 0.066 s mean |
| MRU | 20,480 | 3,001 | 17,479 | 0.853467 | 17,447 | +5,618 / +47.37% | 0.069 s |
| evict_value_v1 | - | - | - | - | - | BLOCKED_LEAKAGE_RISK | - |

Random MetaCDN spread: mean misses 12,499.15; std 27.53; min 12,446; max 12,559.

Closed-loop ranking: LRU < SIEVE < random < MRU.

### Twemcache

| Policy | Scored requests | Hits | Misses | Miss ratio | Evictions | Difference vs LRU | Runtime |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LRU | 8,192 | 2,039 | 6,153 | 0.751099 | 6,153 | 0 / 0.00% | 0.063 s |
| evict_value_v1 | 8,192 | 1,877 | 6,315 | 0.770874 | 6,315 | +162 / +2.63% | 2885.189 s |
| random, mean over 20 seeds | 8,192 | 1,781.10 | 6,410.90 | 0.782581 | 6,410.90 | +257.90 / +4.19% | 0.071 s mean |
| SIEVE | 8,192 | 1,518 | 6,674 | 0.814697 | 6,674 | +521 / +8.47% | 0.122 s |
| MRU | 8,192 | 370 | 7,822 | 0.954834 | 7,822 | +1,669 / +27.12% | 0.077 s |

Random Twemcache spread: mean misses 6,410.90; std 20.26; min 6,378; max 6,458.

Closed-loop ranking: LRU < evict_value_v1 < random < SIEVE < MRU.

## 5. Offline Vs Closed-Loop Comparison

Offline values use the existing cap=32, horizon=16 audit. No offline SIEVE or evict_value_v1 scores are manufactured; those are `NOT_COMPARABLE_FROM_EXISTING_OFFLINE_STATE`.

### MetaCDN

| Policy | Offline optimal rate | Offline mean regret | Closed-loop misses | Closed-loop miss ratio |
| --- | ---: | ---: | ---: | ---: |
| LRU | 0.985689 | 0.014447 | 11,861 | 0.579150 |
| random | 0.940448 | 0.060070 | 12,499.15 | 0.610310 |
| MRU | 0.684851 | 0.317943 | 17,479 | 0.853467 |

Offline ordering: LRU > random > MRU.

Closed-loop ordering among these same three policies: LRU > random > MRU.

### Twemcache

| Policy | Offline optimal rate | Offline mean regret | Closed-loop misses | Closed-loop miss ratio |
| --- | ---: | ---: | ---: | ---: |
| LRU | 0.962298 | 0.038654 | 6,153 | 0.751099 |
| random | 0.934734 | 0.066964 | 6,410.90 | 0.782581 |
| MRU | 0.874422 | 0.128141 | 7,822 | 0.954834 |

Offline ordering: LRU > random > MRU.

Closed-loop ordering among these same three policies: LRU > random > MRU.

The ordering among LRU, random, and MRU agrees in both examined families. This is directional evidence, not a universal correlation claim.

## 6. Learned Policy

Twemcache: evict_value_v1 beats random and SIEVE but loses to LRU by 162 misses, a 2.63% miss increase relative to LRU. Its miss ratio is 0.770874 versus LRU's 0.751099, random's 0.782581, SIEVE's 0.814697, and MRU's 0.954834.

MetaCDN: the learned-policy result is blocked because there is no leakage-safe independent test split. The available scored windows are validation windows, and the model was selected by validation mean regret.

Runtime caveat: evict_value_v1 is extremely slow relative to the simple policies in this pilot. The Twemcache learned-policy run took 2885.189 seconds, whereas simple policy runs were about 0.06-0.12 seconds per full 50k replay.

Reproducibility caveat: the evict_value_v1 artifact is `/home/soroush/projects/augmented-caching/repo/models/evict_value_wulver_v1_best_heavy_r1.pkl`, SHA256 `0c9e8a48066f8bb80bfab31b023c9785ca5b955f408d50c18008dbcc314ea61b`, model identifier `wulver_h4_random_forest`. Loading this artifact during freeze inspection emitted scikit-learn version warnings because the artifact was serialized with scikit-learn 1.9.0 and inspected with scikit-learn 1.8.0.

## 7. Scientific Interpretation

Closed-loop policy separation is meaningful. LRU, random, and MRU separate strongly in both families, and SIEVE plus evict_value_v1 occupy distinct positions in the closed-loop ranking where evaluated.

The offline counterfactual supervision contains information associated with eventual closed-loop outcomes for LRU, random, and MRU: the offline ordering among these three policies agrees with actual closed-loop miss ordering in both examined families.

This supports LAFC-Evict as an offline training and diagnostic layer. Closed-loop evaluation remains necessary because SIEVE and evict_value_v1 do not have directly comparable offline scores in the existing audit, and because different policies can visit different cache-state trajectories.

The pilot does not prove that offline metrics universally predict deployed policy performance. It does not demonstrate that a learned policy beats strong classical policies. It covers only two families and one capacity.

## 8. Reviewer Relevance

LAFC-Evict provides reusable candidate-level counterfactual supervision for training and diagnosing eviction models without repeatedly regenerating the same finite-horizon counterfactual rollouts. The closed-loop pilot shows that, at least for LRU, random, and MRU on the two evaluated families, the offline ordering agrees with actual closed-loop miss ordering.

LAFC-Evict is therefore best positioned as an offline supervision and diagnostic layer complementary to, not a replacement for, closed-loop policy evaluation.

## 9. Classification

PILOT_CLASSIFICATION: B = MIXED.

Reasons:

- technically valid completed evaluations
- meaningful policy separation
- strong three-policy offline/closed-loop ordering agreement
- MetaCDN lacks independent test windows
- learned policy blocked on MetaCDN
- learned policy does not beat LRU on Twemcache
- only two workloads and one capacity

## 10. Production Recommendation

A subsequent full production experiment is recommended, but was not started here.

The smallest defensible expansion is to keep the same discipline as this pilot: add families and capacities gradually, preserve exact split/leakage gates before learned-policy scoring, and keep random seeds fixed at 0..19. A conservative production scope would include all available selected families where trace and split provenance are clear, capacities 32, 64, 128, and 256, and policies LRU, MRU, random, SIEVE, and evict_value_v1 only for cells with leakage-safe scored intervals. Stronger baselines should be added only after adapter validation.
