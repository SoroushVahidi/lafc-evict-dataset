#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

import pandas as pd

from _baseline_common import (
    DEFAULT_BATCH_SIZE,
    available_feature_columns,
    build_file_budget,
    budget_exhausted,
    candidate_file_inventory,
    candidate_schema_summary,
    checkpoint_path,
    consume_budget,
    current_git_commit,
    current_timestamp_utc,
    detected_validation_status,
    duplicate_partition_keys,
    ensure_output_dir_safe,
    guard_output_path,
    iter_candidate_batches,
    load_checkpoint,
    load_manifest,
    parquet_schema_names,
    release_identity,
    release_summary,
    remove_checkpoint,
    repo_relative,
    require_columns,
    save_checkpoint,
    write_json,
)
from lafc_evict_dataset.schema import FEATURE_COLUMNS as ALL_CANDIDATE_FEATURE_COLUMNS

PAIRWISE_SHARED_COLUMNS = [
    "decision_id",
    "capacity",
    "horizon",
    "split",
    "trace_family",
    "trace_name",
    "candidate_a_page_id",
    "candidate_b_page_id",
    "y_loss_a",
    "y_loss_b",
    "y_loss_diff_a_minus_b",
    "label_a_better",
    "label_b_better",
    "is_tie",
]

CORE_FEATURE_COLUMNS = [
    "candidate_lru_score",
    "candidate_predictor_score",
    "candidate_recency_rank",
    "candidate_age_norm",
    "candidate_is_lru_victim",
    "candidate_is_predictor_victim",
]

# Everything else in the candidate feature schema (bucket/confidence fields, recent
# request/hit rates, and the remaining gap/disagreement features) is included by default
# whenever available, so linear_score_pairwise can reuse the already-trained
# linear_regression_y_loss.json model as-is instead of a partial-feature approximation.
OPTIONAL_FEATURE_COLUMNS = [column for column in ALL_CANDIDATE_FEATURE_COLUMNS if column not in CORE_FEATURE_COLUMNS]

# Full robust join key, per the pairwise-plan contract note: partition identity
# columns plus the candidate page id. Dropping any of these risks silently
# joining a candidate row from the wrong (capacity, horizon) simulation run.
PARTITION_KEY_COLUMNS = ["split", "trace_family", "capacity", "horizon"]
WITHIN_PARTITION_KEY_COLUMNS = ["trace_name", "decision_id", "candidate_page_id"]
FULL_JOIN_KEY_COLUMNS = [*PARTITION_KEY_COLUMNS, *WITHIN_PARTITION_KEY_COLUMNS]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Augment the shipped bounded LAFC-Evict pairwise sample with candidate-side "
            "A/B feature columns by joining back to candidate rows. Never regenerates the "
            "full quadratic pairwise view and never rebuilds the release."
        )
    )
    parser.add_argument(
        "--release-root",
        default="release/lafc-evict-v0.1-open-current-contract-preserved",
        help="Repo-relative or absolute preserved release path.",
    )
    parser.add_argument(
        "--pairwise-path",
        default="data/pairwise_sample/pairwise_sample.parquet",
        help="Pairwise sample path relative to the release root.",
    )
    parser.add_argument(
        "--output-dir",
        default="paper/sigmod2027/results/baselines/pairwise",
        help="Directory for plan, checkpoint, and result outputs.",
    )
    parser.add_argument(
        "--mode",
        choices=["plan", "run"],
        default="plan",
        help="Plan mode inspects schema only; run mode streams candidate partitions referenced by the pairwise sample.",
    )
    parser.add_argument(
        "--features",
        nargs="*",
        default=None,
        help="Optional explicit candidate feature list. Defaults to the core features plus any available optional features.",
    )
    parser.add_argument("--max-files", type=int, default=None, help="Process at most this many candidate partitions per invocation.")
    parser.add_argument("--resume", action="store_true", help="Resume from an existing checkpoint.")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing outputs or checkpoints.")
    parser.add_argument(
        "--allow-missing-joins",
        action="store_true",
        help="Do not fail if some pairwise rows cannot be joined to candidate-side features (not recommended).",
    )
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Candidate parquet read batch size.")
    return parser.parse_args(argv)


def output_file(output_dir: Path) -> Path:
    return output_dir / "augmented_pairwise_sample.parquet"


def plan_file(output_dir: Path) -> Path:
    return output_dir / "augmented_pairwise_sample_plan.json"


def shard_dir_path(output_dir: Path, stem: str) -> Path:
    return output_dir / f".{stem}.shards"


