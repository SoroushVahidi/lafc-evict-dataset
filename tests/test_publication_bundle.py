from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

from lafc_evict_dataset.publication import (
    PUBLIC_RELEASE_ARTIFACT_RELATIVE_PATHS,
    collect_release_inventory,
    expected_hf_remote_paths,
    validate_public_text_file,
)
from lafc_evict_dataset.real_release_build import _checksum_lines, build_real_release
from lafc_evict_dataset.real_release_migration import migrate_real_release_contract
from lafc_evict_dataset.publication import (
    ASSOCIATED_PAPER_CITATION,
    ASSOCIATED_PAPER_STATUS,
    ASSOCIATED_PAPER_TITLE,
    SYNTHETIC_DISCLAIMER,
    token_like_matches,
)


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


def _real_release_dir(tmp_path: Path) -> Path:
    repo_root = _repo_root()
    source_dir = tmp_path / "real_source"
    shard_dir = source_dir / "shards"
    shard_dir.mkdir(parents=True)

    candidate_rows = pd.read_csv(repo_root / "examples" / "tiny_candidate_rows.csv")
    candidate_rows["trace_name"] = "cloudphysics_trace"
    candidate_rows["trace_family"] = "cloudphysics"
    candidate_rows["dataset_source"] = "cloudphysics-open"
    shard_path = shard_dir / "cloudphysics_demo__cap3.part0000.csv"
    candidate_rows.to_csv(shard_path, index=False)

    manifest_path = source_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "format": "evict_value_v1_wulver_candidate_csv_shards",
                "shards": [{"path": f"shards/{shard_path.name}", "row_count": int(len(candidate_rows))}],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    selection_path = tmp_path / "families.json"
    selection_path.write_text(
        json.dumps(
            {
                "selected_families": ["cloudphysics"],
                "excluded_families": [
                    {"family": "citibike", "reason": "blocked"},
                    {"family": "brightkite", "reason": "blocked"},
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    release_dir = tmp_path / "release" / "lafc-evict-v0.1-open"
    build_real_release(
        input_manifest=manifest_path,
        family_selection=selection_path,
        output_dir=release_dir,
        dataset_id="lafc-evict-v0.1-open",
        repo_root=repo_root,
        dry_run=False,
        overwrite=True,
        skip_disk_space_check=True,
        pairwise_sample=True,
        max_pairwise_rows=100,
        max_pairs_per_decision=4,
        duckdb_temp_dir=tmp_path / ".duckdb_tmp",
    )
    return release_dir


def _downgrade_release_to_stale_contract(release_dir: Path) -> None:
    candidate_paths = sorted((release_dir / "data" / "candidate_rows").rglob("candidate_rows.parquet"))
    candidates = pd.concat([pd.read_parquet(path) for path in candidate_paths], ignore_index=True)
    group_cols = ["decision_id", "capacity", "horizon", "split", "trace_family", "trace_name"]

    def _stale_row(group: pd.DataFrame) -> pd.Series:
        best = group["y_loss"].min()
        best_candidates = (
            group.loc[group["y_loss"] == best, "candidate_page_id"].astype(str).sort_values().tolist()
        )
        return pd.Series(
            {
                "candidate_count": int(group["candidate_page_id"].nunique()),
                "min_y_loss": float(group["y_loss"].min()),
                "max_y_loss": float(group["y_loss"].max()),
                "mean_y_loss": float(group["y_loss"].mean()),
                "tie_count": int((group["y_loss"] == best).sum()),
                "best_candidate_page_id": best_candidates[0],
            }
        )

    stale_decision_view = (
        candidates.groupby(group_cols, dropna=False, sort=True).apply(_stale_row).reset_index()
    )
    (release_dir / "data" / "decision_view" / "decision_view.parquet").unlink()
    stale_decision_view.to_parquet(release_dir / "data" / "decision_view" / "decision_view.parquet", index=False)

    manifest_path = release_dir / "metadata" / "release_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("dataset_name", None)
    manifest.pop("row_counts", None)
    manifest["candidate_row_count"] = int(len(candidates))
    manifest["decision_row_count"] = int(len(stale_decision_view))
    manifest["pairwise_sample_row_count"] = int(
        len(pd.read_parquet(release_dir / "data" / "pairwise_sample" / "pairwise_sample.parquet"))
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    checksums_path = release_dir / "metadata" / "checksums.sha256"
    checksums_path.write_text(
        "\n".join(_checksum_lines(release_dir, checksums_path)) + "\n",
        encoding="utf-8",
    )


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
    assert manifest["source_release_name"] == release_dir.name
    assert manifest["release_artifact_paths"] == PUBLIC_RELEASE_ARTIFACT_RELATIVE_PATHS
    assert manifest["publication_status"] == "draft_local"
    assert SYNTHETIC_DISCLAIMER in readme
    assert SYNTHETIC_DISCLAIMER in dataset_card
    assert validate_public_text_file(bundle_dir / "publication_manifest.json") == []
    assert dataset_card.startswith("---\n")
    assert 'pretty_name: "LAFC-Evict Sample"' in dataset_card
    assert 'license: "mit"' in dataset_card
    assert "tags:" in dataset_card
    assert "task_categories:" in dataset_card
    assert "size_categories:" in dataset_card
    assert "configs:" in dataset_card
    metadata = zenodo_metadata["metadata"]
    assert metadata["license"] == "MIT"
    assert SYNTHETIC_DISCLAIMER in metadata["description"]
    assert "Soroush Vahidi" in metadata["description"]
    assert ASSOCIATED_PAPER_TITLE in metadata["description"]
    assert ASSOCIATED_PAPER_CITATION in metadata["description"]
    assert ASSOCIATED_PAPER_STATUS in metadata["description"]
    assert "Soroush Vahidi" in metadata["notes"]
    assert ASSOCIATED_PAPER_CITATION in metadata["notes"]
    assert ASSOCIATED_PAPER_STATUS in metadata["notes"]


def test_prepare_publication_bundle_from_real_release_with_pairwise_sample(tmp_path: Path) -> None:
    release_dir = _real_release_dir(tmp_path)
    inventory = collect_release_inventory(release_dir)
    bundle_dir = tmp_path / "publication" / "bundles" / "lafc-evict-v0.1-open"

    assert inventory.has_pairwise_view is False
    assert inventory.has_pairwise_sample is True
    assert "data/pairwise_sample/" in expected_hf_remote_paths(inventory)
    assert "data/pairwise_view/" not in expected_hf_remote_paths(inventory)

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

    manifest = json.loads((bundle_dir / "publication_manifest.json").read_text(encoding="utf-8"))
    dataset_card = (bundle_dir / "dataset_card.md").read_text(encoding="utf-8")

    assert manifest["release_type"] == "real_public"
    assert manifest["source_release_name"] == release_dir.name
    assert manifest["release_artifact_paths"] == PUBLIC_RELEASE_ARTIFACT_RELATIVE_PATHS
    assert manifest["has_pairwise_view"] is False
    assert manifest["has_pairwise_sample"] is True
    assert validate_public_text_file(bundle_dir / "publication_manifest.json") == []
    assert 'pretty_name: "LAFC-Evict v0.1 Open"' in dataset_card
    assert SYNTHETIC_DISCLAIMER not in dataset_card


def test_prepare_publication_bundle_from_migrated_stale_real_release(tmp_path: Path) -> None:
    stale_release = _real_release_dir(tmp_path)
    _downgrade_release_to_stale_contract(stale_release)

    migrated_release = tmp_path / "release" / "lafc-evict-v0.1-open-current-contract"
    migrate_real_release_contract(
        source_release_dir=stale_release,
        output_dir=migrated_release,
        repo_root=_repo_root(),
        staging_mode="copy",
        duckdb_temp_dir=tmp_path / ".duckdb_tmp_migrate",
    )

    inventory = collect_release_inventory(migrated_release)
    bundle_dir = tmp_path / "publication" / "bundles" / "lafc-evict-v0.1-open-current-contract"

    assert inventory.has_pairwise_view is False
    assert inventory.has_pairwise_sample is True
    assert "data/pairwise_sample/" in expected_hf_remote_paths(inventory)

    subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "scripts" / "prepare_publication_bundle.py"),
            "--release-dir",
            str(migrated_release),
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

    manifest = json.loads((bundle_dir / "publication_manifest.json").read_text(encoding="utf-8"))
    assert manifest["dataset_name"] == "lafc-evict-v0.1-open"
    assert manifest["release_type"] == "real_public"
    assert manifest["has_pairwise_sample"] is True
    assert manifest["source_release_name"] == migrated_release.name
    assert manifest["release_artifact_paths"] == PUBLIC_RELEASE_ARTIFACT_RELATIVE_PATHS
    assert validate_public_text_file(bundle_dir / "publication_manifest.json") == []


def test_token_like_detector_catches_fake_tokens() -> None:
    text = "Fake values: " + ("h" "f_") + ("a" * 32) + " " + ("g" "hp_") + ("b" * 32)
    matches = token_like_matches(text)
    assert any(match.startswith("hf_") for match in matches)
    assert any(match.startswith("ghp_") for match in matches)
