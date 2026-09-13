# Production Matrix

No experiment was launched while creating this matrix.

## Tier 1: Cheap Baseline Replay

Purpose: broad closed-loop policy-separation and offline/closed-loop agreement test.

Families:

- cloudphysics
- metacdn
- metakv
- twemcache
- wiki2018

Capacities:

- 32
- 128

Policies:

- LRU
- MRU
- random
- SIEVE

Random seeds:

- 0..19

Offline horizons for comparison:

- H=4
- H=8
- H=16

Scoring:

| Family | Capacity | Scored split | Scored windows | Use in primary test-window claims? |
| --- | ---: | --- | --- | --- |
| cloudphysics | 32,128 | test | `[16384,20479]`, `[20480,24575]` | YES |
| metacdn | 32,128 | validation | `[0,4095]`, `[24576,32767]`, `[36864,45055]` | NO, label as validation-window evidence |
| metakv | 32,128 | test | `[0,4095]` | YES, with no-leading-warmup caveat |
| twemcache | 32,128 | test | `[32768,36863]`, `[40960,45055]` | YES |
| wiki2018 | 32,128 | test | `[24576,28671]` | YES, negative/control case |

Estimated Tier 1 runs:

- Deterministic simple runs: 30 = 5 families x 2 capacities x 3 policies (LRU, MRU, SIEVE).
- Random runs: 200 = 5 families x 2 capacities x 20 seeds.
- Total simple-policy replay runs: 230.

## Tier 2: Gated Learned-Policy Demonstration

Purpose: demonstrate the offline-supervision-to-deployed-policy workflow without turning the design into a days-long learned-policy sweep.

Model:

- evict_value_v1
- `/home/soroush/projects/augmented-caching/repo/models/evict_value_wulver_v1_best_heavy_r1.pkl`
- SHA256 `0c9e8a48066f8bb80bfab31b023c9785ca5b955f408d50c18008dbcc314ea61b`
- identifier `wulver_h4_random_forest`

Recommended learned cells:

| Family | Capacity | Action | Reason |
| --- | ---: | --- | --- |
| twemcache | 32 | Reuse frozen pilot result unless a unified production rerun is explicitly approved | Leakage-safe test windows already evaluated; learned policy beat random/SIEVE but lost to LRU. |
| cloudphysics | 32 | One new learned run after Tier 1 validation and explicit approval | Leakage-safe test windows; offline audit has rare high-regret tail at cap32/H16; adds one independent safe family. |

Blocked or deferred learned cells:

| Family | Capacity | Status | Reason |
| --- | ---: | --- | --- |
| metacdn | any | BLOCKED_LEAKAGE_RISK | No test chunks; validation participated in model selection. |
| metakv | 32,128 | deferred | Safe test chunks exist, but offline signal is weak and test is the first chunk, so it is lower value for an expensive run. |
| wiki2018 | 32,128 | deferred | Safe test chunks exist, but offline labels are fully degenerate; better used as Tier 1 negative control. |
| all safe families x both capacities | any | not recommended initially | Runtime would be disproportionate to the reviewer-facing value. |

Estimated new learned-policy runs:

- 1 recommended new run: cloudphysics cap32.
- 0 random seeds for evict_value_v1 because the policy is deterministic for a fixed model and trace.
