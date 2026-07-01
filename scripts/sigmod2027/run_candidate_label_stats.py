#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from _baseline_common import (
    DEFAULT_GROUP_BY,
    RunningNumericSummary,
    build_file_budget,
    budget_exhausted,
    candidate_file_inventory,
    candidate_schema_summary,
    checkpoint_path,
    consume_budget,
    detected_validation_status,
    decode_group_key,
    encode_group_key,
    ensure_output_dir_safe,
    guard_output_path,
    iter_candidate_batches,
    current_git_commit,
    current_timestamp_utc,
    load_checkpoint,
    load_manifest,
    release_identity,
    release_summary,
    remove_checkpoint,
    repo_relative,
    require_columns,
    reset_outputs,
    save_checkpoint,
    write_csv,
    write_json,
)

TARGET_CHOICES = ("y_loss", "y_value", "both")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan or run resume-safe candidate-label statistics over LAFC-Evict candidate rows."
    )
    parser.add_argument(
        "--release-root",
        default="release/lafc-evict-v0.1-open-current-contract-preserved",
        help="Repo-relative or absolute preserved release path.",
    )
    parser.add_argument(
        "--output-dir",
        default="paper/sigmod2027/results/candidate_label_stats",
        help="Directory for plan, checkpoint, and result outputs.",
    )
    parser.add_argument(
        "--target",
        choices=TARGET_CHOICES,
        default="both",
        help="Candidate-label target to summarize.",
    )
    parser.add_argument(
        "--mode",
        choices=["plan", "run"],
        default="plan",
        help="Plan mode inspects metadata/schema only; run mode streams candidate rows.",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="Process at most this many candidate parquet files in one invocation.",
    )
    parser.add_argument("--resume", action="store_true", help="Resume from an existing checkpoint.")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing outputs or checkpoints.")
    parser.add_argument(
        "--group-by",
        nargs="*",
        default=list(DEFAULT_GROUP_BY),
        help="Grouping columns for breakdown rows.",
    )
    return parser.parse_args(argv)


def selected_targets(target: str) -> list[str]:
    return ["y_loss", "y_value"] if target == "both" else [target]


def summary_output_paths(output_dir: Path, targets: list[str]) -> dict[str, dict[str, Path]]:
    return {
        target: {
            "json": output_dir / f"{target}_summary.json",
            "csv": output_dir / f"{target}_summary.csv",
        }
        for target in targets
    }


def build_plan_payload(
    *,
    args: argparse.Namespace,
    manifest: dict[str, object],
    release_root: Path,
    schema_summary: dict[str, object],
    inventory: list[dict[str, object]],
    targets: list[str],
    outputs: dict[str, dict[str, Path]],
) -> dict[str, object]:
    available_columns = schema_summary["available_columns"]
    required = list(dict.fromkeys([*targets, *args.group_by]))
    missing = require_columns(available_columns, required)
    return {
        "task": "candidate_label_stats",
        "status": "dry_run_checked",
        "mode": "plan",
        "timestamp_utc": current_timestamp_utc(),
        "git_commit": current_git_commit(),
        "release_root": str(release_root),
        "release_identity": release_identity(manifest),
        "input_view": "candidate_rows",
        "input_path": repo_relative(release_root / "data" / "candidate_rows"),
        "full_validation_status": detected_validation_status(release_root),
        "requires_large_memory_machine": True,
        "safe_for_anonymous_manuscript": False,
        "targets": targets,
        "group_by": args.group_by,
        "schema_check": schema_summary,
        "missing_required_columns": missing,
        "candidate_partition_count": len(inventory),
        "candidate_files": [repo_relative(item["path"]) for item in inventory],
        "release_summary": release_summary(manifest),
        "planned_outputs": {
            target: {kind: repo_relative(path) for kind, path in paths.items()} for target, paths in outputs.items()
        },
        "checkpoint_path": repo_relative(checkpoint_path(Path(args.output_dir), "candidate_label_stats")),
        "notes": [
            "Plan mode inspects release metadata and one candidate partition schema only.",
            "Run mode streams candidate parquet files file-by-file without loading the full release into memory.",
        ],
        "limitations": [
            "Plan mode does not prove runtime or memory on the full preserved release.",
        ],
    }


