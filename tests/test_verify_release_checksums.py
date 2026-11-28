import hashlib

import pytest

from lafc_evict_dataset.checksums import main


def test_verify_fixture_outside_working_directory(tmp_path, monkeypatch, capsys):
    root = tmp_path / "release"
    data = root / "data"
    data.mkdir(parents=True)
    payload = data / "test rows.csv"
    payload.write_bytes(b"column\nvalue\n")
    checksum = hashlib.sha256(payload.read_bytes()).hexdigest()
    manifest = tmp_path / "SHA256SUMS"
    manifest.write_text(f"{checksum.upper()} *data/test rows.csv\n", encoding="utf-8")
    monkeypatch.chdir(data)

    args = [str(manifest), "--root", str(root)]
    assert main(args) == 0
    assert capsys.readouterr().out == "Verified 1 files.\n"

    payload.write_bytes(b"column\nchanged\n")
    with pytest.raises(SystemExit) as error:
        main(args)
    assert error.value.code == 1
    assert capsys.readouterr().err == "data/test rows.csv: SHA-256 mismatch\n"

    payload.unlink()
    with pytest.raises(SystemExit) as error:
        main(args)
    assert error.value.code == 1
    assert capsys.readouterr().err == "data/test rows.csv: missing file\n"


def test_verify_rejects_paths_outside_release(tmp_path, capsys):
    outside = tmp_path / "outside.csv"
    outside.write_text("not part of the release\n", encoding="utf-8")
    root = tmp_path / "release"
    root.mkdir()
    (root / "data.csv").symlink_to(outside)
    manifest = tmp_path / "SHA256SUMS"
    manifest.write_text(f"{'0' * 64}  data.csv\n", encoding="utf-8")

    with pytest.raises(SystemExit) as error:
        main([str(manifest), "--root", str(root)])
    assert error.value.code == 1
    assert capsys.readouterr().err == "data.csv: path resolves outside the release directory\n"
