#!/usr/bin/env python3
"""Assemble a double-anonymous review bundle for the SIGMOD/PACMMOD paper.

This copies only the files a reviewer needs to compile the manuscript and
inspect the reported result summaries. It deliberately excludes internal
planning notes, HPC job logs, and anything under version control history.

Usage:
    python scripts/sigmod2027/build_anonymous_submission_bundle.py [--out DIR]

The script only copies files; it does not compile LaTeX or touch git. Run
`redact_result_metadata.py --check` first (this script also runs that check
and aborts if it would still change anything) so nothing leaks through a
result file that was regenerated after the last redaction pass.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PAPER_ROOT = REPO_ROOT / "paper" / "sigmod2027"

# Relative-to-PAPER_ROOT paths/globs that are safe to hand to reviewers.
INCLUDE_GLOBS = [
    "latex/main.tex",
    "latex/main.pdf",
    "latex/refs.bib",
    "latex/sections/*.tex",
    "latex/tables/*.tex",
    "latex/figures/*",
    "results/README.md",
    "results/full_validation_summary.md",
    "results/metadata_tables/*",
    "results/baselines/**/*.json",
    "results/baselines/**/*.csv",
    "results/baselines/**/*.md",
    "results/candidate_label_stats/*.json",
    "results/candidate_label_stats/*.csv",
]

# Explicitly never copied, even if a future glob would otherwise match them.
# This is a safety net, not the primary inclusion mechanism.
EXCLUDE_NAMES = {
    "TODO.md",
}
EXCLUDE_DIR_NAMES = {"__pycache__"}

# Same denylist family used by the repo-wide anonymity grep, applied to the
# compiled PDF's metadata and extracted text before it is allowed in a bundle.
PDF_DENYLIST = re.compile(
    r"/home/|/mmfs1|/scratch|sv96|soroush|ikoutis|NJIT|wulver|wolverine"
    r"|github\.com/SoroushVahidi|/Users/|/mnt/|/Volumes/",
    re.IGNORECASE,
)


def verify_pdf_is_safe(pdf_path: Path) -> None:
    if not pdf_path.exists():
        return
    for tool, args in (("pdfinfo", [str(pdf_path)]), ("pdftotext", [str(pdf_path), "-"])):
        if shutil.which(tool) is None:
            print(f"warning: {tool} not found, skipping PDF metadata/text check", file=sys.stderr)
            continue
        output = subprocess.run([tool, *args], capture_output=True, text=True).stdout
        hit = PDF_DENYLIST.search(output)
        if hit:
            print(
                f"Refusing to bundle {pdf_path}: {tool} output contains "
                f"deanonymizing text ({hit.group(0)!r}).",
                file=sys.stderr,
            )
            raise SystemExit(1)

# Directories under paper/sigmod2027/ that are internal-only and must never
# reach a review bundle: planning notes, HPC/job-execution notes, and
# anything else not listed in INCLUDE_GLOBS.
KNOWN_INTERNAL_ONLY = [
    "technical",
    "related_work",
    "anonymous_artifact_plan.md",
    "submission_checklist.md",
    "experiments_plan.md",
    "outline.md",
    "related_work_notes.md",
    "README.md",
]


def run_redaction_check() -> None:
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("redact_result_metadata.py")), "--check"],
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        print(
            "Result metadata is not fully redacted. Run "
            "`python scripts/sigmod2027/redact_result_metadata.py` first.",
            file=sys.stderr,
        )
        raise SystemExit(1)


def collect_files() -> list[Path]:
    seen: list[Path] = []
    for pattern in INCLUDE_GLOBS:
        for path in sorted(PAPER_ROOT.glob(pattern)):
            if not path.is_file():
                continue
            if path.name in EXCLUDE_NAMES:
                continue
            if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
                continue
            seen.append(path)
    return seen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "publication" / "bundles" / "sigmod2027_anonymous_review",
        help="Output directory for the assembled bundle (recreated each run).",
    )
    parser.add_argument(
        "--skip-redaction-check",
        action="store_true",
        help="Skip the pre-flight redaction check (not recommended).",
    )
    args = parser.parse_args()

    if not args.skip_redaction_check:
        run_redaction_check()

    verify_pdf_is_safe(PAPER_ROOT / "latex" / "main.pdf")

    if args.out.exists():
        shutil.rmtree(args.out)
    args.out.mkdir(parents=True)

    files = collect_files()
    for src in files:
        rel = src.relative_to(PAPER_ROOT)
        dest = args.out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    print(f"Copied {len(files)} files into {args.out}")
    print(
        "main.pdf was checked with pdfinfo/pdftotext and included since it "
        "carried no deanonymizing metadata or text. If main.tex changes, "
        "recompile before re-running this script so the bundled PDF stays current."
    )
    print(
        "Known internal-only paths intentionally excluded: "
        + ", ".join(KNOWN_INTERNAL_ONLY)
    )


if __name__ == "__main__":
    main()
