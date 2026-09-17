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

The `pairwise_sample` view is intentionally NOT included: the source tree's
`pairwise_sample.parquet` is documented as stale/non-canonical
(`docs/CURRENT_PROJECT_STATUS_AND_HANDOFF.md` section 7 -- six-column vs.
nine-column decision-selection key bug), and promoting the corrected
regenerated sample into a public release is explicitly flagged in that same
document as requiring "a separate release decision." The manuscript's
headline benchmark claim (277,995,072 candidate rows / 2,363,286 decisions)
does not depend on the pairwise sample, so this script leaves that decision
out of scope.
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

    return {
        "candidate_partitions_transformed": n_transformed,
        "candidate_partitions_linked": n_linked,
        "candidate_partitions_total": len(parquet_files),
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

    return {
        "total_candidate_rows": int(total),
        "by_family": {k: int(v) for k, v in by_family},
        "by_capacity": {int(k): int(v) for k, v in by_capacity},
        "by_horizon": {int(k): int(v) for k, v in by_horizon},
        "by_split": {k: int(v) for k, v in by_split},
        "families_seen": families_seen,
        "decision_view_rows": int(decision_view_rows),
        "wiki2018_unpseudonymized_leak_count": int(leaked_raw_titles),
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

    ok = (
        recount["total_candidate_rows"] == EXPECTED_CANDIDATE_ROWS
        and recount["decision_view_rows"] == EXPECTED_DECISION_ROWS
        and recount["families_seen"] == sorted(SELECTED_FAMILIES)
        and recount["wiki2018_unpseudonymized_leak_count"] == 0
    )
    print(json.dumps({"matches_manuscript_corpus": ok}, indent=2))
    if not ok:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
