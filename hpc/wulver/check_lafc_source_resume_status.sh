#!/bin/bash

set -euo pipefail

SRC=${1:-/mmfs1/scratch/ikoutis/sv96/lafc-work/source/evict_value_v1_wulver_v0_1_open_source}

echo "source dir: $SRC"
du -sh "$SRC"
echo "total files: $(find "$SRC" -type f | wc -l)"
echo "csv shards: $(find "$SRC" -name '*.csv' -type f | wc -l)"
echo "done markers: $(find "$SRC" -name '*.done.json' -type f | wc -l)"

for name in manifest.json GENERATION_STATUS.txt dataset_summary_extended_v0_1_open.json dataset_summary_v0_1_open.md; do
  if [[ -e "$SRC/$name" ]]; then
    echo "exists: $name"
  else
    echo "missing: $name"
  fi
done

python - "$SRC" <<'PY'
import sys
from collections import defaultdict
from pathlib import Path
import re

src = Path(sys.argv[1])
expected_families = ["wiki2018", "twemcache", "metakv", "metacdn", "cloudphysics"]
expected_caps = ["32", "64", "128", "256"]
done = defaultdict(set)
shards = defaultdict(int)

for path in (src / "logs").glob("*.done.json"):
    match = re.match(r"([^_]+).*__cap(\d+)\.done\.json$", path.name)
    if match:
        done[match.group(1)].add(match.group(2))

for path in (src / "shards").glob("*.csv"):
    match = re.match(r"([^_]+).*__cap(\d+)\.part\d+\.csv$", path.name)
    if match:
        shards[(match.group(1), match.group(2))] += 1

complete = []
partial = []
missing = []
for family in expected_families:
    for cap in expected_caps:
        key = (family, cap)
        if cap in done[family]:
            complete.append(f"{family}:cap{cap}:shards={shards[key]}")
        elif shards[key] > 0:
            partial.append(f"{family}:cap{cap}:shards={shards[key]}")
        else:
            missing.append(f"{family}:cap{cap}")

print("complete units:")
for item in complete:
    print(f"  {item}")

print("partial units:")
if partial:
    for item in partial:
        print(f"  {item}")
else:
    print("  none")

print("missing units:")
if missing:
    for item in missing:
        print(f"  {item}")
else:
    print("  none")

ready = (
    not partial
    and not missing
    and (src / "manifest.json").exists()
    and (src / "dataset_summary_extended_v0_1_open.json").exists()
    and (src / "dataset_summary_v0_1_open.md").exists()
)

if ready:
    print("status: COMPLETE")
    raise SystemExit(0)

print("status: INCOMPLETE")
raise SystemExit(1)
PY
