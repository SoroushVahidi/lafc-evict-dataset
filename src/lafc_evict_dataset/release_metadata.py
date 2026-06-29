from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .io import iter_files

# The release file inventory describes the full on-disk release payload.
# Unlike checksums.sha256, it intentionally includes both metadata/release_manifest.json
# and metadata/checksums.sha256 because both files are part of the shipped artifact tree.
RELEASE_FILE_INVENTORY_REQUIRED_RELATIVE_PATHS: tuple[str, ...] = (
    "metadata/release_manifest.json",
    "metadata/checksums.sha256",
)

_LOCAL_ABSOLUTE_PATH_PREFIXES: tuple[str, ...] = (
    "/home/",
    "/tmp/",
    "/var/",
    "/mnt/",
    "/opt/",
    "/srv/",
    "/Users/",
)


def collect_release_file_inventory(
    release_root: str | Path,
    *,
    include_paths: Iterable[str | Path] = (),
) -> list[str]:
    root = Path(release_root).expanduser().resolve()
    rel_paths = {
        path.resolve().relative_to(root).as_posix()
        for path in iter_files(root)
        if path.is_file()
    }
    for path in include_paths:
        candidate = Path(path)
        if candidate.is_absolute():
            rel_paths.add(candidate.resolve().relative_to(root).as_posix())
        else:
            rel_paths.add(candidate.as_posix())
    return sorted(rel_paths)


def manifest_local_absolute_paths(payload: Any, *, prefix: str = "$") -> list[tuple[str, str]]:
    matches: list[tuple[str, str]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            matches.extend(manifest_local_absolute_paths(value, prefix=f"{prefix}.{key}"))
        return matches
    if isinstance(payload, list):
        for index, value in enumerate(payload):
            matches.extend(manifest_local_absolute_paths(value, prefix=f"{prefix}[{index}]"))
        return matches
    if isinstance(payload, str) and payload.startswith(_LOCAL_ABSOLUTE_PATH_PREFIXES):
        matches.append((prefix, payload))
    return matches
