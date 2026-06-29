# Statistics Jobs

## Goal

Enumerate exactly which benchmark statistics are needed for the SIGMOD paper and classify the cheapest trustworthy source for each one.

## Job table

| Statistic | Needed for | Cheapest source | Why | Expected execution mode |
| --- | --- | --- | --- | --- |
| Candidate-row count | scale table | existing manifest only | already present in `row_counts.candidate_rows` | local metadata read |
| Decision-row count | scale table | existing manifest only | already present in `row_counts.decision_view` | local metadata read |
| Pairwise-sample row count | scale table | existing manifest only | already present in `row_counts.pairwise_sample` | local metadata read |
| Selected families | scope table | existing manifest only | already present in `selected_families` | local metadata read |
| Excluded families | scope table | existing manifest only | already present in `excluded_families` | local metadata read |
| Split counts | composition table | existing manifest only | already present in `row_counts_by_split` | local metadata read |
| Family counts | composition table | existing manifest only | already present in `row_counts_by_trace_family` | local metadata read |
| Capacity counts | composition table | existing manifest only | already present in `row_counts_by_capacity` | local metadata read |
| Horizon counts | composition table | existing manifest only | already present in `row_counts_by_horizon` | local metadata read |
| File count / release bytes | artifact table | publication manifest or release manifest only | already available in preserved metadata | local metadata read |
| Candidate-count per decision distribution | characterization | decision view only | `candidate_count` is already summarized there | local scan of decision view metadata/content |
| Tie fraction | characterization | decision view only | `tie_count` and `optimal_candidate_count` are in decision view | local scan of decision view metadata/content |
| Regret summary distributions | characterization | decision view only | `regret_mean`, `regret_std`, `regret_max`, `regret_sum` are in decision view | local scan of decision view metadata/content |
| Optimal-set size distribution | characterization | decision view only | `optimal_candidate_count` is already in decision view | local scan of decision view |
| Pairwise label balance | characterization | pairwise sample only | pairwise labels are already materialized in the sample | local scan of pairwise-sample parquet |
| Pairwise tie rate | characterization | pairwise sample only | `is_tie` already exists in sample | local scan of pairwise-sample parquet |
| Pairwise composition by split/family | characterization | pairwise sample only | shared decision metadata already exists in sample | local scan of pairwise-sample parquet |
| `y_loss` global summary | characterization | candidate-row scan | not stored in manifest or decision view | likely Wolverine/HPC job |
| `y_value` global summary | characterization | candidate-row scan | not stored in manifest or decision view | likely Wolverine/HPC job |
| `y_loss` percentiles by family | characterization | candidate-row scan | requires reading candidate labels | Wolverine/HPC job |
| Joint breakdown family x capacity x horizon | composition appendix | candidate-row scan | not stored as a manifest cube | Wolverine/HPC job |
| Candidate feature summary statistics | baseline appendix | candidate-row scan | requires reading candidate columns | Wolverine/HPC job |

## Immediate low-cost statistics to extract first

These can be pulled now without heavy dataset rebuilds:

1. manifest-backed scale and composition tables,
2. decision-view candidate-count statistics,
3. decision-view tie and regret summaries,
4. pairwise-sample label-balance summaries.

These are already available in the repository and do not justify another local extraction pass for planning purposes.

## Defer-until-approved or Wolverine-side jobs

- one candidate-row summary pass that emits both `y_loss` and `y_value` global summaries,
- per-family candidate-label percentiles,
- any large joint cube over family, capacity, horizon, and split,
- feature-summary scans across all candidate rows.

## Minimum missing characterization outputs still worth generating

| Output | Supports paper section | Exact input artifact | Exact expected output files | Run site | Full candidate-row scan | Estimated resources | Must wait for source/finalizer completion? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Candidate-row `y_loss` summary | 8 Empirical Characterization | `release/lafc-evict-v0.1-open-current-contract-preserved/data/candidate_rows/` | `paper/sigmod2027/results/candidate_label_stats/y_loss_summary.json`, `paper/sigmod2027/results/candidate_label_stats/y_loss_summary.csv` | Wolverine | yes | `16` CPU, `64G` RAM, `2-4` hours | yes |
| Candidate-row `y_value` summary | 8 Empirical Characterization | `release/lafc-evict-v0.1-open-current-contract-preserved/data/candidate_rows/` | `paper/sigmod2027/results/candidate_label_stats/y_value_summary.json`, `paper/sigmod2027/results/candidate_label_stats/y_value_summary.csv` | Wolverine | yes | same pass as `y_loss` if combined | yes |

## Notes

- Manifest-backed numbers are already suitable for the manuscript if labeled clearly as metadata-backed.
- Decision-view and pairwise-sample statistics are much cheaper than full candidate-row scans and should be prioritized for the next extraction pass.
- Candidate-row scans should be treated as explicit Wolverine jobs only after the current source/finalizer work completes.
- Do not run candidate-row label-distribution scans locally against the preserved release.
