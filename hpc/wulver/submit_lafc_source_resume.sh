#!/bin/bash

set -euo pipefail

RELEASE_REPO="${RELEASE_REPO:-/mmfs1/home/sv96/lafc-work/lafc-evict-dataset}"
AUGMENTED_REPO="${AUGMENTED_REPO:-/mmfs1/home/sv96/lafc-work/Augmented-caching}"
SCRATCH_ROOT="${SCRATCH_ROOT:-/mmfs1/scratch/ikoutis/sv96/lafc-work}"
SOURCE_OUT_DIR="${SOURCE_OUT_DIR:-${SCRATCH_ROOT}/source/evict_value_v1_wulver_v0_1_open_source}"
TRACE_MANIFEST="${TRACE_MANIFEST:-${AUGMENTED_REPO}/analysis/wulver_trace_manifest_v0_1_open.csv}"
LOG_DIR="${LOG_DIR:-${SCRATCH_ROOT}/logs}"
JOB_USER="${JOB_USER:-sv96}"
STAMP="$(date +%Y%m%d-%H%M%S)"
RUN_DIR="${SOURCE_OUT_DIR}/status/resume-run-${STAMP}"
TASK_FILE="${RUN_DIR}/tasks.tsv"
SUBMISSION_FILE="${RUN_DIR}/submission.txt"

mkdir -p "$RUN_DIR"

echo "=== squeue -u ${JOB_USER} ==="
squeue -u "$JOB_USER" || true

python "$RELEASE_REPO/hpc/wulver/prepare_lafc_source_resume_tasks.py" \
  --source-dir "$SOURCE_OUT_DIR" \
  --trace-manifest "$TRACE_MANIFEST" \
  --run-dir "$RUN_DIR"

if [[ ! -s "$TASK_FILE" ]]; then
  echo "No incomplete units remain. Nothing submitted."
  exit 0
fi

TASK_COUNT="$(grep -c . "$TASK_FILE")"
ARRAY_JOB_ID="$(sbatch --parsable --array=1-${TASK_COUNT} "$RELEASE_REPO/hpc/wulver/resume_lafc_source_v0_1_open.sbatch" "$TASK_FILE" | cut -d';' -f1)"
FINALIZE_JOB_ID="$(sbatch --parsable --dependency=afterok:${ARRAY_JOB_ID} "$RELEASE_REPO/hpc/wulver/finalize_lafc_source_v0_1_open.sbatch" "$TASK_FILE" | cut -d';' -f1)"

cat > "$SUBMISSION_FILE" <<EOF
run dir: $RUN_DIR
task file: $TASK_FILE
task count: $TASK_COUNT
array job id: $ARRAY_JOB_ID
finalize job id: $FINALIZE_JOB_ID
array out pattern: ${LOG_DIR}/lafc-src-resume-${ARRAY_JOB_ID}_%a.out
array err pattern: ${LOG_DIR}/lafc-src-resume-${ARRAY_JOB_ID}_%a.err
finalize out: ${LOG_DIR}/lafc-src-finalize-${FINALIZE_JOB_ID}.out
finalize err: ${LOG_DIR}/lafc-src-finalize-${FINALIZE_JOB_ID}.err
monitor command: squeue -j ${ARRAY_JOB_ID},${FINALIZE_JOB_ID}
EOF

echo "run dir: $RUN_DIR"
echo "task file: $TASK_FILE"
echo "array job id: $ARRAY_JOB_ID"
echo "finalize job id: $FINALIZE_JOB_ID"
echo "array out pattern: ${LOG_DIR}/lafc-src-resume-${ARRAY_JOB_ID}_%a.out"
echo "array err pattern: ${LOG_DIR}/lafc-src-resume-${ARRAY_JOB_ID}_%a.err"
echo "finalize out: ${LOG_DIR}/lafc-src-finalize-${FINALIZE_JOB_ID}.out"
echo "finalize err: ${LOG_DIR}/lafc-src-finalize-${FINALIZE_JOB_ID}.err"
echo "next monitor command: squeue -j ${ARRAY_JOB_ID},${FINALIZE_JOB_ID}"
