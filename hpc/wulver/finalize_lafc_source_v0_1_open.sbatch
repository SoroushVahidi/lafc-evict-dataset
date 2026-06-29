#!/bin/bash
#SBATCH --job-name=lafc-src-finalize
#SBATCH --partition=general
#SBATCH --account=ikoutis
#SBATCH --qos=standard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/mmfs1/scratch/ikoutis/sv96/lafc-work/logs/%x-%j.out
#SBATCH --error=/mmfs1/scratch/ikoutis/sv96/lafc-work/logs/%x-%j.err

set -euo pipefail

RELEASE_REPO="${RELEASE_REPO:-/mmfs1/home/sv96/lafc-work/lafc-evict-dataset}"
AUGMENTED_REPO="${AUGMENTED_REPO:-/mmfs1/home/sv96/lafc-work/Augmented-caching}"
SCRATCH_ROOT="${SCRATCH_ROOT:-/mmfs1/scratch/ikoutis/sv96/lafc-work}"
LOG_DIR="${LOG_DIR:-${SCRATCH_ROOT}/logs}"
SOURCE_OUT_DIR="${SOURCE_OUT_DIR:-${SCRATCH_ROOT}/source/evict_value_v1_wulver_v0_1_open_source}"
TMPDIR="${TMPDIR:-${SCRATCH_ROOT}/tmp/${SLURM_JOB_ID:-manual}}"
PIP_CACHE_DIR="${PIP_CACHE_DIR:-${SCRATCH_ROOT}/pip-cache}"
TRACE_MANIFEST="${TRACE_MANIFEST:-$AUGMENTED_REPO/analysis/wulver_trace_manifest_v0_1_open.csv}"
TASK_FILE="${1:-${TASK_FILE:-}}"
STATUS_FILE="${SOURCE_OUT_DIR}/GENERATION_STATUS.txt"
SUMMARY_JSON="${SOURCE_OUT_DIR}/dataset_summary_extended_v0_1_open.json"
SUMMARY_MD="${SOURCE_OUT_DIR}/dataset_summary_v0_1_open.md"
BUILD_MANIFEST="${SOURCE_OUT_DIR}/manifest.json"
JOB_ID="${SLURM_JOB_ID:-unknown}"
START_TS="$(date -Is)"
END_TS=""
SUCCESS=0
FAIL_REASON=""
COMPLETED_UNITS="none"
SKIPPED_UNITS="none"
FAILED_UNITS="none"
MANIFEST_PATH="none"

fail() {
  FAIL_REASON=$*
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

write_status() {
  mkdir -p "$SOURCE_OUT_DIR"
  END_TS="$(date -Is)"
  cat > "$STATUS_FILE" <<EOF
job id: $JOB_ID
hostname: $(hostname)
start time: $START_TS
end time: $END_TS
generation succeeded: $SUCCESS
completed units: $COMPLETED_UNITS
skipped units: $SKIPPED_UNITS
failed units: $FAILED_UNITS
manifest path: $MANIFEST_PATH
task file: ${TASK_FILE:-none}
failure reason: ${FAIL_REASON:-none}
next command: cd $RELEASE_REPO && python scripts/plan_real_release.py --input-manifest $BUILD_MANIFEST --family-selection manifests/lafc_evict_v0_1_open_families.json --repo-root $RELEASE_REPO
EOF
}

trap write_status EXIT

mkdir -p "$LOG_DIR" "$TMPDIR" "$PIP_CACHE_DIR" "$SOURCE_OUT_DIR"
export TMPDIR TMP="$TMPDIR" TEMP="$TMPDIR" PIP_CACHE_DIR

echo "hostname: $(hostname)"
echo "date: $(date)"
echo "repo: $RELEASE_REPO"
echo "augmented repo: $AUGMENTED_REPO"
echo "task file: ${TASK_FILE:-none}"
df -h "$SCRATCH_ROOT"

cd "$AUGMENTED_REPO"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  source .venv/bin/activate
  python -m pip install --upgrade pip setuptools wheel
  if ! python -m pip install -e ".[dev]"; then
    python -m pip install -e .
  fi
else
  source .venv/bin/activate
fi

python scripts/build_evict_value_dataset_wulver_v1.py \
  --trace-manifest "$TRACE_MANIFEST" \
  --capacities 32,64,128,256 \
  --horizons 4,8,16 \
  --split-mode trace_chunk \
  --chunk-size 4096 \
  --split-seed 7 \
  --max-rows-per-shard 500000 \
  --max-requests-per-trace 50000 \
  --out-dir "$SOURCE_OUT_DIR"

[[ -f "$BUILD_MANIFEST" ]] || fail "Global manifest was not written."

# In all-skip resume mode the upstream builder rebuilds manifest.json from
# completed-unit markers, but it does not repopulate split_summary.csv.
# Invoke the helper by file path so it stays independent of package-level
# imports like PyYAML-backed governance helpers.
python "$RELEASE_REPO/src/lafc_evict_dataset/wulver_source_summary.py" \
  --source-root "$SOURCE_OUT_DIR" \
  --out-split-summary "$SOURCE_OUT_DIR/split_summary.csv" \
  --progress-file "$SOURCE_OUT_DIR/status/split_summary_rebuild_progress.json"
python scripts/summarize_wulver_evict_value_dataset.py \
  --manifest "$BUILD_MANIFEST" \
  --out-json "$SUMMARY_JSON" \
  --out-md "$SUMMARY_MD"

cd "$RELEASE_REPO"
hpc/wulver/check_lafc_source_resume_status.sh "$SOURCE_OUT_DIR"

if [[ -n "${TASK_FILE:-}" && -f "$TASK_FILE" ]]; then
  COMPLETED_UNITS="$(awk -F '\t' 'NF >= 2 {print $1 ":cap" $2}' "$TASK_FILE" | paste -sd ',' -)"
fi
MANIFEST_PATH="$BUILD_MANIFEST"
SUCCESS=1
