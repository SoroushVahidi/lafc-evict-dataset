from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from lafc_evict_dataset.release_v0_3 import (
        DEFAULT_V0_3_CAPACITIES,
        DEFAULT_V0_3_CROSS_FAMILY_FOLD,
        DEFAULT_V0_3_OBJECTIVE_FOLD,
        V0_3_RELEASE_NAME,
        V03BuildConfig,
        build_v0_3_candidate_release,
    )
    from lafc_evict_dataset.preview import DEFAULT_CROSS_FAMILY_ROOT, DEFAULT_OBJECTIVE_ROOT

    parser = argparse.ArgumentParser(
        description=(
            "Build the LOCAL, UNPUBLISHED LAFC-Evict v0.3 wiki2018-only expanded candidate release. "
            "Reads only from evict_value_v1_cross_family_v1 and supervision_objective_ablation_v1 "
            "(same sources v0.2 used); does not upload or publish anything."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT / "release" / V0_3_RELEASE_NAME)
    parser.add_argument("--cross-family-root", type=Path, default=DEFAULT_CROSS_FAMILY_ROOT)
    parser.add_argument("--objective-root", type=Path, default=DEFAULT_OBJECTIVE_ROOT)
    parser.add_argument("--cross-family-fold", default=DEFAULT_V0_3_CROSS_FAMILY_FOLD)
    parser.add_argument("--objective-fold", default=DEFAULT_V0_3_OBJECTIVE_FOLD)
    parser.add_argument("--capacity", action="append", help="Capacity to include; may be repeated or comma-separated.")
    parser.add_argument("--dataset-repo", default="SoroushVahidi/lafc-evict")
    parser.add_argument("--v0-2-manifest", type=Path, default=ROOT / "release" / "lafc-evict-v0.2-preview" / "metadata" / "release_manifest.json")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if args.capacity:
        capacities: list[int] = []
        for value in args.capacity:
            for part in value.split(","):
                part = part.strip()
                if part:
                    capacities.append(int(part))
        capacity_tuple = tuple(dict.fromkeys(capacities))
    else:
        capacity_tuple = DEFAULT_V0_3_CAPACITIES

    v0_2_rows = None
    if args.v0_2_manifest.exists():
        v0_2_rows = json.loads(args.v0_2_manifest.read_text(encoding="utf-8")).get("row_counts", {}).get("total_rows")

    try:
        result = build_v0_3_candidate_release(
            V03BuildConfig(
                output_dir=args.output_dir.resolve(),
                repo_root=ROOT,
                objective_root=args.objective_root,
                cross_family_root=args.cross_family_root,
                objective_fold=args.objective_fold,
                cross_family_fold=args.cross_family_fold,
                capacities=capacity_tuple,
                dataset_repo=args.dataset_repo,
                overwrite=args.overwrite,
            ),
            v0_2_rows=v0_2_rows,
        )
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print(f"release_root: {result.release_root}")
    print(f"total_rows: {result.total_rows}")
    print(f"parquet_bytes: {result.parquet_bytes}")
    print(f"validation_errors: {len(result.validation_errors)}")
    for error in result.validation_errors:
        print(f"  - {error}")
    print(f"security_scan_passed: {result.security_scan.get('passed')}")
    for key, scan in result.leakage_scan.items():
        print(f"leakage[{key}]: passed={scan.get('passed')} raw_population={scan.get('raw_value_population')}")
    if result.validation_errors or not result.security_scan.get("passed"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
