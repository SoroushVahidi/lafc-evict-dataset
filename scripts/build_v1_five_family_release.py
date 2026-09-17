from __future__ import annotations

"""Package the canonical five-family LAFC-Evict candidate-row corpus
(`cloudphysics`/"Alibaba Block", `metacdn`, `metakv`, `twemcache`, `wiki2018`)
into a public-release-ready tree.

This does NOT regenerate any labels. It repackages the already-validated
canonical candidate rows and decision view from
`release/lafc-evict-v0.1-open-current-contract-preserved` (the tree whose
`release_manifest.json` records 277,995,072 candidate rows / 2,363,286
decisions -- the exact corpus underlying the Performance Evaluation
manuscript's evaluated five-family benchmark).

The only per-row transformation applied is deterministic pseudonymization of
`wiki2018`'s raw Wikipedia page-title identifiers (`candidate_page_id` in
candidate rows, `optimal_candidate_page_ids` in the decision view), reusing
the exact scheme already used and published for the v0.2/v0.3 wiki2018
releases (`lafc_evict_dataset.preview.pseudonymize_object_id`). The other
four families' candidate identifiers are already opaque
(numeric/hash-like or upstream-anonymized tokens, per
`docs/V0_3_V1_DATA_INVENTORY.md` section 7) and are packaged unchanged, via
hardlink where possible to avoid duplicating ~2.6 GB of already-validated
Parquet bytes on disk.

The `pairwise_sample` view uses the CANONICAL regenerated sample at
`analysis/pairwise_provenance_repair_20260913/artifacts/pairwise_sample_regenerated_canonical.parquet`
(SHA256 `1d770c6999ac999673b46805a6ca173e24b116793b35405d2d211cae7b9eda02`,
tracked in git), NOT the source tree's own
`data/pairwise_sample/pairwise_sample.parquet`, which is documented as
stale/non-canonical (`docs/CURRENT_PROJECT_STATUS_AND_HANDOFF.md` section 7
-- six-column vs. nine-column decision-selection key bug, plus a pre-fix A/B
orientation bug). The canonical sample's label distribution
(a_better=60,673, b_better=61,065, tie=878,262), non-tie count (121,738,
including 2,211 in `test`), and A/B orientation balance (~49.8%/50.2%)
already match the manuscript's committed tables exactly
(`analysis/pairwise_provenance_repair_20260913/REPORT.md`); this script
additionally applies the same wiki2018 pseudonymization used for candidate
rows/decision view to `candidate_a_page_id`/`candidate_b_page_id`, since the
canonical sample (like the source candidate rows before this script's other
transform) still carries raw Wikipedia page titles for wiki2018 rows.
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pandas as pd  # noqa: E402
import pyarrow as pa  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

from lafc_evict_dataset.preview import pseudonymize_object_id  # noqa: E402
from lafc_evict_dataset.io import sha256_file  # noqa: E402

PSEUDONYMIZED_FAMILY = "wiki2018"
SELECTED_FAMILIES = ["cloudphysics", "metacdn", "metakv", "twemcache", "wiki2018"]
EXCLUDED_FAMILIES = ["brightkite", "citibike"]
EXPECTED_CANDIDATE_ROWS = 277_995_072
EXPECTED_DECISION_ROWS = 2_363_286
EXPECTED_PAIRWISE_ROWS = 1_000_000
CANONICAL_PAIRWISE_SAMPLE = (
    ROOT / "analysis" / "pairwise_provenance_repair_20260913" / "artifacts"
    / "pairwise_sample_regenerated_canonical.parquet"
)
CANONICAL_PAIRWISE_SAMPLE_SHA256 = "1d770c6999ac999673b46805a6ca173e24b116793b35405d2d211cae7b9eda02"


def hardlink_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        import shutil

        shutil.copy2(src, dst)


def transform_candidate_partition(src: Path, dst: Path) -> None:
    # Use ParquetFile.read() (not pq.read_table's dataset-factory path): some
    # DT-8 shards store `split` as plain string, others as dictionary<string>
    # (a known pre-existing inconsistency, see V0_3_V1_RELEASE_DESIGN.md
    # section 6). The dataset-factory path fails trying to unify schemas
    # across files; reading one file directly avoids that entirely.
    table = pq.ParquetFile(src).read()
    df = table.to_pandas()
    df["candidate_page_id"] = df["candidate_page_id"].map(pseudonymize_object_id)
    if "split" in df.columns:
        df["split"] = df["split"].astype("string").astype(object)
    dst.parent.mkdir(parents=True, exist_ok=True)
    out_table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(out_table, dst)


def transform_decision_view(src: Path, dst: Path) -> None:
    df = pd.read_parquet(src)
    mask = df["trace_family"].astype(str) == PSEUDONYMIZED_FAMILY

    def pseudonymize_id_list(value: object) -> object:
        if value is None:
            return value
        text = str(value)
        if not text:
            return text
        parts = text.split("|")
        return "|".join(pseudonymize_object_id(part) for part in parts)

    df.loc[mask, "optimal_candidate_page_ids"] = df.loc[mask, "optimal_candidate_page_ids"].map(
        pseudonymize_id_list
    )
    dst.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(dst, index=False)


def transform_pairwise_sample(src: Path, dst: Path) -> None:
    actual_sha256 = sha256_file(src)
    if actual_sha256 != CANONICAL_PAIRWISE_SAMPLE_SHA256:
        raise SystemExit(
            f"Canonical pairwise sample checksum mismatch: expected {CANONICAL_PAIRWISE_SAMPLE_SHA256}, "
            f"got {actual_sha256}. Refusing to package a pairwise sample that does not match the "
            "checksum recorded in analysis/pairwise_provenance_repair_20260913/ARTIFACT_MANIFEST.md."
        )
    df = pd.read_parquet(src)
    mask = df["trace_family"].astype(str) == PSEUDONYMIZED_FAMILY
    df.loc[mask, "candidate_a_page_id"] = df.loc[mask, "candidate_a_page_id"].map(pseudonymize_object_id)
    df.loc[mask, "candidate_b_page_id"] = df.loc[mask, "candidate_b_page_id"].map(pseudonymize_object_id)
    dst.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(dst, index=False)


def build(source_root: Path, output_root: Path, *, overwrite: bool) -> dict:
    if output_root.exists() and any(output_root.iterdir()) and not overwrite:
        raise SystemExit(f"Output dir {output_root} already exists and is non-empty; pass --overwrite")

    candidate_src_root = source_root / "data" / "candidate_rows"
    candidate_dst_root = output_root / "data" / "candidate_rows"
    parquet_files = sorted(candidate_src_root.rglob("candidate_rows.parquet"))
    if not parquet_files:
        raise SystemExit(f"No candidate_rows.parquet files found under {candidate_src_root}")

    n_transformed = 0
    n_linked = 0
    for src_file in parquet_files:
        rel = src_file.relative_to(candidate_src_root)
        dst_file = candidate_dst_root / rel
        if f"trace_family={PSEUDONYMIZED_FAMILY}" in str(rel):
            transform_candidate_partition(src_file, dst_file)
            n_transformed += 1
        else:
            hardlink_or_copy(src_file, dst_file)
            n_linked += 1

    transform_decision_view(
        source_root / "data" / "decision_view" / "decision_view.parquet",
        output_root / "data" / "decision_view" / "decision_view.parquet",
    )

    transform_pairwise_sample(
        CANONICAL_PAIRWISE_SAMPLE,
        output_root / "data" / "pairwise_sample" / "pairwise_sample.parquet",
    )

    return {
        "candidate_partitions_transformed": n_transformed,
        "candidate_partitions_linked": n_linked,
        "candidate_partitions_total": len(parquet_files),
        "pairwise_sample_source": str(CANONICAL_PAIRWISE_SAMPLE),
    }


def independent_recount(output_root: Path) -> dict:
    import duckdb

    con = duckdb.connect()
    candidate_glob = str(output_root / "data" / "candidate_rows" / "**" / "*.parquet")
    total = con.execute(f"SELECT COUNT(*) FROM read_parquet('{candidate_glob}', hive_partitioning=1)").fetchone()[0]
    by_family = con.execute(
        f"SELECT trace_family, COUNT(*) FROM read_parquet('{candidate_glob}', hive_partitioning=1) GROUP BY 1 ORDER BY 1"
    ).fetchall()
    by_capacity = con.execute(
        f"SELECT capacity, COUNT(*) FROM read_parquet('{candidate_glob}', hive_partitioning=1) GROUP BY 1 ORDER BY 1"
    ).fetchall()
    by_horizon = con.execute(
        f"SELECT horizon, COUNT(*) FROM read_parquet('{candidate_glob}', hive_partitioning=1) GROUP BY 1 ORDER BY 1"
    ).fetchall()
    by_split = con.execute(
        f"SELECT split, COUNT(*) FROM read_parquet('{candidate_glob}', hive_partitioning=1) GROUP BY 1 ORDER BY 1"
    ).fetchall()
    families_seen = sorted(r[0] for r in by_family)
    decision_view_rows = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{output_root / 'data' / 'decision_view' / 'decision_view.parquet'}')"
    ).fetchone()[0]

    # pseudonymization sanity: no wiki2018 candidate_page_id should still look
    # like a raw "en:..." page title after transformation.
    leaked_raw_titles = con.execute(
        f"""
        SELECT COUNT(*) FROM read_parquet('{candidate_glob}', hive_partitioning=1)
        WHERE trace_family = 'wiki2018' AND candidate_page_id NOT LIKE 'obj\\_%' ESCAPE '\\'
        """
    ).fetchone()[0]

    pairwise_path = output_root / "data" / "pairwise_sample" / "pairwise_sample.parquet"
    pairwise_stats: dict[str, object] = {}
    if pairwise_path.exists():
        pairwise_stats["total_rows"] = int(
            con.execute(f"SELECT COUNT(*) FROM read_parquet('{pairwise_path}')").fetchone()[0]
        )
        label_row = con.execute(
            f"SELECT SUM(label_a_better), SUM(label_b_better), SUM(is_tie) FROM read_parquet('{pairwise_path}')"
        ).fetchone()
        pairwise_stats["a_better"] = int(label_row[0])
        pairwise_stats["b_better"] = int(label_row[1])
        pairwise_stats["tie"] = int(label_row[2])
        pairwise_stats["unique_decisions"] = int(
            con.execute(f"SELECT COUNT(DISTINCT decision_id) FROM read_parquet('{pairwise_path}')").fetchone()[0]
        )
        pairwise_stats["by_split"] = {
            k: int(v)
            for k, v in con.execute(
                f"SELECT split, COUNT(*) FROM read_parquet('{pairwise_path}') GROUP BY 1 ORDER BY 1"
            ).fetchall()
        }
        pairwise_stats["by_family"] = {
            k: int(v)
            for k, v in con.execute(
                f"SELECT trace_family, COUNT(*) FROM read_parquet('{pairwise_path}') GROUP BY 1 ORDER BY 1"
            ).fetchall()
        }
        pairwise_stats["wiki2018_unpseudonymized_leak_count"] = int(
            con.execute(
                f"""
                SELECT COUNT(*) FROM read_parquet('{pairwise_path}')
                WHERE trace_family = 'wiki2018'
                  AND (candidate_a_page_id NOT LIKE 'obj\\_%' ESCAPE '\\'
                       OR candidate_b_page_id NOT LIKE 'obj\\_%' ESCAPE '\\')
                """
            ).fetchone()[0]
        )

    return {
        "total_candidate_rows": int(total),
        "by_family": {k: int(v) for k, v in by_family},
        "by_capacity": {int(k): int(v) for k, v in by_capacity},
        "by_horizon": {int(k): int(v) for k, v in by_horizon},
        "by_split": {k: int(v) for k, v in by_split},
        "families_seen": families_seen,
        "decision_view_rows": int(decision_view_rows),
        "wiki2018_unpseudonymized_leak_count": int(leaked_raw_titles),
        "pairwise_sample": pairwise_stats,
    }


def write_checksums(output_root: Path, checksums_path: Path) -> None:
    lines = []
    for file_path in sorted(output_root.rglob("*")):
        if file_path.is_file() and file_path.resolve() != checksums_path.resolve():
            digest = sha256_file(file_path)
            rel = file_path.relative_to(output_root).as_posix()
            lines.append(f"{digest}  {rel}")
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    checksums_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root",
        default=str(ROOT / "release" / "lafc-evict-v0.1-open-current-contract-preserved"),
    )
    parser.add_argument("--output-root", default=str(ROOT / "release" / "lafc-evict-v1.0"))
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--recount-only", action="store_true", help="Skip build, only run independent recount")
    args = parser.parse_args()

    source_root = Path(args.source_root).resolve()
    output_root = Path(args.output_root).resolve()

    if not args.recount_only:
        build_stats = build(source_root, output_root, overwrite=args.overwrite)
        print(json.dumps({"build_stats": build_stats}, indent=2))

    recount = independent_recount(output_root)
    print(json.dumps({"independent_recount": recount}, indent=2))

    pairwise = recount.get("pairwise_sample") or {}
    ok = (
        recount["total_candidate_rows"] == EXPECTED_CANDIDATE_ROWS
        and recount["decision_view_rows"] == EXPECTED_DECISION_ROWS
        and recount["families_seen"] == sorted(SELECTED_FAMILIES)
        and recount["wiki2018_unpseudonymized_leak_count"] == 0
        and pairwise.get("total_rows") == EXPECTED_PAIRWISE_ROWS
        and pairwise.get("a_better") == 60_673
        and pairwise.get("b_better") == 61_065
        and pairwise.get("tie") == 878_262
        and pairwise.get("wiki2018_unpseudonymized_leak_count") == 0
    )
    print(json.dumps({"matches_manuscript_corpus": ok}, indent=2))
    if not ok:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
