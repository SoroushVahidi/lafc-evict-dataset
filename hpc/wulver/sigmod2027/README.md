# Wulver SIGMOD 2027 Result Jobs

This directory contains the Wulver Slurm wrappers for the SIGMOD result computations against the preserved release artifact:

- `/mmfs1/scratch/ikoutis/sv96/lafc-work/release/lafc-evict-v0.1-open-current-contract-preserved`

Safety constraints:

- Do not submit these jobs from the login node until you are ready to run the full computations.
- Do not change `RELEASE_ROOT` away from the preserved release artifact.
- Do not write anything under `release/`.
- The best-candidate job requires `paper/sigmod2027/results/baselines/value_regression/linear_regression_y_loss.json` from the value-regression run and fails immediately if it is missing.

## Files

- `run_candidate_label_stats.sbatch`: candidate-label statistics, `16` CPUs, `64G`, `4:00:00`.
- `run_value_regression_baseline.sbatch`: value-regression baseline, `24` CPUs, `96G`, `8:00:00`.
- `run_best_candidate_baseline.sbatch`: best-candidate baseline, `24` CPUs, `96G`, `8:00:00`.

## Submission order

```bash
sbatch hpc/wulver/sigmod2027/run_candidate_label_stats.sbatch
sbatch hpc/wulver/sigmod2027/run_value_regression_baseline.sbatch
# after value regression succeeds:
sbatch hpc/wulver/sigmod2027/run_best_candidate_baseline.sbatch
```

Dependency form:

```bash
jid_value=$(sbatch --parsable hpc/wulver/sigmod2027/run_value_regression_baseline.sbatch)
sbatch --dependency=afterok:${jid_value} hpc/wulver/sigmod2027/run_best_candidate_baseline.sbatch
```

## Notes

- Logs go to `/mmfs1/scratch/ikoutis/sv96/lafc-work/logs`.
- Result outputs stay in `paper/sigmod2027/results/...` inside the repo.
- Each wrapper runs the corresponding `scripts/sigmod2027/*.py` entrypoint with `--mode run --resume`.
