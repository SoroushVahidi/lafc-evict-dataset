#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from _baseline_common import candidate_schema_summary, load_manifest, release_summary, repo_relative, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a dry-run baseline plan for LAFC-Evict value regression without launching heavy training."
    )
    parser.add_argument(
        "--release-root",
        default="release/lafc-evict-v0.1-open-current-contract-preserved",
        help="Repo-relative preserved release path.",
    )
    parser.add_argument(
        "--output-dir",
        default="paper/sigmod2027/results/baselines/value_regression",
        help="Directory for the emitted baseline plan JSON.",
    )
    parser.add_argument(
        "--target",
        choices=["y_loss", "y_value"],
        default="y_loss",
        help="Candidate-level regression target for the plan.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    release_root = Path(args.release_root)
    output_dir = Path(args.output_dir)
    manifest = load_manifest(release_root)
    schema = candidate_schema_summary(release_root, manifest)

    payload = {
        "task": "value_regression",
        "status": "dry_run_checked",
        "mode": "plan",
        "release_root": args.release_root,
        "input_view": "candidate_rows",
        "input_path": repo_relative(release_root / "data" / "candidate_rows"),
        "target": args.target,
        "full_validation_status": "pending",
        "requires_wolverine": True,
        "safe_for_anonymous_manuscript": False,
        "metrics": ["MAE", "RMSE", "spearman_within_decision", "top1_regret_if_available"],
        "baselines": [
            {"name": "lru_score_regression", "status": "planned"},
            {"name": "predictor_score_regression", "status": "planned"},
            {"name": "linear_regression", "status": "planned"},
            {"name": "gradient_boosting", "status": "optional"},
        ],
        "schema_check": schema,
        "release_summary": release_summary(manifest),
        "blockers": [
            "candidate-row execution would touch the full 277,995,072-row release and should run on Wolverine only",
            "full real-release validation is still pending",
        ],
        "recommended_next_step": "Prepare and submit a Wolverine-side candidate-row baseline job after the pairwise sanity path is settled.",
    }
    write_json(output_dir / "plan.json", payload)
    print(f"Wrote {output_dir / 'plan.json'}")


if __name__ == "__main__":
    main()
