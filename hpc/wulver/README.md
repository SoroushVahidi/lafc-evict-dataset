# Wulver Real Release Workflow

Use this directory for the real `lafc-evict-v0.1-open` staged build on Wulver compute nodes and the resumable source-generation workflow that produces the source manifest consumed by that build.

## Safety constraints

- Do not run the full real release build on the login node.
- Do not submit the real build until the source manifest exists on Wulver.
- Do not include blocked families `citibike` or `brightkite`.
- Do not materialize a full pairwise view. Only the capped pairwise sample is allowed.
- Do not delete or overwrite the shared scratch source output tree to resume a timed-out run.

## Files

- `regenerate_lafc_source_v0_1_open.sbatch`: initial monolithic source-generation job for the open-family source dataset.
- `prepare_lafc_source_resume_tasks.py`: inspect the shared scratch output tree and emit only the incomplete family-capacity units.
- `resume_lafc_source_v0_1_open.sbatch`: array worker that rebuilds exactly one family-capacity unit per task.
- `finalize_lafc_source_v0_1_open.sbatch`: dependent post-pass that rebuilds the full shared manifest and summaries after the array completes.
- `submit_lafc_source_resume.sh`: safe login-node helper that checks the queue, plans the missing units, and submits the resume array plus finalizer.
- `check_lafc_source_resume_status.sh`: metadata-only checker for source-generation completion, manifest presence, and partial units.
- `build_lafc_evict_v0_1_open.sbatch`: staged Slurm build on the `general` partition.
- `check_remote_status.sh`: inspect queue, accounting, and job logs for a submitted build.
- `fetch_remote_release.sh`: fetch the finished release directory from Wulver with `rsync`.

## Resume Source Generation

Use this after a source-generation timeout where some `*.done.json` markers already exist in the shared scratch output tree.

```bash
hpc/wulver/check_lafc_source_resume_status.sh
hpc/wulver/submit_lafc_source_resume.sh
```

Why the resume path is split into smaller jobs:

- each array task handles one family-capacity unit, not the entire dataset;
- completed units are omitted at planning time;
- a partial unit such as `metakv:cap256` is rebuilt in place without deleting the 76G shared output tree;
- the dependent finalizer reruns the builder in skip-only mode to reconstruct the full `manifest.json` and summaries once every unit has a `.done.json` marker.

Array logs are written under:

- `/mmfs1/scratch/ikoutis/sv96/lafc-work/logs/lafc-src-resume-<array_job_id>_<task_id>.out`
- `/mmfs1/scratch/ikoutis/sv96/lafc-work/logs/lafc-src-resume-<array_job_id>_<task_id>.err`
- `/mmfs1/scratch/ikoutis/sv96/lafc-work/logs/lafc-src-finalize-<job_id>.out`
- `/mmfs1/scratch/ikoutis/sv96/lafc-work/logs/lafc-src-finalize-<job_id>.err`

## Submit

```bash
export SOURCE_MANIFEST=/absolute/path/to/manifest.json
sbatch hpc/wulver/build_lafc_evict_v0_1_open.sbatch
```

Optional overrides:

- `REPO_DIR`
- `FAMILY_SELECTION`
- `OUTPUT_DIR`
- `DUCKDB_TEMP_DIR`
- `DUCKDB_THREADS`
- `DUCKDB_MEMORY_LIMIT`
- `MAX_PAIRWISE_ROWS`
- `MAX_PAIRS_PER_DECISION`
- `PAIRWISE_SEED`

## Check status

```bash
hpc/wulver/check_remote_status.sh <job_id>
```

## Fetch after completion

Run this from a non-Wulver host with SSH access to Wulver:

```bash
DEST_DIR=./lafc-evict-v0.1-open hpc/wulver/fetch_remote_release.sh
```
