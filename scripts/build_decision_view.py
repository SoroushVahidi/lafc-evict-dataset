from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from lafc_evict_dataset.io import read_candidate_dataframe, write_table
    from lafc_evict_dataset.views import build_decision_view

    parser = argparse.ArgumentParser(description="Build one-row-per-decision LAFC-Evict benchmark view.")
    parser.add_argument("--input-path", required=True, help="Candidate row CSV/Parquet, shard directory, or manifest.json")
    parser.add_argument("--output-path", required=True, help="Output .csv or .parquet file")
    args = parser.parse_args()

    df = read_candidate_dataframe(args.input_path)
    decision_view = build_decision_view(df)
    path = write_table(decision_view, args.output_path)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
