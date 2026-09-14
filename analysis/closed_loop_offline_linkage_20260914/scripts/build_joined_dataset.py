"""Build the joined offline/closed-loop dataset used to answer RQ-CL1-CL4.

Sources (read-only; nothing here is regenerated or resampled):

- Offline LRU/MRU regret:
  analysis/sigmod_target_discriminativeness_20260913/outputs/phase8_lru_mru_stratified.csv
  columns used: trace_family, capacity, horizon, lru_mean_regret, mru_mean_regret
  (lru_optimal_rate/mru_optimal_rate also carried through for reference).
  NOTE: this file has NO column for a "random" or "sieve" policy.

- Offline random-policy regret + discriminativeness context:
  analysis/sigmod_target_discriminativeness_20260913/outputs/phase4_stratified_family_capacity_horizon.csv
  columns used: trace_family, capacity, horizon, mean_random_regret,
  all_tied_fraction, unique_winner_fraction, random_optimal_probability.
  "mean_random_regret" here IS the offline regret of the uniform-random
  selector (Section 2/Section 7 of the target-discriminativeness REPORT.md),
  not a generic aggregate discriminativeness score -- all_tied_fraction and
  random_optimal_probability are kept separately and are NEVER treated as
  policy-specific performance numbers.

  There is NO offline SIEVE quantity anywhere in these files. SIEVE is
  therefore excluded from every offline<->closed-loop comparison below, by
  construction (the join simply never looks for a "sieve" column).

- Closed-loop Tier-1 evidence (frozen, byte-verified):
  analysis/closed_loop_tier1_evidence_20260914/run/<RUN_ID>/summary.csv
  columns used: family, capacity, policy, miss_ratio, scored_split_label.
  Only rows for policy in {lru, mru, random} are used (sieve is read but not
  joined against any offline counterpart, since none exists).

Both offline capacity columns include {32, 64, 128, 256}; only {32, 128} are
used here (Tier 1's actual matrix) -- 64 and 256 are dropped, not silently
included. Both offline files include horizons {4, 8, 16}; the closed-loop
side has no horizon, so each (family, capacity) closed-loop row is compared
against all three offline horizons separately (never pooled into one
horizon-blind number), matching DESIGN.md's "Offline Horizon Relationship"
section ("compare offline ... ordering and regret gaps at each H against the
closed-loop ... ordering and miss gaps").

Output: data/joined_offline_closed_loop.csv, one row per
(family, capacity, horizon) with both offline and closed-loop columns.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]  # .../<harness-or-linkage-worktree>
ANALYSIS_ROOT = Path(__file__).resolve().parents[1]

OFFLINE_DIR = REPO_ROOT / "analysis" / "sigmod_target_discriminativeness_20260913" / "outputs"
PHASE4_PATH = OFFLINE_DIR / "phase4_stratified_family_capacity_horizon.csv"
PHASE8_PATH = OFFLINE_DIR / "phase8_lru_mru_stratified.csv"

EVIDENCE_DIR = REPO_ROOT / "analysis" / "closed_loop_tier1_evidence_20260914" / "run"
RUN_ID = "20260914T023445Z_8a4cd32402a1"
CLOSED_LOOP_SUMMARY_PATH = EVIDENCE_DIR / RUN_ID / "summary.csv"

TIER1_FAMILIES = ("cloudphysics", "metacdn", "metakv", "twemcache", "wiki2018")
TIER1_CAPACITIES = ("32", "128")
OFFLINE_HORIZONS = ("4", "8", "16")

OUT_PATH = ANALYSIS_ROOT / "joined_data" / "joined_offline_closed_loop.csv"


def load_phase8():
    rows = {}
    with open(PHASE8_PATH, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["trace_family"] not in TIER1_FAMILIES or row["capacity"] not in TIER1_CAPACITIES:
                continue
            key = (row["trace_family"], row["capacity"], row["horizon"])
            rows[key] = {
                "offline_lru_mean_regret": float(row["lru_mean_regret"]),
                "offline_lru_optimal_rate": float(row["lru_optimal_rate"]),
                "offline_mru_mean_regret": float(row["mru_mean_regret"]),
                "offline_mru_optimal_rate": float(row["mru_optimal_rate"]),
            }
    return rows


def load_phase4():
    rows = {}
    with open(PHASE4_PATH, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["trace_family"] not in TIER1_FAMILIES or row["capacity"] not in TIER1_CAPACITIES:
                continue
            key = (row["trace_family"], row["capacity"], row["horizon"])
            rows[key] = {
                "offline_random_mean_regret": float(row["mean_random_regret"]),
                "offline_random_optimal_probability": float(row["random_optimal_probability"]),
                "offline_all_tied_fraction": float(row["all_tied_fraction"]),
                "offline_unique_winner_fraction": float(row["unique_winner_fraction"]),
                "offline_n_decisions": int(row["n_decisions"]),
            }
    return rows


def load_closed_loop():
    rows = {}
    with open(CLOSED_LOOP_SUMMARY_PATH, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["family"] not in TIER1_FAMILIES or row["capacity"] not in TIER1_CAPACITIES:
                continue
            if row["policy"] not in ("lru", "mru", "random", "sieve"):
                continue
            key = (row["family"], row["capacity"])
            rows.setdefault(key, {})[row["policy"]] = row
    return rows


def main():
    phase8 = load_phase8()
    phase4 = load_phase4()
    closed_loop = load_closed_loop()

    assert set(k[:2] for k in phase8.keys()) == {(f, c) for f in TIER1_FAMILIES for c in TIER1_CAPACITIES}, \
        "phase8 join key coverage mismatch -- expected exactly 10 (family, capacity) pairs x 3 horizons"
    assert len(phase8) == 30, f"expected 30 phase8 rows after filtering, got {len(phase8)}"
    assert len(phase4) == 30, f"expected 30 phase4 rows after filtering, got {len(phase4)}"
    assert len(closed_loop) == 10, f"expected 10 (family, capacity) closed-loop cells, got {len(closed_loop)}"

    out_rows = []
    for family in TIER1_FAMILIES:
        for capacity in TIER1_CAPACITIES:
            cl_cell = closed_loop[(family, capacity)]
            cl_lru = cl_cell["lru"]
            cl_mru = cl_cell["mru"]
            cl_random = cl_cell["random"]
            cl_sieve = cl_cell.get("sieve")
            split_label = cl_lru["scored_split_label"]
            assert cl_mru["scored_split_label"] == split_label
            assert cl_random["scored_split_label"] == split_label

            cl_lru_mr = float(cl_lru["miss_ratio"])
            cl_mru_mr = float(cl_mru["miss_ratio"])
            cl_random_mr = float(cl_random["miss_ratio"])
            cl_sieve_mr = float(cl_sieve["miss_ratio"]) if cl_sieve else None

            for horizon in OFFLINE_HORIZONS:
                p8 = phase8[(family, capacity, horizon)]
                p4 = phase4[(family, capacity, horizon)]

                row = {
                    "family": family,
                    "capacity": int(capacity),
                    "horizon": int(horizon),
                    "scored_split_label": split_label,
                    "is_metacdn_validation_window": family == "metacdn",
                    "is_wiki2018_offline_degenerate_control": family == "wiki2018",
                    "is_metakv_first_window_no_warmup": family == "metakv",
                    **p8,
                    **p4,
                    "cl_lru_miss_ratio": cl_lru_mr,
                    "cl_mru_miss_ratio": cl_mru_mr,
                    "cl_random_mean_miss_ratio": cl_random_mr,
                    "cl_random_miss_ratio_std": float(cl_random.get("miss_ratio_std") or 0.0),
                    "cl_random_n_seeds": int(float(cl_random.get("n_seeds") or 0)),
                    "cl_sieve_miss_ratio": cl_sieve_mr,
                    "offline_mru_minus_lru_regret_gap": p8["offline_mru_mean_regret"] - p8["offline_lru_mean_regret"],
                    "offline_random_minus_lru_regret_gap": p4["offline_random_mean_regret"] - p8["offline_lru_mean_regret"],
                    "cl_mru_minus_lru_miss_ratio_gap": cl_mru_mr - cl_lru_mr,
                    "cl_random_minus_lru_miss_ratio_gap": cl_random_mr - cl_lru_mr,
                }
                out_rows.append(row)

    assert len(out_rows) == 30, f"expected exactly 30 joined rows (5 families x 2 capacities x 3 horizons), got {len(out_rows)}"
    assert all(r["capacity"] in (32, 128) for r in out_rows), "capacities 64/256 leaked into the joined dataset"
    assert all(r["horizon"] in (4, 8, 16) for r in out_rows)
    metacdn_rows = [r for r in out_rows if r["family"] == "metacdn"]
    assert all(r["scored_split_label"] == "validation" for r in metacdn_rows), "MetaCDN must be labeled validation, never test"
    non_metacdn_rows = [r for r in out_rows if r["family"] != "metacdn"]
    assert all(r["scored_split_label"] == "test" for r in non_metacdn_rows)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(out_rows[0].keys())
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in out_rows:
            writer.writerow(row)

    print(f"Wrote {len(out_rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
