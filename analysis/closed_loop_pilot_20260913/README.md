# LAFC-Evict closed-loop pilot

This directory freezes the completed 2026-09-13 closed-loop cache-policy pilot for LAFC-Evict. The pilot exists to test a reviewer-facing question: whether the offline, candidate-level counterfactual signal in LAFC-Evict corresponds to meaningful differences when policies are actually replayed in closed loop.

The pilot is deliberately small. It evaluates MetaCDN and Twemcache at capacity 32, using LRU, MRU, uniform random with seeds 0..19, SIEVE, and evict_value_v1 only where the learned-policy leakage gate permits it. It is not the final production evaluation.

## Execution Protocol

The script replays each full 50,000-request processed JSONL trace through the existing Augmented-caching closed-loop simulator. Each policy updates its own cache state after its own actions. This is not a replay of the 277M LAFC-Evict candidate table.

Metrics are restricted to predefined scored split windows. Requests outside those windows still affect cache state but do not contribute to scored metrics, so this is not a separate leading warmup protocol. Every policy within a family uses the same scored windows.

MetaCDN is validation-window evidence, not independent test-window evidence. The MetaCDN trace has no test chunks at capacity 32, so evict_value_v1 is blocked there because those validation chunks participated in model selection.

Twemcache is temporally held-out test-window evidence within the same continuous trace. It is not an unseen trace.

## Outputs

Raw result files are preserved without formatting changes:

| File | SHA256 |
| --- | --- |
| `outputs/run_results.csv` | `81bd86d0550f6db2a03836bb899bc3c3026cc210f1f49be981dca317e2725428` |
| `outputs/summary.csv` | `fd5ab07aa565d3af5d198600f527513d8cbc8a95ffeab8a4e1db14219aa76279` |
| `outputs/sanity_checks.json` | `f1abe70549cdf88d5a7b29256c050bc80da06ffd6831a4ce558d65c69f957c11` |
| `outputs/provenance.json` | Generated during freeze; hash recorded in the freeze commit report. |
| `scripts/run_pilot.py` | `4a80279e6b80c05fc8daa4cd06b28efe75c6c89f047e91a4f1a6bddbc47b0e84` |

## Inspecting The Pilot

Read `REPORT.md` for the scientific result, `outputs/summary.csv` for policy-level aggregates, and `outputs/run_results.csv` for per-run rows. `outputs/provenance.json` records repository commits, trace hashes, model provenance, split windows, and reproducibility caveats.

The original command observed for the completed run was:

```sh
python3 analysis/closed_loop_pilot_20260913/scripts/run_pilot.py
```

Reproduction would require the same LAFC-Evict worktree, the Augmented-caching source tree and processed traces, and the evict_value_v1 model artifact listed in `outputs/provenance.json`. No experiment was rerun during this freeze.

## Main Takeaway

The pilot supports using LAFC-Evict as an offline supervision and diagnostic layer that is complementary to closed-loop policy evaluation. For LRU, random, and MRU, the offline ordering agrees with the closed-loop miss ordering in both examined families. The pilot does not show that the learned policy beats LRU, and it does not establish universal prediction from offline metrics to deployed policy quality.