def fresh_state(targets: list[str], group_by: list[str]) -> dict[str, object]:
    return {
        "stage": "run",
        "next_file_index": 0,
        "group_by": group_by,
        "targets": {
            target: {
                "overall": RunningNumericSummary().to_state(),
                "groups": {},
            }
            for target in targets
        },
    }


def load_state(checkpoint: dict[str, object], targets: list[str], group_by: list[str]) -> dict[str, object]:
    state = checkpoint.get("state")
    if not isinstance(state, dict):
        raise ValueError("Checkpoint is missing state")
    if state.get("group_by") != group_by:
        raise ValueError("Checkpoint group-by columns do not match current invocation")
    checkpoint_targets = state.get("targets", {})
    if sorted(checkpoint_targets.keys()) != sorted(targets):
        raise ValueError("Checkpoint targets do not match current invocation")
    return state


def update_state_for_batch(
    *,
    state: dict[str, object],
    batch,
    targets: list[str],
    group_by: list[str],
) -> None:
    group_keys = None
    if group_by:
        key_columns = [batch[column].astype(str).fillna("") for column in group_by]
        group_keys = key_columns[0]
        for series in key_columns[1:]:
            group_keys = group_keys + "\u241f" + series

    target_state = state["targets"]
    for target in targets:
        overall = RunningNumericSummary.from_state(target_state[target]["overall"])
        overall.update(batch[target].to_numpy(dtype=float))
        target_state[target]["overall"] = overall.to_state()

        groups = target_state[target]["groups"]
        if group_keys is None:
            continue
        grouped = batch.groupby(group_keys, sort=False, dropna=False)
        for key, frame in grouped:
            key_text = str(key)
            summary_payload = groups.get(key_text)
            summary = RunningNumericSummary.from_state(summary_payload) if isinstance(summary_payload, dict) else RunningNumericSummary()
            summary.update(frame[target].to_numpy(dtype=float))
            groups[key_text] = summary.to_state()


