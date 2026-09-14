"""Verifies the pilot harness refuses to silently overwrite a non-empty run
directory (mirrors the Tier-1 harness's immutable-run-directory pattern)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from run_pilot import check_run_dir_available  # noqa: E402


def test_check_run_dir_available_passes_for_new_dir(tmp_path):
    run_dir = tmp_path / "new_run"
    check_run_dir_available(run_dir)  # must not raise; directory doesn't exist yet


def test_check_run_dir_available_passes_for_empty_existing_dir(tmp_path):
    run_dir = tmp_path / "empty_run"
    run_dir.mkdir()
    check_run_dir_available(run_dir)  # must not raise; exists but empty


def test_check_run_dir_available_refuses_nonempty_dir(tmp_path):
    run_dir = tmp_path / "nonempty_run"
    run_dir.mkdir()
    (run_dir / "marker.txt").write_text("x", encoding="utf-8")
    with pytest.raises(FileExistsError, match="Refusing to reuse"):
        check_run_dir_available(run_dir)
