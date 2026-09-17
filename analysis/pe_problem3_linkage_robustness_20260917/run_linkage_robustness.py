import os
import json
import csv
import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr, kendalltau

def sign_concordance(x, y):
    agree = sum((x > 0) & (y > 0)) + sum((x < 0) & (y < 0))
    disagree = sum((x > 0) & (y < 0)) + sum((x < 0) & (y > 0))
    tied = sum((x == 0) | (y == 0))
    return agree, disagree, tied

def compute_stats(df, col_x, col_y):
    x = df[col_x].values
    y = df[col_y].values
    n = len(df)
    if n < 2:
        return None, None, None, (0,0,0)
    
    # Handle perfect ties giving NaNs
    if np.std(x) == 0 or np.std(y) == 0:
        return np.nan, np.nan, np.nan, sign_concordance(x, y)

    r, _ = pearsonr(x, y)
    rho, _ = spearmanr(x, y)
    tau, _ = kendalltau(x, y)
    signs = sign_concordance(x, y)
    return r, rho, tau, signs

def exact_family_permutation_pvalue(df, col_x, col_y):
    """
    Exact family block permutation.
    5 families -> 5! = 120 block permutations.
    """
    import itertools
    
    families = df['family'].unique()
    if len(families) != 5:
        return None  # Only implemented for exactly 5 families
        
    x = df[col_x].values
    y = df[col_y].values
    
    obs_r, _, _, _ = compute_stats(df, col_x, col_y)
    if obs_r is None or np.isnan(obs_r):
        return None
        
    obs_abs_r = abs(obs_r)
    
    # Group indices by family
    fam_indices = {f: df.index[df['family'] == f].tolist() for f in families}
    
    count_geq = 0
    total = 0
    
    for perm in itertools.permutations(families):
        total += 1
        perm_y = np.zeros_like(y)
        for orig_fam, dest_fam in zip(families, perm):
            orig_idx = fam_indices[orig_fam]
            dest_idx = fam_indices[dest_fam]
            
            # Simple capacity alignment assumption: the indices are sorted by capacity within family
            for i, o_idx in enumerate(orig_idx):
                perm_y[o_idx] = y[dest_idx[i]]
                
        r_perm, _ = pearsonr(x, perm_y)
        if abs(r_perm) >= obs_abs_r - 1e-9:
            count_geq += 1
            
    return count_geq / total

def main():
    source_path = "/home/soroush/projects/lafc-evict-dataset/worktrees/fix-pe-problem1-selector-orientation-certification-20260917/analysis/closed_loop_offline_linkage_20260914/joined_data/joined_offline_closed_loop.csv"
    output_dir = "/home/soroush/projects/lafc-evict-dataset/worktrees/fix-pe-problem1-selector-orientation-certification-20260917/analysis/pe_problem3_linkage_robustness_20260917"
    os.makedirs(output_dir, exist_ok=True)
    
    df_all = pd.read_csv(source_path)
    
    # Preregistered Primary Horizon is H=16
    df_h16 = df_all[df_all['horizon'] == 16].copy()
    df_h16.reset_index(drop=True, inplace=True)
    
    results = {}
    
    metrics = {
        "mru_vs_lru": ("offline_mru_minus_lru_regret_gap", "cl_mru_minus_lru_miss_ratio_gap"),
        "random_vs_lru": ("offline_random_minus_lru_regret_gap", "cl_random_minus_lru_miss_ratio_gap")
    }
    
    # 1. HEADLINE
    results["headline"] = {}
    for name, (col_x, col_y) in metrics.items():
        r, rho, tau, signs = compute_stats(df_h16, col_x, col_y)
        results["headline"][name] = {
            "n": len(df_h16),
            "pearson": r,
            "spearman": rho,
            "kendall": tau,
            "sign_concordance": {"agree": int(signs[0]), "disagree": int(signs[1]), "tied": int(signs[2])}
        }
        
    # 2. LOFO
    results["lofo"] = {}
    lofo_rows = []
    families = sorted(df_h16['family'].unique())
    for name, (col_x, col_y) in metrics.items():
        results["lofo"][name] = {}
        for fam in families:
            df_lofo = df_h16[df_h16['family'] != fam]
            r, rho, tau, signs = compute_stats(df_lofo, col_x, col_y)
            results["lofo"][name][fam] = {
                "excluded": fam,
                "n": len(df_lofo),
                "pearson": r,
                "spearman": rho,
                "kendall": tau,
                "sign_concordance": {"agree": int(signs[0]), "disagree": int(signs[1]), "tied": int(signs[2])}
            }
            lofo_rows.append({
                "comparison": name,
                "excluded_family": fam,
                "n_remaining": len(df_lofo),
                "pearson": r,
                "spearman": rho,
                "kendall": tau,
                "sign_agree": int(signs[0]),
                "sign_disagree": int(signs[1]),
                "sign_tied": int(signs[2])
            })
            
    pd.DataFrame(lofo_rows).to_csv(os.path.join(output_dir, "lofo_summary.csv"), index=False)

    # 3. EXCLUSIONS (MetaCDN, wiki2018)
    results["exclusions"] = {}
    for name, (col_x, col_y) in metrics.items():
        results["exclusions"][name] = {}
        
        # Exclude MetaCDN
        df_no_metacdn = df_h16[df_h16['family'] != 'metacdn']
        r, rho, tau, signs = compute_stats(df_no_metacdn, col_x, col_y)
        results["exclusions"][name]["exclude_metacdn"] = {
            "n": len(df_no_metacdn),
            "pearson": r, "spearman": rho, "kendall": tau,
            "sign_concordance": {"agree": int(signs[0]), "disagree": int(signs[1]), "tied": int(signs[2])}
        }
        
        # Exclude wiki2018
        df_no_wiki = df_h16[df_h16['family'] != 'wiki2018']
        r, rho, tau, signs = compute_stats(df_no_wiki, col_x, col_y)
        results["exclusions"][name]["exclude_wiki2018"] = {
            "n": len(df_no_wiki),
            "pearson": r, "spearman": rho, "kendall": tau,
            "sign_concordance": {"agree": int(signs[0]), "disagree": int(signs[1]), "tied": int(signs[2])}
        }
        
    # 4. EXACT FAMILY PERMUTATION
    results["family_permutation"] = {}
    for name, (col_x, col_y) in metrics.items():
        pval = exact_family_permutation_pvalue(df_h16, col_x, col_y)
        results["family_permutation"][name] = {
            "null_hypothesis": "The assignment of closed-loop family blocks to offline family blocks is arbitrary. Permuting the 5 blocks preserves the 2-capacity internal structure of each family.",
            "n_permutations": 120,
            "exact_p_value_pearson": pval
        }

    # Save to JSON
    with open(os.path.join(output_dir, "robustness_summary.json"), "w") as f:
        json.dump(results, f, indent=2)
        
    print("Robustness analysis complete.")
    for name in metrics:
        print(f"\n--- {name} ---")
        print(f"Headline Pearson: {results['headline'][name]['pearson']:.3f} (n={results['headline'][name]['n']})")
        print(f"Exact Family-Block Permutation p-value: {results['family_permutation'][name]['exact_p_value_pearson']}")
        min_r = min(results['lofo'][name][f]['pearson'] for f in families)
        max_r = max(results['lofo'][name][f]['pearson'] for f in families)
        print(f"LOFO Pearson range: [{min_r:.3f}, {max_r:.3f}]")

if __name__ == "__main__":
    main()
