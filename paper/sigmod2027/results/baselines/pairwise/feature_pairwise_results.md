# Feature-Based Pairwise Baseline Results

- input file: `paper/sigmod2027/results/baselines/pairwise/augmented_pairwise_sample.parquet`
- evaluation mode: non-tie rows only (121,738 of 1,000,000 rows)
- tie rows skipped: 878,262
- full real-release validation: passed

## Overall results

| Baseline | Rows | Accuracy | Balanced accuracy | Log loss | Recall (a_better) | Recall (b_better) | Macro F1 | AUROC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `random_non_tie` | 121,738 | 0.5006 | 0.5006 | 0.6931 | 0.5015 | 0.4998 | 0.5006 | 0.5000 |
| `majority_non_tie` | 121,738 | 0.5016 | 0.5000 | 0.6931 | 0.0000 | 1.0000 |  | 0.5000 |
| `lru_score_pairwise` | 121,738 | 0.9225 | 0.9225 | 0.2426 | 0.9222 | 0.9229 | 0.9225 | 0.9654 |
| `predictor_score_pairwise` | 121,738 | 0.5016 | 0.5000 | 0.6931 | 0.0000 | 1.0000 |  | 0.5000 |
| `linear_score_pairwise` | 121,738 | 0.9490 | 0.9490 | 0.1161 | 0.9460 | 0.9519 | 0.9490 | 0.9913 |
| `logistic_regression_pairwise` | 121,738 | 0.9660 | 0.9660 | 0.0824 | 0.9659 | 0.9661 | 0.9660 | 0.9950 |

## Split-level results

| Baseline | Split | Rows | Positive rate | Accuracy | Balanced accuracy | Log loss | Recall (a_better) | Recall (b_better) | Macro F1 | AUROC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `random_non_tie` | `train` | 75,311 | 0.4970 | 0.5030 | 0.5030 | 0.6931 | 0.5055 | 0.5006 | 0.5030 | 0.5000 |
| `random_non_tie` | `val` | 44,216 | 0.5000 | 0.4971 | 0.4971 | 0.6931 | 0.4954 | 0.4988 | 0.4971 | 0.5000 |
| `random_non_tie` | `test` | 2,211 | 0.5147 | 0.4903 | 0.4903 | 0.6931 | 0.4886 | 0.4921 | 0.4902 | 0.5000 |
| `majority_non_tie` | `train` | 75,311 | 0.4970 | 0.5030 | 0.5000 | 0.6931 | 0.0000 | 1.0000 |  | 0.5000 |
| `majority_non_tie` | `val` | 44,216 | 0.5000 | 0.5000 | 0.5000 | 0.6932 | 0.0000 | 1.0000 |  | 0.5000 |
| `majority_non_tie` | `test` | 2,211 | 0.5147 | 0.4853 | 0.5000 | 0.6933 | 0.0000 | 1.0000 |  | 0.5000 |
| `lru_score_pairwise` | `train` | 75,311 | 0.4970 | 0.9141 | 0.9141 | 0.2642 | 0.9142 | 0.9141 | 0.9141 | 0.9587 |
| `lru_score_pairwise` | `val` | 44,216 | 0.5000 | 0.9508 | 0.9508 | 0.1715 | 0.9505 | 0.9512 | 0.9508 | 0.9861 |
| `lru_score_pairwise` | `test` | 2,211 | 0.5147 | 0.6427 | 0.6429 | 0.9285 | 0.6344 | 0.6514 | 0.6427 | 0.6856 |
| `predictor_score_pairwise` | `train` | 75,311 | 0.4970 | 0.5030 | 0.5000 | 0.6931 | 0.0000 | 1.0000 |  | 0.5000 |
| `predictor_score_pairwise` | `val` | 44,216 | 0.5000 | 0.5000 | 0.5000 | 0.6932 | 0.0000 | 1.0000 |  | 0.5000 |
| `predictor_score_pairwise` | `test` | 2,211 | 0.5147 | 0.4853 | 0.5000 | 0.6933 | 0.0000 | 1.0000 |  | 0.5000 |
| `linear_score_pairwise` | `train` | 75,311 | 0.4970 | 0.9430 | 0.9430 | 0.1273 | 0.9406 | 0.9453 | 0.9430 | 0.9896 |
| `linear_score_pairwise` | `val` | 44,216 | 0.5000 | 0.9735 | 0.9735 | 0.0753 | 0.9715 | 0.9755 | 0.9735 | 0.9957 |
| `linear_score_pairwise` | `test` | 2,211 | 0.5147 | 0.6621 | 0.6632 | 0.5512 | 0.6283 | 0.6980 | 0.6621 | 0.7563 |
| `logistic_regression_pairwise` | `train` | 75,311 | 0.4970 | 0.9598 | 0.9598 | 0.0942 | 0.9601 | 0.9595 | 0.9598 | 0.9938 |
| `logistic_regression_pairwise` | `val` | 44,216 | 0.5000 | 0.9896 | 0.9896 | 0.0391 | 0.9892 | 0.9899 | 0.9896 | 0.9977 |
| `logistic_regression_pairwise` | `test` | 2,211 | 0.5147 | 0.7078 | 0.7079 | 0.5494 | 0.7056 | 0.7102 | 0.7077 | 0.7816 |

## Notes on class imbalance

- train split positive rate (label_a_better=1) is 0.4970.
- val split positive rate (label_a_better=1) is 0.5000.
- test split positive rate (label_a_better=1) is 0.5147.

## Limitations

- Only the capped shipped pairwise sample is evaluated; the full quadratic pairwise view is never generated.
- Logistic fits use a small custom Newton-Raphson implementation with L2 regularization, not scikit-learn.
