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
    from lafc_evict_dataset.real_release_build import build_real_release, dry_run_real_release

    parser = argparse.ArgumentParser(
        description=(
            "Build a memory-safe real LAFC-Evict public release from an existing candidate-row manifest. "
            "Defaults to dry-run; pass --overwrite to materialize release artifacts."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input-manifest", required=True, help="Path to the source candidate-row manifest.json")
    parser.add_argument("--family-selection", required=True, help="Path to selected/excluded families JSON")
    parser.add_argument("--output-dir", required=True, help="Release output directory")
    parser.add_argument("--dataset-id", default="lafc-evict-v0.1-open", help="Release identifier")
    parser.add_argument("--dry-run", action="store_true", help="Scan metadata and estimate the build without writing output")
    parser.add_argument("--overwrite", action="store_true", help="Materialize the release artifacts")
    parser.add_argument("--skip-disk-space-check", action="store_true", help="Skip the conservative free-disk-space guard")
    parser.add_argument("--pairwise-sample", action="store_true", help="Emit a capped pairwise sample parquet")
    parser.add_argument("--max-pairwise-rows", type=int, default=1_000_000, help="Maximum pairwise sample rows")
    parser.add_argument("--max-pairs-per-decision", type=int, default=8, help="Maximum pairs per sampled decision")
    parser.add_argument("--pairwise-seed", type=int, default=7, help="Seed used to sample decisions for pairwise rows")
    args = parser.parse_args()

    building = args.overwrite and not args.dry_run
    dry_run = not building

    try:
        if dry_run:
            payload = dry_run_real_release(
                input_manifest=args.input_manifest,
                family_selection=args.family_selection,
                output_dir=args.output_dir,
                dataset_id=args.dataset_id,
                skip_disk_space_check=args.skip_disk_space_check,
                pairwise_sample=args.pairwise_sample,
            )
            print(json.dumps(payload, indent=2))
            return

        result = build_real_release(
            input_manifest=args.input_manifest,
            family_selection=args.family_selection,
            output_dir=args.output_dir,
            dataset_id=args.dataset_id,
            repo_root=ROOT,
            dry_run=False,
            overwrite=True,
            skip_disk_space_check=args.skip_disk_space_check,
            pairwise_sample=args.pairwise_sample,
            max_pairwise_rows=args.max_pairwise_rows,
            max_pairs_per_decision=args.max_pairs_per_decision,
            pairwise_seed=args.pairwise_seed,
        )
        print(
            json.dumps(
                {
                    "release_root": str(result.release_root),
                    "dataset_id": result.dataset_id,
                    "selected_families": list(result.selected_families),
                    "excluded_families": list(result.excluded_families),
                    "candidate_row_count": result.candidate_row_count,
                    "decision_row_count": result.decision_row_count,
                    "pairwise_sample_row_count": result.pairwise_sample_row_count,
                    "total_bytes": result.total_bytes,
                    "manifest_path": str(result.manifest_path),
                },
                indent=2,
            )
        )
    except Exception as exc:
        parser.exit(1, f"Error building real release: {exc}\n")


if __name__ == "__main__":
    main()
