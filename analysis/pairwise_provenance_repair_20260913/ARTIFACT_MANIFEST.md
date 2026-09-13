# Pairwise Provenance Repair Artifact Manifest

This manifest records the durable artifact state after final repository-polish
Query 3. It complements the original repair report without changing the
scientific result.

## Historical Shipped Sample

Path:
`release/lafc-evict-v0.1-open-current-contract-preserved/data/pairwise_sample/pairwise_sample.parquet`

SHA256:
`99697a0d20acc643848db6bcb71656b32fad939b004cbe56f2b69b3a418bcb18`

Counts:

- `a_better = 6,134`
- `b_better = 113,898`
- `tie = 879,968`
- total rows: `1,000,000`

Status: `HISTORICAL_NONCANONICAL`

This file is preserved as historical release evidence. It must not be
overwritten or confused with the regenerated canonical analysis sample.

## Regenerated Canonical Sample

Durable path:
`analysis/pairwise_provenance_repair_20260913/artifacts/pairwise_sample_regenerated_canonical.parquet`

Temporary source copied from:
`/tmp/claude-1000/-home-soroush/8a66210e-4d63-4b01-b3ba-10065c25f134/scratchpad/pairwise_repair/generated/pairwise_sample.parquet`

SHA256:
`1d770c6999ac999673b46805a6ca173e24b116793b35405d2d211cae7b9eda02`

Size:
`11,367,843` bytes

Counts:

- `a_better = 60,673`
- `b_better = 61,065`
- `tie = 878,262`
- total rows: `1,000,000`

Status: `CANONICAL_FOR_CURRENT_DECISION_SELECTION`

Storage mode: `TRACKED_IN_GIT`

This is an analysis-evidence artifact. It is not the historical v0.1 shipped
sample, not automatically the public v0.3 pairwise sample, and not a
replacement for release files.

## Generator And Provenance

Generator:
`analysis/pairwise_provenance_repair_20260913/scripts/regenerate_pairwise_v2.py`

Reference implementation:
`analysis/pairwise_provenance_repair_20260913/scripts/regenerate_pairwise.py`

Comparison/check scripts:

- `analysis/pairwise_provenance_repair_20260913/scripts/compare_pairwise_states.py`
- `analysis/pairwise_provenance_repair_20260913/scripts/rerun_pairwise_audit_canonical.py`

Decision-selection provenance:

- historical shipped sample: six-column decision-selection hash key
- regenerated canonical sample: canonical nine-column decision-selection hash
  key

The six-column versus nine-column hash-input change reshuffled which decisions
were selected for the capped pairwise sample. The regenerated canonical sample
therefore matches the current decision-selection semantics and the committed
manuscript pairwise counts.

The canonical regenerated analysis sample must not be confused with the
historical shipped v0.1 sample.
