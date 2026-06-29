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
        ASSOCIATED_PAPER_CITATION,
        ASSOCIATED_PAPER_STATUS,
        ASSOCIATED_PAPER_TITLE,
        PUBLIC_RELEASE_ARTIFACT_RELATIVE_PATHS,
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
    zenodo_metadata_payload: dict[str, object] | None = None
    if required["zenodo_metadata"].exists():
        try:
            zenodo_metadata_payload = json.loads(required["zenodo_metadata"].read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"Invalid JSON in zenodo_metadata.json: {exc}")
    if required["publication_manifest"].exists():
        try:
            manifest = json.loads(required["publication_manifest"].read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"Invalid JSON in publication_manifest.json: {exc}")

    if manifest is not None:
        source_release_name = str(manifest.get("source_release_name", "")).strip()
        if not source_release_name:
            errors.append("Publication manifest must include source_release_name.")
        release_artifact_paths = manifest.get("release_artifact_paths", {})
        if not isinstance(release_artifact_paths, dict):
            errors.append("Publication manifest must include release_artifact_paths.")
        else:
            for key, expected_value in PUBLIC_RELEASE_ARTIFACT_RELATIVE_PATHS.items():
                if str(release_artifact_paths.get(key, "")).strip() != expected_value:
                    errors.append(
                        "Publication manifest must use the standard release-relative artifact path "
                        f"for {key}: {expected_value}"
                    )
        if not str(manifest.get("release_type", "")).strip():
            errors.append("Publication manifest must include an explicit release_type.")

    for path in required.values():
        if not path.exists():
            continue
        errors.extend(validate_public_text_file(path, allow_absolute_paths=False))

    if manifest is not None and str(manifest.get("release_type")) == "synthetic_sample":
        for path in [required["readme"], required["dataset_card"], required["github_release_notes"]]:
            if path.exists() and SYNTHETIC_DISCLAIMER not in path.read_text(encoding="utf-8"):
                errors.append(f"Synthetic sample disclaimer missing from {path.name}")
        if isinstance(zenodo_metadata_payload, dict):
            metadata = zenodo_metadata_payload.get("metadata", {})
            if isinstance(metadata, dict):
                description = str(metadata.get("description", ""))
                notes = str(metadata.get("notes", ""))
                if SYNTHETIC_DISCLAIMER not in description:
                    errors.append("Synthetic sample disclaimer missing from zenodo_metadata.json description.")
                for required_text in [
                    ASSOCIATED_PAPER_TITLE,
                    "Soroush Vahidi",
                    ASSOCIATED_PAPER_CITATION,
                    ASSOCIATED_PAPER_STATUS,
                ]:
                    if required_text not in f"{description}\n{notes}":
                        errors.append(f"Required associated-paper metadata missing from zenodo_metadata.json: {required_text}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise SystemExit(1)
    print("Publication bundle validation passed.")


if __name__ == "__main__":
    main()
