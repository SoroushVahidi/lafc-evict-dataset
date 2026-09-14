"""Programmatic validity gates for a completed pilot run.

Never marks PILOT_VALID unless every gate below passes. This validates
implementation/harness correctness only -- it never asserts a scientific
robustness conclusion.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pilot_lib import DECISIONS_PER_CELL, PILOT_CELLS, PILOT_HORIZON  # noqa: E402

PILOT_DIR = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PILOT_DIR / "PILOT_MANIFEST.json"


def gate(name, passed, detail=""):
    return {"name": name, "passed": bool(passed), "detail": detail}


def main(run_dir: Path):
    gates = []
    manifest = json.loads(MANIFEST_PATH.read_text())

    lru_eq_path = PILOT_DIR / "outputs" / "lru_equivalence_gate_result.json"
    lru_eq = json.loads(lru_eq_path.read_text()) if lru_eq_path.exists() else None
    gates.append(gate("lru_equivalence_gate_ran", lru_eq is not None))
    if lru_eq is not None:
        gates.append(gate("lru_equivalence_mismatches_zero", lru_eq["n_mismatches"] == 0,
                           f"n_mismatches={lru_eq['n_mismatches']}"))

    gates.append(gate("pilot_manifest_exists", MANIFEST_PATH.exists()))
    gates.append(gate("expected_pilot_cells_present",
                       [(d["family"], d["capacity"]) for d in [{"family": f, "capacity": c} for f, c in PILOT_CELLS]] ==
                       [(c["family"], c["capacity"]) for c in manifest["pilot_cells"]]))
    gates.append(gate("expected_decision_count", manifest["total_decisions"] == len(PILOT_CELLS) * DECISIONS_PER_CELL,
                       f"got {manifest['total_decisions']}"))
    for family, capacity in PILOT_CELLS:
        n = sum(1 for d in manifest["decisions"] if d["family"] == family and d["capacity"] == capacity)
        gates.append(gate(f"cell_{family}_{capacity}_has_{DECISIONS_PER_CELL}_decisions", n == DECISIONS_PER_CELL, f"got {n}"))
    gates.append(gate("all_pilot_decisions_at_horizon_16", all(d["horizon"] == PILOT_HORIZON for d in manifest["decisions"])))
    gates.append(gate("selection_used_only_baseline_lru_info", manifest.get("selection_uses_only_baseline_lru_information") is True))

    decision_ids = [d["decision_id"] for d in manifest["decisions"]]
    gates.append(gate("no_duplicate_decision_ids_in_manifest", len(decision_ids) == len(set(decision_ids))))

    cand_path = run_dir / "candidate_results.csv"
    dec_path = run_dir / "decision_metrics.csv"
    gates.append(gate("candidate_results_exists", cand_path.exists()))
    gates.append(gate("decision_metrics_exists", dec_path.exists()))

    if cand_path.exists():
        rows = list(csv.DictReader(open(cand_path, newline="", encoding="utf-8")))
        gates.append(gate("no_failed_candidate_rows", all(r["status"] == "complete" for r in rows)))

        neg_or_nan = []
        for r in rows:
            try:
                loss = float(r["rollout_loss_h"])
                regret = float(r["rollout_regret_h"])
            except ValueError:
                neg_or_nan.append(r["decision_id"])
                continue
            if loss != loss or regret != regret or loss < 0 or regret < 0:
                neg_or_nan.append(r["decision_id"])
        gates.append(gate("no_nan_or_negative_loss_or_regret", len(neg_or_nan) == 0, str(neg_or_nan[:5])))

        keys = [(r["decision_id"], r["reference_policy"], r["continuation_rng_seed"], r["candidate_page_id"]) for r in rows]
        gates.append(gate("no_duplicate_result_keys", len(keys) == len(set(keys))))

        by_decision_policy = {}
        for r in rows:
            k = (r["decision_id"], r["reference_policy"], r["continuation_rng_seed"])
            by_decision_policy.setdefault(k, set()).add(r["candidate_page_id"])
        expected_candidates = {d["decision_id"]: d["candidate_count"] for d in manifest["decisions"]}
        completeness_ok = all(
            len(cands) == expected_candidates[k[0]] for k, cands in by_decision_policy.items()
        )
        gates.append(gate("candidate_completeness_identical_across_policies", completeness_ok))

        mru_windows = {(r["decision_id"],) for r in rows if r["reference_policy"] == "mru"}
        random_seed_counts = {}
        for r in rows:
            if r["reference_policy"] == "random":
                random_seed_counts.setdefault(r["decision_id"], set()).add(r["continuation_rng_seed"])
        gates.append(gate("every_decision_has_10_random_seeds", all(len(s) == 10 for s in random_seed_counts.values()),
                           str({k: len(v) for k, v in random_seed_counts.items() if len(v) != 10})))

        wiki_rows = [r for r in rows if r["family"] == "wiki2018"]
        gates.append(gate("wiki2018_present_and_handled_separately", len(wiki_rows) > 0))

        metacdn_rows = [r for r in rows if r["family"] == "metacdn"]
        gates.append(gate("metacdn_absent_from_pilot_as_designed", len(metacdn_rows) == 0,
                           "MetaCDN is not one of the 4 pre-registered pilot cells; absence is expected, not an error"))

        metakv_rows = [r for r in rows if r["family"] == "metakv"]
        gates.append(gate("metakv_cap128_present", all(r["capacity"] == "128" for r in metakv_rows) and len(metakv_rows) > 0))

    manifest_out_path = run_dir / "run_manifest.json"
    gates.append(gate("run_manifest_exists", manifest_out_path.exists()))
    if manifest_out_path.exists():
        run_manifest = json.loads(manifest_out_path.read_text())
        gates.append(gate("output_file_hashes_recorded", len(run_manifest.get("output_files", {})) >= 4))

    all_pass = all(g["passed"] for g in gates)
    result = {"gates": gates, "PILOT_VALID": all_pass}
    (run_dir / "validity_gates.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    for g in gates:
        print(f"[{'PASS' if g['passed'] else 'FAIL'}] {g['name']}" + (f" -- {g['detail']}" if g["detail"] else ""))
    print(f"\nPILOT_VALID: {all_pass}")
    return all_pass


if __name__ == "__main__":
    run_dir = Path(sys.argv[1])
    ok = main(run_dir)
    raise SystemExit(0 if ok else 1)
