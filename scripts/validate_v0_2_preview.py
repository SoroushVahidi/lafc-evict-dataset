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
    from lafc_evict_dataset.preview import PREVIEW_RELEASE_NAME, validate_preview_release

    parser = argparse.ArgumentParser(
        description="Validate the canonical LAFC-Evict v0.2 real-data preview release.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--release-dir", type=Path, default=ROOT / "release" / PREVIEW_RELEASE_NAME)
    parser.add_argument("--skip-checksums", action="store_true")
    args = parser.parse_args()

    errors = validate_preview_release(args.release_dir, require_checksums=not args.skip_checksums)
    payload = {
        "release_dir": str(args.release_dir.resolve()),
        "passed": not errors,
        "errors": errors,
    }
    print(json.dumps(payload, indent=2))
    if errors:
        parser.exit(1, "v0.2 preview validation failed.\n")


if __name__ == "__main__":
    main()