def resolve_feature_columns(available_columns: list[str], requested: list[str] | None) -> list[str]:
    missing_core = require_columns(available_columns, CORE_FEATURE_COLUMNS)
    if missing_core:
        raise ValueError(f"Candidate rows are missing required core feature columns: {missing_core}")
    if requested is not None:
        return available_feature_columns(available_columns, requested)
    optional_present = [column for column in OPTIONAL_FEATURE_COLUMNS if column in available_columns]
    return [*CORE_FEATURE_COLUMNS, *optional_present]


def reset_augmented_outputs(
    *,
    output_path: Path,
    checkpoint: Path,
    shard_dir: Path,
    overwrite: bool,
    resume: bool,
) -> None:
    if overwrite and resume:
        raise ValueError("Use either --overwrite or --resume, not both")

    existing_output = output_path.exists()
    existing_checkpoint = checkpoint.exists()

    if overwrite:
        if existing_output:
            output_path.unlink()
        if existing_checkpoint:
            checkpoint.unlink()
        if shard_dir.exists():
            shutil.rmtree(shard_dir)
        return

    if resume:
        if existing_output and not existing_checkpoint:
            raise ValueError(
                "Refusing to resume because the final output already exists and no checkpoint remains. "
                "Use --overwrite to replace it."
            )
        return

    if existing_output or existing_checkpoint or shard_dir.exists():
        raise ValueError(
            "Output path or checkpoint already exists. Use --overwrite to replace or --resume to continue."
        )


def build_needed_keys(pairwise_df: pd.DataFrame) -> dict[tuple[str, str, int, int], set[tuple[str, str, str]]]:
    needed: dict[tuple[str, str, int, int], set[tuple[str, str, str]]] = {}
    for page_column in ("candidate_a_page_id", "candidate_b_page_id"):
        columns = [*PARTITION_KEY_COLUMNS, "trace_name", "decision_id", page_column]
        subset = pairwise_df[columns].drop_duplicates()
        for split, trace_family, capacity, horizon, trace_name, decision_id, page_id in subset.itertuples(
            index=False, name=None
        ):
            partition_key = (str(split), str(trace_family), int(capacity), int(horizon))
            needed.setdefault(partition_key, set()).add((str(trace_name), str(decision_id), str(page_id)))
    return needed


def relevant_inventory(
    inventory: list[dict[str, object]],
    needed: dict[tuple[str, str, int, int], set[tuple[str, str, str]]],
) -> list[dict[str, object]]:
    relevant = []
    for entry in inventory:
        key = (str(entry["split"]), str(entry["trace_family"]), int(entry["capacity"]), int(entry["horizon"]))
        if key in needed:
            relevant.append(entry)
    return relevant


def extract_matches_for_partition(
    path: Path,
    entry: dict[str, object],
    within_keys: set[tuple[str, str, str]],
    feature_columns: list[str],
    batch_size: int,
) -> pd.DataFrame:
    columns = [*WITHIN_PARTITION_KEY_COLUMNS, *feature_columns]
    within_key_strings = {"␟".join(key) for key in within_keys}
    matched_frames: list[pd.DataFrame] = []
    for batch in iter_candidate_batches(path, columns=columns, batch_size=batch_size):
        key_series = (
            batch["trace_name"].astype(str)
            + "␟"
            + batch["decision_id"].astype(str)
            + "␟"
            + batch["candidate_page_id"].astype(str)
        )
        mask = key_series.isin(within_key_strings)
        if mask.any():
            matched_frames.append(batch.loc[mask].copy())
    if matched_frames:
        matched = pd.concat(matched_frames, ignore_index=True)
    else:
        matched = pd.DataFrame(columns=columns)
    matched["split"] = str(entry["split"])
    matched["trace_family"] = str(entry["trace_family"])
    matched["capacity"] = int(entry["capacity"])
    matched["horizon"] = int(entry["horizon"])
    return matched


def merge_side(pairwise_df: pd.DataFrame, lookup_df: pd.DataFrame, side: str, feature_columns: list[str]) -> pd.DataFrame:
    page_column = f"candidate_{side}_page_id"
    rename_map = {column: f"{column}_{side}" for column in feature_columns}
    lookup_renamed = lookup_df.rename(columns={"candidate_page_id": page_column, **rename_map})
    lookup_renamed = lookup_renamed[[*PARTITION_KEY_COLUMNS, "trace_name", "decision_id", page_column, *rename_map.values()]]
    return pairwise_df.merge(
        lookup_renamed,
        on=[*PARTITION_KEY_COLUMNS, "trace_name", "decision_id", page_column],
        how="left",
        validate="many_to_one",
    )


