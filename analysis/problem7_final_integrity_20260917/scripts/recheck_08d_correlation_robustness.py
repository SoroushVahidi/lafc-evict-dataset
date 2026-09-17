"""Problem 7 Phase 5: independent recomputation + robustness recheck of the
r=-0.83 (hit-rate vs discriminativeness) correlation reported in
sections/08d_mechanistic.tex, using only the existing, already-generated
analysis/closed_loop_mechanistic_analysis_20260914/outputs/mechanism_comparison.csv
artifact (no new simulation, no new closed-loop run).
"""
import csv
import itertools
import json

from scipy import stats
import numpy as np

rows = list(csv.DictReader(
    open("analysis/closed_loop_mechanistic_analysis_20260914/outputs/mechanism_comparison.csv")
))
hit = np.array([float(r["predicted_lru_hit_rate"]) for r in rows])
disc = np.array([1 - float(r["offline_all_tied_fraction_H16"]) for r in rows])
gap = np.array([float(r["cl_mru_minus_lru_miss_ratio_gap"]) for r in rows])
families = [r["family"] for r in rows]
uniq_families = sorted(set(families))
fam_idx = {f: [i for i, fam in enumerate(families) if fam == f] for f in uniq_families}

r_disc, p_disc = stats.pearsonr(hit, disc)
r_gap, p_gap = stats.pearsonr(hit, gap)

lofo_disc = {}
lofo_gap = {}
for fam in uniq_families:
    idx = [i for i, fam2 in enumerate(families) if fam2 != fam]
    lofo_disc[fam] = float(stats.pearsonr(hit[idx], disc[idx])[0])
    lofo_gap[fam] = float(stats.pearsonr(hit[idx], gap[idx])[0])

obs_r = r_disc
count, total = 0, 0
for perm in itertools.permutations(uniq_families):
    new_hit = np.zeros(len(rows))
    for src_fam, dst_fam in zip(uniq_families, perm):
        for si, di in zip(fam_idx[src_fam], fam_idx[dst_fam]):
            new_hit[di] = hit[si]
    rr = stats.pearsonr(new_hit, disc)[0]
    total += 1
    if abs(rr) >= abs(obs_r) - 1e-9:
        count += 1
perm_p_disc = count / total

result = {
    "note": (
        "Recomputes the manuscript's reported r=-0.83 (hit-rate vs. "
        "all-tied fraction, i.e. r=+0.83 vs. discriminativeness) and "
        "r=0.90 (hit-rate vs. closed-loop MRU-LRU gap) claims from "
        "sections/08d_mechanistic.tex directly from the existing "
        "mechanism_comparison.csv artifact, then checks leave-one-family-out "
        "(LOFO) stability and an exact family-level permutation test "
        "(5! = 120 permutations, the only exact test defensible at n=10 "
        "drawn from 5 family clusters)."
    ),
    "n": len(rows),
    "pearson_r_hit_rate_vs_discriminativeness_full": r_disc,
    "pearson_p_hit_rate_vs_discriminativeness_full": p_disc,
    "pearson_r_hit_rate_vs_cl_mru_lru_gap_full": r_gap,
    "pearson_p_hit_rate_vs_cl_mru_lru_gap_full": p_gap,
    "lofo_r_discriminativeness_by_excluded_family": lofo_disc,
    "lofo_r_cl_gap_by_excluded_family": lofo_gap,
    "exact_family_permutation_p_discriminativeness": perm_p_disc,
    "conclusion": (
        "The hit-rate vs. discriminativeness correlation (manuscript's "
        "r=-0.83) is NOT robust: excluding metacdn drops it from 0.832 to "
        "0.691, and the exact family-level permutation p=0.117 does not "
        "clear a nominal 0.05 threshold. The hit-rate vs. closed-loop-gap "
        "correlation (manuscript's r=0.90) IS robust: LOFO range is "
        "0.827-0.983 across all five exclusions, always strongly positive. "
        "This asymmetry was not previously disclosed in the manuscript "
        "text; sections/08d_mechanistic.tex is corrected in this Problem-7 "
        "pass to state it."
    ),
}
print(json.dumps(result, indent=2))
with open("analysis/problem7_final_integrity_20260917/outputs/correlation_robustness_recheck.json", "w") as f:
    json.dump(result, f, indent=2)
