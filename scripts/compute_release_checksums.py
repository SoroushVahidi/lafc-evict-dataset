from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from lafc_evict_dataset.io import ensure_parent, fail_if_output_exists, iter_files, sha256_file

    parser = argparse.ArgumentParser(
        description=(
            "Compute deterministic SHA256 checksums for a release file or directory tree. "
            "Output uses the standard '<sha256>  <relative-path>' format."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input-path", required=True, help="File or directory to hash")
    parser.add_argument("--output-path", default="manifests/checksums.sha256")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing checksum file.")
    args = parser.parse_args()

    try:
        input_path = Path(args.input_path).resolve()
        output_path = ensure_parent(args.output_path).resolve()
        fail_if_output_exists(output_path, overwrite=args.overwrite, kind="Checksum output")
        lines: list[str] = []

        for file_path in iter_files(input_path):
            if file_path.resolve() == output_path:
                continue
            digest = sha256_file(file_path)
            rel = file_path.resolve().relative_to(input_path) if input_path.is_dir() else Path(file_path.name)
            lines.append(f"{digest}  {rel.as_posix()}")

        output_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        print(f"Wrote {output_path}")
    except Exception as exc:
        parser.exit(1, f"Error computing release checksums: {exc}\n")


if __name__ == "__main__":
    main()
