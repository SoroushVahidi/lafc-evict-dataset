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
    from lafc_evict_dataset.real_release import (
        build_real_release_command,
        load_family_selection,
        render_real_release_report,
        summarize_candidate_source,
    )

    parser = argparse.ArgumentParser(
        description="Plan a real LAFC-Evict public release from an existing candidate-row manifest without copying large data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input-manifest", required=True, help="Path to the source candidate-row manifest.json")
    parser.add_argument("--family-selection", required=True, help="Path to the selected/excluded families JSON manifest")
    parser.add_argument("--release-name", required=True, help="Release name, for example lafc-evict-v0.1-open")
    parser.add_argument("--output", required=True, help="Markdown output path for the readiness report")
    args = parser.parse_args()

    try:
        selected_families, excluded_families = load_family_selection(args.family_selection)
        summary = summarize_candidate_source(
            args.input_manifest,
            include_families=set(selected_families),
            exclude_families=set(excluded_families),
        )
        build_command = build_real_release_command(
            input_path=args.input_manifest,
            output_dir=ROOT / "release" / args.release_name,
            dataset_id=args.release_name,
            include_families=selected_families,
            exclude_families=excluded_families,
            family_selection=args.family_selection,
        )
        report = render_real_release_report(
            summary,
            release_name=args.release_name,
            build_command=build_command,
        )
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        print(
            json.dumps(
                {
                    "release_name": args.release_name,
                    "report_path": str(output_path.resolve()),
                    "source_manifest": str(Path(args.input_manifest).resolve()),
                    "selected_families": list(selected_families),
                    "excluded_families": list(excluded_families),
                    "blocked_families_present": list(summary.blocked_families_present),
                    "missing_selected_families": list(summary.missing_selected_families),
                    "estimated_selected_rows": summary.estimated_rows_selected,
                    "estimated_selected_bytes": summary.total_bytes_selected,
                    "ready_to_proceed": summary.ready_to_proceed,
                },
                indent=2,
            )
        )
    except Exception as exc:
        parser.exit(1, f"Error planning real release: {exc}\n")


if __name__ == "__main__":
    main()
