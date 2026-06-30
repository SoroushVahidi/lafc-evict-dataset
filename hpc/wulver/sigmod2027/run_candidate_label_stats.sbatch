#!/bin/bash
#SBATCH --job-name=sigmod-cand-stats
#SBATCH --partition=general
#SBATCH --account=ikoutis
#SBATCH --qos=standard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=/mmfs1/scratch/ikoutis/sv96/lafc-work/logs/%x-%j.out
#SBATCH --error=/mmfs1/scratch/ikoutis/sv96/lafc-work/logs/%x-%j.err

set -euo pipefail

REPO_DIR="${REPO_DIR:-/mmfs1/home/sv96/lafc-work/lafc-evict-dataset}"
RELEASE_ROOT="${RELEASE_ROOT:-/mmfs1/scratch/ikoutis/sv96/lafc-work/release/lafc-evict-v0.1-open-current-contract-preserved}"
SCRATCH_ROOT="${SCRATCH_ROOT:-/mmfs1/scratch/ikoutis/sv96/lafc-work}"
LOG_DIR="${LOG_DIR:-${SCRATCH_ROOT}/logs}"
OUTPUT_DIR="${OUTPUT_DIR:-${REPO_DIR}/paper/sigmod2027/results/candidate_label_stats}"
TMPDIR="${TMPDIR:-${SCRATCH_ROOT}/tmp/${SLURM_JOB_ID:-manual}-candidate-label-stats}"

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

[[ -d "$REPO_DIR" ]] || fail "Repo directory does not exist: $REPO_DIR"
[[ -d "$RELEASE_ROOT" ]] || fail "Release root does not exist: $RELEASE_ROOT"

case "$RELEASE_ROOT" in
  /mmfs1/scratch/ikoutis/sv96/lafc-work/release/lafc-evict-v0.1-open-current-contract-preserved) ;;
  *) fail "RELEASE_ROOT must point at the preserved release artifact: $RELEASE_ROOT" ;;
esac

case "$LOG_DIR" in
  /mmfs1/scratch/ikoutis/sv96/lafc-work/logs*) ;;
  *) fail "LOG_DIR must stay under scratch logs: $LOG_DIR" ;;
esac

case "$OUTPUT_DIR" in
  "${REPO_DIR}"/*) ;;
  *) fail "OUTPUT_DIR must stay under the repository: $OUTPUT_DIR" ;;
esac

mkdir -p "$LOG_DIR" "$TMPDIR" "$OUTPUT_DIR"
export TMPDIR TMP="$TMPDIR" TEMP="$TMPDIR" PYTHONUNBUFFERED=1

echo "hostname: $(hostname)"
echo "date: $(date)"
echo "repo: $REPO_DIR"
echo "release_root: $RELEASE_ROOT"
echo "output_dir: $OUTPUT_DIR"

cd "$REPO_DIR"
python scripts/sigmod2027/run_candidate_label_stats.py \
  --release-root "$RELEASE_ROOT" \
  --output-dir "${OUTPUT_DIR#${REPO_DIR}/}" \
  --target both \
  --mode run \
  --resume
