from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from lafc_evict_dataset.publication import SYNTHETIC_DISCLAIMER, token_like_matches


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _sample_release_dir(tmp_path: Path) -> Path:
    release_dir = tmp_path / "release" / "lafc-evict-sample-v0.1"
    subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "scripts" / "build_sample_release.py"),
            "--input",
            str(_repo_root() / "examples" / "tiny_candidate_rows.csv"),
            "--output-dir",
            str(release_dir),
            "--overwrite",
        ],
        check=True,
    )
    return release_dir


def test_prepare_publication_bundle_from_synthetic_sample(tmp_path: Path) -> None:
    release_dir = _sample_release_dir(tmp_path)
    bundle_dir = tmp_path / "publication" / "bundles" / "lafc-evict-sample-v0.1"

    subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "scripts" / "prepare_publication_bundle.py"),
            "--release-dir",
            str(release_dir),
            "--output-dir",
            str(bundle_dir),
            "--overwrite",
        ],
        check=True,
    )

    assert (bundle_dir / "README.md").exists()
    assert (bundle_dir / "dataset_card.md").exists()
    assert (bundle_dir / "zenodo_metadata.json").exists()
    assert (bundle_dir / "github_release_notes.md").exists()
    assert (bundle_dir / "publication_manifest.json").exists()


def test_validate_publication_bundle_and_manifest_contents(tmp_path: Path) -> None:
    release_dir = _sample_release_dir(tmp_path)
    bundle_dir = tmp_path / "publication" / "bundles" / "lafc-evict-sample-v0.1"
    subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "scripts" / "prepare_publication_bundle.py"),
            "--release-dir",
            str(release_dir),
            "--output-dir",
            str(bundle_dir),
            "--overwrite",
        ],
        check=True,
    )

    subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "scripts" / "validate_publication_bundle.py"),
            "--bundle-dir",
            str(bundle_dir),
        ],
        check=True,
    )

    zenodo_metadata = json.loads((bundle_dir / "zenodo_metadata.json").read_text(encoding="utf-8"))
    manifest = json.loads((bundle_dir / "publication_manifest.json").read_text(encoding="utf-8"))
    readme = (bundle_dir / "README.md").read_text(encoding="utf-8")
    dataset_card = (bundle_dir / "dataset_card.md").read_text(encoding="utf-8")

    assert isinstance(zenodo_metadata, dict)
    assert manifest["release_type"] == "synthetic_sample"
    assert Path(manifest["source_release_directory"]) == release_dir.resolve()
    assert manifest["publication_status"] == "draft_local"
    assert SYNTHETIC_DISCLAIMER in readme
    assert SYNTHETIC_DISCLAIMER in dataset_card
    assert dataset_card.startswith("---\n")
    assert 'pretty_name: "LAFC-Evict Sample"' in dataset_card
    assert 'license: "mit"' in dataset_card
    assert "tags:" in dataset_card
    assert "task_categories:" in dataset_card
    assert "size_categories:" in dataset_card
    assert "configs:" in dataset_card


def test_token_like_detector_catches_fake_tokens() -> None:
    text = "Fake values: " + ("h" "f_") + ("a" * 32) + " " + ("g" "hp_") + ("b" * 32)
    matches = token_like_matches(text)
    assert any(match.startswith("hf_") for match in matches)
    assert any(match.startswith("ghp_") for match in matches)
