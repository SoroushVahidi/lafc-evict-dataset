import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from full_lib import (  # noqa: E402
    CAPACITIES, DECISIONS_PER_PRIMARY_STRATUM, DIAGNOSTIC_DECISIONS_PER_FAMILY,
    FAMILIES, HORIZONS, RANDOM_SEEDS,
)


def test_matrix_matches_frozen_design():
    assert FAMILIES == ("cloudphysics", "metacdn", "metakv", "twemcache", "wiki2018")
    assert CAPACITIES == (32, 128)
    assert HORIZONS == (4, 8, 16)
    assert RANDOM_SEEDS == tuple(range(10))
    assert DECISIONS_PER_PRIMARY_STRATUM == 500
    assert DIAGNOSTIC_DECISIONS_PER_FAMILY == 100


def test_primary_sample_size_is_5000():
    assert len(FAMILIES) * len(CAPACITIES) * DECISIONS_PER_PRIMARY_STRATUM == 5000


def test_diagnostic_sample_size_is_500():
    assert len(FAMILIES) * DIAGNOSTIC_DECISIONS_PER_FAMILY == 500


def test_reuses_pilot_reuse_distance_and_metrics_unchanged():
    # Confirms full_lib imports (not reimplements) the pilot-validated code.
    import full_lib
    assert full_lib.simulate_rollout_misses.__module__ == "lafc.evict_value_v2_rollout"
    assert full_lib.optimal_set_jaccard.__module__ == "metrics"
