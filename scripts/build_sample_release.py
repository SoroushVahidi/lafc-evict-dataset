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
    from lafc_evict_dataset.release import build_sample_release

    parser = argparse.ArgumentParser(
        description=(
            "Build a fully synthetic LAFC-Evict sample release dry run from existing candidate rows. "
            "This workflow uses only synthetic example rows and does not require raw traces."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input",
        default="examples/tiny_candidate_rows.csv",
        help="Synthetic candidate-row CSV used to build the sample release.",
    )
    parser.add_argument(
        "--output-dir",
        default="release/lafc-evict-sample-v0.1",
        help="Output directory for the generated dry-run release package.",
    )
    parser.add_argument("--include-ties", action="store_true", help="Include pairwise tie rows in the pairwise view.")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing output directory.")
    args = parser.parse_args()

    try:
        result = build_sample_release(
            input_path=args.input,
            output_dir=args.output_dir,
            overwrite=args.overwrite,
            include_ties=args.include_ties,
        )
        print(
            json.dumps(
                {
                    "release_root": str(result.release_root),
                    "candidate_row_count": result.candidate_row_count,
                    "decision_row_count": result.decision_row_count,
                    "pairwise_row_count": result.pairwise_row_count,
                    "generated_files": list(result.generated_files),
                },
                indent=2,
            )
        )
    except Exception as exc:
        parser.exit(1, f"Error building synthetic sample release: {exc}\n")


if __name__ == "__main__":
    main()
