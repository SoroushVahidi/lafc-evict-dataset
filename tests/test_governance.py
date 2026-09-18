from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from lafc_evict_dataset.governance import (
    REQUIRED_FAMILIES,
    REQUIRED_REGISTRY_FIELDS,
    load_source_family_registry,
    select_release_families,
)


def _registry_path() -> Path:
    return Path(__file__).resolve().parents[1] / "manifests" / "source_family_registry.yaml"


def _selector_script() -> Path:
    return Path(__file__).resolve().parents[1] / "scripts" / "select_release_families.py"


def test_registry_contains_every_required_family() -> None:
    registry = load_source_family_registry(_registry_path())
    families = {str(entry["family"]) for entry in registry}
    assert families == set(REQUIRED_FAMILIES)


def test_registry_entries_have_all_required_fields() -> None:
    registry = load_source_family_registry(_registry_path())
    for entry in registry:
        assert set(REQUIRED_REGISTRY_FIELDS).issubset(entry.keys())


def test_v0_1_open_selection_matches_intended_families() -> None:
    registry = load_source_family_registry(_registry_path())
    payload = select_release_families(registry, release_scope="v0.1-open")

    assert payload["selected_families"] == [
        "cloudphysics",
        "metacdn",
        "metakv",
        "twemcache",
        "wiki2018",
    ]


def test_citibike_and_brightkite_are_excluded_with_reasons() -> None:
    registry = load_source_family_registry(_registry_path())
    payload = select_release_families(registry, release_scope="v0.1-open")
    excluded = {entry["family"]: entry["reason"] for entry in payload["excluded_families"]}

    assert "citibike" in excluded
    assert "brightkite" in excluded
    assert "blocked_pending_review" in excluded["citibike"]
    assert "blocked_pending_review" in excluded["brightkite"]


def test_publication_clearance_is_explicit_and_fail_closed() -> None:
    registry = load_source_family_registry(_registry_path())
    clearance = {str(entry["family"]): str(entry["publication_clearance"]) for entry in registry}
    licenses = {str(entry["family"]): str(entry["upstream_license"]) for entry in registry}

    expected_public = {
        "cloudphysics": "CC BY 4.0",
        "metacdn": "Apache License 2.0",
        "metakv": "Apache License 2.0",
        "twemcache": "CC BY 4.0",
        "wiki2018": "CC0-1.0",
    }
    expected_blocked = {"brightkite", "citibike"}

    assert set(clearance) == set(expected_public) | expected_blocked
    assert {
        family for family, status in clearance.items() if status == "cleared_for_public_release"
    } == set(expected_public)
    assert {
        family for family, status in clearance.items() if status == "blocked"
    } == expected_blocked

    for family, expected_license in expected_public.items():
        assert licenses[family] == expected_license


def test_selector_output_contains_exclusion_reasons(tmp_path: Path) -> None:
    output_path = tmp_path / "lafc_evict_v0_1_open_families.json"
    result = subprocess.run(
        [
            sys.executable,
            str(_selector_script()),
            "--registry",
            str(_registry_path()),
            "--release-scope",
            "v0.1-open",
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload == written
    assert payload["warning"].endswith("It is not legal advice.")
    assert any(entry["reason"] for entry in payload["excluded_families"])


def test_selector_fails_clearly_when_registry_is_malformed(tmp_path: Path) -> None:
    bad_registry = tmp_path / "bad_registry.yaml"
    bad_registry.write_text("families:\n  - family: twemcache\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(_selector_script()),
            "--registry",
            str(bad_registry),
            "--release-scope",
            "v0.1-open",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "missing required fields" in result.stderr.lower()


def test_load_registry_rejects_missing_top_level_list(tmp_path: Path) -> None:
    bad_registry = tmp_path / "bad_top_level.yaml"
    bad_registry.write_text("not_families: []\n", encoding="utf-8")

    with pytest.raises(ValueError, match="top-level 'families' list"):
        load_source_family_registry(bad_registry)
