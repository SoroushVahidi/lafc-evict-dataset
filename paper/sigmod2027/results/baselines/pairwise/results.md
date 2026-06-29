# Light Pairwise Baseline Results

These results come only from the shipped pairwise sample:

- input file: `release/lafc-evict-v0.1-open-current-contract-preserved/data/pairwise_sample/pairwise_sample.parquet`
- evaluation mode: non-tie rows only
- full real-release validation: pending
- candidate feature baselines: pending feature join or augmented pairwise export

## Commands

```bash
python scripts/sigmod2027/run_pairwise_baseline.py --mode run-light --baseline majority_non_tie --release-root release/lafc-evict-v0.1-open-current-contract-preserved --output-dir paper/sigmod2027/results/baselines/pairwise
python scripts/sigmod2027/run_pairwise_baseline.py --mode run-light --baseline random_non_tie --seed 7 --release-root release/lafc-evict-v0.1-open-current-contract-preserved --output-dir paper/sigmod2027/results/baselines/pairwise
```

## Evaluation population

- total shipped pairwise rows: `1,000,000`
- tie rows skipped: `879,968` (`87.9968%`)
- non-tie rows evaluated: `120,032` (`12.0032%`)

Warning:
The shipped pairwise sample is highly tie-heavy. These results should be interpreted as sanity checks on the non-tie subset, not as headline learned-baseline results.

## Overall results

| Baseline | Evaluated rows | Accuracy | Log loss | Interpretation |
| --- | --- | --- | --- | --- |
| `majority_non_tie` | 120,032 | 0.9489 | 0.2023 | Strong because train and validation non-tie labels are highly imbalanced toward `label_a_better = 0` |
| `random_non_tie` | 120,032 | 0.4980 | 0.6931 | Behaves as expected for a random non-feature baseline |

## Split-level results

| Baseline | Split | Rows | Positive rate (`label_a_better`) | Accuracy | Log loss |
| --- | --- | --- | --- | --- | --- |
| `majority_non_tie` | `train` | 74,141 | 0.0590 | 0.9410 | 0.2243 |
| `majority_non_tie` | `val` | 44,080 | 0.0225 | 0.9775 | 0.1232 |
| `majority_non_tie` | `test` | 1,811 | 0.4219 | 0.5781 | 1.2288 |
| `random_non_tie` | `train` | 74,141 | 0.0590 | 0.4961 | 0.6931 |
| `random_non_tie` | `val` | 44,080 | 0.0225 | 0.5014 | 0.6931 |
| `random_non_tie` | `test` | 1,811 | 0.4219 | 0.4964 | 0.6931 |

## Takeaways

- A trivial majority classifier looks strong on train and validation because the non-tie subset is extremely imbalanced.
- Test accuracy for the majority baseline falls to `0.5781`, which shows that the class skew is materially different in the test non-tie subset.
- Feature-based pairwise baselines remain pending because the shipped pairwise sample omits candidate-side predictor and LRU features.
