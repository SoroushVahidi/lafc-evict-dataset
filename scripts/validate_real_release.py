from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from lafc_evict_dataset.real_release_validation import validate_real_release

    parser = argparse.ArgumentParser(
        description="Validate a real LAFC-Evict release directory, manifest, checksums, and aggregate consistency.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--release-root", required=True, help="Path to the built release directory")
    args = parser.parse_args()

    errors = validate_real_release(args.release_root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise SystemExit(1)
    print("Real release validation passed.")


if __name__ == "__main__":
    main()
