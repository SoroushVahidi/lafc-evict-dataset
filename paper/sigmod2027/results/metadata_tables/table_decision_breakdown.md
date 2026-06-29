# table_decision_breakdown

All counts in this file come from the decision view only. No candidate-row parquet contents were read.

## By trace family

| trace_family | decision_rows |
| --- | --- |
| wiki2018 | 598,560 |
| cloudphysics | 576,219 |
| metakv | 454,053 |
| twemcache | 397,494 |
| metacdn | 336,960 |

## By capacity

| capacity | decision_rows |
| --- | --- |
| 32 | 613,314 |
| 64 | 599,172 |
| 128 | 582,678 |
| 256 | 568,122 |

## By horizon

| horizon | decision_rows |
| --- | --- |
| 4 | 787,762 |
| 8 | 787,762 |
| 16 | 787,762 |

## By split

| split | decision_rows |
| --- | --- |
| test | 242,418 |
| train | 1,746,882 |
| val | 373,986 |

## By trace family and split

| trace_family | split | decision_rows |
| --- | --- | --- |
| cloudphysics | test | 94,584 |
| cloudphysics | train | 435,801 |
| cloudphysics | val | 45,834 |
| metacdn | train | 201,672 |
| metacdn | val | 135,288 |
| metakv | test | 33,945 |
| metakv | train | 306,765 |
| metakv | val | 113,343 |
| twemcache | test | 64,737 |
| twemcache | train | 302,388 |
| twemcache | val | 30,369 |
| wiki2018 | test | 49,152 |
| wiki2018 | train | 500,256 |
| wiki2018 | val | 49,152 |
