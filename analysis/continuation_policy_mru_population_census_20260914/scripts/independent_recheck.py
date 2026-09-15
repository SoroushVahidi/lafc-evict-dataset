"""Independent recheck for the full-population MRU census.

Deliberately does not import or call validate_census.py. It streams the raw
JSONL files, recomputes independent headline completeness and metrics, then
compares them to the summarizer outputs when those are available.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


FAMILIES = ("cloudphysics", "metacdn", "metakv", "twemcache", "wiki2018")
CAPACITIES = (32, 64, 128, 256)
HORIZONS = (4, 8, 16)
EXPECTED_RECORDS = 2_363_286
RUN_ID = "20260914T042528Z_1a29e773a113"
RAW_RUN_DIR = Path(
    "/home/soroush/projects/lafc-evict-dataset/repo/.claude/worktrees/"
    "continuation-mru-population-census-20260914/analysis/"
    "continuation_policy_mru_population_census_20260914/outputs"
) / RUN_ID
VALIDATED_DIR = Path(__file__).resolve().parents[1] / "validated" / RUN_ID


def median(values: list[float]) -> float | None:
    if not values:
        return None
    values = sorted(values)
    n = len(values)
    mid = n // 2
    return values[mid] if n % 2 else (values[mid - 1] + values[mid]) / 2


def pct(values: list[float], q: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    idx = min(len(values) - 1, max(0, math.ceil(q * len(values)) - 1))
    return values[idx]


def add_metric(acc: dict, row: dict) -> None:
    acc["n"] += 1
    acc["jaccards"].append(float(row["optimal_set_jaccard"]))
    ccr = float(row["ccr_mean_over_LRU_optimal"])
    acc["ccr"].append(ccr)
    acc["still"].append(float(row["ccr_prob_still_optimal"]))
    acc["discordant"] += int(row["pairwise_discordant"])
    pairs = int(row["candidate_count"]) * (int(row["candidate_count"]) - 1) // 2
    acc["pairs"] += pairs


def finish(acc: dict) -> dict:
    n = acc["n"]
    return {
        "n": n,
        "jaccard_mean": sum(acc["jaccards"]) / n if n else None,
        "jaccard_median": median(acc["jaccards"]),
        "jaccard_eq_1_fraction": sum(1 for v in acc["jaccards"] if v == 1.0) / n if n else None,
        "strict_reversal_count": acc["discordant"],
        "strict_reversal_fraction": acc["discordant"] / acc["pairs"] if acc["pairs"] else None,
        "ccr_mean": sum(acc["ccr"]) / n if n else None,
        "ccr_median": median(acc["ccr"]),
        "ccr_p95": pct(acc["ccr"], 0.95),
        "ccr_max": max(acc["ccr"]) if n else None,
        "nonzero_regret_fraction": sum(1 for v in acc["ccr"] if v > 0.0) / n if n else None,
        "fraction_lru_optimal_still_mru_optimal": sum(acc["still"]) / n if n else None,
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def refresh_evidence_manifest(validated_dir: Path) -> None:
    artifacts = []
    for path in sorted(p for p in validated_dir.rglob("*") if p.is_file() and p.name != "EVIDENCE_MANIFEST.json"):
        artifacts.append({
            "relative_path": str(path.relative_to(validated_dir)),
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    manifest = {
        "run_id": RUN_ID,
        "validated_dir": str(validated_dir),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    (validated_dir / "EVIDENCE_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


def update_validation_gates(validated_dir: Path, result: dict) -> None:
    gate_path = validated_dir / "validity_gates.json"
    report_path = validated_dir / "VALIDATION_REPORT.json"
    if not gate_path.exists():
        return
    validity = json.loads(gate_path.read_text(encoding="utf-8"))
    existing = {g["name"]: g for g in validity.get("gates", [])}
    additions = [
        ("independent_record_count_match", result["gates"]["record_count"], f"observed={result['total_records']}"),
        ("independent_unique_key_match", result["gates"]["unique_keys"], f"unique={result['unique_keys']} duplicates={result['duplicate_keys']}"),
        ("independent_coverage_match", result["gates"]["coverage"], ""),
        ("independent_headline_metric_match", result["gates"]["headline_metric_match"] is True, ""),
    ]
    for name, passed, detail in additions:
        existing[name] = {"name": name, "passed": bool(passed), "detail": detail}
    gates = list(existing.values())
    validity["gates"] = gates
    validity["FULL_CENSUS_VALID"] = all(g["passed"] for g in gates)
    gate_path.write_text(json.dumps(validity, indent=2, sort_keys=True), encoding="utf-8")
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["FULL_CENSUS_VALID"] = validity["FULL_CENSUS_VALID"]
        report["independent_recheck_status"] = result["status"]
        report["independent_recheck_gates"] = result["gates"]
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=RAW_RUN_DIR)
    parser.add_argument("--validated-dir", type=Path, default=VALIDATED_DIR)
    args = parser.parse_args()

    keys = set()
    duplicate_keys = 0
    chunks = set()
    coverage = set()
    all_acc = defaultdict(lambda: {"n": 0, "jaccards": [], "ccr": [], "still": [], "discordant": 0, "pairs": 0})

    for path in sorted((args.run_dir / "chunks").glob("*.jsonl")):
        chunks.add(path.stem)
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                key = row["decision_id"]
                if key in keys:
                    duplicate_keys += 1
                keys.add(key)
                coverage.add((row["family"], int(row["capacity"]), int(row["horizon"])))
                add_metric(all_acc["A_all_decisions"], row)
                if not (row["all_tied_lru"] and row["all_tied_mru"]):
                    add_metric(all_acc["B_excluding_both_tied"], row)
                if not row["all_tied_lru"]:
                    add_metric(all_acc["C_discriminative_under_LRU"], row)
                if (not row["all_tied_lru"]) or (not row["all_tied_mru"]):
                    add_metric(all_acc["D_discriminative_under_either"], row)
                if row["family"] != "wiki2018":
                    add_metric(all_acc["excluding_wiki2018"], row)

    summaries = {name: finish(acc) for name, acc in all_acc.items()}
    expected_coverage = {(f, c, h) for f in FAMILIES for c in CAPACITIES for h in HORIZONS}
    result = {
        "status": "PASS",
        "total_records": sum(s["n"] for name, s in summaries.items() if name == "A_all_decisions"),
        "unique_keys": len(keys),
        "duplicate_keys": duplicate_keys,
        "chunk_count": len(chunks),
        "coverage_complete": coverage == expected_coverage,
        "observed_families": sorted({x[0] for x in coverage}),
        "observed_capacities": sorted({x[1] for x in coverage}),
        "observed_horizons": sorted({x[2] for x in coverage}),
        "summaries": summaries,
    }
    gates = {
        "record_count": result["total_records"] == EXPECTED_RECORDS,
        "unique_keys": len(keys) == EXPECTED_RECORDS and duplicate_keys == 0,
        "chunk_count": len(chunks) == 60,
        "coverage": coverage == expected_coverage,
    }

    summary_path = args.validated_dir / "summary_overall.json"
    if summary_path.exists():
        primary = json.loads(summary_path.read_text(encoding="utf-8"))
        a = primary["analysis_sets"]["A_all_decisions"]
        c = primary["analysis_sets"]["C_discriminative_under_LRU"]
        tol = 1e-12
        gates["headline_metric_match"] = (
            abs(a["optimal_set_jaccard"]["mean"] - summaries["A_all_decisions"]["jaccard_mean"]) <= tol
            and abs(c["ccr_mean_over_LRU_optimal"]["mean"] - summaries["C_discriminative_under_LRU"]["ccr_mean"]) <= tol
            and a["strict_reversal_count"] == summaries["A_all_decisions"]["strict_reversal_count"]
        )
    else:
        gates["headline_metric_match"] = None

    result["gates"] = gates
    if any(v is False for v in gates.values()):
        result["status"] = "FAIL"
    elif any(v is None for v in gates.values()):
        result["status"] = "PASS_PENDING_SUMMARY_COMPARISON"
    out = args.validated_dir / "independent_recheck.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    update_validation_gates(args.validated_dir, result)
    refresh_evidence_manifest(args.validated_dir)
    print(json.dumps({"status": result["status"], "gates": gates}, indent=2, sort_keys=True))
    return 0 if result["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
