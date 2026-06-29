from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

EXPECTED_FAMILIES = ["wiki2018", "twemcache", "metakv", "metacdn", "cloudphysics"]
EXPECTED_CAPACITIES = [32, 64, 128, 256]


def safe_trace_name(trace_name: str) -> str:
    return trace_name.replace("/", "__").replace(":", "_")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan only the incomplete family-capacity units for Wulver source generation resume.",
    )
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--trace-manifest", required=True)
    parser.add_argument("--run-dir", required=True)
    return parser.parse_args()


def load_manifest_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit(f"Trace manifest is empty: {path}")
    return rows


def discover_unit_state(source_dir: Path) -> tuple[dict[str, set[str]], dict[tuple[str, str], int]]:
    done_by_family: dict[str, set[str]] = defaultdict(set)
    shard_counts: dict[tuple[str, str], int] = defaultdict(int)

    done_pattern = re.compile(r"([^_]+).*__cap(\d+)\.done\.json$")
    for path in (source_dir / "logs").glob("*.done.json"):
        match = done_pattern.match(path.name)
        if match:
            done_by_family[match.group(1)].add(match.group(2))

    shard_pattern = re.compile(r"([^_]+).*__cap(\d+)\.part\d+\.csv$")
    for path in (source_dir / "shards").glob("*.csv"):
        match = shard_pattern.match(path.name)
        if match:
            shard_counts[(match.group(1), match.group(2))] += 1

    return done_by_family, shard_counts


def write_unit_manifest(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    source_dir = Path(args.source_dir)
    trace_manifest = Path(args.trace_manifest)
    run_dir = Path(args.run_dir)
    manifest_dir = run_dir / "manifests"
    plan_json = run_dir / "plan.json"
    tasks_tsv = run_dir / "tasks.tsv"

    rows = load_manifest_rows(trace_manifest)
    fieldnames = list(rows[0].keys())
    by_family: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        family = (row.get("trace_family") or "").strip()
        if family:
            by_family[family].append(row)

    done_by_family, shard_counts = discover_unit_state(source_dir)
    tasks: list[dict[str, object]] = []
    summary: dict[str, list[str]] = {"complete": [], "partial": [], "missing": []}

    for family in EXPECTED_FAMILIES:
        family_rows = by_family.get(family, [])
        if not family_rows:
            raise SystemExit(f"Family is missing from trace manifest: {family}")
        for capacity in EXPECTED_CAPACITIES:
            cap_text = str(capacity)
            state: str
            if cap_text in done_by_family[family]:
                state = "complete"
            elif shard_counts[(family, cap_text)] > 0:
                state = "partial"
            else:
                state = "missing"
            summary[state].append(f"{family}:cap{cap_text}")
            if state == "complete":
                continue
            unit_manifest = manifest_dir / f"{family}__cap{cap_text}.csv"
            write_unit_manifest(unit_manifest, family_rows, fieldnames)
            tasks.append(
                {
                    "family": family,
                    "capacity": capacity,
                    "state": state,
                    "trace_count": len(family_rows),
                    "existing_shards": shard_counts[(family, cap_text)],
                    "unit_manifest": str(unit_manifest),
                }
            )

    run_dir.mkdir(parents=True, exist_ok=True)
    with tasks_tsv.open("w", encoding="utf-8", newline="") as handle:
        for task in tasks:
            handle.write(
                "\t".join(
                    [
                        str(task["family"]),
                        str(task["capacity"]),
                        str(task["state"]),
                        str(task["trace_count"]),
                        str(task["existing_shards"]),
                        str(task["unit_manifest"]),
                    ]
                )
                + "\n"
            )

    payload = {
        "source_dir": str(source_dir),
        "trace_manifest": str(trace_manifest),
        "task_count": len(tasks),
        "tasks": tasks,
        "summary": summary,
    }
    plan_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"run_dir: {run_dir}")
    print(f"tasks_file: {tasks_tsv}")
    print(f"task_count: {len(tasks)}")
    print("complete units:")
    for item in summary["complete"]:
        print(f"  {item}")
    print("resume units:")
    for task in tasks:
        print(
            "  "
            f"{task['family']}:cap{task['capacity']}:state={task['state']}:"
            f"existing_shards={task['existing_shards']}:manifest={task['unit_manifest']}"
        )


if __name__ == "__main__":
    main()
