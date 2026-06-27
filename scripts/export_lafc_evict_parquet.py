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
    from lafc_evict_dataset.io import ensure_parent, read_candidate_dataframe, sha256_file
    from lafc_evict_dataset.schema import CANONICAL_COLUMNS, normalize_split_value
    from lafc_evict_dataset.validation import validate_candidate_dataframe

    parser = argparse.ArgumentParser(description="Export LAFC-Evict candidate rows to release-ready Parquet partitions.")
    parser.add_argument("--input-path", required=True, help="Candidate row CSV/Parquet, shard directory, or manifest.json")
    parser.add_argument("--output-dir", required=True, help="Release output directory")
    parser.add_argument("--dataset-id", default="lafc-evict-v0.1-open")
    parser.add_argument("--allow-cross-split-duplicate-decision-ids", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    candidate_root = output_dir / "candidate_rows"
    manifest_path = output_dir / "release_manifest.json"

    df = read_candidate_dataframe(args.input_path)
    df = df[CANONICAL_COLUMNS].copy()
    df["split"] = df["split"].map(normalize_split_value)

    errors = validate_candidate_dataframe(
        df,
        allow_cross_split_duplicate_decision_ids=args.allow_cross_split_duplicate_decision_ids,
    )
    if errors:
        raise SystemExit("\n".join(errors))

    candidate_root.mkdir(parents=True, exist_ok=True)
    file_entries: list[dict[str, object]] = []
    partition_cols = ["split", "trace_family", "capacity", "horizon"]

    for values, group in df.groupby(partition_cols, dropna=False, sort=True):
        split, trace_family, capacity, horizon = values
        partition_dir = (
            candidate_root
            / f"split={split}"
            / f"trace_family={trace_family}"
            / f"capacity={int(capacity)}"
            / f"horizon={int(horizon)}"
        )
        partition_dir.mkdir(parents=True, exist_ok=True)
        out_file = partition_dir / "candidate_rows.parquet"
        group.to_parquet(out_file, index=False)
        file_entries.append(
            {
                "path": str(out_file.relative_to(output_dir)),
                "row_count": int(len(group)),
                "sha256": sha256_file(out_file),
                "split": split,
                "trace_family": trace_family,
                "capacity": int(capacity),
                "horizon": int(horizon),
            }
        )

    manifest = {
        "dataset_id": args.dataset_id,
        "format": "lafc-evict-candidate-parquet-v1",
        "row_count": int(len(df)),
        "decision_count": int(df[["trace_name", "capacity", "horizon", "decision_id"]].drop_duplicates().shape[0]),
        "columns": CANONICAL_COLUMNS,
        "partitions": partition_cols,
        "files": file_entries,
    }
    ensure_parent(manifest_path).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
