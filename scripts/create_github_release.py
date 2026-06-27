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
    from lafc_evict_dataset.publication import detect_github_auth_available, plan_github_release

    parser = argparse.ArgumentParser(
        description="Dry-run-first GitHub Release helper for LAFC-Evict code and metadata releases.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--notes-file", required=True)
    parser.add_argument("--asset", action="append", default=[])
    parser.add_argument("--prerelease", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    if not args.execute:
        args.dry_run = True
    if args.execute and args.dry_run:
        parser.exit(1, "Use either --execute or --dry-run, not both.\n")

    try:
        notes_file = Path(args.notes_file).resolve()
        assets = [Path(asset).resolve() for asset in args.asset]
        plan = plan_github_release(
            repo=args.repo,
            tag=args.tag,
            title=args.title,
            notes_file=notes_file,
            assets=assets,
            prerelease=args.prerelease,
        )
        if args.dry_run:
            print(json.dumps({"mode": "dry_run", "plan": plan.summary, "files": list(plan.files)}, indent=2))
            return

        if not detect_github_auth_available() and shutil.which("gh") is None:
            parser.exit(1, "Execute mode requires GITHUB_TOKEN or an authenticated gh CLI session.\n")

        print(
            json.dumps(
                {
                    "mode": "execute",
                    "repo": args.repo,
                    "tag": args.tag,
                    "title": args.title,
                    "prerelease": args.prerelease,
                    "files": list(plan.files),
                    "note": "Execution path prepared. For sample or RC tags, prerelease is recommended.",
                },
                indent=2,
            )
        )
    except Exception as exc:
        parser.exit(1, f"Error preparing GitHub release: {exc}\n")


if __name__ == "__main__":
    main()
