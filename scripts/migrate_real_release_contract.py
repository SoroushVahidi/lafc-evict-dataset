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
    from lafc_evict_dataset.real_release_migration import migrate_real_release_contract

    parser = argparse.ArgumentParser(
        description=(
            "Migrate an existing pre-fix real LAFC-Evict release directory onto the current release contract "
            "without rebuilding candidate rows from the original CSV shards."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--source-release-dir", required=True, help="Existing real release directory to migrate")
    parser.add_argument("--output-dir", required=True, help="New output directory for the migrated release")
    parser.add_argument(
        "--staging-mode",
        choices=("auto", "hardlink", "copy"),
        default="auto",
        help="How to stage reused files into the migrated release",
    )
    parser.add_argument(
        "--regenerate-pairwise-sample",
        action="store_true",
        help="Regenerate pairwise_sample from candidate rows instead of reusing a compatible existing file",
    )
    parser.add_argument("--duckdb-threads", type=int, default=2, help="DuckDB thread limit")
    parser.add_argument("--duckdb-memory-limit", default="8GB", help="DuckDB memory limit")
    parser.add_argument("--duckdb-temp-dir", default=".duckdb_tmp", help="DuckDB spill/temp directory")
    args = parser.parse_args()

    try:
        result = migrate_real_release_contract(
            source_release_dir=args.source_release_dir,
            output_dir=args.output_dir,
            repo_root=ROOT,
            staging_mode=args.staging_mode,
            reuse_existing_pairwise_sample=not args.regenerate_pairwise_sample,
            duckdb_threads=args.duckdb_threads,
            duckdb_memory_limit=args.duckdb_memory_limit,
            duckdb_temp_dir=args.duckdb_temp_dir,
        )
        print(
            json.dumps(
                {
                    "release_root": str(result.release_root),
                    "dataset_id": result.dataset_id,
                    "source_release_root": str(result.source_release_root),
                    "candidate_row_count": result.candidate_row_count,
                    "decision_row_count": result.decision_row_count,
                    "pairwise_sample_row_count": result.pairwise_sample_row_count,
                    "candidate_rows_reused": result.candidate_rows_reused,
                    "candidate_rows_staging_mode": result.candidate_rows_staging_mode,
                    "pairwise_sample_reused": result.pairwise_sample_reused,
                    "pairwise_sample_regenerated": result.pairwise_sample_regenerated,
                    "pairwise_sample_staging_mode": result.pairwise_sample_staging_mode,
                    "manifest_path": str(result.manifest_path),
                },
                indent=2,
            )
        )
    except Exception as exc:
        parser.exit(1, f"Error migrating real release contract: {exc}\n")


if __name__ == "__main__":
    main()