def plan_payload(
    *,
    release_root: Path,
    manifest: dict[str, object],
    pairwise_path: Path,
    pairwise_schema: list[str],
    candidate_schema: dict[str, object],
    feature_columns: list[str],
    output_path: Path,
) -> dict[str, object]:
    missing_shared = require_columns(pairwise_schema, PAIRWISE_SHARED_COLUMNS)
    return {
        "task": "build_augmented_pairwise_sample",
        "status": "dry_run_checked",
        "mode": "plan",
        "timestamp_utc": current_timestamp_utc(),
        "git_commit": current_git_commit(),
        "release_root": str(release_root),
        "release_identity": release_identity(manifest),
        "input_view": "pairwise_sample_joined_to_candidate_rows",
        "input_path": repo_relative(pairwise_path),
        "candidate_input_path": repo_relative(release_root / "data" / "candidate_rows"),
        "full_validation_status": detected_validation_status(release_root),
        "requires_large_memory_machine": True,
        "safe_for_anonymous_manuscript": False,
        "pairwise_schema_check": {
            "required_shared_columns": PAIRWISE_SHARED_COLUMNS,
            "available_columns": pairwise_schema,
            "missing_required_columns": missing_shared,
        },
        "candidate_schema_check": candidate_schema,
        "join_key_columns": FULL_JOIN_KEY_COLUMNS,
        "feature_columns": feature_columns,
        "planned_output_file": repo_relative(output_path),
        "release_summary": release_summary(manifest),
        "notes": [
            "Only the capped shipped pairwise sample is augmented; the full quadratic pairwise view is never generated.",
            "Run mode streams candidate parquet partitions in batches and only retains rows referenced by the pairwise sample.",
            "The full 277M-row candidate release is never loaded into memory at once.",
        ],
        "limitations": [
            "Candidate partitions not referenced by any pairwise-sample row are skipped entirely (partition pruning).",
        ],
    }


