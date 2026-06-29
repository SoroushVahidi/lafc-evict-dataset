# Full Validation Plan

## Status

This command has now been run successfully against the preserved release. The June 29, 2026 overnight log records `start_utc=2026-06-29T04:13:25+00:00`, `end_utc=2026-06-29T04:13:51+00:00`, `exit_status=0`, and `Real release validation passed.`

## Executed command

```bash
python scripts/validate_real_release.py \
  --release-root release/lafc-evict-v0.1-open-current-contract-preserved
```

## Current caveat

- The validator CLI reports pass/fail but does not rewrite `metadata/validation_report.md`.
- The release-internal `metadata/validation_report.md` therefore remains stale and still reflects earlier build-time paths.
- Manuscript and status files should cite the June 29 log and preserved-release validation pass, not the stale internal report.

## What remains

- keep upload/publication claims pending,
- keep candidate-row label-distribution statistics pending,
- keep feature-based baselines pending until a feature join or augmented export exists.
