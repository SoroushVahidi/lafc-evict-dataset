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
    from lafc_evict_dataset.real_release_migration_plan import (
        DEFAULT_CANDIDATE_SAMPLE_SIZE,
        plan_real_release_migration,
    )

    parser = argparse.ArgumentParser(
        description=(
            "Inspect an existing real release using manifest data, filesystem metadata, and a small Parquet "
            "schema sample, then print a migration plan without copying data or rebuilding artifacts."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--source-release-dir", required=True, help="Existing real release directory to inspect")
    parser.add_argument(
        "--candidate-sample-size",
        type=int,
        default=DEFAULT_CANDIDATE_SAMPLE_SIZE,
        help="How many candidate-row parquet partitions to sample for schema inspection",
    )
    parser.add_argument(
        "--suggested-output-dir",
        help="Optional output directory to use in the recommended future heavy command",
    )
    args = parser.parse_args()

    try:
        plan = plan_real_release_migration(
            args.source_release_dir,
            candidate_sample_size=args.candidate_sample_size,
            suggested_output_dir=args.suggested_output_dir,
        )
        print(json.dumps(plan.to_dict(), indent=2))
    except Exception as exc:
        parser.exit(1, f"Error planning real release migration: {exc}\n")


if __name__ == "__main__":
    main()
