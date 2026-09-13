#!/usr/bin/env python3
"""Regenerate the pairwise sample using the CURRENT (post-fix) code in this
checkout, against the CURRENT candidate_rows partitions (the same population
already used throughout the target-discriminativeness audit), with the
manifest-recorded parameters (seed=7, max_pairwise_rows=1_000_000,
max_pairs_per_decision=8).

Writes to an isolated location -- never overwrites the on-disk release file.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path("/home/soroush/projects/lafc-evict-dataset/repo")
sys.path.insert(0, str(REPO_ROOT / "src"))

from lafc_evict_dataset.real_release_build import (  # noqa: E402
    PAIRWISE_ORIENTATION_METHOD,
    _build_pairwise_sample,
    _duckdb_connect,
    _register_candidate_partitions,
)

RELEASE_ROOT = REPO_ROOT / "release" / "lafc-evict-v0.1-open-current-contract-preserved"
CANDIDATE_ROOT = RELEASE_ROOT / "data" / "candidate_rows"
OUT_DIR = Path(__file__).resolve().parent / "generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / "pairwise_sample.parquet"

MAX_PAIRWISE_ROWS = 1_000_000
MAX_PAIRS_PER_DECISION = 8
PAIRWISE_SEED = 7

manifest = json.loads(
    (RELEASE_ROOT / "metadata" / "release_manifest.json").read_text(encoding="utf-8")
)
recorded = manifest["pairwise_sample"]
assert recorded["max_pairwise_rows"] == MAX_PAIRWISE_ROWS
assert recorded["max_pairs_per_decision"] == MAX_PAIRS_PER_DECISION
assert recorded["pairwise_seed"] == PAIRWISE_SEED
print(f"Confirmed manifest-recorded params match: {recorded}")
print(f"Current code's PAIRWISE_ORIENTATION_METHOD = {PAIRWISE_ORIENTATION_METHOD!r}")

con = _duckdb_connect()
t0 = time.time()
_register_candidate_partitions(con, CANDIDATE_ROOT)
n_candidates = con.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
print(f"Registered candidates view: {n_candidates} rows in {time.time()-t0:.1f}s")

if OUT_PATH.exists():
    OUT_PATH.unlink()

t1 = time.time()
count = _build_pairwise_sample(
    con,
    pairwise_sample_path=OUT_PATH,
    max_pairwise_rows=MAX_PAIRWISE_ROWS,
    max_pairs_per_decision=MAX_PAIRS_PER_DECISION,
    pairwise_seed=PAIRWISE_SEED,
)
elapsed = time.time() - t1
print(f"Built pairwise sample: {count} rows in {elapsed:.1f}s -> {OUT_PATH}")

sha256 = hashlib.sha256(OUT_PATH.read_bytes()).hexdigest()
print(f"SHA256: {sha256}")

summary = con.execute(
    f"""
    SELECT
        COUNT(*) AS n_rows,
        SUM(is_tie) AS n_ties,
        SUM(label_a_better) AS n_a_better,
        SUM(label_b_better) AS n_b_better,
        COUNT(DISTINCT concat_ws('|', trace_name, dataset_source, capacity, horizon, decision_id, decision_t, decision_chunk_id, split)) AS n_unique_decisions
    FROM read_parquet('{OUT_PATH}')
    """
).fetchone()
cols = ["n_rows", "n_ties", "n_a_better", "n_b_better", "n_unique_decisions"]
report = dict(zip(cols, summary))
report["sha256"] = sha256
report["n_candidates_source"] = n_candidates
report["candidate_root"] = str(CANDIDATE_ROOT)
report["generator_function"] = "lafc_evict_dataset.real_release_build._build_pairwise_sample"
report["orientation_method"] = PAIRWISE_ORIENTATION_METHOD
report["max_pairwise_rows"] = MAX_PAIRWISE_ROWS
report["max_pairs_per_decision"] = MAX_PAIRS_PER_DECISION
report["pairwise_seed"] = PAIRWISE_SEED
report["elapsed_seconds"] = elapsed
report["output_path"] = str(OUT_PATH)

with open(OUT_DIR.parent / "regeneration_report.json", "w") as f:
    json.dump(report, f, indent=2, default=str)

print(json.dumps(report, indent=2, default=str))
