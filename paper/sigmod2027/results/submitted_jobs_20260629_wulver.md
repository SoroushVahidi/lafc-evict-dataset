# Wulver SIGMOD Result Submission Note

- Date/time: Mon Jun 29 22:12:21 EDT 2026
- Host: login02
- Branch: `wulver-sync-origin-master-with-finalizer-fixes-20260629`
- Commit at submission time: `7b7e596` (`Add Wulver SIGMOD result job scripts`)
- Release root: `/mmfs1/scratch/ikoutis/sv96/lafc-work/release/lafc-evict-v0.1-open-current-contract-preserved`

## Release checks

- Apparent size: `2.7G`
- Total files: `176`
- Parquet files: `170`
- Candidate parquet files: `168`

## Codex config

- Config path edited: `/home/sv96/.codex/config.toml`
- Backup path created: `/home/sv96/.codex/config.toml.bak.20260629_221010`
- Future Codex agents were configured with full-access defaults using the documented user config file and keys:
  - `approval_policy = "never"`
  - `sandbox_mode = "danger-full-access"`

## Job submissions

- Candidate-label stats job ID: `1085536`
  - Submission outcome: submitted, then failed quickly.
  - Failure cause: missing checkpoint file `/mmfs1/home/sv96/lafc-work/lafc-evict-dataset/paper/sigmod2027/results/candidate_label_stats/.candidate_label_stats.checkpoint.json` while running with `--resume`.
- Value-regression job ID: `1085537`
  - Submission outcome: submitted, then failed quickly.
  - Failure cause: missing checkpoint file `/mmfs1/home/sv96/lafc-work/lafc-evict-dataset/paper/sigmod2027/results/baselines/value_regression/.value_regression_y_loss.checkpoint.json` while running with `--resume`.

## Resume fix and resubmission

- Root cause: the SIGMOD result runners treated `--resume` as "load checkpoint unconditionally", so a fresh run failed before any work started if the checkpoint file did not exist yet.
- Fix commit: `83a7b6b` (`Allow fresh SIGMOD result runs with resume`)
- Candidate-label stats resubmission job ID: `1085544`
- Value-regression resubmission job ID: `1085545`
- Queue state at Mon Jun 29 22:18:50 EDT 2026:
  - `1085544` (`sigmod-cand-stats`) running on `n0006`
  - `1085545` (`sigmod-value-reg`) running on `n0119`
- Best-candidate remains not submitted.

Exact next action after value regression succeeds:

```bash
sbatch hpc/wulver/sigmod2027/run_best_candidate_baseline.sbatch
```
