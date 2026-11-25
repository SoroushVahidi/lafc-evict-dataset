"""Compare two published SHA-256 inventories without downloading dataset payloads."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re


def read_checksums(path: Path) -> dict[str, str]:
    result = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-fA-F]{64}) [ *](.+)", line)
        if match is None:
            raise ValueError(f"{path}:{number}: invalid sha256sum row")
        digest, name = match.groups()
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or str(relative) == ".":
            raise ValueError(f"{path}:{number}: expected a safe relative path")
        name = str(relative)
        if name in result:
            raise ValueError(f"{path}:{number}: duplicate path {name!r}")
        result[name] = digest.lower()
    if not result:
        raise ValueError(f"{path}: empty inventory")
    return result


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
