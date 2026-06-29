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
    from lafc_evict_dataset.real_release_build import _checksum_lines
    from lafc_evict_dataset.release_metadata import collect_release_file_inventory, manifest_local_absolute_paths

    parser = argparse.ArgumentParser(
        description=(
            "Inspect or repair lightweight release metadata only. This updates release_manifest.json "
            "and checksums.sha256 without reading Parquet row data."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--release-root", required=True, help="Release directory to inspect or repair")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the repaired release_manifest.json and checksums.sha256 instead of reporting a dry run",
    )
    args = parser.parse_args()

    release_root = Path(args.release_root).expanduser().resolve()
    manifest_path = release_root / "metadata" / "release_manifest.json"
    checksums_path = release_root / "metadata" / "checksums.sha256"
    if not manifest_path.exists():
        parser.exit(1, f"Missing release manifest: {manifest_path}\n")
    if not checksums_path.exists():
        parser.exit(1, f"Missing release checksums file: {checksums_path}\n")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    current_inventory = (
        [str(value) for value in manifest.get("file_inventory", [])]
        if isinstance(manifest.get("file_inventory"), list)
        else []
    )
    expected_inventory = collect_release_file_inventory(release_root)
    local_path_matches = manifest_local_absolute_paths(manifest)

    summary: dict[str, object] = {
        "release_root": str(release_root),
        "dry_run": not args.apply,
        "file_inventory_count_before": len(current_inventory),
        "file_inventory_count_after": len(expected_inventory),
        "missing_from_file_inventory": sorted(set(expected_inventory) - set(current_inventory)),
        "extra_in_file_inventory": sorted(set(current_inventory) - set(expected_inventory)),
        "local_absolute_paths_detected": [
            {"field": field, "value": value} for field, value in local_path_matches
        ],
    }

    inventory_changed = current_inventory != expected_inventory
    if not args.apply:
        summary["would_update_manifest"] = inventory_changed
        summary["would_rewrite_checksums"] = inventory_changed
        print(json.dumps(summary, indent=2))
        return

    if inventory_changed:
        manifest["file_inventory"] = expected_inventory
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        checksums_path.write_text(
            "\n".join(_checksum_lines(release_root, checksums_path)) + "\n",
            encoding="utf-8",
        )

    summary["updated_manifest"] = inventory_changed
    summary["rewrote_checksums"] = inventory_changed
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
