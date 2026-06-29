#!/bin/bash
#SBATCH --job-name=lafc-src-resume
#SBATCH --partition=general
#SBATCH --account=ikoutis
#SBATCH --qos=standard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=12:00:00
#SBATCH --output=/mmfs1/scratch/ikoutis/sv96/lafc-work/logs/%x-%A_%a.out
#SBATCH --error=/mmfs1/scratch/ikoutis/sv96/lafc-work/logs/%x-%A_%a.err

set -euo pipefail

RELEASE_REPO="${RELEASE_REPO:-/mmfs1/home/sv96/lafc-work/lafc-evict-dataset}"
AUGMENTED_REPO="${AUGMENTED_REPO:-/mmfs1/home/sv96/lafc-work/Augmented-caching}"
SCRATCH_ROOT="${SCRATCH_ROOT:-/mmfs1/scratch/ikoutis/sv96/lafc-work}"
LOG_DIR="${LOG_DIR:-${SCRATCH_ROOT}/logs}"
SOURCE_OUT_DIR="${SOURCE_OUT_DIR:-${SCRATCH_ROOT}/source/evict_value_v1_wulver_v0_1_open_source}"
TMPDIR="${TMPDIR:-${SCRATCH_ROOT}/tmp/${SLURM_JOB_ID:-manual}-${SLURM_ARRAY_TASK_ID:-0}}"
PIP_CACHE_DIR="${PIP_CACHE_DIR:-${SCRATCH_ROOT}/pip-cache}"
STATUS_DIR="${STATUS_DIR:-${SOURCE_OUT_DIR}/status/units}"
HORIZONS="${HORIZONS:-4,8,16}"
CHUNK_SIZE="${CHUNK_SIZE:-4096}"
SPLIT_SEED="${SPLIT_SEED:-7}"
MAX_ROWS_PER_SHARD="${MAX_ROWS_PER_SHARD:-500000}"
MAX_REQUESTS_PER_TRACE="${MAX_REQUESTS_PER_TRACE:-50000}"
TASK_FILE="${1:-${TASK_FILE:-}}"
TASK_INDEX="${SLURM_ARRAY_TASK_ID:-1}"
JOB_ID="${SLURM_JOB_ID:-unknown}"
ARRAY_JOB_ID="${SLURM_ARRAY_JOB_ID:-$JOB_ID}"
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

on_term() {
  FAIL_REASON=${FAIL_REASON:-received termination signal}
  exit 124
}

write_status() {
  mkdir -p "$STATUS_DIR"
  END_TS="$(date -Is)"
  cat > "$UNIT_STATUS_FILE" <<EOF
job id: $JOB_ID
array job id: $ARRAY_JOB_ID
array task id: $TASK_INDEX
unit: $UNIT_ID
source state at submission: $UNIT_STATE
trace count: $TRACE_COUNT
existing shards before: $EXISTING_SHARDS
done markers before: $DONE_BEFORE
done markers after: $DONE_AFTER
start time: $START_TS
end time: $END_TS
generation succeeded: $SUCCESS
completed units: $COMPLETED_UNITS
skipped units: $SKIPPED_UNITS
failed units: $FAILED_UNITS
manifest path: $MANIFEST_PATH
task file: $TASK_FILE
unit manifest: $UNIT_MANIFEST
failure reason: ${FAIL_REASON:-none}
EOF
}

trap on_term TERM INT
trap write_status EXIT

[[ -n "$TASK_FILE" && -f "$TASK_FILE" ]] || fail "Task file is required."

TASK_LINE="$(sed -n "${TASK_INDEX}p" "$TASK_FILE")"
[[ -n "$TASK_LINE" ]] || fail "Task index ${TASK_INDEX} is not present in $TASK_FILE"
IFS=$'\t' read -r FAMILY CAPACITY UNIT_STATE TRACE_COUNT EXISTING_SHARDS UNIT_MANIFEST <<< "$TASK_LINE"
[[ -n "${FAMILY:-}" && -n "${CAPACITY:-}" && -n "${UNIT_MANIFEST:-}" ]] || fail "Malformed task line: $TASK_LINE"
[[ -f "$UNIT_MANIFEST" ]] || fail "Unit manifest is missing: $UNIT_MANIFEST"

