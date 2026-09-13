# Runtime Estimate

No benchmark was launched for this estimate.

## Pilot Measurements

Frozen pilot at capacity 32:

- Simple policies: roughly 0.06-0.12 seconds per 50,000-request replay.
- evict_value_v1 on Twemcache: 2885.189 seconds, about 48 minutes, for one deterministic 50,000-request replay.
- Random variance with 20 seeds was already small relative to policy gaps:
  - MetaCDN std 27.53 misses, SE 6.16, approximate 95% CI half-width 12.1 misses.
  - Twemcache std 20.26 misses, SE 4.53, approximate 95% CI half-width 8.9 misses.

## Recommended Matrix Runtime

Tier 1:

- 30 deterministic simple runs: 5 families x 2 capacities x LRU/MRU/SIEVE.
- 200 random runs: 5 families x 2 capacities x 20 seeds.
- Total: 230 simple-policy replay runs.
- Expected local runtime: less than 5 minutes including Python startup, file reads, CSV writes, and validation. Raw simulation time should be well under 1 minute.

Tier 2:

- Recommended new learned run count: 1, cloudphysics cap32, after Tier 1 validation and explicit approval.
- Reuse frozen Twemcache cap32 learned-policy result unless a unified rerun is explicitly required.
- Expected local runtime: at least 48 minutes for one cap32 learned run; budget 1-2 hours including validation and artifact loading overhead.

## Larger Learned-Policy Matrices

The safe-test learned-policy families are cloudphysics, metakv, twemcache, and wiki2018. MetaCDN is blocked for learned-policy production claims.

Sequential lower-bound estimates using the pilot's 48-minute cap32 runtime:

| Candidate learned matrix | Runs | Lower-bound sequential time | Practical note |
| --- | ---: | ---: | --- |
| 1 new safe family x cap32 | 1 | 0.8 h | Recommended after Tier 1. |
| 2 safe families x cap32 | 2 | 1.6 h | Locally feasible but not necessary initially. |
| 4 safe families x cap32 | 4 | 3.2 h | Possible but weak value for wiki2018/metakv. |
| 4 safe families x capacities 32,128 | 8 | 6.4 h lower bound | Likely longer because scoring cost grows with candidate count; use Wulver or avoid. |
| 4 safe families x all canonical capacities | 16 | 12.8 h lower bound | Not recommended for the reviewer-facing production pass. |

Capacity scaling caveat: evict_value_v1 scores every resident candidate at full-cache misses, so cap128 may be substantially slower than cap32 even if miss counts fall. Treat the table above as a lower bound, not a promise.

## Parallelization

Simple Tier 1 runs are safe to parallelize because policies are independent and cheap, but parallelization is not needed.

Learned-policy runs are deterministic and independent, but local parallelization is only partially attractive. The pilot behaved like a long CPU-bound run, and multiple concurrent learned-policy processes could contend for CPU/cache and make wall-clock behavior harder to interpret. Prefer one learned cell at a time locally, or use Wulver for any approved multi-cell learned sweep.
