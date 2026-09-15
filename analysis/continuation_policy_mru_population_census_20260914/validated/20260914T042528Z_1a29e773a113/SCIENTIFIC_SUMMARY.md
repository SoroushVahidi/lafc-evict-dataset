# Full-Population MRU Continuation Census Scientific Summary

FULL_CENSUS_VALID: true
Robustness classification: ROBUST
Set C median Jaccard: 1.0
Set C mean CCR: 0.000638212890510199
Set C fraction CCR <= 1: 1.0
Set C strict reversal fraction: 5.378211541952576e-07

Wiki2018 is reported separately and is not used alone to support robustness; the excluding-wiki2018 and informative-strata summaries remain robust.

Worst Set-C cell by mean Jaccard: {'analysis_set': 'C_discriminative_under_LRU', 'family': 'cloudphysics', 'capacity': 32, 'horizon': 16, 'decisions': 6423, 'decision_horizon_units': 6423, 'jaccard_mean': 0.9804326226680316, 'jaccard_median': 1.0, 'jaccard_eq_1_fraction': 0.8449322746380196, 'jaccard_below_0_8_fraction': 0.036898645492760396, 'strict_reversal_count': 110, 'strict_reversal_fraction': 3.452813226660238e-05, 'ccr_mean': 0.0038991050730797167, 'ccr_median': 0.0, 'ccr_p95': 0.03225806451612903, 'ccr_max': 0.1935483870967742, 'nonzero_regret_fraction': 0.09746224505682703, 'fraction_lru_optimal_still_mru_optimal': 0.9961008949269202, 'both_tied_fraction': 0.0}

Safe manuscript claim:

In a pre-registered continuation-policy sensitivity study, sampled MRU and random continuations at capacities 32 and 128 were robust under the Set-C criterion; a separate full-population MRU census over capacities 32, 64, 128, and 256 also satisfied the same MRU robustness criterion. These results support stability of the LRU-derived labels for MRU continuation in the evaluated families, capacities, and horizons, while not constituting a full-population random-continuation validation or a guarantee for every possible deployed continuation policy.
