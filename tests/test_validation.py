from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

from lafc_evict_dataset.validation import validate_candidate_dataframe


def _load_example() -> pd.DataFrame:
    return pd.read_csv(Path(__file__).resolve().parents[1] / "examples" / "tiny_candidate_rows.csv")


def test_validation_catches_missing_required_columns() -> None:
    df = _load_example().drop(columns=["y_loss"])
    errors = validate_candidate_dataframe(df)
    assert errors
    assert "Missing required columns" in errors[0]


def test_checksum_script_produces_output(tmp_path: Path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("lafc-evict\n", encoding="utf-8")
    output = tmp_path / "checksums.sha256"
    script = Path(__file__).resolve().parents[1] / "scripts" / "compute_release_checksums.py"

    subprocess.run(
        [sys.executable, str(script), "--input-path", str(tmp_path), "--output-path", str(output)],
        check=True,
    )

    text = output.read_text(encoding="utf-8")
    assert "sample.txt" in text
    assert len(text.split()[0]) == 64


def test_validation_fails_on_duplicate_decision_id_across_splits() -> None:
    df = _load_example()
    df.loc[df["candidate_page_id"] == "C", "split"] = "test"
    errors = validate_candidate_dataframe(df)
    assert any("spanning multiple splits" in error for error in errors)


def test_validation_fails_on_nonnumeric_labels() -> None:
    df = _load_example()
    df["y_loss"] = df["y_loss"].astype(object)
    df.loc[0, "y_loss"] = "not-a-number"
    errors = validate_candidate_dataframe(df)
    assert any("must be present and numeric" in error for error in errors)


def test_validation_file_reports_parse_failure_for_bad_labels(tmp_path: Path) -> None:
    df = _load_example()
    df["y_value"] = df["y_value"].astype(object)
    df.loc[0, "y_value"] = "broken"
    csv_path = tmp_path / "bad.csv"
    df.to_csv(csv_path, index=False)
    script = Path(__file__).resolve().parents[1] / "scripts" / "validate_release_schema.py"

    result = subprocess.run(
        [sys.executable, str(script), "--input-path", str(csv_path)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Failed to read candidate rows" in result.stderr or "must be present and numeric" in result.stderr


def test_export_manifest_correctness_and_overwrite_guard(tmp_path: Path) -> None:
    example = Path(__file__).resolve().parents[1] / "examples" / "tiny_candidate_rows.csv"
    output_dir = tmp_path / "release"
    export_script = Path(__file__).resolve().parents[1] / "scripts" / "export_lafc_evict_parquet.py"

    first = subprocess.run(
        [sys.executable, str(export_script), "--input-path", str(example), "--output-dir", str(output_dir)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "\"row_count\": 9" in first.stdout

    manifest = json.loads((output_dir / "release_manifest.json").read_text(encoding="utf-8"))
    assert manifest["dataset_id"] == "lafc-evict-v0.1-open"
    assert manifest["row_count"] == 9
    assert manifest["decision_count"] == 3
    assert len(manifest["files"]) == 3

    second = subprocess.run(
        [sys.executable, str(export_script), "--input-path", str(example), "--output-dir", str(output_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert second.returncode == 1
    assert "--overwrite" in second.stderr


def test_release_manifest_can_be_read_back_as_input(tmp_path: Path) -> None:
    example = Path(__file__).resolve().parents[1] / "examples" / "tiny_candidate_rows.csv"
    output_dir = tmp_path / "release"
    export_script = Path(__file__).resolve().parents[1] / "scripts" / "export_lafc_evict_parquet.py"
    pairwise_script = Path(__file__).resolve().parents[1] / "scripts" / "build_pairwise_view.py"

    subprocess.run(
        [sys.executable, str(export_script), "--input-path", str(example), "--output-dir", str(output_dir)],
        check=True,
    )
    result = subprocess.run(
        [
            sys.executable,
            str(pairwise_script),
            "--input-path",
            str(output_dir / "release_manifest.json"),
            "--output-path",
            str(tmp_path / "pairwise.csv"),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Wrote" in result.stdout


def test_pairwise_cli_include_ties_changes_row_count(tmp_path: Path) -> None:
    example = Path(__file__).resolve().parents[1] / "examples" / "tiny_candidate_rows.csv"
    script = Path(__file__).resolve().parents[1] / "scripts" / "build_pairwise_view.py"
    without_ties = tmp_path / "pairwise_without_ties.csv"
    with_ties = tmp_path / "pairwise_with_ties.csv"

    subprocess.run(
        [sys.executable, str(script), "--input-path", str(example), "--output-path", str(without_ties)],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(script),
            "--input-path",
            str(example),
            "--output-path",
            str(with_ties),
            "--include-ties",
        ],
        check=True,
    )

    rows_without = pd.read_csv(without_ties)
    rows_with = pd.read_csv(with_ties)
    assert len(rows_without) == 8
    assert len(rows_with) == 9
    assert rows_with["is_tie"].sum() == 1


def test_decision_view_script_overwrite_guard(tmp_path: Path) -> None:
    example = Path(__file__).resolve().parents[1] / "examples" / "tiny_candidate_rows.csv"
    script = Path(__file__).resolve().parents[1] / "scripts" / "build_decision_view.py"
    output = tmp_path / "decision_view.csv"

    subprocess.run(
        [sys.executable, str(script), "--input-path", str(example), "--output-path", str(output)],
        check=True,
    )
    result = subprocess.run(
        [sys.executable, str(script), "--input-path", str(example), "--output-path", str(output)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "--overwrite" in result.stderr
