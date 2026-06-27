from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _build_release_and_bundle(tmp_path: Path) -> tuple[Path, Path]:
    release_dir = tmp_path / "release" / "lafc-evict-sample-v0.1"
    bundle_dir = tmp_path / "publication" / "bundles" / "lafc-evict-sample-v0.1"
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
    return release_dir, bundle_dir


def test_huggingface_dry_run_succeeds_without_token(tmp_path: Path) -> None:
    release_dir, _ = _build_release_and_bundle(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "scripts" / "publish_to_huggingface.py"),
            "--release-dir",
            str(release_dir),
            "--repo-id",
            "SoroushVahidi/lafc-evict-sample",
            "--repo-type",
            "dataset",
            "--private",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert '"mode": "dry_run"' in result.stdout


def test_zenodo_dry_run_succeeds_without_token(tmp_path: Path) -> None:
    _, bundle_dir = _build_release_and_bundle(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "scripts" / "create_zenodo_deposit.py"),
            "--bundle-dir",
            str(bundle_dir),
            "--sandbox",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert '"mode": "dry_run"' in result.stdout


def test_github_release_dry_run_succeeds_without_token(tmp_path: Path) -> None:
    _, bundle_dir = _build_release_and_bundle(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "scripts" / "create_github_release.py"),
            "--repo",
            "SoroushVahidi/lafc-evict-dataset",
            "--tag",
            "v0.1.0-sample",
            "--title",
            "LAFC-Evict sample v0.1",
            "--notes-file",
            str(bundle_dir / "github_release_notes.md"),
            "--prerelease",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert '"mode": "dry_run"' in result.stdout


def test_huggingface_execute_fails_without_token_or_auth(tmp_path: Path) -> None:
    release_dir, _ = _build_release_and_bundle(tmp_path)
    env = {
        **os.environ,
        "HF_TOKEN": "",
        "HF_HOME": str(tmp_path / "hf_home"),
        "HOME": str(tmp_path / "home"),
        "PATH": "",
    }
    result = subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "scripts" / "publish_to_huggingface.py"),
            "--release-dir",
            str(release_dir),
            "--repo-id",
            "SoroushVahidi/lafc-evict-sample",
            "--repo-type",
            "dataset",
            "--private",
            "--execute",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "requires HF_TOKEN or a pre-authenticated" in result.stderr


def test_zenodo_execute_fails_without_token(tmp_path: Path) -> None:
    _, bundle_dir = _build_release_and_bundle(tmp_path)
    env = {**os.environ, "ZENODO_TOKEN": ""}
    result = subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "scripts" / "create_zenodo_deposit.py"),
            "--bundle-dir",
            str(bundle_dir),
            "--sandbox",
            "--execute",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "requires ZENODO_TOKEN" in result.stderr


def test_github_execute_fails_without_token_or_gh_auth(tmp_path: Path) -> None:
    _, bundle_dir = _build_release_and_bundle(tmp_path)
    env = {**os.environ, "GITHUB_TOKEN": "", "PATH": ""}
    result = subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "scripts" / "create_github_release.py"),
            "--repo",
            "SoroushVahidi/lafc-evict-dataset",
            "--tag",
            "v0.1.0-sample",
            "--title",
            "LAFC-Evict sample v0.1",
            "--notes-file",
            str(bundle_dir / "github_release_notes.md"),
            "--prerelease",
            "--execute",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "requires GITHUB_TOKEN or an authenticated gh CLI session" in result.stderr
