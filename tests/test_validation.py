from __future__ import annotations

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
