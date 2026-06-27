from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from lafc_evict_dataset.publication import (
        collect_release_inventory,
        detect_hf_auth_available,
        plan_huggingface_upload,
    )

    parser = argparse.ArgumentParser(
        description="Dry-run-first Hugging Face dataset upload helper for LAFC-Evict releases.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--release-dir", required=True)
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--repo-type", default="dataset")
    parser.add_argument("--private", action="store_true")
    parser.add_argument("--allow-public", action="store_true")
    parser.add_argument("--allow-synthetic-public", action="store_true")
    parser.add_argument("--large-folder", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    if not args.execute:
        args.dry_run = True
    if args.execute and args.dry_run:
        parser.exit(1, "Use either --execute or --dry-run, not both.\n")

    try:
        inventory = collect_release_inventory(args.release_dir)
        plan = plan_huggingface_upload(
            inventory,
            repo_id=args.repo_id,
            repo_type=args.repo_type,
            private=args.private,
            allow_public=args.allow_public,
            allow_synthetic_public=args.allow_synthetic_public,
            large_folder=args.large_folder,
        )
        if args.dry_run:
            print(json.dumps({"mode": "dry_run", "plan": plan.summary, "files": list(plan.files)}, indent=2))
            return

        if not detect_hf_auth_available():
            hf_cli = shutil.which("hf") or shutil.which("huggingface-cli")
            if hf_cli is None:
                parser.exit(1, "Execute mode requires HF_TOKEN or a pre-authenticated Hugging Face CLI session.\n")
            parser.exit(1, "Execute mode requires HF_TOKEN or a pre-authenticated Hugging Face CLI session.\n")

        try:
            import huggingface_hub  # noqa: F401
        except Exception as exc:
            parser.exit(1, f"Execute mode requires huggingface_hub: {exc}\n")

        print(
            json.dumps(
                {
                    "mode": "execute",
                    "repo_id": args.repo_id,
                    "repo_type": args.repo_type,
                    "private": args.private,
                    "large_folder": args.large_folder,
                    "files_to_upload": list(plan.files),
                    "note": "Execution path prepared. Real upload implementation intentionally remains manual-first.",
                },
                indent=2,
            )
        )
    except Exception as exc:
        parser.exit(1, f"Error preparing Hugging Face publication: {exc}\n")


if __name__ == "__main__":
    main()
