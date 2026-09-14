"""Shared library for the FULL continuation-policy-sensitivity experiment.

Deliberately imports pilot_lib.py and metrics.py UNCHANGED from the
already-committed, already-tested pilot implementation
(experiment/continuation-sensitivity-pilot-20260914 @ 3b3b6d7) rather than
reimplementing them here -- this is the same validated code path the pilot
used (52,480/52,480 LRU-equivalence comparisons, 0 mismatches; 23/23
pilot validity gates; 32/32 unit tests), not a fresh reimplementation that
could silently diverge in semantics.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PILOT_SCRIPTS_DIR = (
    "/home/soroush/projects/lafc-evict-dataset/repo/.claude/worktrees/"
    "continuation-sensitivity-pilot-20260914/analysis/"
    "continuation_policy_sensitivity_pilot_20260914/scripts"
)
if PILOT_SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, PILOT_SCRIPTS_DIR)

# Re-exported, unchanged, from the pilot implementation:
from pilot_lib import (  # noqa: E402,F401
    AUGMENTED_CACHING_PILOT_SRC,
    PROCESSED_TRACE_DIR,
    _simulate_lru_misses,
    assert_no_learned_policy,
    build_requests_from_lists,
    enumerate_decision_positions,
    load_trace,
    reconstruct_candidates_at_t,
    sha256_file,
    sha256_text,
    simulate_rollout_misses,
    summarize_decision_at,
)
from metrics import (  # noqa: E402,F401
    cross_continuation_regret,
    kendall_tau_b,
    optimal_set_jaccard,
    pairwise_taxonomy,
)

# ---------------------------------------------------------------------------
# Full-experiment matrix, verbatim from
# analysis/continuation_policy_sensitivity_design_20260914/{DESIGN,MATRIX}.md
# ---------------------------------------------------------------------------

FAMILIES: Tuple[str, ...] = ("cloudphysics", "metacdn", "metakv", "twemcache", "wiki2018")
CAPACITIES: Tuple[int, ...] = (32, 128)
HORIZONS: Tuple[int, ...] = (4, 8, 16)
PRIMARY_STRATIFICATION_HORIZON = 16  # baseline-LRU stratification uses H=16, the design's primary horizon
DECISIONS_PER_PRIMARY_STRATUM = 500
DIAGNOSTIC_DECISIONS_PER_FAMILY = 100
FULL_SAMPLING_SEED = 20260914
SELECTION_SUBSAMPLE_SIZE = 1000  # per-stratum stage-1 pool size before stratified/decile selection
RANDOM_SEEDS: Tuple[int, ...] = tuple(range(10))  # pilot-validated; escalation criterion did not trigger

EXPECTED_TRACE_SHA256 = {
    "cloudphysics": "fedb3d31ee3c1dd847d25f967392cdf0fdec1e9c1fbb6808772e281bc8d4fb57",
    "metacdn": "7301f02e1373cb7e06f1ed2c417a8ebe16581319354780f811c8d032391f4e73",
    "metakv": "4c229e841d546cd57a2edb6e3ddc53461ff4dc03d366e9d24e4239a89db7e0de",
    "twemcache": "62df27062ce2595c843fd91e01d26c9783ff8f165f6b26e983696eda7ada0bb9",
    "wiki2018": "3813084bebfcf463ac22a685494b46aea45aded55d314411c9fbb058b5d67608",
}

SPLIT_LABEL = {"cloudphysics": "test", "metacdn": "validation", "metakv": "test",
               "twemcache": "test", "wiki2018": "test"}
