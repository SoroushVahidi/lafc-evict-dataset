#!/usr/bin/env python3
"""Extract metadata-backed benchmark tables for the SIGMOD paper.

This script intentionally avoids scanning candidate-row parquet shards. It only
reads the preserved release manifest, checksums file, decision view parquet, and
pairwise sample parquet files.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable

import duckdb
import pyarrow.parquet as pq


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--release-root",
        default="release/lafc-evict-v0.1-open-current-contract-preserved",
        help="Path to the preserved release root.",
    )
    parser.add_argument(
        "--results-dir",
        default="paper/sigmod2027/results/metadata_tables",
        help="Directory for Markdown and CSV outputs.",
    )
    parser.add_argument(
        "--latex-tables-dir",
        default="paper/sigmod2027/latex/tables",
        help="Directory for generated LaTeX table files.",
    )
    parser.add_argument(
        "--bundle-dir",
        default="/tmp/lafc-evict-v0.1-open-current-contract-preserved-publication-bundle",
        help="Optional existing local publication bundle directory.",
    )
    return parser.parse_args()


def fmt_int(value: object) -> str:
    if value is None:
        return "pending"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        if value.is_integer():
            return f"{int(value):,}"
        return f"{value:,.2f}"
    return str(value)


def latex_escape(text: object) -> str:
    s = str(text)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    for src, dst in replacements.items():
        s = s.replace(src, dst)
    return s


def write_csv(path: Path, rows: list[dict[str, object]], headers: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, object]], headers: list[str], *, title: str | None = None, intro: str | None = None) -> None:
    lines: list[str] = []
    if title:
        lines.append(f"# {title}")
        lines.append("")
    if intro:
        lines.append(intro)
        lines.append("")
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(fmt_int(row.get(header, "")) for header in headers) + " |")
    lines.append("")
    path.write_text("\n".join(lines))


def latex_table(
    *,
    caption: str,
    label: str,
    headers: list[str],
    rows: list[dict[str, object]],
    align: str,
    size: str = r"\small",
) -> str:
    lines = [
        r"\begin{table}[t]",
        r"  \centering",
        f"  {size}",
        f"  \\caption{{{latex_escape(caption)}}}",
        f"  \\label{{{label}}}",
        f"  \\begin{{tabular}}{{{align}}}",
        r"    \toprule",
        "    " + " & ".join(latex_escape(h) for h in headers) + r" \\",
        r"    \midrule",
    ]
    for row in rows:
        lines.append("    " + " & ".join(latex_escape(fmt_int(row.get(h, ""))) for h in headers) + r" \\")
    lines.extend(
        [
            r"    \bottomrule",
            r"  \end{tabular}",
            r"\end{table}",
            "",
        ]
    )
    return "\n".join(lines)


def write_latex(path: Path, content: str) -> None:
    path.write_text(content)


def render_section_markdown(
    path: Path,
    *,
    title: str,
    intro: str,
    sections: list[tuple[str, list[dict[str, object]], list[str]]],
) -> None:
    lines = [f"# {title}", "", intro, ""]
    for heading, rows, headers in sections:
        lines.append(f"## {heading}")
        lines.append("")
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for row in rows:
            lines.append("| " + " | ".join(fmt_int(row.get(header, "")) for header in headers) + " |")
        lines.append("")
    path.write_text("\n".join(lines))


def compact_counts(rows: Iterable[dict[str, object]], key: str, value: str) -> str:
    return "; ".join(f"{row[key]}={fmt_int(row[value])}" for row in rows)


def query_rows(conn: duckdb.DuckDBPyConnection, sql: str) -> list[dict[str, object]]:
    result = conn.execute(sql)
    columns = [item[0] for item in result.description]
    return [dict(zip(columns, row)) for row in result.fetchall()]


def parquet_row_count(path: Path) -> int:
    return pq.ParquetFile(path).metadata.num_rows


def main() -> None:
    args = parse_args()
    release_root = Path(args.release_root).resolve()
    results_dir = Path(args.results_dir)
    latex_dir = Path(args.latex_tables_dir)
    bundle_dir = Path(args.bundle_dir)

    results_dir.mkdir(parents=True, exist_ok=True)
    latex_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = release_root / "metadata/release_manifest.json"
    checksums_path = release_root / "metadata/checksums.sha256"
    validation_report_path = release_root / "metadata/validation_report.md"
    decision_path = release_root / "data/decision_view/decision_view.parquet"
    pairwise_dir = release_root / "data/pairwise_sample"
    pairwise_files = sorted(pairwise_dir.glob("*.parquet"))

    manifest = json.loads(manifest_path.read_text())
    checksums_count = sum(1 for line in checksums_path.read_text().splitlines() if line.strip())
    file_inventory = manifest.get("file_inventory", [])
    candidate_parquet_count = sum(
        1
        for item in file_inventory
        if item.startswith("data/candidate_rows/") and item.endswith(".parquet")
    )
    total_release_files = len(file_inventory)
    selected_families = manifest.get("selected_families", [])
    excluded_families = manifest.get("excluded_families", [])
    row_counts = manifest.get("row_counts", {})
    pairwise_rows = row_counts.get("pairwise_sample")
    if pairwise_rows is None and pairwise_files:
        pairwise_rows = sum(parquet_row_count(path) for path in pairwise_files)

    conn = duckdb.connect()
    decision_sql_path = str(decision_path).replace("'", "''")
    pairwise_sql_path = str(pairwise_files[0]).replace("'", "''") if pairwise_files else None

    decision_by_family = query_rows(
        conn,
        f"""
        SELECT trace_family, COUNT(*) AS decision_rows
        FROM read_parquet('{decision_sql_path}')
        GROUP BY 1
        ORDER BY decision_rows DESC, trace_family
        """,
    )
    decision_by_capacity = query_rows(
        conn,
        f"""
        SELECT capacity, COUNT(*) AS decision_rows
        FROM read_parquet('{decision_sql_path}')
        GROUP BY 1
        ORDER BY capacity
        """,
    )
    decision_by_horizon = query_rows(
        conn,
        f"""
        SELECT horizon, COUNT(*) AS decision_rows
        FROM read_parquet('{decision_sql_path}')
        GROUP BY 1
        ORDER BY horizon
        """,
    )
    decision_by_split = query_rows(
        conn,
        f"""
        SELECT split, COUNT(*) AS decision_rows
        FROM read_parquet('{decision_sql_path}')
        GROUP BY 1
        ORDER BY split
        """,
    )
    decision_by_family_split = query_rows(
        conn,
        f"""
        SELECT trace_family, split, COUNT(*) AS decision_rows
        FROM read_parquet('{decision_sql_path}')
        GROUP BY 1, 2
        ORDER BY trace_family, split
        """,
    )
    candidate_stats_by_family = query_rows(
        conn,
        f"""
        SELECT
          trace_family,
          MIN(candidate_count) AS min_candidate_count,
          quantile_cont(candidate_count, 0.5) AS median_candidate_count,
          AVG(candidate_count) AS mean_candidate_count,
          MAX(candidate_count) AS max_candidate_count
        FROM read_parquet('{decision_sql_path}')
        GROUP BY 1
        ORDER BY trace_family
        """,
    )
    candidate_stats_overall = query_rows(
        conn,
        f"""
        SELECT
          'overall' AS trace_family,
          MIN(candidate_count) AS min_candidate_count,
          quantile_cont(candidate_count, 0.5) AS median_candidate_count,
          AVG(candidate_count) AS mean_candidate_count,
          MAX(candidate_count) AS max_candidate_count
        FROM read_parquet('{decision_sql_path}')
        """,
    )
    tie_distribution = query_rows(
        conn,
        f"""
        SELECT tie_count, COUNT(*) AS decision_rows
        FROM read_parquet('{decision_sql_path}')
        GROUP BY 1
        ORDER BY tie_count
        """,
    )
    tie_summary = query_rows(
        conn,
        f"""
        SELECT
          COUNT(*) AS total_decisions,
          SUM(CASE WHEN tie_count > 1 THEN 1 ELSE 0 END) AS decisions_with_tie_count_gt_1,
          AVG(CASE WHEN tie_count > 1 THEN 1.0 ELSE 0.0 END) AS fraction_with_tie_count_gt_1,
          MAX(tie_count) AS max_tie_count
        FROM read_parquet('{decision_sql_path}')
        """,
    )[0]
    decision_columns = {field.name for field in pq.ParquetFile(decision_path).schema_arrow}
    regret_rows: list[dict[str, object]] = []
    regret_available = {"regret_mean", "regret_std", "regret_max"}.issubset(decision_columns)
    if regret_available:
        regret_rows = query_rows(
            conn,
            f"""
            SELECT 'regret_mean' AS metric, AVG(regret_mean) AS mean_value, STDDEV_SAMP(regret_mean) AS std_value, MAX(regret_mean) AS max_value
            FROM read_parquet('{decision_sql_path}')
            UNION ALL
            SELECT 'regret_std' AS metric, AVG(regret_std) AS mean_value, STDDEV_SAMP(regret_std) AS std_value, MAX(regret_std) AS max_value
            FROM read_parquet('{decision_sql_path}')
            UNION ALL
            SELECT 'regret_max' AS metric, AVG(regret_max) AS mean_value, STDDEV_SAMP(regret_max) AS std_value, MAX(regret_max) AS max_value
            FROM read_parquet('{decision_sql_path}')
            """
        )

    pairwise_summary: list[dict[str, object]] = []
    pairwise_by_split: list[dict[str, object]] = []
    pairwise_by_family: list[dict[str, object]] = []
    pairwise_label_summary: list[dict[str, object]] = []
    if pairwise_sql_path is not None:
        pairwise_columns = {field.name for field in pq.ParquetFile(pairwise_files[0]).schema_arrow}
        pairwise_summary = query_rows(
            conn,
            f"""
            SELECT
              COUNT(*) AS pairwise_rows,
              COUNT(DISTINCT decision_id) AS unique_decisions_represented
            FROM read_parquet('{pairwise_sql_path}')
            """
            if "decision_id" in pairwise_columns
            else f"SELECT COUNT(*) AS pairwise_rows, NULL AS unique_decisions_represented FROM read_parquet('{pairwise_sql_path}')"
        )
        pairwise_by_split = query_rows(
            conn,
            f"""
            SELECT split, COUNT(*) AS pairwise_rows
            FROM read_parquet('{pairwise_sql_path}')
            GROUP BY 1
            ORDER BY split
            """
            if "split" in pairwise_columns
            else "SELECT 'unavailable' AS split, NULL AS pairwise_rows"
        )
        pairwise_by_family = query_rows(
            conn,
            f"""
            SELECT trace_family, COUNT(*) AS pairwise_rows
            FROM read_parquet('{pairwise_sql_path}')
            GROUP BY 1
            ORDER BY pairwise_rows DESC, trace_family
            """
            if "trace_family" in pairwise_columns
            else "SELECT 'unavailable' AS trace_family, NULL AS pairwise_rows"
        )
        if {"label_a_better", "label_b_better", "is_tie"}.issubset(pairwise_columns):
            pairwise_label_summary = query_rows(
                conn,
                f"""
                SELECT
                  SUM(CASE WHEN label_a_better THEN 1 ELSE 0 END) AS label_a_better_rows,
                  SUM(CASE WHEN label_b_better THEN 1 ELSE 0 END) AS label_b_better_rows,
                  SUM(CASE WHEN is_tie THEN 1 ELSE 0 END) AS is_tie_rows
                FROM read_parquet('{pairwise_sql_path}')
                """
            )

    dataset_scale_rows = [
        {"metric": "candidate rows", "value": row_counts.get("candidate_rows"), "notes": "manifest-backed; pending full validation"},
        {"metric": "decision rows", "value": row_counts.get("decision_view"), "notes": "manifest-backed and decision-view-backed; pending full validation"},
        {"metric": "pairwise-sample rows", "value": pairwise_rows, "notes": "manifest-backed and pairwise-sample-backed; pending full validation"},
        {"metric": "candidate parquet files", "value": candidate_parquet_count, "notes": "counted from manifest file inventory only"},
        {"metric": "total release files", "value": total_release_files, "notes": "manifest-backed"},
        {"metric": "manifest file_inventory count", "value": total_release_files, "notes": "manifest-backed"},
        {"metric": "checksum entry count", "value": checksums_count, "notes": "checksums.sha256 line count"},
        {"metric": "selected trace families", "value": ", ".join(selected_families), "notes": "manifest-backed"},
        {"metric": "excluded/pending trace families", "value": ", ".join(excluded_families), "notes": "manifest-backed"},
        {"metric": "full validation status", "value": "pending", "notes": "full real-release validation has not been run"},
    ]
    split_count_rows = [
        {
            "split": split_name,
            "row_count": count,
            "count_type": "candidate rows",
            "source": "manifest row_counts_by_split",
        }
        for split_name, count in sorted(manifest.get("row_counts_by_split", {}).items())
    ]
    candidate_count_rows = candidate_stats_overall + candidate_stats_by_family

    tie_summary_rows = [
        {"statistic": "total decisions", "value": tie_summary["total_decisions"], "notes": "decision-view-backed"},
        {
            "statistic": "decisions with tie_count > 1",
            "value": tie_summary["decisions_with_tie_count_gt_1"],
            "notes": "decision-view-backed",
        },
        {
            "statistic": "fraction with tie_count > 1",
            "value": tie_summary["fraction_with_tie_count_gt_1"],
            "notes": "decision-view-backed",
        },
        {"statistic": "max tie_count", "value": tie_summary["max_tie_count"], "notes": "decision-view-backed"},
    ]
    if regret_available:
        for regret_row in regret_rows:
            tie_summary_rows.append(
                {
                    "statistic": f"{regret_row['metric']} mean/std/max",
                    "value": f"{fmt_int(regret_row['mean_value'])} / {fmt_int(regret_row['std_value'])} / {fmt_int(regret_row['max_value'])}",
                    "notes": "decision-view-backed",
                }
            )
    else:
        tie_summary_rows.append(
            {
                "statistic": "regret summaries",
                "value": "pending",
                "notes": "regret columns not present in decision view",
            }
        )

    pairwise_summary_rows = []
    if pairwise_summary:
        row = pairwise_summary[0]
        pairwise_summary_rows.extend(
            [
                {"statistic": "pairwise rows", "value": row["pairwise_rows"], "notes": "pairwise-sample-backed"},
                {
                    "statistic": "unique decisions represented",
                    "value": row["unique_decisions_represented"],
                    "notes": "pairwise-sample-backed" if row["unique_decisions_represented"] is not None else "decision_id unavailable",
                },
            ]
        )
    if pairwise_label_summary:
        labels = pairwise_label_summary[0]
        pairwise_summary_rows.extend(
            [
                {"statistic": "label_a_better rows", "value": labels["label_a_better_rows"], "notes": "pairwise-sample-backed"},
                {"statistic": "label_b_better rows", "value": labels["label_b_better_rows"], "notes": "pairwise-sample-backed"},
                {"statistic": "is_tie rows", "value": labels["is_tie_rows"], "notes": "pairwise-sample-backed"},
            ]
        )

    artifact_layout_rows = [
        {"artifact": "candidate rows", "relative_path": "data/candidate_rows/", "status": "present", "notes": "partitioned candidate-row parquet shards"},
        {"artifact": "decision view", "relative_path": "data/decision_view/decision_view.parquet", "status": "present", "notes": "single derived decision-view parquet"},
        {"artifact": "pairwise sample", "relative_path": "data/pairwise_sample/pairwise_sample.parquet", "status": "present", "notes": "capped shipped sample; not full pairwise materialization"},
        {"artifact": "release manifest", "relative_path": "metadata/release_manifest.json", "status": "present", "notes": "manifest-backed release metadata"},
        {"artifact": "validation report", "relative_path": "metadata/validation_report.md", "status": "present", "notes": "lightweight validation report present"},
        {"artifact": "checksums", "relative_path": "metadata/checksums.sha256", "status": "present", "notes": "175 checksum entries"},
        {
            "artifact": "publication bundle",
            "relative_path": "anonymous review artifact path pending",
            "status": "local bundle exists" if bundle_dir.exists() else "pending",
            "notes": "anonymous artifact not finalized yet; public-facing upload pending",
        },
    ]

    write_csv(results_dir / "table_dataset_scale.csv", dataset_scale_rows, ["metric", "value", "notes"])
    write_markdown(
        results_dir / "table_dataset_scale.md",
        dataset_scale_rows,
        ["metric", "value", "notes"],
        title="table_dataset_scale",
        intro="All values are manifest-backed unless noted otherwise. Full real-release validation remains pending.",
    )
    write_latex(
        latex_dir / "table_dataset_scale.tex",
        latex_table(
            caption="Dataset scale values from preserved-release metadata. The counts are manifest-backed or view-backed as noted, and full real-release validation remains pending.",
            label="tab:dataset-scale",
            headers=["metric", "value"],
            rows=[{"metric": row["metric"], "value": row["value"]} for row in dataset_scale_rows],
            align="lp{0.46\\columnwidth}",
            size=r"\footnotesize",
        ),
    )

    write_csv(results_dir / "table_split_counts.csv", split_count_rows, ["split", "row_count", "count_type", "source"])
    write_markdown(
        results_dir / "table_split_counts.md",
        split_count_rows,
        ["split", "row_count", "count_type", "source"],
        title="table_split_counts",
        intro="These are manifest-backed candidate-row counts by split. No candidate-row parquet contents were scanned.",
    )
    write_latex(
        latex_dir / "table_split_counts.tex",
        latex_table(
            caption="Split counts from manifest-backed candidate-row metadata. These are candidate-row counts, not decision-view counts, and full real-release validation remains pending.",
            label="tab:split-counts",
            headers=["split", "row_count"],
            rows=[{"split": row["split"], "row_count": row["row_count"]} for row in split_count_rows],
            align="lr",
        ),
    )

    write_csv(results_dir / "table_decision_breakdown_by_trace_family.csv", decision_by_family, ["trace_family", "decision_rows"])
    write_csv(results_dir / "table_decision_breakdown_by_capacity.csv", decision_by_capacity, ["capacity", "decision_rows"])
    write_csv(results_dir / "table_decision_breakdown_by_horizon.csv", decision_by_horizon, ["horizon", "decision_rows"])
    write_csv(results_dir / "table_decision_breakdown_by_split.csv", decision_by_split, ["split", "decision_rows"])
    write_csv(results_dir / "table_decision_breakdown_by_trace_family_split.csv", decision_by_family_split, ["trace_family", "split", "decision_rows"])
    render_section_markdown(
        results_dir / "table_decision_breakdown.md",
        title="table_decision_breakdown",
        intro="All counts in this file come from the decision view only. No candidate-row parquet contents were read.",
        sections=[
            ("By trace family", decision_by_family, ["trace_family", "decision_rows"]),
            ("By capacity", decision_by_capacity, ["capacity", "decision_rows"]),
            ("By horizon", decision_by_horizon, ["horizon", "decision_rows"]),
            ("By split", decision_by_split, ["split", "decision_rows"]),
            ("By trace family and split", decision_by_family_split, ["trace_family", "split", "decision_rows"]),
        ],
    )
    decision_summary_rows = [
        {"dimension": "trace_family", "counts": compact_counts(decision_by_family, "trace_family", "decision_rows")},
        {"dimension": "capacity", "counts": compact_counts(decision_by_capacity, "capacity", "decision_rows")},
        {"dimension": "horizon", "counts": compact_counts(decision_by_horizon, "horizon", "decision_rows")},
        {"dimension": "split", "counts": compact_counts(decision_by_split, "split", "decision_rows")},
    ]
    write_latex(
        latex_dir / "table_decision_breakdown.tex",
        latex_table(
            caption="Decision-view-backed benchmark composition by family, capacity, horizon, and split. Full real-release validation remains pending.",
            label="tab:decision-breakdown",
            headers=["dimension", "counts"],
            rows=decision_summary_rows,
            align="lp{0.62\\columnwidth}",
            size=r"\footnotesize",
        ),
    )

    write_csv(
        results_dir / "table_candidate_count_stats.csv",
        candidate_count_rows,
        ["trace_family", "min_candidate_count", "median_candidate_count", "mean_candidate_count", "max_candidate_count"],
    )
    write_markdown(
        results_dir / "table_candidate_count_stats.md",
        candidate_count_rows,
        ["trace_family", "min_candidate_count", "median_candidate_count", "mean_candidate_count", "max_candidate_count"],
        title="table_candidate_count_stats",
        intro="All statistics in this file come from the decision view only.",
    )
    write_latex(
        latex_dir / "table_candidate_count_stats.tex",
        latex_table(
            caption="Decision-view-backed candidate-count statistics. These values summarize the number of candidates per decision and remain pending full real-release validation.",
            label="tab:candidate-count-stats",
            headers=["group", "min", "med", "mean", "max"],
            rows=[
                {
                    "group": row["trace_family"],
                    "min": row["min_candidate_count"],
                    "med": row["median_candidate_count"],
                    "mean": row["mean_candidate_count"],
                    "max": row["max_candidate_count"],
                }
                for row in candidate_count_rows
            ],
            align="lrrrr",
            size=r"\scriptsize",
        ),
    )

    write_csv(results_dir / "table_tie_count_distribution.csv", tie_distribution, ["tie_count", "decision_rows"])
    write_csv(results_dir / "table_regret_tie_summary.csv", tie_summary_rows, ["statistic", "value", "notes"])
    if regret_rows:
        write_csv(results_dir / "table_regret_summary.csv", regret_rows, ["metric", "mean_value", "std_value", "max_value"])
    render_section_markdown(
        results_dir / "table_regret_tie_stats.md",
        title="table_regret_tie_stats",
        intro="These tie and regret summaries are decision-view-backed. Regret rows are emitted only when the relevant columns are present in the decision view.",
        sections=[
            ("Summary", tie_summary_rows, ["statistic", "value", "notes"]),
            ("Tie-count distribution", tie_distribution, ["tie_count", "decision_rows"]),
        ],
    )
    write_latex(
        latex_dir / "table_regret_tie_stats.tex",
        latex_table(
            caption="Decision-view-backed tie and regret summaries. Full real-release validation remains pending.",
            label="tab:regret-ties",
            headers=["statistic", "value"],
            rows=[{"statistic": row["statistic"], "value": row["value"]} for row in tie_summary_rows],
            align="lp{0.42\\columnwidth}",
            size=r"\footnotesize",
        ),
    )

    if pairwise_summary_rows:
        write_csv(results_dir / "table_pairwise_sample_summary.csv", pairwise_summary_rows, ["statistic", "value", "notes"])
    if pairwise_by_split:
        write_csv(results_dir / "table_pairwise_sample_by_split.csv", pairwise_by_split, ["split", "pairwise_rows"])
    if pairwise_by_family:
        write_csv(results_dir / "table_pairwise_sample_by_trace_family.csv", pairwise_by_family, ["trace_family", "pairwise_rows"])
    if pairwise_label_summary:
        write_csv(results_dir / "table_pairwise_sample_label_summary.csv", pairwise_label_summary, ["label_a_better_rows", "label_b_better_rows", "is_tie_rows"])
    render_section_markdown(
        results_dir / "table_pairwise_sample_stats.md",
        title="table_pairwise_sample_stats",
        intro="All statistics in this file come from the shipped pairwise sample only.",
        sections=[
            ("Summary", pairwise_summary_rows, ["statistic", "value", "notes"]),
            ("By split", pairwise_by_split, ["split", "pairwise_rows"]),
            ("By trace family", pairwise_by_family, ["trace_family", "pairwise_rows"]),
            (
                "Label summary",
                pairwise_label_summary,
                ["label_a_better_rows", "label_b_better_rows", "is_tie_rows"],
            ),
        ],
    )
    pairwise_compact_rows = [
        {"statistic": "pairwise rows", "value": pairwise_rows},
        {
            "statistic": "split breakdown",
            "value": compact_counts(pairwise_by_split, "split", "pairwise_rows") if pairwise_by_split else "pending",
        },
        {
            "statistic": "family breakdown",
            "value": compact_counts(pairwise_by_family, "trace_family", "pairwise_rows") if pairwise_by_family else "pending",
        },
    ]
    if pairwise_summary:
        pairwise_compact_rows.append(
            {
                "statistic": "unique decisions represented",
                "value": pairwise_summary[0]["unique_decisions_represented"],
            }
        )
    if pairwise_label_summary:
        labels = pairwise_label_summary[0]
        pairwise_compact_rows.append(
            {
                "statistic": "label distribution",
                "value": (
                    f"a_better={fmt_int(labels['label_a_better_rows'])}; "
                    f"b_better={fmt_int(labels['label_b_better_rows'])}; "
                    f"tie={fmt_int(labels['is_tie_rows'])}"
                ),
            }
        )
    write_latex(
        latex_dir / "table_pairwise_sample_stats.tex",
        latex_table(
            caption="Pairwise-sample-backed summary statistics for the shipped sample view. Full real-release validation remains pending.",
            label="tab:pairwise-sample-stats",
            headers=["statistic", "value"],
            rows=pairwise_compact_rows,
            align="lp{0.42\\columnwidth}",
            size=r"\footnotesize",
        ),
    )

    write_csv(results_dir / "table_artifact_layout.csv", artifact_layout_rows, ["artifact", "relative_path", "status", "notes"])
    write_markdown(
        results_dir / "table_artifact_layout.md",
        artifact_layout_rows,
        ["artifact", "relative_path", "status", "notes"],
        title="table_artifact_layout",
        intro="Artifact paths are release-relative for manuscript safety. The anonymous review artifact is not finalized yet.",
    )
    write_latex(
        latex_dir / "table_artifact_layout.tex",
        latex_table(
            caption="Release artifact layout using release-relative paths. The table is metadata-backed where applicable, and the anonymous review artifact remains pending.",
            label="tab:artifact-layout",
            headers=["artifact", "relative_path"],
            rows=[{"artifact": row["artifact"], "relative_path": row["relative_path"]} for row in artifact_layout_rows],
            align="lp{0.52\\columnwidth}",
            size=r"\footnotesize",
        ),
    )

    summary = {
        "release_root": args.release_root,
        "results_dir": args.results_dir,
        "latex_tables_dir": args.latex_tables_dir,
        "candidate_rows_scanned": False,
        "generated_tables": [
            "table_dataset_scale",
            "table_split_counts",
            "table_decision_breakdown",
            "table_candidate_count_stats",
            "table_regret_tie_stats",
            "table_pairwise_sample_stats",
            "table_artifact_layout",
        ],
    }
    (results_dir / "summary.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
