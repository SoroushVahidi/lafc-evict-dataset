# Runtime and Storage Estimate

No benchmark was run to produce this estimate; it is derived analytically
from the matrix in `MATRIX.md` and from timing references already recorded
elsewhere in this project's frozen evidence.

## Primary sample (5,000 decisions)

- 5,000 decisions × 3 horizons × 2 continuations (MRU deterministic,
  random) × up to ~128 candidates × ≤16-step rollout ≈ 6×10^7 step
  operations (Section "Runtime feasibility check" in `MATRIX.md`).
- Each step operation is a plain dict/OrderedDict membership check and
  occasional pop/insert — the same order of cost as the Tier-1 harness's
  own per-request simulation loop, which the Tier-1 production run
  (230 full 50,000-request closed-loop replays) completed in **~24 seconds
  wall clock** end to end (frozen evidence:
  `analysis/closed_loop_tier1_evidence_20260914/.../provenance.json`,
  `start_time_utc`/`end_time_utc`). The continuation-sensitivity workload
  here is smaller in total per-step count (6×10^7 vs. Tier-1's
  ~230×50,000 ≈ 1.15×10^7 full-trace steps, so roughly 5x more raw step
  operations) but each step is cheaper (no feature computation, no ML
  scoring) — **estimated wall clock: low minutes on a single core**,
  comfortably under 10 minutes even with generous overhead, not hours.
- MRU adds no seed multiplier (deterministic). Random continuation at 10
  seeds (Section "Random continuation" in `DESIGN.md`) multiplies only the
  random-continuation share of the workload by 10x, not the whole matrix
  (MRU and the LRU-reproduction check stay at 1x) — still comfortably
  within a similar low-minutes budget given the small per-decision rollout
  size (≤16 steps), unlike Tier-1's full-50,000-request replays.

## Diagnostic oversample (500 decisions: 100 × 5 families)

An order of magnitude smaller than the primary sample; negligible
additional cost (well under a minute).

## Pilot (80 decisions: 20 × 4 cells)

Trivial — well under a second of computation; the pilot's main purpose is
correctness verification and obtaining a *real* measured wall-clock number
to replace this analytic estimate before committing to the full run.

## Storage

Per-decision output rows (candidate_page_id, capacity, horizon,
continuation policy, rollout_loss, rollout_regret, plus the small tie-aware
metric columns) are comparable in width to the existing
`evict_value_v2_rollout.py` candidate-row schema (~15-20 columns). At
5,000 decisions × ~3 horizons × ~2 continuations × ~80 average candidates
≈ 2.4M rows for the primary sample (plus a much smaller diagnostic
oversample and pilot) — comparable in scale to the existing frozen pilot's
own output CSVs, i.e. **tens of MB, not GB**. No large binary artifacts are
produced; everything fits comfortably as committed CSV/JSON evidence,
consistent with this project's established pattern of freezing small,
text-based scientific evidence.

## Local workstation vs. Wulver

**Local workstation is adequate.** Nothing in this design's cost profile
approaches the multi-hour-to-day-scale jobs already documented elsewhere
in this project (e.g. the target-discriminativeness audit's own reference
point of ">8 hours wall clock on Wulver's general partition" for one
linear scoring pass over the full 168-partition canonical release, or the
frozen pilot's ~48-minutes-per-cell `evict_value_v1` learned-policy
replay). This design deliberately avoids both of those cost regimes by
sampling decisions rather than enumerating the full release, and by using
cheap, short-horizon (≤16-step) rollouts rather than full-trace replays or
model inference. Wulver would only become relevant if a future reviewer
demanded full-population enumeration instead of the sampling design in
`MATRIX.md` — not a requirement of this task's own "smallest scientifically
defensible" framing.
