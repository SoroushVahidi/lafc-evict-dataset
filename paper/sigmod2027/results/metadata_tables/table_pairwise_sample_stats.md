# table_pairwise_sample_stats

All statistics in this file come from the shipped pairwise sample only.

## Summary

| statistic | value | notes |
| --- | --- | --- |
| pairwise rows | 1,000,000 | pairwise-sample-backed |
| unique decisions represented | 118,635 | pairwise-sample-backed |
| label_a_better rows | 6,134 | pairwise-sample-backed |
| label_b_better rows | 113,898 | pairwise-sample-backed |
| is_tie rows | 879,968 | pairwise-sample-backed |

## By split

| split | pairwise_rows |
| --- | --- |
| test | 102,024 |
| train | 737,896 |
| val | 160,080 |

## By trace family

| trace_family | pairwise_rows |
| --- | --- |
| wiki2018 | 250,872 |
| cloudphysics | 245,336 |
| metakv | 190,584 |
| twemcache | 169,064 |
| metacdn | 144,144 |

## Label summary

| label_a_better_rows | label_b_better_rows | is_tie_rows |
| --- | --- | --- |
| 6,134 | 113,898 | 879,968 |
