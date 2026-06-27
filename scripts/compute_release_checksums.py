from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from lafc_evict_dataset.io import ensure_parent, iter_files, sha256_file

    parser = argparse.ArgumentParser(description="Compute SHA256 checksums for release files.")
    parser.add_argument("--input-path", required=True, help="File or directory to hash")
    parser.add_argument("--output-path", default="manifests/checksums.sha256")
    args = parser.parse_args()

    input_path = Path(args.input_path).resolve()
    output_path = ensure_parent(args.output_path).resolve()
    lines: list[str] = []

    for file_path in iter_files(input_path):
        if file_path.resolve() == output_path:
            continue
        digest = sha256_file(file_path)
        rel = file_path.resolve().relative_to(input_path) if input_path.is_dir() else file_path.name
        lines.append(f"{digest}  {rel}")

    output_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
