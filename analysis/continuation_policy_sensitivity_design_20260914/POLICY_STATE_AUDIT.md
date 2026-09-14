# Policy-State Audit: Can an Alternative Continuation Be Well Defined?

This is the load-bearing question for the whole design: substituting a
continuation policy after an LRU-generated prefix is only scientifically
meaningful if that policy's required state is actually recoverable from
that prefix, not invented.

## Exact current generator semantics (verified from source, not memory)

Canonical LAFC-Evict candidate labels are produced in the **secondary
repository** (`/home/soroush/projects/augmented-caching/repo`, branch
`chore/repository-polish` / `main`), by:

- `src/lafc/evict_value_wulver_v1.py::iter_candidate_rows()` (the
  production dataset builder, invoked by
  `scripts/experiments/canonical/build_evict_value_dataset_wulver_v1.py`)
- calling `src/lafc/evict_value_dataset_v1.py::_simulate_lru_misses()` as
  the continuation simulator.

The `lafc-evict-dataset` repository (this repository) is a **downstream
consumer only** — `src/lafc_evict_dataset/views.py::build_decision_view()`
aggregates already-generated `candidate_rows.parquet` into `decision_view`
(computing `tie_count`/`optimal_candidate_count`, currently defined
identically as `len(optimal)` where `optimal = group[regret == 0]`); it
contains no cache simulation of its own. `release/` (the canonical
277,995,072-row candidate table) is `.gitignore`d and is **not present in
this local checkout** — this design was produced from the generator source
code and the already-frozen offline summary statistics, not from row-level
inspection of the canonical parquet.

Confirmed generator mechanics:

```python
# per decision (t, capacity), per candidate:
after = [p for p in candidates if p != candidate] + [pid]   # forced eviction + unconditional admission of the requesting page
for h in cfg.horizons:                                       # horizons = (4, 8, 16) in the "heavy" canonical runbook
    fut_h = future[t+1 : t+1+h]                              # H FUTURE REQUESTS, not misses/decisions
    y_loss = float(_simulate_lru_misses(after, fut_h, capacity=capacity))
    y_value = -y_loss                                         # exact, no rescaling
```

- `_simulate_lru_misses` is a **bespoke inline** `collections.OrderedDict`
  LRU replay, decoupled from the reusable `LRUPolicy` class used elsewhere
  in the simulator (`src/lafc/policies/lru.py`) — two independently
  written "LRU" implementations exist in this codebase.
- Cache state at the decision point is **exactly one thing**: a strict
  recency-ordered resident set (the `OrderedDict`). Auxiliary structures
  (`bucket_by_page`, `conf_by_page`, bounded 64-length request/hit
  history `deque`s) exist **only for ML feature computation**, never for
  eviction mechanics.
- Admission is unconditional; objects are unit-sized (capacity compared by
  `len(order)`, not the `Page.weight` field that exists elsewhere in the
  codebase for weighted policies but is unused here).
- Ties are represented only in the derived `decision_view`
  (`tie_count`/`optimal_candidate_count`), not in the raw candidate rows.

## Classification, per policy

| Policy | Required state | Recoverable from the LRU prefix? | Classification |
|---|---|---|---|
| **LRU** (current) | Strict recency order | Is exactly what the prefix already is | **A — WELL_DEFINED_FROM_PREFIX** (trivially; this is the status quo) |
| **MRU** | "Which resident item was referenced most recently" | **Yes, exactly.** This is the *same* recency-ordered structure the generator already maintains for its own LRU eviction (`order`, an `OrderedDict`); MRU only needs to read from the opposite end (`next(reversed(order))`) instead of the front (`next(iter(order))`). No new state, no new tracking, no assumption. | **A — WELL_DEFINED_FROM_PREFIX** |
| **random** | None beyond the resident set (memoryless w.r.t. history) | Yes, trivially — needs only `list(order.keys())` and a seed. Stochastic consequence: candidate losses under random continuation are themselves random variables, requiring a seed/aggregation design (see DESIGN.md). | **A — WELL_DEFINED_FROM_PREFIX** (deterministic per seed; expectation requires averaging) |
| **SIEVE** | A per-resident **visited bit** and a **hand pointer**, both accumulated over the policy's own operating history | **No.** An LRU-generated prefix never sets or tracks a visited bit or a hand position for any resident item — these are SIEVE-specific state that only exists if SIEVE itself has been running. Substituting SIEVE here requires an arbitrary cold-start assumption (all visited bits `False`, hand `None`). Given the horizon is only 4-16 requests, a cold-started SIEVE's *first* eviction within that window is mechanically identical to FIFO (evict the oldest unvisited resident, which is everyone, so it picks the recency-order head exactly like `_choose_victim`'s existing `"fifo"` branch) — meaning a naive SIEVE substitution here would not exercise SIEVE's actual distinguishing mechanism (the second-chance re-admission logic) within such a short window anyway, on top of resting on an assumption with no principled justification. | **C — NOT_WELL_DEFINED_FOR_COUNTERFACTUAL_SUBSTITUTION** (excluded from the primary comparison; see DESIGN.md for why it is not chosen "merely because it was used in Tier 1") |
| **FIFO** (mentioned for completeness; already implemented in `evict_value_v2_rollout.py`) | Insertion order only, no reorder-on-hit | Yes, exactly — same `order` structure, just skip the `move_to_end` on hit. | **A — WELL_DEFINED_FROM_PREFIX** (not selected as primary; see DESIGN.md, kept as a documented cheap secondary option since it is already coded) |
| **blind_oracle** (Belady-style; already implemented) | Full visibility of the finite-horizon future | Not "recovered from the prefix" in the same sense — it is a look-ahead oracle, well-defined by construction over the already-fixed horizon window, not a deployable continuation policy | **A, but a different kind of well-definedness** (a diagnostic upper bound, not a "reasonable alternative continuation" in the reviewer's sense; excluded from primary set for that reason, not a state problem) |

## Conclusion

Two continuation alternatives are genuinely, cheaply, and defensibly
well-defined from the existing LRU-generated prefix with **zero new
tracked state**: **MRU** and **random**. SIEVE is excluded from the
primary comparison not for convenience but because its required state
structurally does not exist in this generator's prefix and any
substitution would rest on an assumption (cold visited bits) that a short
horizon would render nearly meaningless anyway. This conclusion was
reached by reading the actual generator code, not by assuming Tier 1's
policy roster should carry over.
