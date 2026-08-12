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
        execute_zenodo_v0_2_draft,
        plan_zenodo_upload,
        plan_zenodo_v0_2_draft,
        render_zenodo_v0_2_dry_run,
    )

    parser = argparse.ArgumentParser(
        description="Dry-run-first Zenodo deposit helper for LAFC-Evict publication bundles.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--bundle-dir")
    parser.add_argument("--metadata", help="Zenodo metadata JSON for the v0.2 manifest-driven draft workflow.")
    parser.add_argument("--manifest", help="Exact Zenodo file manifest for the v0.2 manifest-driven draft workflow.")
    parser.add_argument(
        "--release-dir",
        help="Optional release directory to include when uploading release payload files. Required with --include-release-files.",
    )
    parser.add_argument("--sandbox", action="store_true")
    parser.add_argument("--production", action="store_true")
    parser.add_argument("--include-release-files", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--create-draft", action="store_true", help="Create an unpublished draft in the v0.2 workflow.")
    parser.add_argument("--upload", action="store_true", help="Upload manifest files in the v0.2 workflow.")
    parser.add_argument("--verify", action="store_true", help="Verify draft files and metadata after upload in the v0.2 workflow.")
    parser.add_argument("--no-publish", action="store_true", help="Required for v0.2 draft creation; publication is a separate gate.")
    parser.add_argument("--deposition-id", type=int, help="Resume an existing unpublished v0.2 draft; never creates a second deposition.")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()

    manifest_workflow = bool(args.metadata or args.manifest or args.create_draft or args.upload or args.verify or args.no_publish)

    if not args.production and not manifest_workflow:
        args.sandbox = True
    if manifest_workflow and not args.sandbox:
        args.production = True
    if manifest_workflow:
        if not args.create_draft:
            args.dry_run = True
    elif not args.execute:
        args.dry_run = True
    if args.execute and args.dry_run:
        parser.exit(1, "Use either --execute or --dry-run, not both.\n")
    if args.publish:
        parser.exit(1, "--publish is disabled for draft creation. Use a separate publication-gate command after draft review.\n")

    if manifest_workflow:
        if not args.metadata:
            parser.exit(1, "The v0.2 workflow requires --metadata.\n")
        if not args.manifest:
            parser.exit(1, "The v0.2 workflow requires --manifest.\n")
        if not args.release_dir:
            parser.exit(1, "The v0.2 workflow requires --release-dir.\n")
        if args.include_release_files:
            parser.exit(1, "The v0.2 workflow uploads only files listed in --manifest; do not use --include-release-files.\n")

        try:
            plan = plan_zenodo_v0_2_draft(
                metadata_path=args.metadata,
                release_dir=args.release_dir,
                manifest_path=args.manifest,
                production=not args.sandbox,
            )
            if args.dry_run or not args.create_draft:
                print(json.dumps(render_zenodo_v0_2_dry_run(plan), indent=2))
                return

            if not args.upload or not args.verify or not args.no_publish:
                parser.exit(1, "Draft creation requires --upload --verify --no-publish.\n")
            if not detect_zenodo_auth_available():
                parser.exit(1, "Draft creation requires a configured Zenodo token environment variable.\n")

            result = execute_zenodo_v0_2_draft(
                metadata_path=args.metadata,
                release_dir=args.release_dir,
                manifest_path=args.manifest,
                production=not args.sandbox,
                deposition_id=args.deposition_id,
            )
            print(
                json.dumps(
                    {
                        "mode": "create_draft",
                        "target": result.target,
                        "deposition_id": result.deposition_id,
                        "concept_record_id": result.concept_record_id,
                        "metadata_title": result.metadata_title,
                        "uploaded_filenames": list(result.uploaded_filenames),
                        "uploaded_file_count": len(result.uploaded_filenames),
                        "total_bytes": result.total_bytes,
                        "doi": result.doi,
                        "prereserved_doi": result.prereserved_doi,
                        "state": result.state,
                        "submitted": result.submitted,
                        "links": result.links,
                        "published": False,
                    },
                    indent=2,
                )
            )
            return
        except Exception as exc:
            parser.exit(1, f"Error preparing Zenodo v0.2 draft: {exc}\n")

    if not args.bundle_dir:
        parser.exit(1, "Legacy publication-bundle workflow requires --bundle-dir.\n")

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
        release_dir = Path(args.release_dir).resolve() if args.release_dir else None
        if args.include_release_files and release_dir is None:
            parser.exit(1, "--include-release-files requires --release-dir because publication bundles omit local absolute paths.\n")
        plan = plan_zenodo_upload(
            bundle_dir,
            sandbox=args.sandbox,
            include_release_files=args.include_release_files,
            release_dir=release_dir if release_dir is not None and release_dir.exists() else None,
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
            parser.exit(1, "Execute mode requires a configured Zenodo token environment variable.\n")

        result = execute_zenodo_deposit(
            bundle_dir,
            sandbox=args.sandbox,
            include_release_files=args.include_release_files,
            release_dir=release_dir if release_dir is not None and release_dir.exists() else None,
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
