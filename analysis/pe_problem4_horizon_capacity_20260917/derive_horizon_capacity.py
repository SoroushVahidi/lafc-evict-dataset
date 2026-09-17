import os
import csv
import json

def main():
    source_path = "/home/soroush/projects/lafc-evict-dataset/worktrees/fix-pe-problem1-selector-orientation-certification-20260917/analysis/problem4_matched_horizon_20260917/outputs/matched_family_capacity_horizon_metrics.csv"
    output_dir = "/home/soroush/projects/lafc-evict-dataset/worktrees/fix-pe-problem1-selector-orientation-certification-20260917/analysis/pe_problem4_horizon_capacity_20260917"
    os.makedirs(output_dir, exist_ok=True)
    
    output_csv = os.path.join(output_dir, "horizon_capacity_analysis.csv")
    output_summary = os.path.join(output_dir, "horizon_capacity_summary.json")
    
    rows = []
    
    with open(source_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            family = row['reader_family']
            capacity = int(row['capacity'])
            horizon = int(row['horizon'])
            H_over_C = float(horizon) / capacity
            n_decisions = int(row['n_decisions'])
            all_tied_fraction = float(row['all_tied_fraction'])
            discriminative_fraction = 1.0 - all_tied_fraction
            random_optimal_probability = float(row['random_optimal_probability'])
            mean_random_regret = float(row['expected_random_regret'])
            mean_random_regret_per_request = mean_random_regret / horizon
            
            rows.append({
                'family': family,
                'capacity': capacity,
                'horizon': horizon,
                'H_over_C': H_over_C,
                'n_decisions': n_decisions,
                'all_tied_fraction': all_tied_fraction,
                'discriminative_fraction': discriminative_fraction,
                'random_optimal_probability': random_optimal_probability,
                'mean_random_regret': mean_random_regret,
                'mean_random_regret_per_request': mean_random_regret_per_request
            })
            
    # Sort rows by family, capacity, and horizon for neatness
    rows.sort(key=lambda x: (x['family'], x['capacity'], x['horizon']))
    
    # Write CSV
    headers = [
        'family', 'capacity', 'horizon', 'H_over_C', 'n_decisions',
        'all_tied_fraction', 'discriminative_fraction', 'random_optimal_probability',
        'mean_random_regret', 'mean_random_regret_per_request'
    ]
    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
            
    # Compute pooled averages for different H_over_C groups or specific insights
    # Group by H_over_C
    groups = {}
    for r in rows:
        ratio = r['H_over_C']
        if ratio not in groups:
            groups[ratio] = []
        groups[ratio].append(r)
        
    summary_by_ratio = {}
    for ratio, g_rows in sorted(groups.items()):
        total_decisions = sum(x['n_decisions'] for x in g_rows)
        # Weighted mean of all_tied_fraction
        weighted_all_tied = sum(x['all_tied_fraction'] * x['n_decisions'] for x in g_rows) / total_decisions
        weighted_disc = 1.0 - weighted_all_tied
        weighted_rand_opt = sum(x['random_optimal_probability'] * x['n_decisions'] for x in g_rows) / total_decisions
        weighted_regret = sum(x['mean_random_regret'] * x['n_decisions'] for x in g_rows) / total_decisions
        weighted_regret_per_req = sum(x['mean_random_regret_per_request'] * x['n_decisions'] for x in g_rows) / total_decisions
        
        summary_by_ratio[str(ratio)] = {
            'ratio': ratio,
            'cells_count': len(g_rows),
            'total_decisions': total_decisions,
            'pooled_all_tied_fraction': weighted_all_tied,
            'pooled_discriminative_fraction': weighted_disc,
            'pooled_random_optimal_probability': weighted_rand_opt,
            'pooled_mean_random_regret': weighted_regret,
            'pooled_mean_random_regret_per_request': weighted_regret_per_req
        }
        
    # Write summary JSON
    summary_data = {
        'total_cells': len(rows),
        'by_ratio_pooled': summary_by_ratio,
        'all_ratios_covered': sorted(list(set(r['H_over_C'] for r in rows))),
        'all_ratios_covered_str': [f"{x:.4f}" for x in sorted(list(set(r['H_over_C'] for r in rows)))]
    }
    
    with open(output_summary, 'w') as f:
        json.dump(summary_data, f, indent=2)
        
    print("Derived H/C analysis complete. Outputs written to:")
    print(f"  CSV: {output_csv}")
    print(f"  JSON: {output_summary}")
    print("\nPooled metrics by H/C ratio:")
    for ratio_str, info in sorted(summary_by_ratio.items(), key=lambda x: float(x[0])):
        print(f"  H/C = {float(ratio_str):.4f} (cells: {info['cells_count']}): "
              f"pooled_all_tied = {info['pooled_all_tied_fraction']:.4f}, "
              f"pooled_disc = {info['pooled_discriminative_fraction']:.4f}, "
              f"pooled_regret_per_req = {info['pooled_mean_random_regret_per_request']:.6f}")

if __name__ == "__main__":
    main()
