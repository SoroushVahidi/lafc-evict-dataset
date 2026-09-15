"""Validate the completed full-population LRU-vs-MRU continuation census.

This script treats the raw census directory as immutable evidence. It first
hashes every relevant raw file, then performs structural, schema, key, and
provenance gates, and finally hashes the same files again to prove validation
did not modify the raw output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter, OrderedDict, defaultdict
from datetime import datetime, timezone
from pathlib import Path


FAMILIES = ("cloudphysics", "metacdn", "metakv", "twemcache", "wiki2018")
CAPACITIES = (32, 64, 128, 256)
HORIZONS = (4, 8, 16)
EXPECTED_TOTAL_RECORDS = 2_363_286
EXPECTED_HARNESS_COMMIT = "1a29e773a113c8d47b13debe9893f4f5a9050099"
EXPECTED_RUN_ID = "20260914T042528Z_1a29e773a113"
EXPECTED_TRACE_SHA256 = {
    "cloudphysics": "fedb3d31ee3c1dd847d25f967392cdf0fdec1e9c1fbb6808772e281bc8d4fb57",
    "metacdn": "7301f02e1373cb7e06f1ed2c417a8ebe16581319354780f811c8d032391f4e73",
    "metakv": "4c229e841d546cd57a2edb6e3ddc53461ff4dc03d366e9d24e4239a89db7e0de",
    "twemcache": "62df27062ce2595c843fd91e01d26c9783ff8f165f6b26e983696eda7ada0bb9",
    "wiki2018": "3813084bebfcf463ac22a685494b46aea45aded55d314411c9fbb058b5d67608",
}
SPLIT_LABEL = {
    "cloudphysics": "test",
    "metacdn": "validation",
    "metakv": "test",
    "twemcache": "test",
    "wiki2018": "test",
}
RAW_ROOT = Path(
    "/home/soroush/projects/lafc-evict-dataset/repo/.claude/worktrees/"
    "continuation-mru-population-census-20260914/analysis/"
    "continuation_policy_mru_population_census_20260914"
)
DEFAULT_RUN_DIR = RAW_ROOT / "outputs" / EXPECTED_RUN_ID
TRACE_DIR = Path("/home/soroush/projects/augmented-caching/repo/data/processed")
VALIDATED_ROOT = Path(__file__).resolve().parents[1] / "validated" / EXPECTED_RUN_ID
DECISION_RE = re.compile(r"^(?P<family>[^|]+)\|c(?P<capacity>\d+)\|t(?P<t>\d+)\|h(?P<h>\d+)$")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git_out(repo: str | Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=False)
    return proc.stdout.strip()


def raw_files(run_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for base in (run_dir, RAW_ROOT / "logs"):
        if base.exists():
            paths.extend(p for p in base.rglob("*") if p.is_file() and p.suffix in {".jsonl", ".done", ".json", ".log"})
    prelaunch = RAW_ROOT / "outputs" / "prelaunch_lru_equivalence_result.json"
    if prelaunch.exists():
        paths.append(prelaunch)
    return sorted(set(paths))


def evidence_manifest(paths: list[Path]) -> dict:
    entries = []
    total_size = 0
    for path in paths:
        size = path.stat().st_size
        total_size += size
        try:
            rel = str(path.relative_to(RAW_ROOT))
        except ValueError:
            rel = str(path)
        entries.append({"relative_path": rel, "size": size, "sha256": sha256_file(path)})
    return {
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "raw_root": str(RAW_ROOT),
        "file_count": len(entries),
        "total_size": total_size,
        "files": entries,
    }


def manifest_map(manifest: dict) -> dict[str, tuple[int, str]]:
    return {f["relative_path"]: (int(f["size"]), str(f["sha256"])) for f in manifest["files"]}


def enumerate_expected_positions(family: str, capacity: int) -> list[int]:
    order: OrderedDict[str, None] = OrderedDict()
    positions: list[int] = []
    trace_path = TRACE_DIR / family / "trace.jsonl"
    with open(trace_path, "r", encoding="utf-8") as fh:
        for t, line in enumerate(fh):
            item = str(json.loads(line)["item_id"])
            if item in order:
                order.move_to_end(item)
                continue
            if len(order) < capacity:
                order[item] = None
                continue
            positions.append(t)
            order.popitem(last=False)
            order[item] = None
    return positions


def expected_key_map() -> dict[str, int]:
    expected: dict[str, int] = {}
    for family in FAMILIES:
        for capacity in CAPACITIES:
            positions = enumerate_expected_positions(family, capacity)
            for horizon in HORIZONS:
                chunk = f"{family}_{capacity}_{horizon}"
                for t in positions:
                    expected[f"{family}|c{capacity}|t{t}|h{horizon}"] = len(positions)
                expected[f"__chunk_count__:{chunk}"] = len(positions)
    return expected


def gate(name: str, passed: bool, detail: str = "") -> dict:
    return {"name": name, "passed": bool(passed), "detail": detail}


def is_finite_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def validate_record(row: dict, chunk_family: str, chunk_capacity: int, chunk_horizon: int) -> list[str]:
    errors: list[str] = []
    required = {
        "decision_id", "family", "capacity", "horizon", "request_t", "candidate_count",
        "lru_min_loss", "mru_min_loss", "lru_optimal_set_size", "mru_optimal_set_size",
        "optimal_set_intersection_size", "optimal_set_union_size", "optimal_set_jaccard",
        "kendall_tau_b", "pairwise_concordant", "pairwise_discordant",
        "pairwise_a_tie_b_strict", "pairwise_a_strict_b_tie", "pairwise_both_tied",
        "ccr_mean_over_LRU_optimal", "ccr_best_case", "ccr_worst_case",
        "ccr_prob_still_optimal", "all_tied_lru", "all_tied_mru",
        "scored_split_label", "status",
    }
    missing = sorted(required - set(row))
    if missing:
        return [f"missing fields {missing}"]

    if row["status"] != "complete":
        errors.append("status not complete")
    if row["family"] not in FAMILIES or row["family"] != chunk_family:
        errors.append("invalid family")
    if row["capacity"] not in CAPACITIES or int(row["capacity"]) != chunk_capacity:
        errors.append("invalid capacity")
    if row["horizon"] not in HORIZONS or int(row["horizon"]) != chunk_horizon:
        errors.append("invalid horizon")
    if row["scored_split_label"] != SPLIT_LABEL.get(str(row["family"])):
        errors.append("invalid split label")

    m = DECISION_RE.match(str(row["decision_id"]))
    if not m:
        errors.append("invalid decision_id format")
    else:
        if (m.group("family") != row["family"] or int(m.group("capacity")) != int(row["capacity"])
                or int(m.group("h")) != int(row["horizon"]) or int(m.group("t")) != int(row["request_t"])):
            errors.append("decision_id inconsistent with fields")

    ints = [
        "capacity", "horizon", "request_t", "candidate_count", "lru_optimal_set_size",
        "mru_optimal_set_size", "optimal_set_intersection_size", "optimal_set_union_size",
        "pairwise_concordant", "pairwise_discordant", "pairwise_a_tie_b_strict",
        "pairwise_a_strict_b_tie", "pairwise_both_tied",
    ]
    for key in ints:
        if not isinstance(row[key], int) or isinstance(row[key], bool):
            errors.append(f"{key} not int")
        elif row[key] < 0:
            errors.append(f"{key} negative")

    numeric = ["lru_min_loss", "mru_min_loss", "optimal_set_jaccard", "ccr_mean_over_LRU_optimal",
               "ccr_best_case", "ccr_worst_case", "ccr_prob_still_optimal"]
    for key in numeric:
        if not is_finite_number(row[key]):
            errors.append(f"{key} not finite")
        elif key.endswith("loss") and row[key] < 0:
            errors.append(f"{key} negative")
    if row["kendall_tau_b"] is not None and not is_finite_number(row["kendall_tau_b"]):
        errors.append("kendall_tau_b not finite/null")
    if row["kendall_tau_b"] is not None and not -1.0 <= float(row["kendall_tau_b"]) <= 1.0:
        errors.append("kendall_tau_b out of bounds")

    cand = int(row["candidate_count"])
    lru_opt = int(row["lru_optimal_set_size"])
    mru_opt = int(row["mru_optimal_set_size"])
    inter = int(row["optimal_set_intersection_size"])
    union = int(row["optimal_set_union_size"])
    jacc = float(row["optimal_set_jaccard"])
    if cand != int(row["capacity"]):
        errors.append("candidate_count != capacity")
    if not (1 <= lru_opt <= cand and 1 <= mru_opt <= cand):
        errors.append("optimal set size outside 1..candidate_count")
    if inter > lru_opt or inter > mru_opt:
        errors.append("intersection exceeds an optimal set")
    if union < lru_opt or union < mru_opt or union > cand:
        errors.append("union invalid")
    if union != lru_opt + mru_opt - inter:
        errors.append("union cardinality inconsistent")
    if union and abs(jacc - (inter / union)) > 1e-12:
        errors.append("jaccard inconsistent")
    if not 0.0 <= jacc <= 1.0:
        errors.append("jaccard out of bounds")
    if not 0.0 <= float(row["ccr_prob_still_optimal"]) <= 1.0:
        errors.append("ccr_prob_still_optimal out of bounds")
    if float(row["ccr_mean_over_LRU_optimal"]) < -1e-12 or float(row["ccr_best_case"]) < -1e-12 or float(row["ccr_worst_case"]) < -1e-12:
        errors.append("negative cross-continuation regret")
    if float(row["ccr_best_case"]) - float(row["ccr_mean_over_LRU_optimal"]) > 1e-12:
        errors.append("ccr best > mean")
    if float(row["ccr_mean_over_LRU_optimal"]) - float(row["ccr_worst_case"]) > 1e-12:
        errors.append("ccr mean > worst")

    if not isinstance(row["all_tied_lru"], bool) or not isinstance(row["all_tied_mru"], bool):
        errors.append("all_tied flags not bool")
    if bool(row["all_tied_lru"]) != (lru_opt == cand):
        errors.append("all_tied_lru inconsistent")
    if bool(row["all_tied_mru"]) != (mru_opt == cand):
        errors.append("all_tied_mru inconsistent")

    pairwise_keys = ["pairwise_concordant", "pairwise_discordant", "pairwise_a_tie_b_strict",
                     "pairwise_a_strict_b_tie", "pairwise_both_tied"]
    total_pairs = cand * (cand - 1) // 2
    if sum(int(row[k]) for k in pairwise_keys) != total_pairs:
        errors.append("pairwise taxonomy total inconsistent")
    if row["all_tied_lru"] and row["all_tied_mru"] and int(row["pairwise_both_tied"]) != total_pairs:
        errors.append("both all-tied but pairwise_both_tied != all pairs")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--validated-dir", type=Path, default=VALIDATED_ROOT)
    args = parser.parse_args()

    args.validated_dir.mkdir(parents=True, exist_ok=True)
    raw_path = args.run_dir.resolve()
    raw_size = int(subprocess.check_output(["du", "-sb", str(raw_path)], text=True).split()[0])

    initial_manifest = evidence_manifest(raw_files(args.run_dir))
    (args.validated_dir / "RAW_EVIDENCE_MANIFEST.json").write_text(
        json.dumps(initial_manifest, indent=2, sort_keys=True), encoding="utf-8"
    )

    expected_map = expected_key_map()
    expected_keys = {k for k in expected_map if not k.startswith("__chunk_count__:")}
    expected_chunks = {f"{f}_{c}_{h}" for f in FAMILIES for c in CAPACITIES for h in HORIZONS}
    expected_chunk_counts = {k.split(":", 1)[1]: v for k, v in expected_map.items() if k.startswith("__chunk_count__:")}

    chunk_dir = args.run_dir / "chunks"
    jsonl_paths = sorted(chunk_dir.glob("*.jsonl"))
    done_paths = sorted(chunk_dir.glob("*.done"))
    jsonl_chunks = {p.stem for p in jsonl_paths}
    done_chunks = {p.stem for p in done_paths}

    observed_keys: set[str] = set()
    duplicate_keys: Counter[str] = Counter()
    records = 0
    chunk_counts: Counter[str] = Counter()
    observed_families: set[str] = set()
    observed_capacities: set[int] = set()
    observed_horizons: set[int] = set()
    schema_errors: list[dict] = []
    numeric_errors = 0
    jaccard_errors = 0
    fraction_errors = 0
    negative_errors = 0
    taxonomy_errors = 0
    cardinality_errors = 0
    ccr_negative_errors = 0

    for path in jsonl_paths:
        try:
            family, cap_s, h_s = path.stem.rsplit("_", 2)
            cap = int(cap_s)
            horizon = int(h_s)
        except ValueError:
            schema_errors.append({"file": path.name, "line": 0, "errors": ["invalid chunk filename"]})
            continue
        with open(path, "r", encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                records += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    schema_errors.append({"file": path.name, "line": line_no, "errors": [f"malformed json: {exc}"]})
                    continue
                errors = validate_record(row, family, cap, horizon)
                if errors and len(schema_errors) < 100:
                    schema_errors.append({"file": path.name, "line": line_no, "decision_id": row.get("decision_id"), "errors": errors})
                numeric_errors += sum("finite" in e or "NaN" in e or "Inf" in e for e in errors)
                jaccard_errors += sum("jaccard" in e for e in errors)
                fraction_errors += sum("prob_still_optimal out of bounds" in e for e in errors)
                negative_errors += sum("negative" in e for e in errors)
                taxonomy_errors += sum("taxonomy" in e or "pairwise" in e for e in errors)
                cardinality_errors += sum("set size" in e or "intersection" in e or "union" in e for e in errors)
                ccr_negative_errors += sum("negative cross-continuation regret" in e for e in errors)
                key = str(row.get("decision_id"))
                if key in observed_keys:
                    duplicate_keys[key] += 1
                else:
                    observed_keys.add(key)
                chunk_counts[path.stem] += 1
                if row.get("family") in FAMILIES:
                    observed_families.add(row["family"])
                if isinstance(row.get("capacity"), int):
                    observed_capacities.add(row["capacity"])
                if isinstance(row.get("horizon"), int):
                    observed_horizons.add(row["horizon"])

    missing_keys = expected_keys - observed_keys
    extra_keys = observed_keys - expected_keys

    done_errors: list[str] = []
    for done_path in done_paths:
        try:
            marker = json.loads(done_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            done_errors.append(f"{done_path.name}: malformed marker {exc}")
            continue
        jsonl_path = done_path.with_suffix(".jsonl")
        if not jsonl_path.exists():
            done_errors.append(f"{done_path.name}: missing jsonl")
            continue
        if marker.get("n_decisions") != expected_chunk_counts.get(done_path.stem):
            done_errors.append(f"{done_path.name}: n_decisions mismatch")
        if marker.get("chunk_sha256") != sha256_file(jsonl_path):
            done_errors.append(f"{done_path.name}: chunk_sha256 mismatch")

    progress = json.loads((args.run_dir / "progress.json").read_text(encoding="utf-8")) if (args.run_dir / "progress.json").exists() else {}
    provenance = json.loads((args.run_dir / "provenance.json").read_text(encoding="utf-8")) if (args.run_dir / "provenance.json").exists() else {}
    lru_eq_path = RAW_ROOT / "outputs" / "prelaunch_lru_equivalence_result.json"
    lru_eq = json.loads(lru_eq_path.read_text(encoding="utf-8")) if lru_eq_path.exists() else {}
    actual_trace_hashes = {family: sha256_file(TRACE_DIR / family / "trace.jsonl") for family in FAMILIES}

    final_manifest = evidence_manifest(raw_files(args.run_dir))
    initial_map = manifest_map(initial_manifest)
    final_map = manifest_map(final_manifest)

    manifest_consistent = (
        progress.get("total_done") == EXPECTED_TOTAL_RECORDS
        and progress.get("total_expected") == EXPECTED_TOTAL_RECORDS
        and provenance.get("total_decisions_done") == EXPECTED_TOTAL_RECORDS
        and provenance.get("total_decisions_expected") == EXPECTED_TOTAL_RECORDS
        and set(provenance.get("families", [])) == set(FAMILIES)
        and tuple(provenance.get("capacities", [])) == CAPACITIES
        and tuple(provenance.get("horizons", [])) == HORIZONS
        and tuple(provenance.get("continuations", [])) == ("lru", "mru")
    )

    source_primary = provenance.get("primary_repo", {}).get("head")
    source_secondary = provenance.get("secondary_repo", {}).get("head")
    harness_commit = source_primary
    trace_hash_consistent = actual_trace_hashes == EXPECTED_TRACE_SHA256 == provenance.get("trace_sha256_verified")
    lru_gate_passed = lru_eq.get("gate_pass") is True and lru_eq.get("n_mismatches") == 0

    gates = [
        gate("expected_chunk_count", len(jsonl_chunks) == 60 and jsonl_chunks == expected_chunks, f"jsonl={len(jsonl_chunks)}"),
        gate("all_chunks_done", len(done_chunks) == 60 and done_chunks == expected_chunks and not done_errors, "; ".join(done_errors[:5])),
        gate("expected_total_records", records == EXPECTED_TOTAL_RECORDS, f"observed={records}"),
        gate("unique_decision_horizon_keys", not duplicate_keys and len(observed_keys) == records, f"duplicates={sum(duplicate_keys.values())}"),
        gate("no_missing_keys", not missing_keys, f"missing={len(missing_keys)}"),
        gate("no_extra_keys", not extra_keys, f"extra={len(extra_keys)}"),
        gate("expected_families", tuple(sorted(observed_families)) == FAMILIES, str(sorted(observed_families))),
        gate("expected_capacities", tuple(sorted(observed_capacities)) == CAPACITIES, str(sorted(observed_capacities))),
        gate("expected_horizons", tuple(sorted(observed_horizons)) == HORIZONS, str(sorted(observed_horizons))),
        gate("only_expected_policies", tuple(provenance.get("continuations", [])) == ("lru", "mru"), str(provenance.get("continuations"))),
        gate("schema_valid", not schema_errors, f"errors={len(schema_errors)}"),
        gate("finite_numeric_values", numeric_errors == 0, f"errors={numeric_errors}"),
        gate("no_invalid_negative_values", negative_errors == 0, f"errors={negative_errors}"),
        gate("jaccard_bounds", jaccard_errors == 0, f"errors={jaccard_errors}"),
        gate("fraction_bounds", fraction_errors == 0, f"errors={fraction_errors}"),
        gate("optimal_set_cardinality_consistency", cardinality_errors == 0, f"errors={cardinality_errors}"),
        gate("taxonomy_consistency", taxonomy_errors == 0, f"errors={taxonomy_errors}"),
        gate("nonnegative_cross_continuation_regret", ccr_negative_errors == 0, f"errors={ccr_negative_errors}"),
        gate("manifest_consistency", manifest_consistent, ""),
        gate("run_id_consistency", provenance.get("run_id") == EXPECTED_RUN_ID and args.run_dir.name == EXPECTED_RUN_ID, provenance.get("run_id", "")),
        gate("source_commit_consistency", source_primary == EXPECTED_HARNESS_COMMIT, str(source_primary)),
        gate("trace_hash_consistency", trace_hash_consistent, ""),
        gate("lru_equivalence_gate_passed", lru_gate_passed, json.dumps(lru_eq, sort_keys=True)),
        gate("expected_per_chunk_record_counts", dict(chunk_counts) == expected_chunk_counts, ""),
        gate("progress_per_chunk_counts", all(progress.get("chunks", {}).get(k, {}) == {"done": v, "expected": v} for k, v in expected_chunk_counts.items()), ""),
        gate("no_raw_file_hash_changed_during_validation", initial_map == final_map, ""),
    ]
    full_valid = all(g["passed"] for g in gates)

    report = {
        "validation_time_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "FULL_CENSUS_VALID": full_valid,
        "raw_run_id": EXPECTED_RUN_ID,
        "raw_run_path": str(raw_path),
        "raw_run_size": raw_size,
        "raw_manifest_created": str(args.validated_dir / "RAW_EVIDENCE_MANIFEST.json"),
        "raw_files_hashed": initial_manifest["file_count"],
        "expected_chunks": 60,
        "observed_chunks": len(jsonl_chunks),
        "observed_done_markers": len(done_chunks),
        "expected_records": EXPECTED_TOTAL_RECORDS,
        "observed_records": records,
        "unique_keys": len(observed_keys),
        "duplicate_keys": sum(duplicate_keys.values()),
        "missing_keys": len(missing_keys),
        "extra_keys": len(extra_keys),
        "expected_families": list(FAMILIES),
        "observed_families": sorted(observed_families),
        "expected_capacities": list(CAPACITIES),
        "observed_capacities": sorted(observed_capacities),
        "expected_horizons": list(HORIZONS),
        "observed_horizons": sorted(observed_horizons),
        "policy_scope_valid": tuple(provenance.get("continuations", [])) == ("lru", "mru"),
        "schema_valid": not schema_errors,
        "numeric_validity": numeric_errors == 0 and negative_errors == 0 and jaccard_errors == 0 and fraction_errors == 0,
        "provenance_valid": manifest_consistent and trace_hash_consistent and lru_gate_passed and source_primary == EXPECTED_HARNESS_COMMIT,
        "source_primary_commit": source_primary,
        "source_secondary_commit": source_secondary,
        "harness_commit": harness_commit,
        "lru_equivalence_status": "PASSED" if lru_gate_passed else "FAILED",
        "lru_equivalence_comparisons": lru_eq.get("total_candidate_horizon_comparisons"),
        "lru_equivalence_mismatches": lru_eq.get("n_mismatches"),
        "schema_error_samples": schema_errors[:20],
        "missing_key_samples": sorted(missing_keys)[:20],
        "extra_key_samples": sorted(extra_keys)[:20],
        "duplicate_key_samples": duplicate_keys.most_common(20),
        "raw_hash_changed": initial_map != final_map,
    }
    validity = {"FULL_CENSUS_VALID": full_valid, "gates": gates}
    (args.validated_dir / "VALIDATION_REPORT.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    (args.validated_dir / "validity_gates.json").write_text(json.dumps(validity, indent=2, sort_keys=True), encoding="utf-8")
    (args.validated_dir / "RAW_EVIDENCE_MANIFEST_POST_VALIDATION.json").write_text(
        json.dumps(final_manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps({"FULL_CENSUS_VALID": full_valid, "gates_failed": [g["name"] for g in gates if not g["passed"]]}, indent=2))
    return 0 if full_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
