from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from lafc_evict_dataset.validation import validate_candidate_file

    parser = argparse.ArgumentParser(
        description=(
            "Validate canonical LAFC-Evict candidate rows. "
            "Checks required columns, split values, label presence/numericity, "
            "decision grouping consistency, and cross-split decision ID reuse."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input-path", required=True, help="Candidate row CSV/Parquet, shard directory, or manifest.json")
    parser.add_argument(
        "--allow-cross-split-duplicate-decision-ids",
        action="store_true",
        help="Allow the same decision_id to appear in multiple splits when explicitly documented.",
    )
    args = parser.parse_args()

    errors = validate_candidate_file(
        args.input_path,
        allow_cross_split_duplicate_decision_ids=args.allow_cross_split_duplicate_decision_ids,
    )
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise SystemExit(1)
    print("Schema validation passed.")


if __name__ == "__main__":
    main()
