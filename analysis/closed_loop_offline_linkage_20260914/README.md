# Tier-1 Offline / Closed-Loop Linkage Analysis

This directory joins the frozen Tier-1 closed-loop evidence
(`analysis/closed_loop_tier1_evidence_20260914/`, a byte-verified snapshot of
`experiment/closed-loop-tier1-harness-20260913` @ `8a4cd32402a1c053af5db17c26cf05ee88842d8c`,
run `20260914T023445Z_8a4cd32402a1`) against the frozen offline
target-discriminativeness evidence (`analysis/sigmod_target_discriminativeness_20260913/`,
unmodified) to answer RQ-CL1 through RQ-CL4 as far as the existing frozen
artifacts permit. **No new trace replay, label generation, or simulation was
performed to produce this analysis** -- every number here is a re-slicing or
statistical summary of two already-frozen, already-committed datasets.

## MetaKV window semantics -- resolved

Before any interpretation, one apparent inconsistency was investigated: the
production design describes MetaKV's scored window as `[0,4095]` with a
"first-window/no-leading-warmup" caveat, while the general scoring-protocol
text elsewhere says the simulator replays continuously and unscored requests
still affect cache state -- which reads, if taken together carelessly, as
though there might be an unscored prefix *before* a window that itself
starts at request 0.

**Resolution, confirmed directly from the frozen Tier-1 evidence, not
inferred:** in every one of the other 9 (family, capacity) cells,
`evictions == misses` exactly (the cache is already full by the time the
scored window begins, because those windows sit deep in the 50,000-request
trace). For MetaKV specifically, in all 6 rows (2 capacities x {LRU, MRU,
SIEVE}), `evictions == misses - capacity` exactly:

| Family/capacity/policy | misses | evictions | misses − evictions |
|---|---:|---:|---:|
| metakv/32/lru | 3035 | 3003 | 32 |
| metakv/32/mru | 3339 | 3307 | 32 |
| metakv/32/sieve | 3036 | 3004 | 32 |
| metakv/128/lru | 2986 | 2858 | 128 |
| metakv/128/mru | 3242 | 3114 | 128 |
| metakv/128/sieve | 2860 | 2732 | 128 |

This is only possible if the cache is genuinely **empty** at the start of
MetaKV's scored window and the first `capacity` misses fill it without
evicting anything -- i.e. **Classification A**: scoring begins from request
0 with an initially empty cache, so there is no leading warm-up, by
construction of which window was chosen, not by any code defect. The
experiment's *execution* is correct and exactly as the design intended.

**Documentation correction needed (not applied to any frozen file):** the
phrase "though the full trace still replays continuously beforehand within
this window" (used in `DESIGN.md`'s family-inventory table and echoed in
`analysis/closed_loop_production_tier1_20260913/README.md`) is a copy-paste
artifact of the generic scoring-protocol sentence applied to every family
without adjusting for MetaKV's special first-window case -- there is no
"beforehand" possible for a window that starts at t=0. The corrected
statement should read: *"MetaKV's scored window `[0,4095]` is the start of
the trace; the cache is empty when scoring begins (no warmup). This differs
from every other Tier-1 family, whose windows are deep enough into the trace
that the cache is already full when scoring begins (confirmed empirically:
`evictions == misses` for every non-MetaKV cell, but `evictions = misses -
capacity` exactly for every MetaKV cell)."* This correction is recorded here
only; per this task's constraints, `analysis/closed_loop_production_design_20260913/`
and the already-committed harness README are frozen and were not edited.

This cold-start difference is carried through every MetaKV interpretation
below (see the metakv/cap128 discordance in RQ-CL1/RQ-CL2, and the
mechanistic-explanation section) and sensitivity analyses with/without
MetaKV are provided throughout.

## Sources