def build_target_payload(
    *,
    target: str,
    release_root: Path,
    manifest: dict[str, object],
    output_paths: dict[str, Path],
    state: dict[str, object],
    files_total: int,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    group_by = state["group_by"]
    target_state = state["targets"][target]
    overall = RunningNumericSummary.from_state(target_state["overall"])
    groups_payload = target_state["groups"]

    csv_rows: list[dict[str, object]] = []
    overall_summary = overall.to_summary_dict()
    csv_rows.append(
        {
            "target": target,
            "summary_scope": "overall",
            "count": overall_summary["count"],
            "missing_count": overall_summary["missing_count"],
            "total_rows_seen": overall_summary["total_rows_seen"],
            "min": overall_summary["min"],
            "max": overall_summary["max"],
            "mean": overall_summary["mean"],
            "std": overall_summary["std"],
            **overall_summary["quantiles"],
            "quantiles_approximate": overall_summary["quantiles_approximate"],
        }
    )

    grouped_summaries: list[dict[str, object]] = []
    for key in sorted(groups_payload):
        summary = RunningNumericSummary.from_state(groups_payload[key]).to_summary_dict()
        record = {
            **{column: value for column, value in zip(group_by, decode_group_key(key))},
            **summary,
        }
        grouped_summaries.append(record)
        csv_rows.append(
            {
                "target": target,
                "summary_scope": "group",
                **{column: value for column, value in zip(group_by, decode_group_key(key))},
                "count": summary["count"],
                "missing_count": summary["missing_count"],
                "total_rows_seen": summary["total_rows_seen"],
                "min": summary["min"],
                "max": summary["max"],
                "mean": summary["mean"],
                "std": summary["std"],
                **summary["quantiles"],
                "quantiles_approximate": summary["quantiles_approximate"],
            }
        )

    payload = {
        "task": "candidate_label_stats",
        "status": "available",
        "mode": "run",
        "timestamp_utc": current_timestamp_utc(),
        "git_commit": current_git_commit(),
        "release_root": str(release_root),
        "release_identity": release_identity(manifest),
        "input_view": "candidate_rows",
        "input_path": repo_relative(release_root / "data" / "candidate_rows"),
        "full_validation_status": detected_validation_status(release_root),
        "requires_large_memory_machine": True,
        "safe_for_anonymous_manuscript": True,
        "target": target,
        "group_by": group_by,
        "files_total": files_total,
        "files_processed": files_total,
        "release_summary": release_summary(manifest),
        "output_files": {kind: repo_relative(path) for kind, path in output_paths.items()},
        "overall_summary": overall_summary,
        "group_summaries": grouped_summaries,
        "notes": [
            "Run mode streamed candidate parquet files without loading the full release into memory.",
            "Quantiles are exact on small inputs and bounded-memory approximations on larger inputs.",
        ],
        "limitations": [
            "Grouped summaries accumulate one numeric summary per unique group key in memory.",
            "Quantiles become approximate once the bounded reservoir sample is saturated.",
        ],
    }
    return payload, csv_rows


def run(args: argparse.Namespace) -> None:
    release_root = Path(args.release_root)
    output_dir = ensure_output_dir_safe(Path(args.output_dir), release_root)
    manifest = load_manifest(release_root)
    inventory = candidate_file_inventory(release_root, manifest)
    schema_summary = candidate_schema_summary(release_root, manifest)
    targets = selected_targets(args.target)
    outputs = summary_output_paths(output_dir, targets)
    checkpoint = checkpoint_path(output_dir, "candidate_label_stats")
    checkpoint = guard_output_path(checkpoint, release_root)
    for path_group in outputs.values():
        for output_path in path_group.values():
            guard_output_path(output_path, release_root)

    if args.mode == "plan":
        payload = build_plan_payload(
            args=args,
            manifest=manifest,
            release_root=release_root,
            schema_summary=schema_summary,
            inventory=inventory,
            targets=targets,
            outputs=outputs,
        )
        write_json(output_dir / "plan.json", payload)
        print(f"Wrote {output_dir / 'plan.json'}")
        return

    reset_outputs(
        output_paths=[path for path_group in outputs.values() for path in path_group.values()],
        checkpoint_paths=[checkpoint],
        overwrite=args.overwrite,
        resume=args.resume,
    )

    checkpoint_payload = load_checkpoint(checkpoint, missing_ok=args.resume) if args.resume else None
    if checkpoint_payload is None:
        state = fresh_state(targets, args.group_by)
    else:
        state = load_state(checkpoint_payload, targets, args.group_by)

    budget = build_file_budget(args.max_files)
    start_index = int(state["next_file_index"])
    required_columns = list(dict.fromkeys([*targets, *args.group_by]))

    for file_index in range(start_index, len(inventory)):
        if budget_exhausted(budget):
            break
        item = inventory[file_index]
        path = item["path"]
        for batch in iter_candidate_batches(path, columns=required_columns):
            update_state_for_batch(state=state, batch=batch, targets=targets, group_by=args.group_by)
        state["next_file_index"] = file_index + 1
        save_checkpoint(
            checkpoint,
            {
                "task": "candidate_label_stats",
                "release_root": str(release_root),
                "state": state,
            },
        )
        budget = consume_budget(budget)

    if int(state["next_file_index"]) < len(inventory):
        remaining = len(inventory) - int(state["next_file_index"])
        print(
            json.dumps(
                {
                    "task": "candidate_label_stats",
                    "status": "partial",
                    "files_total": len(inventory),
                    "files_processed": int(state["next_file_index"]),
                    "files_remaining": remaining,
                    "checkpoint_path": repo_relative(checkpoint),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return

    for target in targets:
        payload, rows = build_target_payload(
            target=target,
            release_root=release_root,
            manifest=manifest,
            output_paths=outputs[target],
            state=state,
            files_total=len(inventory),
        )
        write_json(outputs[target]["json"], payload)
        write_csv(outputs[target]["csv"], rows)

    remove_checkpoint(checkpoint)
    print(json.dumps({target: repo_relative(paths["json"]) for target, paths in outputs.items()}, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> None:
    run(parse_args(argv))


if __name__ == "__main__":
    main()
