from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from lafc_evict_dataset.publication import (
    execute_zenodo_deposit,
    safe_zenodo_bundle_filenames,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_script_module(script_name: str):
    path = _repo_root() / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(script_name.replace(".py", ""), path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, object] | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text or json.dumps(self._payload)

    def json(self) -> dict[str, object]:
        return self._payload


class _FakeZenodoSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.metadata_payload: dict[str, object] | None = None
        self.uploaded_urls: list[str] = []

    def post(self, url: str, **kwargs: object) -> _FakeResponse:
        self.calls.append(("POST", url))
        return _FakeResponse(
            201,
            {
                "id": 12345,
                "links": {
                    "bucket": "https://sandbox.zenodo.org/api/files/bucket-12345",
                    "latest_draft": "https://sandbox.zenodo.org/api/deposit/depositions/12345",
                    "html": "https://sandbox.zenodo.org/deposit/12345",
                },
            },
        )

    def put(self, url: str, **kwargs: object) -> _FakeResponse:
        self.calls.append(("PUT", url))
        if url.endswith("/api/deposit/depositions/12345"):
            payload = kwargs.get("json")
            assert isinstance(payload, dict)
            self.metadata_payload = payload
            return _FakeResponse(
                200,
                {
                    "id": 12345,
                    "links": {
                        "bucket": "https://sandbox.zenodo.org/api/files/bucket-12345",
                        "latest_draft": "https://sandbox.zenodo.org/api/deposit/depositions/12345",
                        "html": "https://sandbox.zenodo.org/deposit/12345",
                    },
                    "metadata": payload.get("metadata", {}),
                },
            )
        self.uploaded_urls.append(url)
        return _FakeResponse(200, {"filename": Path(url).name})

    def get(self, url: str, **kwargs: object) -> _FakeResponse:
        self.calls.append(("GET", url))
        metadata = {}
        if self.metadata_payload is not None:
            payload = self.metadata_payload.get("metadata", {})
            if isinstance(payload, dict):
                metadata = payload
        return _FakeResponse(
            200,
            {
                "id": 12345,
                "conceptrecid": "67890",
                "doi": None,
                "submitted": False,
                "state": "unsubmitted",
                "links": {
                    "self": "https://sandbox.zenodo.org/api/deposit/depositions/12345",
                    "html": "https://sandbox.zenodo.org/deposit/12345",
                    "latest_draft": "https://sandbox.zenodo.org/api/deposit/depositions/12345",
                    "latest_draft_html": "https://sandbox.zenodo.org/deposit/12345",
                },
                "metadata": {
                    **metadata,
                    "prereserve_doi": {"doi": "10.5072/zenodo.12345"},
                },
            },
        )


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
    payload = json.loads(result.stdout)
    assert payload["target"] == "sandbox"
    assert payload["files"] == list(safe_zenodo_bundle_filenames(bundle_dir))
    assert all(not name.startswith("release::") for name in payload["files"])


def test_zenodo_dry_run_makes_no_network_calls(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _, bundle_dir = _build_release_and_bundle(tmp_path)
    module = _load_script_module("create_zenodo_deposit.py")

    def _should_not_run(*args: object, **kwargs: object) -> object:
        raise AssertionError("execute_zenodo_deposit should not run during dry-run")

    monkeypatch.setattr("lafc_evict_dataset.publication.execute_zenodo_deposit", _should_not_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "create_zenodo_deposit.py",
            "--bundle-dir",
            str(bundle_dir),
            "--sandbox",
            "--dry-run",
        ],
    )

    module.main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["mode"] == "dry_run"
    assert payload["target"] == "sandbox"


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
    env = {**os.environ, "ZENODO_SANDBOX_TOKEN": "", "ZENODO_TOKEN": ""}
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
    assert "requires ZENODO_SANDBOX_TOKEN or ZENODO_TOKEN" in result.stderr


def test_zenodo_execute_uses_sandbox_base_url_by_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _, bundle_dir = _build_release_and_bundle(tmp_path)
    session = _FakeZenodoSession()
    monkeypatch.setenv("ZENODO_SANDBOX_TOKEN", "sandbox-token")
    monkeypatch.delenv("ZENODO_TOKEN", raising=False)

    result = execute_zenodo_deposit(bundle_dir, session=session)

    assert session.calls[0] == ("POST", "https://sandbox.zenodo.org/api/deposit/depositions")
    assert result.target == "sandbox"


def test_zenodo_execute_creates_updates_uploads_and_does_not_publish(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, bundle_dir = _build_release_and_bundle(tmp_path)
    session = _FakeZenodoSession()
    monkeypatch.setenv("ZENODO_SANDBOX_TOKEN", "sandbox-token")
    monkeypatch.delenv("ZENODO_TOKEN", raising=False)

    result = execute_zenodo_deposit(bundle_dir, session=session)

    expected_files = list(safe_zenodo_bundle_filenames(bundle_dir))
    assert result.deposition_id == 12345
    assert result.concept_record_id == "67890"
    assert result.metadata_title == "lafc-evict-sample 0.1"
    assert list(result.uploaded_filenames) == expected_files
    assert result.prereserved_doi == "10.5072/zenodo.12345"
    assert result.submitted is False
    assert result.state == "unsubmitted"
    assert result.links["html"] == "https://sandbox.zenodo.org/deposit/12345"
    assert len(session.uploaded_urls) == len(expected_files)
    assert sorted(Path(url).name for url in session.uploaded_urls) == sorted(expected_files)
    assert all("/actions/publish" not in url for _, url in session.calls)


def test_zenodo_execute_fails_clearly_without_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _, bundle_dir = _build_release_and_bundle(tmp_path)
    monkeypatch.delenv("ZENODO_SANDBOX_TOKEN", raising=False)
    monkeypatch.delenv("ZENODO_TOKEN", raising=False)

    with pytest.raises(ValueError, match="ZENODO_SANDBOX_TOKEN or ZENODO_TOKEN"):
        execute_zenodo_deposit(bundle_dir, session=_FakeZenodoSession())


def test_zenodo_execute_redacts_token_in_error_messages(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _, bundle_dir = _build_release_and_bundle(tmp_path)
    token = "sandbox-secret-token"

    class _ErrorSession(_FakeZenodoSession):
        def post(self, url: str, **kwargs: object) -> _FakeResponse:
            self.calls.append(("POST", url))
            return _FakeResponse(401, payload={"message": f"bad token {token}"})

    monkeypatch.setenv("ZENODO_SANDBOX_TOKEN", token)
    monkeypatch.delenv("ZENODO_TOKEN", raising=False)

    with pytest.raises(RuntimeError) as excinfo:
        execute_zenodo_deposit(bundle_dir, session=_ErrorSession())

    message = str(excinfo.value)
    assert token not in message
    assert "[REDACTED_TOKEN]" in message


def test_zenodo_cli_defaults_to_sandbox_until_production_flag_is_passed(tmp_path: Path) -> None:
    _, bundle_dir = _build_release_and_bundle(tmp_path)
    sandbox_result = subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "scripts" / "create_zenodo_deposit.py"),
            "--bundle-dir",
            str(bundle_dir),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    production_result = subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "scripts" / "create_zenodo_deposit.py"),
            "--bundle-dir",
            str(bundle_dir),
            "--production",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(sandbox_result.stdout)["target"] == "sandbox"
    assert json.loads(production_result.stdout)["target"] == "production"


def test_zenodo_publish_flag_is_rejected(tmp_path: Path) -> None:
    _, bundle_dir = _build_release_and_bundle(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "scripts" / "create_zenodo_deposit.py"),
            "--bundle-dir",
            str(bundle_dir),
            "--sandbox",
            "--publish",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "--publish is disabled for this workflow." in result.stderr


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
