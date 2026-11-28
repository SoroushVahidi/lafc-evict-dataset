"""Compare two published SHA-256 inventories without downloading dataset payloads."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Load the shared parser without importing release dependencies.
SRC = Path(__file__).resolve().parents[1] / "src" / "lafc_evict_dataset"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from checksums import read_checksums  # noqa: E402


def compare(left: dict[str, str], right: dict[str, str], prefix: str = "") -> dict:
    left = {name: digest for name, digest in left.items() if name.startswith(prefix)}
    right = {name: digest for name, digest in right.items() if name.startswith(prefix)}
    common = left.keys() & right.keys()
    return {
        "prefix": prefix,
        "unchanged": sum(left[name] == right[name] for name in common),
        "changed": sorted(name for name in common if left[name] != right[name]),
        "added": sorted(right.keys() - left.keys()),
        "removed": sorted(left.keys() - right.keys()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--prefix", default="", help="Restrict to matching paths (for example data/)")
    args = parser.parse_args()
    try:
        result = compare(read_checksums(args.left), read_checksums(args.right), args.prefix)
    except (OSError, ValueError) as err:
        parser.exit(2, f"{err}\n")
    if not (result["unchanged"] or any(result[name] for name in ("added", "removed", "changed"))):
        parser.exit(2, "No files matched the requested comparison.\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
