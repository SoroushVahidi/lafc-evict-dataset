# Pairwise-sample provenance repair (2026-09-13)

Follow-up to the SIGMOD target-discriminativeness audit
(`../sigmod_target_discriminativeness_20260913/`), which discovered that the
on-disk `pairwise_sample.parquet` in the canonical release directory does not
reproduce the manuscript's own committed pairwise statistics. This directory
traces the exact root cause, regenerates a verified canonical replacement,
and reruns the pairwise information-content analysis on it. **No manuscript
file was edited. No file inside `release/` was modified, moved, or deleted.**

**Final-polish preservation update (2026-09-13):** the regenerated canonical
analysis sample has now been durably preserved in Git at
`analysis/pairwise_provenance_repair_20260913/artifacts/pairwise_sample_regenerated_canonical.parquet`.
See `ARTIFACT_MANIFEST.md` for the exact SHA256, size, counts, and
historical-vs-canonical distinction.

See `REPORT.md` for the full write-up. Summary of the finding:

- The on-disk `release/lafc-evict-v0.1-open-current-contract-preserved/data/pairwise_sample/pairwise_sample.parquet`
  (call it **A**, "stale") was built on 2026-06-27, under a commit that
  predates **two** later fixes, not one as previously assumed.
- Regenerating the sample (call it **B**, "canonical") with the *current*
  code and the *current* candidate population reproduces the manuscript's
  committed table
  (`paper/sigmod2027/results/metadata_tables/table_pairwise_sample_label_summary.csv`,
  call it **C**) **exactly**: 878,262 ties / 60,673 `a_better` / 61,065
  `b_better`, all out of 1,000,000 rows.
- The root cause is **not** "orientation only" (that was an incomplete
  working assumption carried over from the prior session). A second,
  independent fix — commit `1f5f272`, four days before the orientation fix
  `3b49189` — changed which 6-vs-9 decision-key columns feed the `hash()`
  call that selects *which decisions* get sampled. That alone reproduces the
  observed 94.76% pair-identity mismatch between A and B (verified directly,
  see REPORT.md Phase 3).

## Reproduce

The regenerated parquet is now committed to git as a durable analysis-evidence
artifact. It can also be regenerated deterministically from data + code already
in this repo:

```bash
python3 analysis/pairwise_provenance_repair_20260913/scripts/regenerate_pairwise_v2.py
python3 analysis/pairwise_provenance_repair_20260913/scripts/compare_pairwise_states.py
python3 analysis/pairwise_provenance_repair_20260913/scripts/rerun_pairwise_audit_canonical.py
```

The first script writes to `generated/pairwise_sample.parquet` next to itself
(gitignored scratch output recommended -- see note in the script). The other
two read that file plus the stale release file plus the manuscript's committed
CSV.

**Note on `regenerate_pairwise_v2.py`**: this is a provably-equivalent,
filter-pushed-down reformulation of
`lafc_evict_dataset.real_release_build._build_pairwise_sample`, not a
modification of its logic — see the script's docstring for the equivalence
proof. A verbatim call to the unmodified function
(`regenerate_pairwise.py`, also included) is correct but impractically slow
on this machine (>15 minutes with no output; killed) because DuckDB does not
push the `sampled_decisions` filter ahead of the self-join, so it was
materializing on the order of the full ~24.8-billion-pair universe before
applying the cap. `regenerate_pairwise_v2.py` produces byte-identical output
in ~930 seconds by pre-filtering `candidates` to `sampled_decisions` before
the self-join — a valid reordering because both sides of that join already
share a matching decision key, so restricting to `sampled_decisions`
membership before or after the join cannot change which pairs survive.

## Files

- `REPORT.md` -- full findings (Phases 1-8)
- `ARTIFACT_MANIFEST.md` -- durable artifact manifest added during final
  repository polish
- `artifacts/pairwise_sample_regenerated_canonical.parquet` -- canonical
  regenerated analysis sample, tracked in Git
- `scripts/regenerate_pairwise.py` -- verbatim call to the unmodified
  generator (kept for reference; impractically slow, do not run without a
  long timeout)
- `scripts/regenerate_pairwise_v2.py` -- the practical, equivalent version
  actually used
- `scripts/compare_pairwise_states.py` -- stale vs. regenerated vs. manuscript
  comparison (Phase 2)
- `scripts/rerun_pairwise_audit_canonical.py` -- Phase 5 re-audit on the
  canonical sample, with a before/after comparison to the prior (stale-file-
  based) audit
- `outputs/canonical_pairwise_report.json`, `outputs/canonical_pairwise_strict_density.csv`,
  `outputs/pairwise_three_state_comparison.json` -- machine-readable results
