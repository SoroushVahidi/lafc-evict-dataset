#!/usr/bin/env python3
"""Regenerate the pairwise sample using the CURRENT (post-fix) generation
logic, reformulated for tractability.

WHY THIS EXISTS: calling `_build_pairwise_sample` from
`real_release_build.py` directly (unmodified) against the full 277,995,072-row
`candidates` view ran for >15 minutes with zero output and was killed. Root
cause: its `pairs` CTE self-joins `candidates a JOIN candidates b` on the
full, unfiltered 9-column decision key across ALL 277,995,072 rows, and only
afterwards joins to the small `sampled_decisions` filter. DuckDB's optimizer
did not push that filter ahead of the self-join (plausibly because the
LIMIT inside `sampled_decisions` is a computed scalar subquery, which can
block certain plan rewrites) -- so it was materializing on the order of the
FULL pairwise universe (~24.79 billion candidate pairs, matching the
`quadratic_expansion_effect` figure from the target-discriminativeness
audit's Phase 7 script) before ever applying the cap.

FIX (a provably equivalent reordering, not an approximation): filter
`candidates` down to only rows whose decision key is in `sampled_decisions`
*before* the self-join, producing `candidates_sampled`. This is a valid
rewrite because for any pair (a, b) that survives the original query, a and
b already share the same decision key (enforced by the a/b join condition)
and that key must be a member of `sampled_decisions` (enforced by the final
join) -- so pre-filtering both sides of the self-join to `sampled_decisions`
membership cannot drop or add any surviving pair. Every other clause below
(orientation hash formula, is_tie definition, row_number/pair_rank_in_decision
tie-break ordering, final ORDER BY, final LIMIT) is copied verbatim from
`lafc_evict_dataset.real_release_build._build_pairwise_sample` -- see that
function's source (as of this checkout's HEAD) for the byte-for-byte
comparison this script's docstring claims.
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
    DECISION_GROUP_COLUMNS,
    PAIRWISE_ORIENTATION_METHOD,
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

manifest = json.loads((RELEASE_ROOT / "metadata" / "release_manifest.json").read_text(encoding="utf-8"))
recorded = manifest["pairwise_sample"]
assert recorded["max_pairwise_rows"] == MAX_PAIRWISE_ROWS
assert recorded["max_pairs_per_decision"] == MAX_PAIRS_PER_DECISION
assert recorded["pairwise_seed"] == PAIRWISE_SEED
print(f"Confirmed manifest-recorded params match: {recorded}")
print(f"Current code's PAIRWISE_ORIENTATION_METHOD = {PAIRWISE_ORIENTATION_METHOD!r}")

group_cols = list(DECISION_GROUP_COLUMNS)
group_list = ", ".join(group_cols)

con = _duckdb_connect()
t0 = time.time()
_register_candidate_partitions(con, CANDIDATE_ROOT)
n_candidates = con.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
print(f"Registered candidates view: {n_candidates} rows in {time.time()-t0:.1f}s")

# --- sampled_decisions: verbatim logic from _build_pairwise_sample ---
t1 = time.time()
con.execute(
    f"""
    CREATE OR REPLACE TEMP TABLE sampled_decisions AS
    SELECT * FROM (
        SELECT DISTINCT {group_list} FROM candidates
    )
    ORDER BY hash(concat_ws('|', {group_list}, {str(PAIRWISE_SEED)!r}))
    LIMIT (
        SELECT GREATEST(
            1,
            CAST(CEIL({MAX_PAIRWISE_ROWS}::DOUBLE / GREATEST({MAX_PAIRS_PER_DECISION}, 1)) AS BIGINT)
        )
    )
    """
)
n_sampled_decisions = con.execute("SELECT COUNT(*) FROM sampled_decisions").fetchone()[0]
print(f"sampled_decisions: {n_sampled_decisions} decisions in {time.time()-t1:.1f}s")

# --- PROVABLY EQUIVALENT REWRITE: pre-filter candidates before the self-join ---
t2 = time.time()
join_sd = " AND ".join(f"c.{col} = d.{col}" for col in group_cols)
con.execute(
    f"""
    CREATE OR REPLACE TEMP TABLE candidates_sampled AS
    SELECT c.* FROM candidates c
    INNER JOIN sampled_decisions d ON {join_sd}
    """
)
n_candidates_sampled = con.execute("SELECT COUNT(*) FROM candidates_sampled").fetchone()[0]
print(f"candidates_sampled: {n_candidates_sampled} rows in {time.time()-t2:.1f}s")

# --- everything below is verbatim from _build_pairwise_sample, with
# `candidates` replaced by `candidates_sampled` and the now-redundant final
# `INNER JOIN sampled_decisions d` dropped (already enforced by the filter
# above) ---
join_same_decision = " AND ".join(f"a.{col} = b.{col}" for col in group_cols)
orientation_hash_expr = (
    "hash(concat_ws('|', "
    + ", ".join(f"CAST({col} AS VARCHAR)" for col in group_cols)
    + ", candidate_id_low, candidate_id_high, "
    + f"{PAIRWISE_ORIENTATION_METHOD!r}))"
)

if OUT_PATH.exists():
    OUT_PATH.unlink()

t3 = time.time()
con.execute(
    f"""
    COPY (
        WITH pairs AS (
            SELECT
                {", ".join(f"a.{col}" for col in group_cols)},
                CAST(a.candidate_page_id AS VARCHAR) AS candidate_id_low,
                CAST(b.candidate_page_id AS VARCHAR) AS candidate_id_high,
                a.y_loss AS y_loss_low,
                b.y_loss AS y_loss_high,
                row_number() OVER (
                    PARTITION BY {", ".join(f"a.{col}" for col in group_cols)}
                    ORDER BY CAST(a.candidate_page_id AS VARCHAR), CAST(b.candidate_page_id AS VARCHAR)
                ) AS pair_rank_in_decision
            FROM candidates_sampled a
            INNER JOIN candidates_sampled b
                ON {join_same_decision}
                AND CAST(a.candidate_page_id AS VARCHAR) < CAST(b.candidate_page_id AS VARCHAR)
        ),
        oriented AS (
            SELECT
                *,
                ({orientation_hash_expr} % 2 = 1) AS swap_orientation
            FROM pairs
        )
        SELECT
            {group_list},
            CASE WHEN swap_orientation THEN candidate_id_high ELSE candidate_id_low END AS candidate_a_page_id,
            CASE WHEN swap_orientation THEN candidate_id_low ELSE candidate_id_high END AS candidate_b_page_id,
            CASE WHEN swap_orientation THEN y_loss_high ELSE y_loss_low END AS y_loss_a,
            CASE WHEN swap_orientation THEN y_loss_low ELSE y_loss_high END AS y_loss_b,
            (
                CASE WHEN swap_orientation THEN y_loss_high ELSE y_loss_low END
                - CASE WHEN swap_orientation THEN y_loss_low ELSE y_loss_high END
            ) AS y_loss_diff_a_minus_b,
            CASE
                WHEN swap_orientation THEN CASE WHEN y_loss_high < y_loss_low THEN 1 ELSE 0 END
                ELSE CASE WHEN y_loss_low < y_loss_high THEN 1 ELSE 0 END
            END AS label_a_better,
            CASE
                WHEN swap_orientation THEN CASE WHEN y_loss_low < y_loss_high THEN 1 ELSE 0 END
                ELSE CASE WHEN y_loss_high < y_loss_low THEN 1 ELSE 0 END
            END AS label_b_better,
            CASE WHEN y_loss_low = y_loss_high THEN 1 ELSE 0 END AS is_tie
        FROM oriented
        WHERE pair_rank_in_decision <= {MAX_PAIRS_PER_DECISION}
        ORDER BY {group_list}, candidate_id_low, candidate_id_high
        LIMIT {MAX_PAIRWISE_ROWS}
    )
    TO {str(OUT_PATH)!r} (FORMAT PARQUET)
    """
)
elapsed = time.time() - t3
count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{OUT_PATH}')").fetchone()[0]
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
        COUNT(DISTINCT concat_ws('|', {group_list})) AS n_unique_decisions
    FROM read_parquet('{OUT_PATH}')
    """
).fetchone()
cols = ["n_rows", "n_ties", "n_a_better", "n_b_better", "n_unique_decisions"]
report = dict(zip(cols, summary))
report["sha256"] = sha256
report["n_candidates_source"] = n_candidates
report["n_sampled_decisions"] = n_sampled_decisions
report["n_candidates_sampled"] = n_candidates_sampled
report["candidate_root"] = str(CANDIDATE_ROOT)
report["generator_logic_source"] = "lafc_evict_dataset.real_release_build._build_pairwise_sample (verbatim except sampled_decisions pre-filter pushdown, proven equivalent -- see script docstring)"
report["orientation_method"] = PAIRWISE_ORIENTATION_METHOD
report["max_pairwise_rows"] = MAX_PAIRWISE_ROWS
report["max_pairs_per_decision"] = MAX_PAIRS_PER_DECISION
report["pairwise_seed"] = PAIRWISE_SEED
report["elapsed_seconds_pair_build"] = elapsed
report["output_path"] = str(OUT_PATH)

with open(OUT_DIR.parent / "regeneration_report.json", "w") as f:
    json.dump(report, f, indent=2, default=str)

print(json.dumps(report, indent=2, default=str))
