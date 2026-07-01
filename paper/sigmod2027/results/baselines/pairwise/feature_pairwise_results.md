# Feature-Based Pairwise Baseline Results

- input file: `paper/sigmod2027/results/baselines/pairwise/augmented_pairwise_sample.parquet`
- evaluation mode: non-tie rows only (120,032 of 1,000,000 rows)
- tie rows skipped: 879,968
- full real-release validation: passed

## Overall results

| Baseline | Rows | Accuracy | Log loss |
| --- | --- | --- | --- |
| `random_non_tie` | 120,032 | 0.4993 | 0.6931 |
| `majority_non_tie` | 120,032 | 0.9489 | 0.2023 |
| `lru_score_pairwise` | 120,032 | 0.9596 | 0.1326 |
| `predictor_score_pairwise` | 120,032 | 0.9489 | 0.2023 |
| `linear_score_pairwise` | 120,032 | 0.9530 | 0.1072 |
| `logistic_regression_pairwise` | 120,032 | 0.9676 | 0.0774 |

## Split-level results

| Baseline | Split | Rows | Positive rate | Accuracy | Log loss |
| --- | --- | --- | --- | --- | --- |
| `random_non_tie` | `train` | 74,141 | 0.0590 | 0.4992 | 0.6931 |
| `random_non_tie` | `val` | 44,080 | 0.0225 | 0.5002 | 0.6931 |
| `random_non_tie` | `test` | 1,811 | 0.4219 | 0.4815 | 0.6931 |
| `majority_non_tie` | `train` | 74,141 | 0.0590 | 0.9410 | 0.2243 |
| `majority_non_tie` | `val` | 44,080 | 0.0225 | 0.9775 | 0.1232 |
| `majority_non_tie` | `test` | 1,811 | 0.4219 | 0.5781 | 1.2288 |
| `lru_score_pairwise` | `train` | 74,141 | 0.0590 | 0.9521 | 0.1519 |
| `lru_score_pairwise` | `val` | 44,080 | 0.0225 | 0.9843 | 0.0710 |
| `lru_score_pairwise` | `test` | 1,811 | 0.4219 | 0.6637 | 0.8425 |
| `predictor_score_pairwise` | `train` | 74,141 | 0.0590 | 0.9410 | 0.2243 |
| `predictor_score_pairwise` | `val` | 44,080 | 0.0225 | 0.9775 | 0.1232 |
| `predictor_score_pairwise` | `test` | 1,811 | 0.4219 | 0.5781 | 1.2288 |
| `linear_score_pairwise` | `train` | 74,141 | 0.0590 | 0.9447 | 0.1194 |
| `linear_score_pairwise` | `val` | 44,080 | 0.0225 | 0.9823 | 0.0654 |
| `linear_score_pairwise` | `test` | 1,811 | 0.4219 | 0.5837 | 0.6208 |
| `logistic_regression_pairwise` | `train` | 74,141 | 0.0590 | 0.9607 | 0.0904 |
| `logistic_regression_pairwise` | `val` | 44,080 | 0.0225 | 0.9897 | 0.0373 |
| `logistic_regression_pairwise` | `test` | 1,811 | 0.4219 | 0.7151 | 0.5191 |

## Notes on class imbalance

- train split positive rate (label_a_better=1) is 0.0590.
- val split positive rate (label_a_better=1) is 0.0225.
- test split positive rate (label_a_better=1) is 0.4219.
- Positive rate varies substantially across splits, consistent with the tie-heavy, imbalanced nature of the shipped pairwise sample; headline accuracy numbers should always be read alongside log loss and split-level breakdowns.

## Limitations

- Only the capped shipped pairwise sample is evaluated; the full quadratic pairwise view is never generated.
- Logistic fits use a small custom Newton-Raphson implementation with L2 regularization, not scikit-learn.
