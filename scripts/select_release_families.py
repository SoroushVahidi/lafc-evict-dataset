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
    from lafc_evict_dataset.governance import (
        load_source_family_registry,
        select_release_families,
        write_selected_families_manifest,
    )

    parser = argparse.ArgumentParser(
        description=(
            "Select trace families for a named LAFC-Evict release scope from the machine-readable "
            "source-family registry. This is a release-governance aid, not legal advice."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--registry",
        default="manifests/source_family_registry.yaml",
        help="YAML registry of source-family redistribution and review status.",
    )
    parser.add_argument(
        "--release-scope",
        default="v0.1-open",
        help="Named release scope to evaluate.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional JSON output path. If omitted, the selector prints JSON to stdout only.",
    )
    args = parser.parse_args()

    try:
        registry = load_source_family_registry(args.registry)
        payload = select_release_families(registry, release_scope=args.release_scope)
        if args.output:
            write_selected_families_manifest(payload, args.output)
        print(json.dumps(payload, indent=2, sort_keys=True))
    except Exception as exc:
        parser.exit(1, f"Error selecting release families: {exc}\n")


if __name__ == "__main__":
    main()