def run(args: argparse.Namespace) -> dict[str, object] | None:
    release_root = Path(args.release_root)
    output_dir = ensure_output_dir_safe(Path(args.output_dir), release_root)
    manifest = load_manifest(release_root)
    pairwise_path = release_root / args.pairwise_path
    pairwise_schema = parquet_schema_names(pairwise_path)
    missing_shared = require_columns(pairwise_schema, PAIRWISE_SHARED_COLUMNS)
    if missing_shared:
        raise ValueError(f"Pairwise sample is missing required shared columns: {missing_shared}")

    candidate_schema = candidate_schema_summary(release_root, manifest)
    feature_columns = resolve_feature_columns(candidate_schema["available_columns"], args.features)

    output_path = guard_output_path(output_file(output_dir), release_root)

    if args.mode == "plan":
        payload = plan_payload(
            release_root=release_root,
            manifest=manifest,
            pairwise_path=pairwise_path,
            pairwise_schema=pairwise_schema,
            candidate_schema=candidate_schema,
            feature_columns=feature_columns,
            output_path=output_path,
        )
        write_json(plan_file(output_dir), payload)
        print(f"Wrote {plan_file(output_dir)}")
        return None

    checkpoint = guard_output_path(checkpoint_path(output_dir, "augmented_pairwise_sample"), release_root)
    shard_dir = guard_output_path(shard_dir_path(output_dir, "augmented_pairwise_sample"), release_root)
    reset_augmented_outputs(
        output_path=output_path,
        checkpoint=checkpoint,
        shard_dir=shard_dir,
        overwrite=args.overwrite,
        resume=args.resume,
    )

    pairwise_df = pd.read_parquet(pairwise_path, columns=PAIRWISE_SHARED_COLUMNS)
    needed = build_needed_keys(pairwise_df)

    inventory = candidate_file_inventory(release_root, manifest)
    duplicates = duplicate_partition_keys(inventory)
    if duplicates:
        rendered = ", ".join(str(key) for key in duplicates)
        raise ValueError(f"Duplicate candidate partitions found in manifest: {rendered}")
    relevant = relevant_inventory(inventory, needed)

    checkpoint_payload = load_checkpoint(checkpoint, missing_ok=True) if args.resume else None
    next_index = int(checkpoint_payload.get("next_file_index", 0)) if checkpoint_payload else 0

    shard_dir.mkdir(parents=True, exist_ok=True)
    budget = build_file_budget(args.max_files)
    for index in range(next_index, len(relevant)):
        if budget_exhausted(budget):
            break
        entry = relevant[index]
        partition_key = (str(entry["split"]), str(entry["trace_family"]), int(entry["capacity"]), int(entry["horizon"]))
        within_keys = needed.get(partition_key, set())
        matched = extract_matches_for_partition(entry["path"], entry, within_keys, feature_columns, args.batch_size)
        matched.to_parquet(shard_dir / f"part-{index:04d}.parquet", index=False)
        save_checkpoint(checkpoint, {"task": "build_augmented_pairwise_sample", "next_file_index": index + 1})
        budget = consume_budget(budget)

    checkpoint_payload = load_checkpoint(checkpoint, missing_ok=True)
    processed = int(checkpoint_payload.get("next_file_index", 0)) if checkpoint_payload else 0
    if processed < len(relevant):
        print(
            json.dumps(
                {
                    "task": "build_augmented_pairwise_sample",
                    "status": "partial",
                    "candidate_partitions_total": len(relevant),
                    "candidate_partitions_processed": processed,
                    "checkpoint_path": repo_relative(checkpoint),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return None

    shard_files = sorted(shard_dir.glob("part-*.parquet"))
    if shard_files:
        lookup_df = pd.concat([pd.read_parquet(path) for path in shard_files], ignore_index=True)
    else:
        lookup_df = pd.DataFrame(columns=[*FULL_JOIN_KEY_COLUMNS, *feature_columns])
    lookup_df = lookup_df.drop_duplicates(subset=FULL_JOIN_KEY_COLUMNS, keep="first")

    merged = pairwise_df
    for side in ("a", "b"):
        merged = merge_side(merged, lookup_df, side, feature_columns)

    if len(merged) != len(pairwise_df):
        raise ValueError(
            "Row count mismatch after joining candidate-side features: "
            f"input pairwise rows={len(pairwise_df)}, output rows={len(merged)}. "
            "This indicates the candidate-feature join produced duplicate or dropped rows."
        )

    probe_columns = [f"{column}_a" for column in CORE_FEATURE_COLUMNS] + [f"{column}_b" for column in CORE_FEATURE_COLUMNS]
    missing_mask = merged[probe_columns].isna().any(axis=1)
    missing_count = int(missing_mask.sum())
    if missing_count and not args.allow_missing_joins:
        sample_columns = [
            "decision_id",
            "trace_name",
            "split",
            "trace_family",
            "capacity",
            "horizon",
            "candidate_a_page_id",
            "candidate_b_page_id",
        ]
        sample = merged.loc[missing_mask, sample_columns].head(20)
        raise ValueError(
            f"{missing_count} of {len(merged)} pairwise rows failed to join required candidate-side core features. "
            "Sample rows with missing joins:\n" + sample.to_string(index=False)
        )

    output_columns = list(PAIRWISE_SHARED_COLUMNS)
    for column in feature_columns:
        output_columns.append(f"{column}_a")
        output_columns.append(f"{column}_b")
    final_df = merged[output_columns]

    tmp_path = output_path.with_name(output_path.name + ".tmp")
    final_df.to_parquet(tmp_path, index=False)
    os.replace(tmp_path, output_path)

    shutil.rmtree(shard_dir, ignore_errors=True)
    remove_checkpoint(checkpoint)

    summary = {
        "task": "build_augmented_pairwise_sample",
        "status": "available",
        "mode": "run",
        "timestamp_utc": current_timestamp_utc(),
        "git_commit": current_git_commit(),
        "release_root": str(release_root),
        "release_identity": release_identity(manifest),
        "input_path": repo_relative(pairwise_path),
        "candidate_input_path": repo_relative(release_root / "data" / "candidate_rows"),
        "full_validation_status": detected_validation_status(release_root),
        "requires_large_memory_machine": True,
        "safe_for_anonymous_manuscript": True,
        "join_key_columns": FULL_JOIN_KEY_COLUMNS,
        "feature_columns": feature_columns,
        "candidate_partitions_scanned": len(relevant),
        "input_rows": int(len(pairwise_df)),
        "output_rows": int(len(final_df)),
        "missing_join_count": missing_count,
        "output_file": repo_relative(output_path),
        "release_summary": release_summary(manifest),
        "notes": [
            "Only the capped shipped pairwise sample is augmented; the full quadratic pairwise view is never generated.",
            "Candidate parquet partitions were streamed in batches; only rows referenced by the pairwise sample were retained.",
        ],
        "limitations": [
            "Feature values reflect the candidate row at the time the release was built; no re-simulation is performed.",
        ],
    }
    write_json_summary = plan_file(output_dir).with_name("augmented_pairwise_sample_report.json")
    write_json(write_json_summary, summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main(argv: list[str] | None = None) -> None:
    run(parse_args(argv))


if __name__ == "__main__":
    main()
