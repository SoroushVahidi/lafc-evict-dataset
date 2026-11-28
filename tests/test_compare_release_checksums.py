import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "compare_release_checksums.py"


def test_data_prefix_omits_metadata_changes(tmp_path):
    previous, current = tmp_path / "previous", tmp_path / "current"
    previous.write_text(f"{'0' * 64}  README.md\n{'1' * 64}  data/rows.parquet\n")
    current.write_text(f"{'2' * 64}  README.md\n{'1' * 64} *data/rows.parquet\n")
    run = subprocess.run([sys.executable, "-S", str(SCRIPT), str(previous), str(current), "--prefix", "data/"],
                         text=True, capture_output=True, check=True)
    assert '"unchanged": 1' in run.stdout
    assert '"changed": []' in run.stdout


@pytest.mark.parametrize("second", ["data/rows.parquet", "../outside"])
def test_duplicate_or_unsafe_path_is_an_error(tmp_path, second):
    inventory = tmp_path / "inventory"
    inventory.write_text(f"{'0' * 64}  data/rows.parquet\n{'1' * 64}  {second}\n")
    result = subprocess.run([sys.executable, str(SCRIPT), str(inventory), str(inventory)],
                            capture_output=True, text=True)
    assert result.returncode == 2
