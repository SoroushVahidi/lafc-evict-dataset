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
        SYNTHETIC_DISCLAIMER,
        validate_public_text_file,
    )

    parser = argparse.ArgumentParser(
        description="Validate a prepared publication bundle for completeness and dry-run publication safety.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--bundle-dir", required=True)
    args = parser.parse_args()

    bundle_dir = Path(args.bundle_dir).resolve()
    required = {
        "dataset_card": bundle_dir / "dataset_card.md",
        "zenodo_metadata": bundle_dir / "zenodo_metadata.json",
        "github_release_notes": bundle_dir / "github_release_notes.md",
        "publication_manifest": bundle_dir / "publication_manifest.json",
        "readme": bundle_dir / "README.md",
    }
    errors: list[str] = []
    for label, path in required.items():
        if not path.exists():
            errors.append(f"Missing {label}: {path}")

    manifest: dict[str, object] | None = None
    if required["zenodo_metadata"].exists():
        try:
            json.loads(required["zenodo_metadata"].read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"Invalid JSON in zenodo_metadata.json: {exc}")
    if required["publication_manifest"].exists():
        try:
            manifest = json.loads(required["publication_manifest"].read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"Invalid JSON in publication_manifest.json: {exc}")

    if manifest is not None:
        release_dir = Path(str(manifest.get("source_release_directory", "")))
        if not release_dir.exists():
            errors.append(f"Referenced release directory does not exist: {release_dir}")
        checksum_path = Path(str(manifest.get("checksum_file_path", "")))
        if not checksum_path.exists():
            errors.append(f"Referenced checksum file does not exist: {checksum_path}")
        validation_report_path = Path(str(manifest.get("validation_report_path", "")))
        if not validation_report_path.exists():
            errors.append(f"Referenced validation report does not exist: {validation_report_path}")
        if not str(manifest.get("release_type", "")).strip():
            errors.append("Publication manifest must include an explicit release_type.")

    for path in required.values():
        if not path.exists():
            continue
        allow_absolute = path.name == "publication_manifest.json"
        errors.extend(validate_public_text_file(path, allow_absolute_paths=allow_absolute))

    if manifest is not None and str(manifest.get("release_type")) == "synthetic_sample":
        for path in [required["readme"], required["dataset_card"], required["github_release_notes"]]:
            if path.exists() and SYNTHETIC_DISCLAIMER not in path.read_text(encoding="utf-8"):
                errors.append(f"Synthetic sample disclaimer missing from {path.name}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise SystemExit(1)
    print("Publication bundle validation passed.")


if __name__ == "__main__":
    main()
