"""Read a release inventory and verify its payload using SHA-256."""

from __future__ import annotations

import argparse
import re
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath


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


def checksum_lines(root: Path, output: Path) -> list[str]:
    """Hash files in stable order and exclude the inventory itself."""
    from .io import iter_files, sha256_file

    root = root.resolve()
    output = output.resolve()
    is_directory = root.is_dir()
    lines = []
    for file in iter_files(root):
        resolved = file.resolve()
        if resolved != output:
            relative = resolved.relative_to(root) if is_directory else Path(file.name)
            lines.append(f"{sha256_file(file)}  {relative.as_posix()}")
    return lines


def verify_checksums(root: Path, expected: Mapping[str, str]) -> list[str]:
    from .io import sha256_file

    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"Expected a release directory: {root}")

    errors = []
    for name, digest in expected.items():
        try:
            path = (root / name).resolve(strict=True)
            if not path.is_relative_to(root):
                errors.append(f"{name}: path resolves outside the release directory")
            elif not path.is_file():
                errors.append(f"{name}: expected a regular file")
            elif sha256_file(path) != digest:
                errors.append(f"{name}: SHA-256 mismatch")
        except FileNotFoundError:
            errors.append(f"{name}: missing file")
        except (OSError, RuntimeError) as exc:
            errors.append(f"{name}: {exc}")
    return errors


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="SHA-256 inventory path")
    parser.add_argument(
        "--root", type=Path, required=True, help="Base directory for manifest entries"
    )
    args = parser.parse_args(argv)
    try:
        expected = read_checksums(args.manifest)
        errors = verify_checksums(args.root, expected)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")
    if errors:
        parser.exit(1, "\n".join(errors) + "\n")
    print(f"Verified {len(expected)} files.")
    return 0
