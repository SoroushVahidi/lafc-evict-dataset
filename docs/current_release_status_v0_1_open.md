# Current Release Status: `lafc-evict-v0.1-open`

## Current local release paths

- Stale repo-local release: `/home/soroush/lafc-evict-dataset/release/lafc-evict-v0.1-open`
- Preserved current-contract release: `/home/soroush/lafc-evict-dataset/release/lafc-evict-v0.1-open-current-contract-preserved`
- Fresh publication bundle: `/tmp/lafc-evict-v0.1-open-current-contract-final-publication-bundle-20260629`

## What has passed

- Preserved current-contract release copied into durable repo-local storage.
- Lightweight metadata repair completed on the preserved release.
- Full real-release validation passed on the preserved release on 2026-06-29 (`start_utc=2026-06-29T04:13:25+00:00`, `end_utc=2026-06-29T04:13:51+00:00`, `exit_status=0`).
- Publication bundle regenerated from the preserved release.
- Publication bundle validation passed.
- Public-facing bundle files were checked and do not contain `/home/soroush`, `/tmp`, or `/mmfs1` absolute paths.
- Normal repository tests passed with `python -m pytest`.

## What has not yet passed

- The release-internal `metadata/validation_report.md` was not refreshed by the overnight validation command and still reflects earlier build-time paths.
- No upload or publication step has been run.
- No commit or push has been performed.

## Wolverine heavy resume command to run later

There is no repo-local Slurm wrapper script. The repo-side heavy build command below should be run only from a Wolverine Slurm allocation, not on this local machine:

```bash
python scripts/build_real_release.py \
  --input-manifest /home/soroush/Augmented-caching/data/derived/evict_value_v1_wulver_heavy_r1/manifest.json \
  --family-selection /home/soroush/lafc-evict-dataset/manifests/lafc_evict_v0_1_open_families.json \
  --output-dir /tmp/lafc-evict-v0.1-open-current-contract \
  --dataset-id lafc-evict-v0.1-open \
  --duckdb-threads 2 \
  --duckdb-memory-limit 8GB \
  --duckdb-temp-dir /tmp/lafc-evict-v0.1-open-current-contract-duckdb-tmp \
  --resume \
  --skip-disk-space-check \
  --stage decision_view \
  --stage metadata \
  --stage checksums \
  --stage validate \
  --pairwise-sample \
  --max-pairwise-rows 1000000 \
  --max-pairs-per-decision 8 \
  --pairwise-seed 7
```

## Warning

This release is preserved and fully validated locally, but it is not yet published and its internal `metadata/validation_report.md` remains stale.
