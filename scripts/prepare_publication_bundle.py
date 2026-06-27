from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from lafc_evict_dataset.io import ensure_clean_output_dir
    from lafc_evict_dataset.publication import (
        build_publication_manifest,
        collect_release_inventory,
        render_dataset_card,
        render_github_release_notes,
        render_publication_readme,
        render_zenodo_metadata,
        write_json,
    )

    parser = argparse.ArgumentParser(
        description=(
            "Prepare a metadata-only publication bundle from an existing LAFC-Evict release directory. "
            "This does not duplicate Parquet or other release data files."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--release-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    try:
        inventory = collect_release_inventory(args.release_dir)
        bundle_dir = ensure_clean_output_dir(args.output_dir, overwrite=args.overwrite, kind="Publication bundle output directory")
        (bundle_dir / "README.md").write_text(render_publication_readme(inventory), encoding="utf-8")
        (bundle_dir / "dataset_card.md").write_text(render_dataset_card(inventory), encoding="utf-8")
        write_json(bundle_dir / "zenodo_metadata.json", render_zenodo_metadata(inventory))
        (bundle_dir / "github_release_notes.md").write_text(render_github_release_notes(inventory), encoding="utf-8")
        write_json(bundle_dir / "publication_manifest.json", build_publication_manifest(inventory, bundle_dir=bundle_dir))
        print(f"Prepared publication bundle at {bundle_dir}")
    except Exception as exc:
        parser.exit(1, f"Error preparing publication bundle: {exc}\n")


if __name__ == "__main__":
    main()
