# Current Release Status: `lafc-evict-v0.1-open`

## Current local release paths

- Stale repo-local release: `/home/soroush/lafc-evict-dataset/release/lafc-evict-v0.1-open`
- Preserved current-contract release: `/home/soroush/lafc-evict-dataset/release/lafc-evict-v0.1-open-current-contract-preserved`
- Fresh publication bundle: `/tmp/lafc-evict-v0.1-open-current-contract-preserved-publication-bundle`

## What has passed

- Preserved current-contract release copied into durable repo-local storage.
- Lightweight metadata repair completed on the preserved release.
- Publication bundle regenerated from the preserved release.
- Publication bundle validation passed.
- Public-facing bundle files were checked and do not contain `/home/soroush`, `/tmp`, or `/mmfs1` absolute paths.
- Normal repository tests passed with `python -m pytest`.

## What has not yet passed

- Full real-release validation has not been run on the preserved release.
- No upload or publication step has been run.
- No commit or push has been performed.

## Full validation command to run later

Run only after explicit approval:

```bash
python scripts/validate_real_release.py \
  --release-root /home/soroush/lafc-evict-dataset/release/lafc-evict-v0.1-open-current-contract-preserved
```

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

This release is preserved and lightly audited, but it is not yet fully validated or published.
