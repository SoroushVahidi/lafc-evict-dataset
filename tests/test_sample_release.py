from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd


def _script_path() -> Path:
    return Path(__file__).resolve().parents[1] / "scripts" / "build_sample_release.py"


def _example_path() -> Path:
    return Path(__file__).resolve().parents[1] / "examples" / "tiny_candidate_rows.csv"


def test_sample_release_command_succeeds_and_creates_expected_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "lafc-evict-sample-v0.1"
    result = subprocess.run(
        [
            sys.executable,
            str(_script_path()),
            "--input",
            str(_example_path()),
            "--output-dir",
            str(output_dir),
            "--overwrite",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["candidate_row_count"] == 9
    assert payload["decision_row_count"] == 3
    assert payload["pairwise_row_count"] == 8

    expected_files = [
        output_dir / "data" / "decision_view" / "decision_view.parquet",
        output_dir / "data" / "pairwise_view" / "pairwise_view.parquet",
        output_dir / "metadata" / "release_manifest.json",
        output_dir / "metadata" / "checksums.sha256",
        output_dir / "metadata" / "validation_report.md",
        output_dir / "README.md",
    ]
    for path in expected_files:
        assert path.exists(), path

    candidate_files = sorted((output_dir / "data" / "candidate_rows").rglob("*.parquet"))
    assert len(candidate_files) == 3


def test_sample_release_manifest_counts_and_disclaimer(tmp_path: Path) -> None:
    output_dir = tmp_path / "lafc-evict-sample-v0.1"
    subprocess.run(
        [
            sys.executable,
            str(_script_path()),
            "--input",
            str(_example_path()),
            "--output-dir",
            str(output_dir),
            "--overwrite",
        ],
        check=True,
    )

    manifest = json.loads((output_dir / "metadata" / "release_manifest.json").read_text(encoding="utf-8"))
    report = (output_dir / "metadata" / "validation_report.md").read_text(encoding="utf-8")
    checksums = (output_dir / "metadata" / "checksums.sha256").read_text(encoding="utf-8")
    readme = (output_dir / "README.md").read_text(encoding="utf-8")

    assert manifest["dataset_name"] == "lafc-evict-sample"
    assert manifest["version"] == "0.1"
    assert manifest["release_type"] == "synthetic_sample"
    assert manifest["schema_version"] == "lafc-evict-candidate-v1"
    assert manifest["row_counts"] == {
        "candidate_rows": 9,
        "decision_view": 3,
        "pairwise_view": 8,
    }
    assert manifest["note"] == "Synthetic sample release only; not suitable for scientific benchmarking."
    assert "This sample release contains synthetic rows only and does not include raw traces or external trace-derived data." in report
    assert checksums.strip()
    assert readme.startswith("---\n")
    assert 'pretty_name: "LAFC-Evict Sample"' in readme
    assert 'license: "mit"' in readme
    assert "tags:" in readme
    assert '- "synthetic"' in readme
    assert "task_categories:" in readme
    assert "configs:" in readme
    assert '  - split: "validation"' in readme
    assert '    path: "data/candidate_rows/split=val/**/*.parquet"' in readme
    assert "This is a synthetic sample release for testing the publication workflow. It is not suitable for scientific benchmarking." in readme


def test_sample_release_overwrite_protection(tmp_path: Path) -> None:
    output_dir = tmp_path / "lafc-evict-sample-v0.1"
    subprocess.run(
        [
            sys.executable,
            str(_script_path()),
            "--input",
            str(_example_path()),
            "--output-dir",
            str(output_dir),
            "--overwrite",
        ],
        check=True,
    )

    result = subprocess.run(
        [
            sys.executable,
            str(_script_path()),
            "--input",
            str(_example_path()),
            "--output-dir",
            str(output_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "--overwrite" in result.stderr


def test_sample_release_include_ties_changes_pairwise_output(tmp_path: Path) -> None:
    without_ties = tmp_path / "without_ties"
    with_ties = tmp_path / "with_ties"
    subprocess.run(
        [
            sys.executable,
            str(_script_path()),
            "--input",
            str(_example_path()),
            "--output-dir",
            str(without_ties),
            "--overwrite",
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(_script_path()),
            "--input",
            str(_example_path()),
            "--output-dir",
            str(with_ties),
            "--overwrite",
            "--include-ties",
        ],
        check=True,
    )

    pairwise_without = pd.read_parquet(without_ties / "data" / "pairwise_view" / "pairwise_view.parquet")
    pairwise_with = pd.read_parquet(with_ties / "data" / "pairwise_view" / "pairwise_view.parquet")
    manifest_with = json.loads((with_ties / "metadata" / "release_manifest.json").read_text(encoding="utf-8"))

    assert len(pairwise_without) == 8
    assert len(pairwise_with) == 9
    assert int(pairwise_with["is_tie"].sum()) == 1
    assert manifest_with["include_ties"] is True
