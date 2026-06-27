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
    from lafc_evict_dataset.publication import (
        detect_zenodo_auth_available,
        execute_zenodo_deposit,
        plan_zenodo_upload,
    )

    parser = argparse.ArgumentParser(
        description="Dry-run-first Zenodo deposit helper for LAFC-Evict publication bundles.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--bundle-dir", required=True)
    parser.add_argument("--sandbox", action="store_true")
    parser.add_argument("--production", action="store_true")
    parser.add_argument("--include-release-files", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()

    if not args.production:
        args.sandbox = True
    if not args.execute:
        args.dry_run = True
    if args.execute and args.dry_run:
        parser.exit(1, "Use either --execute or --dry-run, not both.\n")
    if args.publish:
        parser.exit(1, "--publish is disabled for this workflow.\n")

    bundle_dir = Path(args.bundle_dir).resolve()
    zenodo_metadata = bundle_dir / "zenodo_metadata.json"
    publication_manifest_path = bundle_dir / "publication_manifest.json"
    if not zenodo_metadata.exists():
        parser.exit(1, f"Missing Zenodo metadata file: {zenodo_metadata}\n")
    if not publication_manifest_path.exists():
        parser.exit(1, f"Missing publication manifest: {publication_manifest_path}\n")

    try:
        metadata = json.loads(zenodo_metadata.read_text(encoding="utf-8"))
        publication_manifest = json.loads(publication_manifest_path.read_text(encoding="utf-8"))
        release_dir = Path(str(publication_manifest.get("source_release_directory", ""))).resolve()
        plan = plan_zenodo_upload(
            bundle_dir,
            sandbox=args.sandbox,
            include_release_files=args.include_release_files,
            release_dir=release_dir if release_dir.exists() else None,
        )
        if args.dry_run:
            print(
                json.dumps(
                    {
                        "mode": "dry_run",
                        "target": "sandbox" if args.sandbox else "production",
                        "metadata_title": metadata.get("metadata", {}).get("title", ""),
                        "include_release_files": args.include_release_files,
                        "files": list(plan.files),
                    },
                    indent=2,
                )
            )
            return

        if not detect_zenodo_auth_available():
            parser.exit(1, "Execute mode requires ZENODO_SANDBOX_TOKEN or ZENODO_TOKEN.\n")

        result = execute_zenodo_deposit(
            bundle_dir,
            sandbox=args.sandbox,
            include_release_files=args.include_release_files,
            release_dir=release_dir if release_dir.exists() else None,
        )

        print(
            json.dumps(
                {
                    "mode": "execute",
                    "target": result.target,
                    "include_release_files": args.include_release_files,
                    "files": list(plan.files),
                    "deposition_id": result.deposition_id,
                    "concept_record_id": result.concept_record_id,
                    "metadata_title": result.metadata_title,
                    "uploaded_filenames": list(result.uploaded_filenames),
                    "doi": result.doi,
                    "prereserved_doi": result.prereserved_doi,
                    "state": result.state,
                    "submitted": result.submitted,
                    "links": result.links,
                },
                indent=2,
            )
        )
    except Exception as exc:
        parser.exit(1, f"Error preparing Zenodo deposit: {exc}\n")


if __name__ == "__main__":
    main()
