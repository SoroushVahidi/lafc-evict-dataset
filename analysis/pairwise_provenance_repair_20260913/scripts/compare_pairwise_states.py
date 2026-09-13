#!/usr/bin/env python3
"""Compare three states of the LAFC-Evict pairwise sample (Phase 3 of the
pairwise-provenance repair):

A. the stale on-disk release file
   release/lafc-evict-v0.1-open-current-contract-preserved/data/pairwise_sample/pairwise_sample.parquet
B. the newly regenerated post-fix sample (current code, current candidate
   population, manifest-recorded seed/params)
   analysis/pairwise_provenance_repair_20260913/generated/pairwise_sample.parquet
C. the manuscript-committed summary (aggregate counts only -- no row-level
   data was ever committed, since release/ is gitignored)
   paper/sigmod2027/results/metadata_tables/table_pairwise_sample_label_summary.csv

This script only reads; it never writes to the stale release file.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import duckdb
import pandas as pd

REPO_ROOT = Path("/home/soroush/projects/lafc-evict-dataset/repo")
STALE_PATH = REPO_ROOT / "release/lafc-evict-v0.1-open-current-contract-preserved/data/pairwise_sample/pairwise_sample.parquet"
REGEN_PATH = Path(
    "/tmp/claude-1000/-home-soroush/8a66210e-4d63-4b01-b3ba-10065c25f134/"
    "scratchpad/pairwise_repair/generated/pairwise_sample.parquet"
)
MANUSCRIPT_CSV = REPO_ROOT / "paper/sigmod2027/results/metadata_tables/table_pairwise_sample_label_summary.csv"
OUT_DIR = Path(__file__).resolve().parent.parent / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

con = duckdb.connect()


def summarize(path: Path) -> dict[str, object]:
    row = con.execute(
        f"""
        SELECT
            COUNT(*) AS n_rows,
            SUM(is_tie) AS n_ties,
            SUM(label_a_better) AS n_a_better,
            SUM(label_b_better) AS n_b_better
        FROM read_parquet('{path}')
        """
    ).fetchone()
    cols = ["n_rows", "n_ties", "n_a_better", "n_b_better"]
    out = dict(zip(cols, row))
    out["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    out["size_bytes"] = path.stat().st_size
    out["path"] = str(path)
    return out


report: dict[str, object] = {}
report["A_stale"] = summarize(STALE_PATH)

if REGEN_PATH.exists():
    report["B_regenerated"] = summarize(REGEN_PATH)
else:
    report["B_regenerated"] = {"status": "not yet generated"}

manuscript_df = pd.read_csv(MANUSCRIPT_CSV)
report["C_manuscript"] = {
    "n_a_better": int(manuscript_df["label_a_better_rows"].iloc[0]),
    "n_b_better": int(manuscript_df["label_b_better_rows"].iloc[0]),
    "n_ties": int(manuscript_df["is_tie_rows"].iloc[0]),
    "n_rows": int(manuscript_df[["label_a_better_rows", "label_b_better_rows", "is_tie_rows"]].sum(axis=1).iloc[0]),
    "path": str(MANUSCRIPT_CSV),
    "note": "aggregate counts only -- row-level pair identities were never committed to git (release/ is gitignored)",
}

if REGEN_PATH.exists():
    a = report["A_stale"]
    b = report["B_regenerated"]
    c = report["C_manuscript"]
    report["comparison"] = {
        "A_vs_B_identical_bytes": a["sha256"] == b["sha256"],
        "A_vs_B_tie_count_diff": a["n_ties"] - b["n_ties"],
        "B_vs_C_tie_count_diff": b["n_ties"] - c["n_ties"],
        "A_vs_C_tie_count_diff": a["n_ties"] - c["n_ties"],
        "B_matches_C_exactly": (b["n_ties"] == c["n_ties"] and b["n_a_better"] == c["n_a_better"] and b["n_b_better"] == c["n_b_better"]),
        "A_matches_C_exactly": (a["n_ties"] == c["n_ties"] and a["n_a_better"] == c["n_a_better"] and a["n_b_better"] == c["n_b_better"]),
    }

    # Same-unordered-pair-identity check between A and B (only possible between
    # A and B, since C has no row-level data committed to git).
    # pairwise_sample.parquet's schema only carries 5 decision-identifying
    # columns (trace_name, capacity, horizon, decision_id, split), not the
    # full 9-column canonical decision key -- this is the shipped schema, not
    # a simplification introduced by this script.
    pair_key_expr = (
        "concat_ws('|', trace_name, capacity, horizon, decision_id, split, "
        "LEAST(candidate_a_page_id, candidate_b_page_id), "
        "GREATEST(candidate_a_page_id, candidate_b_page_id))"
    )
    overlap = con.execute(
        f"""
        WITH a_keys AS (SELECT {pair_key_expr} AS k FROM read_parquet('{STALE_PATH}')),
             b_keys AS (SELECT {pair_key_expr} AS k FROM read_parquet('{REGEN_PATH}'))
        SELECT
            (SELECT COUNT(*) FROM a_keys) AS a_n,
            (SELECT COUNT(*) FROM b_keys) AS b_n,
            (SELECT COUNT(*) FROM a_keys INNER JOIN b_keys USING (k)) AS overlap_n
        """
    ).fetchone()
    a_n, b_n, overlap_n = overlap
    report["pair_identity_overlap_A_vs_B"] = {
        "a_unordered_pairs": a_n,
        "b_unordered_pairs": b_n,
        "overlap_unordered_pairs": overlap_n,
        "overlap_fraction_of_a": overlap_n / a_n if a_n else None,
        "same_unordered_pair_sample": overlap_n == a_n == b_n,
    }

with open(OUT_DIR / "pairwise_three_state_comparison.json", "w") as f:
    json.dump(report, f, indent=2, default=str)

print(json.dumps(report, indent=2, default=str))
