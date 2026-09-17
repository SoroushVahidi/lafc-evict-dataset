from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "metadata" / "model_feature_schema_v2.json"
VALIDATOR_SCRIPT = ROOT / "scripts" / "validate_model_features.py"


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_schema_file_is_valid_json_and_exists() -> None:
    schema = _load_schema()
    assert schema["schema_name"] == "lafc-evict-model-feature-schema-v2"


def test_official_feature_set_excludes_all_18_known_constants() -> None:
    schema = _load_schema()
    official = set(schema["rules"]["official_model_feature_set"])
    deprecated = {f["name"] for f in schema["deprecated_legacy_features"]}
    assert len(deprecated) == 18 + 1  # 18 constants + candidate_is_predictor_victim alias
    assert official.isdisjoint(deprecated)


def test_candidate_is_predictor_victim_is_deprecated_not_official() -> None:
    schema = _load_schema()
    official = set(schema["rules"]["official_model_feature_set"])
    deprecated_names = {f["name"] for f in schema["deprecated_legacy_features"]}
    assert "candidate_is_predictor_victim" not in official
    assert "candidate_is_predictor_victim" in deprecated_names
    entry = next(f for f in schema["deprecated_legacy_features"] if f["name"] == "candidate_is_predictor_victim")
    assert entry["category"] == "REDUNDANT_ALIAS"
    assert entry["duplicate_of"] == "candidate_is_lru_victim"


def test_labels_and_split_excluded_from_official_feature_set() -> None:
    schema = _load_schema()
    official = set(schema["rules"]["official_model_feature_set"])
    assert official.isdisjoint(set(schema["label_columns"]))
    assert official.isdisjoint(set(schema["split_column"]))
    assert official.isdisjoint(set(schema["prohibited_leakage_columns"]))


def test_official_feature_set_has_exactly_the_seven_valid_features() -> None:
    schema = _load_schema()
    official = schema["rules"]["official_model_feature_set"]
    assert set(official) == {
        "candidate_recency_rank",
        "candidate_age_norm",
        "candidate_lru_score",
        "candidate_is_lru_victim",
        "score_gap_to_lru_victim",
        "recent_candidate_request_rate",
        "recent_candidate_hit_rate",
    }


def test_validator_cli_passes_on_schema_alone() -> None:
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_SCRIPT), "--schema", str(SCHEMA_PATH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_validator_catches_a_reintroduced_constant_official_feature(tmp_path: Path) -> None:
    """Functional regression test: if a future edit silently reintroduces a
    constant column into the official feature set, or the data regresses to
    constant, the validator must fail closed, not pass silently."""
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT / "scripts"))
    import importlib

    validate_model_features = importlib.import_module("validate_model_features")

    schema = _load_schema()

    df = pd.DataFrame(
        {
            "candidate_recency_rank": [0.0] * 100,  # regressed to constant
            "candidate_age_norm": list(range(100)),
            "candidate_lru_score": list(range(100)),
            "candidate_is_lru_victim": [0.0, 1.0] * 50,
            "score_gap_to_lru_victim": list(range(100)),
            "recent_candidate_request_rate": list(range(100)),
            "recent_candidate_hit_rate": list(range(100)),
        }
    )
    parquet_path = tmp_path / "bad_candidate_rows.parquet"
    df.to_parquet(parquet_path, index=False)

    errors = validate_model_features.validate_data_against_schema(str(parquet_path), schema)
    assert any("candidate_recency_rank" in e and "constant" in e for e in errors)


def test_validator_catches_a_reintroduced_duplicate_pair(tmp_path: Path) -> None:
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT / "scripts"))
    import importlib

    validate_model_features = importlib.import_module("validate_model_features")

    schema = _load_schema()

    df = pd.DataFrame(
        {
            "candidate_recency_rank": list(range(100)),
            "candidate_age_norm": list(range(100)),  # duplicate of recency_rank
            "candidate_lru_score": list(range(100)),
            "candidate_is_lru_victim": [0.0, 1.0] * 50,
            "score_gap_to_lru_victim": list(range(100)),
            "recent_candidate_request_rate": list(range(100)),
            "recent_candidate_hit_rate": list(range(1, 101)),
        }
    )
    parquet_path = tmp_path / "dup_candidate_rows.parquet"
    df.to_parquet(parquet_path, index=False)

    errors = validate_model_features.validate_data_against_schema(str(parquet_path), schema)
    assert any(
        "candidate_recency_rank" in e and "candidate_age_norm" in e and "duplicate" in e for e in errors
    )


def test_real_release_candidate_rows_pass_model_feature_validation() -> None:
    candidate_rows = (
        ROOT
        / "release"
        / "lafc-evict-v0.1-open-current-contract-preserved"
        / "data"
        / "candidate_rows"
    )
    if not candidate_rows.exists():
        pytest.skip("canonical candidate rows not present in this checkout")
    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR_SCRIPT),
            "--schema",
            str(SCHEMA_PATH),
            "--candidate-rows-glob",
            str(candidate_rows / "**" / "*.parquet"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_alias_leakage_checks_and_feature_schema_reconciliation() -> None:
    """Verifies that the programmatic schema constants, JSON metadata, and forensic
    audit outputs are perfectly aligned, and that the redundant alias is exactly
    bit-identical (zero neq rows) to the LRU indicator on the audited dataset."""
    from lafc_evict_dataset.schema import ACTIVE_MODEL_FEATURES, DEPRECATED_LEGACY_FEATURES, FEATURE_COLUMNS
    
    # 1. Reconcile python schema constants with FEATURE_COLUMNS
    assert len(ACTIVE_MODEL_FEATURES) == 7
    assert len(DEPRECATED_LEGACY_FEATURES) == 19
    assert set(ACTIVE_MODEL_FEATURES).isdisjoint(set(DEPRECATED_LEGACY_FEATURES))
    assert set(ACTIVE_MODEL_FEATURES) | set(DEPRECATED_LEGACY_FEATURES) == set(FEATURE_COLUMNS)

    # 2. Reconcile JSON metadata with python schema constants
    schema = _load_schema()
    json_official = set(schema["rules"]["official_model_feature_set"])
    json_deprecated = {f["name"] for f in schema["deprecated_legacy_features"]}
    
    assert set(ACTIVE_MODEL_FEATURES) == json_official
    assert set(DEPRECATED_LEGACY_FEATURES) == json_deprecated

    # 3. Verify forensic audit bit-identity from validated artifacts
    audit_artifact_path = ROOT / "analysis" / "feature_provenance_repair_20260917" / "artifacts" / "alias_leakage_checks.json"
    if audit_artifact_path.exists():
        audit_payload = json.loads(audit_artifact_path.read_text(encoding="utf-8"))
        assert audit_payload["predictor_victim_neq_lru_victim_count"] == 0

