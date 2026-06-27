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
    from lafc_evict_dataset.io import (
        ensure_clean_output_dir,
        ensure_parent,
        fail_if_output_exists,
        read_candidate_dataframe,
        sha256_file,
    )
    from lafc_evict_dataset.real_release import (
        dry_run_export_plan,
        filter_candidate_dataframe_by_family,
    )
    from lafc_evict_dataset.schema import CANONICAL_COLUMNS, DECISION_KEY_COLUMNS, normalize_split_value
    from lafc_evict_dataset.validation import validate_candidate_dataframe

    parser = argparse.ArgumentParser(
        description=(
            "Export generated LAFC-Evict candidate rows into release-ready Parquet partitions. "
            "Input must already be candidate rows; raw traces are not required."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input-path", required=True, help="Candidate row CSV/Parquet, shard directory, or manifest.json")
    parser.add_argument("--output-dir", required=True, help="Release output directory")
    parser.add_argument("--dataset-id", default="lafc-evict-v0.1-open", help="Release identifier written into release_manifest.json")
    parser.add_argument("--include-family", action="append", default=[], help="Trace family to include. Repeat for multiple families.")
    parser.add_argument("--exclude-family", action="append", default=[], help="Trace family to exclude. Repeat for multiple families.")
    parser.add_argument("--dry-run", action="store_true", help="Scan metadata and estimate the export without writing Parquet output.")
    parser.add_argument(
        "--allow-cross-split-duplicate-decision-ids",
        action="store_true",
        help="Allow the same decision_id to appear in multiple splits when explicitly documented.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing output directory and manifest.")
    args = parser.parse_args()

    try:
        include_families = set(args.include_family)
        exclude_families = set(args.exclude_family)
        if args.dry_run:
            print(
                json.dumps(
                    dry_run_export_plan(
                        args.input_path,
                        include_families=include_families,
                        exclude_families=exclude_families,
                    ),
                    indent=2,
                )
            )
            return

        output_dir = ensure_clean_output_dir(args.output_dir, overwrite=args.overwrite, kind="Output directory").resolve()
        candidate_root = output_dir / "candidate_rows"
        manifest_path = fail_if_output_exists(
            output_dir / "release_manifest.json",
            overwrite=args.overwrite,
            kind="Release manifest",
        )

        df = read_candidate_dataframe(args.input_path)
        df = filter_candidate_dataframe_by_family(
            df,
            include_families=include_families,
            exclude_families=exclude_families,
        )
        if df.empty:
            raise ValueError("Family filters excluded every candidate row. Adjust --include-family/--exclude-family.")
        df = df[CANONICAL_COLUMNS].copy()
        df["split"] = df["split"].map(normalize_split_value)
        df = df.sort_values([*DECISION_KEY_COLUMNS, "candidate_page_id"]).reset_index(drop=True)

        errors = validate_candidate_dataframe(
            df,
            allow_cross_split_duplicate_decision_ids=args.allow_cross_split_duplicate_decision_ids,
        )
        if errors:
            raise ValueError("\n".join(errors))

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
            if out_file.exists() and not args.overwrite:
                raise FileExistsError(
                    f"Partition output already exists at {out_file}. Pass --overwrite to replace files."
                )
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
            "decision_count": int(df[DECISION_KEY_COLUMNS].drop_duplicates().shape[0]),
            "columns": CANONICAL_COLUMNS,
            "partitions": partition_cols,
            "selected_families": sorted(df["trace_family"].astype(str).unique().tolist()),
            "excluded_families": sorted(exclude_families),
            "files": file_entries,
        }
        ensure_parent(manifest_path).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(json.dumps(manifest, indent=2))
    except Exception as exc:
        parser.exit(1, f"Error exporting LAFC-Evict release: {exc}\n")


if __name__ == "__main__":
    main()