UNIT_ID="${FAMILY}__cap${CAPACITY}"
UNIT_STATUS_FILE="${STATUS_DIR}/${UNIT_ID}.status.txt"

case "$SOURCE_OUT_DIR" in
  /mmfs1/scratch/ikoutis/sv96/lafc-work/source/*) ;;
  *) fail "SOURCE_OUT_DIR is not under scratch: $SOURCE_OUT_DIR" ;;
esac
case "$LOG_DIR" in
  /mmfs1/scratch/ikoutis/sv96/lafc-work/logs*) ;;
  *) fail "LOG_DIR is not under scratch: $LOG_DIR" ;;
esac

mkdir -p "$LOG_DIR" "$TMPDIR" "$PIP_CACHE_DIR" "$STATUS_DIR" "$SOURCE_OUT_DIR"
export TMPDIR TMP="$TMPDIR" TEMP="$TMPDIR" PIP_CACHE_DIR

read -r DONE_BEFORE DONE_AFTER < <(python - "$UNIT_MANIFEST" "$SOURCE_OUT_DIR" "$CAPACITY" <<'PY'
import csv
import sys
from pathlib import Path

manifest = Path(sys.argv[1])
source_dir = Path(sys.argv[2])
capacity = sys.argv[3]

rows = list(csv.DictReader(manifest.open(newline="", encoding="utf-8")))

def safe_trace_name(value: str) -> str:
    return value.replace("/", "__").replace(":", "_")

count = 0
for row in rows:
    marker = source_dir / "logs" / f"{safe_trace_name(row['trace_name'])}__cap{capacity}.done.json"
    if marker.exists():
        count += 1
print(count, count)
PY
)
DONE_AFTER="$DONE_BEFORE"

echo "hostname: $(hostname)"
echo "date: $(date)"
echo "repo: $RELEASE_REPO"
echo "augmented repo: $AUGMENTED_REPO"
echo "task file: $TASK_FILE"
echo "unit: $UNIT_ID"
echo "source state: $UNIT_STATE"
echo "trace count: $TRACE_COUNT"
echo "existing shards: $EXISTING_SHARDS"
echo "done markers before: $DONE_BEFORE"
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
  --trace-manifest "$UNIT_MANIFEST" \
  --capacities "$CAPACITY" \
  --horizons "$HORIZONS" \
  --split-mode trace_chunk \
  --chunk-size "$CHUNK_SIZE" \
  --split-seed "$SPLIT_SEED" \
  --max-rows-per-shard "$MAX_ROWS_PER_SHARD" \
  --max-requests-per-trace "$MAX_REQUESTS_PER_TRACE" \
  --out-dir "$SOURCE_OUT_DIR"

DONE_AFTER="$(python - "$UNIT_MANIFEST" "$SOURCE_OUT_DIR" "$CAPACITY" <<'PY'
import csv
import sys
from pathlib import Path

manifest = Path(sys.argv[1])
source_dir = Path(sys.argv[2])
capacity = sys.argv[3]

rows = list(csv.DictReader(manifest.open(newline="", encoding="utf-8")))

def safe_trace_name(value: str) -> str:
    return value.replace("/", "__").replace(":", "_")

count = 0
for row in rows:
    marker = source_dir / "logs" / f"{safe_trace_name(row['trace_name'])}__cap{capacity}.done.json"
    if marker.exists():
        count += 1
print(count)
PY
)"

if [[ "$DONE_AFTER" -lt "$TRACE_COUNT" ]]; then
  FAILED_UNITS="$UNIT_ID"
  fail "Unit is still missing done markers after rebuild."
fi

if [[ "$DONE_BEFORE" -ge "$TRACE_COUNT" ]]; then
  SKIPPED_UNITS="$UNIT_ID"
else
  COMPLETED_UNITS="$UNIT_ID"
fi

SUCCESS=1
echo "unit finished: $UNIT_ID"
