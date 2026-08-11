from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _parse_capacities(values: list[str] | None) -> tuple[int, ...]:
    if not values:
        from lafc_evict_dataset.preview import DEFAULT_CAPACITIES

        return DEFAULT_CAPACITIES
    capacities: list[int] = []
    for value in values:
        for part in value.split(","):
            part = part.strip()
            if part:
                capacities.append(int(part))
    return tuple(dict.fromkeys(capacities))


def main() -> None:
    from lafc_evict_dataset.preview import (
        DEFAULT_CROSS_FAMILY_ROOT,
        DEFAULT_OBJECTIVE_ROOT,
        DEFAULT_SHARDS_PER_CAPACITY,
        PREVIEW_DATASET_REPO,
        PREVIEW_RELEASE_NAME,
        PreviewBuildConfig,
        build_preview_release,
    )

    parser = argparse.ArgumentParser(
        description="Build the canonical local LAFC-Evict v0.2 real-data preview release.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT / "release" / PREVIEW_RELEASE_NAME)
    parser.add_argument("--cross-family-root", type=Path, default=DEFAULT_CROSS_FAMILY_ROOT)
    parser.add_argument("--objective-root", type=Path, default=DEFAULT_OBJECTIVE_ROOT)
    parser.add_argument("--cross-family-fold", default="brightkite")
    parser.add_argument("--objective-fold", default="brightkite")
    parser.add_argument("--capacity", action="append", help="Capacity to include; may be repeated or comma-separated.")
    parser.add_argument("--cross-family-rows-per-capacity", type=int, default=900_000)
    parser.add_argument("--objective-rows-per-capacity", type=int, default=700_000)
    parser.add_argument("--shards-per-capacity", type=int, default=DEFAULT_SHARDS_PER_CAPACITY)
    parser.add_argument("--dataset-repo", default=PREVIEW_DATASET_REPO)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    try:
        result = build_preview_release(
            PreviewBuildConfig(
                output_dir=args.output_dir.resolve(),
                repo_root=ROOT,
                objective_root=args.objective_root.resolve(),
                cross_family_root=args.cross_family_root.resolve(),
                objective_fold=args.objective_fold,
                cross_family_fold=args.cross_family_fold,
                capacities=_parse_capacities(args.capacity),
                objective_rows_per_capacity=args.objective_rows_per_capacity,
                cross_family_rows_per_capacity=args.cross_family_rows_per_capacity,
                shards_per_capacity=args.shards_per_capacity,
                dataset_repo=args.dataset_repo,
                overwrite=args.overwrite,
            )
        )
        print(
            json.dumps(
                {
                    "release_root": str(result.release_root),
                    "manifest_path": str(result.manifest_path),
                    "total_rows": result.total_rows,
                    "parquet_bytes": result.parquet_bytes,
                    "data_files": [str(path) for path in result.data_files],
                    "security_scan": result.security_scan,
                    "validation_errors": list(result.validation_errors),
                },
                indent=2,
            )
        )
    except Exception as exc:
        parser.exit(1, f"Error building v0.2 preview release: {exc}\n")


if __name__ == "__main__":
    main()
