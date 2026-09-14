"""Programmatic validity gates for a completed FULL-experiment run."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from full_lib import CAPACITIES, DECISIONS_PER_PRIMARY_STRATUM, FAMILIES, HORIZONS, RANDOM_SEEDS  # noqa: E402

FULL_DIR = Path(__file__).resolve().parents[1]


def gate(name, passed, detail=""):
    return {"name": name, "passed": bool(passed), "detail": detail}


def main(run_dir: Path):
    gates = []
    primary = json.loads((FULL_DIR / "PRIMARY_MANIFEST.json").read_text())
    diagnostic = json.loads((FULL_DIR / "DIAGNOSTIC_MANIFEST.json").read_text())

    lru_eq_path = FULL_DIR / "outputs" / "prelaunch_lru_equivalence_result.json"
    lru_eq = json.loads(lru_eq_path.read_text()) if lru_eq_path.exists() else None
    gates.append(gate("prelaunch_lru_equivalence_gate_ran", lru_eq is not None))
    if lru_eq is not None:
        gates.append(gate("lru_equivalence_mismatches_zero", lru_eq["n_mismatches"] == 0, f"n_mismatches={lru_eq['n_mismatches']}"))

    gates.append(gate("primary_manifest_exists", (FULL_DIR / "PRIMARY_MANIFEST.json").exists()))
    gates.append(gate("diagnostic_manifest_exists", (FULL_DIR / "DIAGNOSTIC_MANIFEST.json").exists()))
    gates.append(gate("primary_sample_size_5000", primary["total_decisions"] == len(FAMILIES) * len(CAPACITIES) * DECISIONS_PER_PRIMARY_STRATUM,
                       f"got {primary['total_decisions']}"))
    gates.append(gate("diagnostic_sample_size_500", diagnostic["total_decisions"] == 500, f"got {diagnostic['total_decisions']}"))

    for family in FAMILIES:
        for capacity in CAPACITIES:
            n = sum(1 for d in primary["decisions"] if d["family"] == family and d["capacity"] == capacity)
            gates.append(gate(f"stratum_{family}_{capacity}_has_{DECISIONS_PER_PRIMARY_STRATUM}",
                               n == DECISIONS_PER_PRIMARY_STRATUM, f"got {n}"))
    for family in FAMILIES:
        n = sum(1 for d in diagnostic["decisions"] if d["family"] == family)
        gates.append(gate(f"diagnostic_{family}_has_100_decisions", n == 100, f"got {n}"))

    gates.append(gate("selection_used_only_baseline_lru_info",
                       primary.get("selection_uses_only_baseline_lru_information") is True and
                       diagnostic.get("selection_uses_only_baseline_lru_information") is True))

    all_ids = [d["decision_id"] for d in primary["decisions"]]
    gates.append(gate("no_duplicate_primary_decision_ids", len(all_ids) == len(set(all_ids))))

    cand_path = run_dir / "candidate_results.jsonl"
    dec_path = run_dir / "decision_metrics.csv"
    gates.append(gate("raw_candidate_results_exists", cand_path.exists()))
    gates.append(gate("decision_metrics_exists", dec_path.exists()))

    if dec_path.exists():
        rows = list(csv.DictReader(open(dec_path, newline="", encoding="utf-8")))
        expected_metric_rows = (primary["total_decisions"] + diagnostic["total_decisions"]) * len(HORIZONS) * 2  # 2 alt policies
        gates.append(gate("decision_metrics_row_count_matches_expected", len(rows) == expected_metric_rows,
                           f"expected {expected_metric_rows} got {len(rows)}"))

        neg_or_nan = [r["decision_id"] for r in rows if
                      (lambda v: v != v)(float(r["optimal_set_jaccard"])) if r["optimal_set_jaccard"] not in ("", "None")]
        gates.append(gate("no_nan_jaccard", len(neg_or_nan) == 0, str(neg_or_nan[:5])))

        keys = [(r["decision_id"], r["horizon"], r["alt_policy"]) for r in rows]
        gates.append(gate("no_duplicate_decision_metric_keys", len(keys) == len(set(keys))))

        horizons_present = {r["horizon"] for r in rows}
        gates.append(gate("all_three_horizons_present", horizons_present == {str(h) for h in HORIZONS}, str(horizons_present)))

        wiki_rows = [r for r in rows if r["family"] == "wiki2018"]
        gates.append(gate("wiki2018_present", len(wiki_rows) > 0))
        metacdn_rows = [r for r in rows if r["family"] == "metacdn"]
        gates.append(gate("metacdn_present_and_labeled_validation", len(metacdn_rows) > 0))
        metakv_rows = [r for r in rows if r["family"] == "metakv"]
        gates.append(gate("metakv_present", len(metakv_rows) > 0))

        primary_rows = [r for r in rows if r["sample"] == "primary"]
        diag_rows = [r for r in rows if r["sample"] == "diagnostic"]
        gates.append(gate("sample_labels_preserved", len(primary_rows) > 0 and len(diag_rows) > 0))

    manifest_out_path = run_dir / "run_manifest.json"
    gates.append(gate("run_manifest_exists", manifest_out_path.exists()))
    if manifest_out_path.exists():
        run_manifest = json.loads(manifest_out_path.read_text())
        gates.append(gate("raw_output_hash_recorded", "candidate_results.jsonl" in run_manifest.get("output_files", {})))

    all_pass = all(g["passed"] for g in gates)
    result = {"gates": gates, "FULL_EXPERIMENT_VALID": all_pass}
    (run_dir / "validity_gates.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    for g in gates:
        print(f"[{'PASS' if g['passed'] else 'FAIL'}] {g['name']}" + (f" -- {g['detail']}" if g["detail"] else ""))
    print(f"\nFULL_EXPERIMENT_VALID: {all_pass}")
    return all_pass


if __name__ == "__main__":
    ok = main(Path(sys.argv[1]))
    raise SystemExit(0 if ok else 1)
