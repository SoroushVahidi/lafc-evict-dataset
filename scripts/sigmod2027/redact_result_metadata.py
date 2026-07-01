#!/usr/bin/env python3
"""Redact non-scientific, deanonymizing environment metadata from committed
SIGMOD/PACMMOD result JSON and Markdown files.

This does not touch scientific claims: row counts, metrics, split names,
timestamps, and validation status are left untouched. It only rewrites:

- absolute local/HPC paths (e.g. ``/mmfs1/scratch/<user>/...``) into a
  relative, review-safe placeholder,
- the ``requires_wolverine`` field name into a neutral
  ``requires_large_memory_machine`` name (same boolean value),
- prose mentions of the internal HPC cluster nickname into a neutral
  description of the execution environment.

Safe to re-run (idempotent): if a file has already been redacted, running
this again is a no-op for that file.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOTS = (
    REPO_ROOT / "paper" / "sigmod2027" / "results",
)

# Exact absolute-path prefixes observed in committed result files, mapped to a
# relative, review-safe placeholder. Extend this list if new absolute paths
# are ever committed by a future baseline run.
PATH_REPLACEMENTS = {
    "/mmfs1/scratch/ikoutis/sv96/lafc-work/release/lafc-evict-v0.1-open-current-contract-preserved": "release/<evaluated-open-release>",
}

# Ordered (pattern, replacement) pairs for free-text mentions of the internal
# HPC cluster nickname inside prose fields (limitations, notes,
# recommended_next_step, etc.). Longer/more specific patterns are listed
# first so they take priority over the bare "Wolverine" fallback.
PROSE_REPLACEMENTS = [
    (re.compile(r"\bon Wolverine only\b"), "on a large-memory execution environment only"),
    (re.compile(r"\ba Wolverine-side\b"), "a large-memory-environment-side"),
    (re.compile(r"\bWolverine-scale\b"), "large-memory-environment-scale"),
    (re.compile(r"\bon Wolverine\b"), "on a large-memory execution environment"),
    (re.compile(r"\bWolverine-side\b"), "large-memory-environment-side"),
    (re.compile(r"\bWolverine\b"), "the large-memory execution environment"),
    (re.compile(r"\bwolverine\b"), "the large-memory execution environment"),
]

FIELD_RENAME = ('"requires_wolverine"', '"requires_large_memory_machine"')


def redact_text(text: str) -> str:
    for absolute_path, placeholder in PATH_REPLACEMENTS.items():
        text = text.replace(absolute_path, placeholder)
    text = text.replace(*FIELD_RENAME)
    for pattern, replacement in PROSE_REPLACEMENTS:
        text = pattern.sub(replacement, text)
    return text


def iter_target_files(roots: tuple[Path, ...]):
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in {".json", ".md", ".csv"}:
                continue
            if path.name.startswith("submitted_jobs_"):
                # Raw job-submission logs are relocated out of the paper tree
                # rather than redacted in place; see internal/wulver_job_logs/.
                continue
            yield path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        action="append",
        dest="roots",
        help="Directory to scan (repeatable). Defaults to paper/sigmod2027/results.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if any file would be changed, without writing.",
    )
    args = parser.parse_args()

    roots = tuple(Path(r) for r in args.roots) if args.roots else DEFAULT_ROOTS

    changed = []
    for path in iter_target_files(roots):
        original = path.read_text(encoding="utf-8")
        redacted = redact_text(original)
        if redacted != original:
            changed.append(path)
            if not args.check:
                path.write_text(redacted, encoding="utf-8")

    if changed:
        label = "Would redact" if args.check else "Redacted"
        for path in changed:
            print(f"{label}: {path.relative_to(REPO_ROOT)}")
    else:
        print("No deanonymizing metadata found.")

    if args.check and changed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
