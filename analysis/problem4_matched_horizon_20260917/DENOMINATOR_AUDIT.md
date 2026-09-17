# Problem 4 denominator audit: matched long-horizon population

Date: 2026-09-17

## Canonical state

- Source branch: `experiment/problem3-informativeness-stratification-20260917`
- Source SHA: `c8ddd157c835e51c73630869f6b48761fd2cdd42`
- Problem-4 branch: `fix/problem4-matched-long-horizon-population-20260917`
- Worktree: `/home/soroush/projects/lafc-evict-dataset/worktrees/problem4-matched-long-horizon-population-20260917`

## Artifacts audited

- Canonical H16 authority:
  `/home/soroush/projects/lafc-evict-dataset/repo/release/lafc-evict-v0.1-open-current-contract-preserved/data/decision_view/decision_view.parquet`
- Problem-3 copied long-horizon summaries:
  `analysis/problem3_informativeness_20260917/outputs/horizon_h16_h128_primary_decision_micro_summary.csv`
  and
  `analysis/problem3_informativeness_20260917/outputs/horizon_h16_h128_combined_family_capacity_horizon.csv`
- Superseded long-horizon production package:
  `/home/soroush/projects/augmented-caching/worktrees/pe-h16-h128-comparative-integration-20260916/analysis/pe_long_horizon_production_v1`
- Corrected canonical-regeneration handoff and manifest:
  `/home/soroush/projects/augmented-caching/worktrees/pe-h16-h128-comparative-integration-20260916/analysis/pe_long_horizon_canonical_regen_20260916/HANDOFF.md`
  and
  `/home/soroush/projects/augmented-caching/worktrees/pe-h16-h128-comparative-integration-20260916/configs/pe_long_horizon_canonical_regen_20260916/manifest.json`

## Root cause

The previous manuscript-facing long-horizon comparison mixed:

- canonical H16 release population: `787,762` physical eviction decisions; and
- superseded H32/H64/H128 production population: `706,888` physical eviction decisions.

This was not caused by finite trace suffix eligibility. The canonical generator labels
decisions near the end of a trace with the available suffix (`future[:H]`) rather
than dropping them. The corrected canonical-regeneration manifest expected the same
canonical H16 physical decision count for H32/H64/H128, with
`92,665,024` candidate rows per horizon.

The mismatch came from the superseded H32/H64/H128 production artifact. Its own
handoff marks `analysis/pe_long_horizon_production_v1` as logically superseded
because of "stale/undercovered twemcache provenance and non-canonical trace-name
split hashing." The preserved source audit quantifies the twemcache undercoverage:

- canonical H16 twemcache candidate rows across all capacities: `14,776,736`
- canonical H4/H8/H16 twemcache candidate rows: `44,330,208`
- superseded long-horizon twemcache candidate rows across all H32/H64/H128:
  `10,591,392`

All non-twemcache H32/H64/H128 cells in the superseded summary match the local
canonical recomputation. The denominator loss is therefore localized to the stale
twemcache production path, not to a family/capacity mismatch, failed completed
tasks, or a scientifically meaningful H128 suffix rule.

## Common population

The matched population is the exact canonical H16 physical eviction-decision
population:

```text
trace_name | trace_family | capacity | decision_t | split
```

The explicit compact key artifact and manifest are:

`analysis/problem4_matched_horizon_20260917/artifacts/common_population_keys.parquet`
`analysis/problem4_matched_horizon_20260917/artifacts/common_population_manifest.json`

The parquet records every canonical physical decision key as
`trace_family`, `reader_family`, `trace_name`, `capacity`, `decision_t`,
`split`, and `physical_key`. The manifest records per-cell counts, min/max
`decision_t`, split counts, and SHA256 hashes of sorted physical keys. Total
common decisions: `787,762`.

## Recomputed matched evidence

The matched H16/H32/H64/H128 metrics were recomputed from the canonical trace
sources named by the corrected canonical-regeneration manifest. The recomputation
does not regenerate or modify the public candidate release. It writes compact
decision-level aggregates only:

- `outputs/matched_cell_horizon_metrics_raw.csv`
- `outputs/matched_primary_micro_summary.csv`
- `outputs/matched_family_summary.csv`
- `outputs/matched_capacity_summary.csv`
- `outputs/matched_paired_transition_micro_summary.csv`
- `outputs/matched_monotonicity_micro_summary.csv`

Primary matched micro results:

| H | decisions | all-tied | random-optimal | expected random regret |
| ---: | ---: | ---: | ---: | ---: |
| 16 | 787,762 | 0.619295 | 0.986942 | 0.013216 |
| 32 | 787,762 | 0.580717 | 0.979700 | 0.020891 |
| 64 | 787,762 | 0.555142 | 0.972409 | 0.028961 |
| 128 | 787,762 | 0.543395 | 0.966060 | 0.036095 |

## Validation

`outputs/validation.json` records:

- H16 recomputed cell metrics match the canonical release decision view for
  decision count, all-tied fraction, random-optimal probability, expected random
  regret, and loss range.
- H32/H64/H128 recomputed non-twemcache cells match the preserved production
  artifact; twemcache intentionally differs because the preserved production
  artifact is superseded and undercovered.
- Every horizon has the same decision count: `787,762`.

## Scientific implication

The old aggregate H16-to-H32 comparison was concerning because it mixed
denominators and used a superseded long-horizon production population. After exact
matching, the qualitative horizon conclusion strengthens: informativeness increases
monotonically in the matched micro aggregate, but substantial degeneracy remains at
H128 (`54.34%` all-tied).