| Purpose | File | What it contains |
|---|---|---|
| Offline LRU/MRU regret | `analysis/sigmod_target_discriminativeness_20260913/outputs/phase8_lru_mru_stratified.csv` | Per (family, capacity, horizon): `lru_mean_regret`, `mru_mean_regret`, optimal rates. **No SIEVE column.** |
| Offline random regret + discriminativeness | `analysis/sigmod_target_discriminativeness_20260913/outputs/phase4_stratified_family_capacity_horizon.csv` | Per (family, capacity, horizon): `mean_random_regret` (the uniform-random selector's offline regret -- a policy-specific number), plus `all_tied_fraction`/`random_optimal_probability` (aggregate discriminativeness statistics, kept separate and never treated as policy performance). |
| Closed-loop Tier-1 evidence | `analysis/closed_loop_tier1_evidence_20260914/run/20260914T023445Z_8a4cd32402a1/summary.csv` | Per (family, capacity, policy): `miss_ratio`, `scored_split_label`. |

Both offline files cover capacities `{32,64,128,256}` and horizons
`{4,8,16}`; only capacities `{32,128}` (Tier 1's actual matrix) are used --
64 and 256 are dropped, never silently included (enforced by
`test_no_capacity_64_or_256_leaked_into_analysis`). **There is no offline
SIEVE quantity anywhere in the frozen evidence**, so SIEVE never appears in
any offline<->closed-loop comparison (enforced by
`test_no_sieve_offline_column_exists_anywhere`); it is reported only on the
closed-loop side, descriptively.

## Pre-registered RQs (exact wording, from `DESIGN.md`'s "Pre-Registered Questions")

- **RQ-CL1**: Do offline LAFC-Evict policy rankings among LRU, random, and MRU agree with closed-loop miss rankings?
- **RQ-CL2**: Does the strength of offline counterfactual separation predict the magnitude of closed-loop policy separation?
- **RQ-CL3**: How does agreement vary by workload and cache capacity?
- **RQ-CL4**: Which offline horizon H in {4,8,16} is most aligned with closed-loop behavior?

Not broadened. RQ-CL5 (learned-policy competitiveness) and RQ-CL6 (wiki2018
control, already answered descriptively in the Tier-1 execution report) are
out of scope for this linkage analysis.

## Method: tie-aware, no invented thresholds

"Offline tie" and "closed-loop tie" both mean **exact** equality of the
relevant gap (`mru_regret - lru_regret`, etc.) -- these come from population
statistics (offline) or exact integer hit/miss counts (closed-loop), so an
exact zero is meaningful, not a rounding artifact (wiki2018 realizes this
exactly, on both sides, at every cell). No tolerance-based "near tie"
threshold was applied in the primary analysis. `scripts/compute_rq_analyses.py`
reports pairwise concordant/discordant/tie counts (a Kendall-tau building
block) plus a 3-item (LRU/random/MRU) Kendall tau-b per cell -- a
tie-capable rank-association statistic, computed via `scipy.stats.kendalltau`.
Pearson r, Spearman rho, and Kendall tau-b are all reported for RQ-CL2, with
p-values labeled `TWO_SIDED_CAUTION_TINY_N` and explicitly not treated as
evidence of significance anywhere in this report, per instruction (n=8-10
per horizon).

**Horizon pseudo-replication guard**: closed-loop has no horizon dimension,
so pooling all 3 offline horizons together for one correlation would count
each (family, capacity) closed-loop value 3 times. Every RQ-CL2/RQ-CL4
statistic here is therefore computed **per horizon** (n=10 family-capacity
cells) as primary; an explicitly labeled `_SECONDARY`/pooled view (n=30, with
repeated closed-loop values, carrying an explicit `CAUTION` string) exists
only as a documented secondary view, never as a headline number.

## Files

- `data/joined_offline_closed_loop.csv` -- the 30-row (5 families x 2 capacities x 3 horizons) joined table underlying every statistic below.
- `outputs/rq_cl1_rank_agreement.json` -- per-horizon concordance counts + per-cell 3-item tau-b (primary).
- `outputs/rq_cl1_sensitivity_exclusions.json` -- same, excluding wiki2018 / MetaCDN / MetaKV in turn.
- `outputs/rq_cl2_gap_correspondence.json` -- per-horizon Pearson/Spearman/Kendall (primary, excluding-wiki2018, test-window-only, and pooled-secondary views).
- `outputs/rq_cl2_scatter_data.csv` -- the raw (offline_gap, closed_loop_gap) points underlying every RQ-CL2 correlation.
- `outputs/rq_cl3_workload_capacity_dependence.json` -- per-family/capacity summary at H=16, plus one exploratory (not pre-registered) discriminativeness-vs-separation correlation.
- `outputs/rq_cl4_horizon_alignment.json` -- cross-horizon comparison of the RQ-CL1/RQ-CL2 statistics.
- `SCIENTIFIC_SUMMARY.md`, `REVIEWER_ISSUE_MATRIX.md`, `HISTORICAL_REJECTION_RISK_MATRIX.md` -- interpretation.
- `scripts/build_joined_dataset.py`, `scripts/compute_rq_analyses.py` -- primary code path (run in that order).
- `scripts/independent_recheck.py` -- a **second, independent** code path (pandas + hand-rolled Pearson-r + hand-rolled concordance counter) that recomputes the headline numbers and asserts exact agreement with the primary path's outputs.
- `tests/test_analysis_consistency.py` -- 14 assertions (row counts, no capacity 64/256 leakage, MetaCDN always `validation`, wiki2018 exactly degenerate on both sides, no offline SIEVE column, pseudo-replication labeling present, frozen-evidence hash integrity, independent-recheck pass, and rebuild-determinism).

Reproduce everything with:
```sh
cd analysis/closed_loop_offline_linkage_20260914
python3 scripts/build_joined_dataset.py
python3 scripts/compute_rq_analyses.py
python3 scripts/independent_recheck.py
python3 -m pytest tests/ -v
```
