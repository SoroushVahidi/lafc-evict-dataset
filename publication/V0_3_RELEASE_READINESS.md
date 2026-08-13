# LAFC-Evict v0.3 local publication readiness

The complete check-by-check report is maintained at
`reports/V0_3_RELEASE_READINESS.md`. The local release is
`READY_FOR_PUBLICATION`; no Hugging Face or Zenodo action has been performed.

## Novelty/documentation gate (2026-08-12 addendum)

A separate pre-publication novelty, differentiation, and documentation audit
was completed and is preserved at
`reports/v0_3_novelty_audit_20260812/NOVELTY_AUDIT_REPORT.md`. It found the
technical gate above passed but identified nine documentation blockers
(missing differentiation section, missing data dictionary, undocumented
capacity-imbalance and label-censoring caveats, a misleading unexplained
config name, an overstated schema claim, an incomplete version-history
section, and a citation-metadata DOI error). All nine were remediated as
documentation-only edits (no Parquet payload change); the full record is at
`reports/v0_3_novelty_audit_20260812/DOCUMENTATION_REMEDIATION_REPORT.md`.

Combined status: **TECHNICALLY_READY** +
**NOVELTY_AND_DOCUMENTATION_GATE_PASSED** = **READY_FOR_PUBLICATION**
(local readiness only; still no Hugging Face or Zenodo action performed).

Prepared assets:

- `release/lafc-evict-v0.3-candidate/` — HF-oriented package.
- `release/lafc-evict-v0.3-zenodo-flat/` — flat local Zenodo package.
- `publication/zenodo_v0_3_metadata_draft.json` — metadata draft with no
  unminted version DOI.
- `publication/zenodo_v0_3_flat_file_manifest.json` — verified 17-file flat
  package manifest.

The two scientific Parquet files are byte-identical between both packages and
retain the pre-preparation baseline hashes.
