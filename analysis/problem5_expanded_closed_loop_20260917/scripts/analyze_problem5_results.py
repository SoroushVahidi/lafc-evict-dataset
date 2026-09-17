"""Problem-5 Phases 6-8: combine expanded results with frozen Tier-1 evidence,
answer the pre-specified scientific questions, and produce the primary table
and policy-spread analysis.

Inputs (read-only):
- analysis/closed_loop_offline_linkage_20260914/joined_data/joined_offline_closed_loop.csv
  (frozen Tier-1 LRU/MRU/random/SIEVE miss ratios + offline H=16 informativeness,
  n=10 rows at horizon=16, the same 10 cells this script adds ARC/LIRS/S3-FIFO to)
- analysis/problem5_expanded_closed_loop_20260917/outputs/problem5_expanded_run_results.jsonl
  (this Problem-5 run's ARC/LIRS/S3-FIFO miss ratios)

Outputs:
- outputs/problem5_primary_table.csv (+ .tex)
- outputs/problem5_policy_spread.csv
- outputs/problem5_scientific_answers.json
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ANALYSIS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ANALYSIS_DIR.parents[1]
OUT_DIR = ANALYSIS_DIR / "outputs"

JOINED_CSV = REPO_ROOT / "analysis" / "closed_loop_offline_linkage_20260914" / "joined_data" / "joined_offline_closed_loop.csv"
EXPANDED_JSONL = OUT_DIR / "problem5_expanded_run_results.jsonl"

EXISTING_POLICIES = ["lru", "mru", "random", "sieve"]
EXPANDED_POLICIES = ["arc", "lirs", "s3fifo"]
ALL_POLICIES = EXISTING_POLICIES + EXPANDED_POLICIES


def load_existing() -> dict:
    """Return {(family, capacity): {..H=16 offline + closed-loop fields..}}"""
    out = {}
    with open(JOINED_CSV, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if int(row["horizon"]) != 16:
                continue
            key = (row["family"], int(row["capacity"]))
            out[key] = {
                "lru": float(row["cl_lru_miss_ratio"]),
                "mru": float(row["cl_mru_miss_ratio"]),
                "random": float(row["cl_random_mean_miss_ratio"]),
                "sieve": float(row["cl_sieve_miss_ratio"]),
                # Use the manuscript's standard discriminative-fraction
                # definition (1 - all_tied_fraction), consistent with
                # Problems 3-4, rather than the much stricter
                # offline_unique_winner_fraction column (exactly one
                # strictly-optimal candidate, near-zero for every one of
                # these 10 cells -- a real property of this benchmark's tie
                # structure, but not a usable discriminativeness proxy here
                # since it has ~zero variance across cells).
                "offline_discriminative_fraction": 1.0 - float(row["offline_all_tied_fraction"]),
                "offline_all_tied_fraction": float(row["offline_all_tied_fraction"]),
                "offline_n_decisions": int(row["offline_n_decisions"]),
            }
    return out


def load_expanded() -> dict:
    out = {}
    with open(EXPANDED_JSONL, encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            key = (row["family"], int(row["capacity"]))
            out.setdefault(key, {})[row["policy"]] = float(row["miss_ratio"])
    return out


def pearson(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0:
        return float("nan")
    return cov / (vx ** 0.5 * vy ** 0.5)


def main() -> None:
    existing = load_existing()
    expanded = load_expanded()
    assert set(existing.keys()) == set(expanded.keys()), (
        f"cell mismatch: existing={sorted(existing.keys())} expanded={sorted(expanded.keys())}"
    )

    rows = []
    for (family, capacity) in sorted(existing.keys()):
        e = existing[(family, capacity)]
        x = expanded[(family, capacity)]
        row = {
            "family": family,
            "capacity": capacity,
            "lru": e["lru"],
            "mru": e["mru"],
            "random": e["random"],
            "sieve": e["sieve"],
            "arc": x["arc"],
            "lirs": x["lirs"],
            "s3fifo": x["s3fifo"],
            "offline_discriminative_fraction": e["offline_discriminative_fraction"],
            "offline_all_tied_fraction": e["offline_all_tied_fraction"],
        }
        miss_ratios = {p: row[p] for p in ALL_POLICIES}
        best_policy = min(miss_ratios, key=miss_ratios.get)
        row["best_policy_all7"] = best_policy
        row["best_miss_ratio_all7"] = miss_ratios[best_policy]
        row["lru_is_best_all7"] = best_policy == "lru"
        row["policy_spread_all7"] = max(miss_ratios.values()) - min(miss_ratios.values())
        # Old (Tier-1, 4-policy) spread, for the population-vs-landscape decomposition.
        old_miss_ratios = {p: row[p] for p in EXISTING_POLICIES}
        row["policy_spread_old4"] = max(old_miss_ratios.values()) - min(old_miss_ratios.values())
        for p in EXPANDED_POLICIES:
            row[f"{p}_relative_diff_vs_lru"] = (row[p] - row["lru"]) / row["lru"] if row["lru"] else float("nan")
        rows.append(row)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Primary table (Phase 8) ---
    primary_fields = ["family", "capacity"] + ALL_POLICIES + [
        "best_policy_all7", "lru_is_best_all7",
    ]
    with open(OUT_DIR / "problem5_primary_table.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=primary_fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in primary_fields})

    with open(OUT_DIR / "problem5_primary_table.tex", "w", encoding="utf-8") as fh:
        fh.write("\\begin{table}[t]\n  \\centering\n  \\small\n")
        fh.write(
            "  \\caption{Expanded Tier-1 closed-loop comparison: miss ratio by "
            "family, capacity, and policy. LRU/MRU/random/SIEVE reproduced "
            "byte-for-byte from the frozen Tier-1 evidence "
            "(\\texttt{analysis/closed\\_loop\\_tier1\\_evidence\\_20260914/}); "
            "ARC, LIRS, S3-FIFO added under the identical protocol "
            "(Problem 5).}\n"
        )
        fh.write("  \\label{tab:expanded-closed-loop}\n")
        fh.write("  \\begin{tabular}{llrrrrrrr}\n    \\toprule\n")
        fh.write("    Family & Cap. & LRU & MRU & Random & SIEVE & ARC & LIRS & S3-FIFO \\\\\n    \\midrule\n")
        for row in rows:
            fh.write(
                f"    {row['family']} & {row['capacity']} & "
                f"{row['lru']:.4f} & {row['mru']:.4f} & {row['random']:.4f} & "
                f"{row['sieve']:.4f} & {row['arc']:.4f} & {row['lirs']:.4f} & "
                f"{row['s3fifo']:.4f} \\\\\n"
            )
        fh.write("    \\bottomrule\n  \\end{tabular}\n\\end{table}\n")

    # --- Policy spread vs informativeness (Phase 7) ---
    spread_fields = [
        "family", "capacity", "policy_spread_all7", "policy_spread_old4",
        "offline_discriminative_fraction", "offline_all_tied_fraction",
        "best_policy_all7",
    ]
    with open(OUT_DIR / "problem5_policy_spread.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=spread_fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in spread_fields})

    spreads_all7 = [row["policy_spread_all7"] for row in rows]
    spreads_old4 = [row["policy_spread_old4"] for row in rows]
    disc = [row["offline_discriminative_fraction"] for row in rows]
    r_all7 = pearson(disc, spreads_all7)
    r_old4 = pearson(disc, spreads_old4)

    # --- Scientific questions (Phase 6) ---
    n_cells = len(rows)
    n_lru_best_all7 = sum(1 for r in rows if r["lru_is_best_all7"])
    exceptions_all7 = [
        {"family": r["family"], "capacity": r["capacity"], "best_policy": r["best_policy_all7"],
         "lru_miss_ratio": r["lru"], "best_miss_ratio": r["best_miss_ratio_all7"],
         "relative_gap_pct": 100.0 * (r["lru"] - r["best_miss_ratio_all7"]) / r["lru"] if r["lru"] else float("nan")}
        for r in rows if not r["lru_is_best_all7"]
    ]
    # Was this exception already known from the old 4-policy Tier-1 table?
    known_exception_cells = {("metakv", 32), ("metakv", 128)}  # metakv/cap128 documented; cap32 checked too
    old4_exceptions = [
        (r["family"], r["capacity"]) for r in rows
        if min(r["lru"], r["mru"], r["random"], r["sieve"]) < r["lru"]
    ]
    new_exceptions = [
        e for e in exceptions_all7
        if (e["family"], e["capacity"]) not in set(old4_exceptions)
    ]

    substantial_new_winner = [
        e for e in exceptions_all7 if e["relative_gap_pct"] >= 5.0 and e["best_policy"] in EXPANDED_POLICIES
    ]

    answers = {
        "Q1_lru_competitive": {
            "n_cells": n_cells,
            "n_cells_lru_is_best_of_7": n_lru_best_all7,
            "n_cells_lru_is_best_of_4_old": sum(
                1 for r in rows if r["lru"] == min(r["lru"], r["mru"], r["random"], r["sieve"])
            ),
            "exceptions_of_7": exceptions_all7,
            "conclusion": (
                "LRU remains the best or tied-best policy in "
                f"{n_lru_best_all7}/{n_cells} cells under the expanded 7-policy "
                "landscape (vs. previously best in 9/10 under the 4-policy "
                "landscape)."
            ),
        },
        "Q2_discriminativeness_vs_spread": {
            "pearson_r_offline_discriminative_fraction_vs_policy_spread_all7": r_all7,
            "pearson_r_offline_discriminative_fraction_vs_policy_spread_old4": r_old4,
            "n": n_cells,
            "conclusion": (
                "Correlation between offline discriminativeness and closed-loop "
                "policy spread computed both for the original 4-policy landscape "
                "and the expanded 7-policy landscape; see pearson_r fields."
            ),
        },
        "Q3_new_exceptions": {
            "old_4_policy_exceptions": [{"family": f, "capacity": c} for f, c in old4_exceptions],
            "new_exceptions_from_expansion": new_exceptions,
            "conclusion": (
                "No new family/capacity exception beyond the known metakv cells "
                "was introduced by the expanded policy set."
                if not new_exceptions else
                f"{len(new_exceptions)} new exception(s) found: {new_exceptions}"
            ),
        },
        "Q4_offline_closedloop_link_survives": {
            "note": (
                "The original MRU-vs-LRU and random-vs-LRU offline<->closed-loop "
                "correspondence (r=0.83-0.97, n=10) is untouched by this analysis "
                "(Problem 5 does not recompute it); this question is instead "
                "answered via the policy_spread correlation above, which is the "
                "closed-loop-only, no-offline-counterpart-required generalization "
                "described in COMPARATOR_PROTOCOL.md Phase 7."
            ),
        },
        "Q5_new_policy_changes_interpretation": {
            "substantial_new_winners_ge_5pct": substantial_new_winner,
            "conclusion": (
                "No expanded policy substantially (>=5% relative) beats all "
                "existing Tier-1 comparators anywhere in a way that would change "
                "the manuscript's interpretation."
                if not substantial_new_winner else
                f"{len(substantial_new_winner)} cell(s) show a substantial new "
                f"winner: {substantial_new_winner}"
            ),
        },
    }

    (OUT_DIR / "problem5_scientific_answers.json").write_text(
        json.dumps(answers, indent=2, sort_keys=True), encoding="utf-8"
    )

    print(json.dumps(answers, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
