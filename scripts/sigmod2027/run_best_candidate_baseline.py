#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from _baseline_common import candidate_schema_summary, load_manifest, release_summary, repo_relative, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a dry-run baseline plan for LAFC-Evict best-candidate prediction without launching heavy training."
    )
    parser.add_argument(
        "--release-root",
        default="release/lafc-evict-v0.1-open-current-contract-preserved",
        help="Repo-relative preserved release path.",
    )
    parser.add_argument(
        "--output-dir",
        default="paper/sigmod2027/results/baselines/best_candidate",
        help="Directory for the emitted baseline plan JSON.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    release_root = Path(args.release_root)
    output_dir = Path(args.output_dir)
    manifest = load_manifest(release_root)
    schema = candidate_schema_summary(release_root, manifest)

    payload = {
        "task": "best_candidate",
        "status": "dry_run_checked",
        "mode": "plan",
        "release_root": args.release_root,
        "input_view": "candidate_rows",
        "input_path": repo_relative(release_root / "data" / "candidate_rows"),
        "full_validation_status": "pending",
        "requires_wolverine": True,
        "safe_for_anonymous_manuscript": False,
        "metrics": ["top1_accuracy", "topk_accuracy", "selected_candidate_regret"],
        "baselines": [
            {"name": "random_candidate", "status": "planned"},
            {"name": "lru_victim_choice", "status": "planned"},
            {"name": "predictor_victim_choice", "status": "planned"},
            {"name": "best_candidate_from_linear_score", "status": "planned"},
            {"name": "best_candidate_from_gradient_boosting", "status": "optional"},
        ],
        "schema_check": schema,
        "release_summary": release_summary(manifest),
        "blockers": [
            "decision-grouped candidate-row evaluation requires Wolverine-scale access to candidate-row shards",
            "full real-release validation is still pending",
        ],
        "recommended_next_step": "Implement the ranking or decision-group reconstruction path on Wolverine after value-regression feature handling is stable.",
    }
    write_json(output_dir / "plan.json", payload)
    print(f"Wrote {output_dir / 'plan.json'}")


if __name__ == "__main__":
    main()
