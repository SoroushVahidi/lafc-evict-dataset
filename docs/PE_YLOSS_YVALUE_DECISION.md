# y_loss / y_value: Audit and Manuscript Recommendation

Status: NOT_PRESENT prior to this task as a standalone decision document
(the redundancy was known — `dataset_card/SCHEMA.md` already documents
`y_value` as "Convenience target equal to `-y_loss`" — but no document
recommended a specific manuscript treatment).

## Reviewer concern

*Why store both `y_loss` and `y_value` if `y_value = -y_loss`?*

## Audit of current schema/API usage

- `src/lafc_evict_dataset/schema.py`: both columns are required, typed
  `float`, part of the same candidate-row contract.
- `dataset_card/SCHEMA.md`: documents `y_loss` as "Finite-horizon
  counterfactual LRU-continuation miss count after forcing this eviction"
  and `y_value` as "Convenience target equal to `-y_loss`" — the schema
  itself already frames `y_value` as derived, not independent.
- `scripts/sigmod2027/run_value_regression_baseline.py`: exposes a
  `--target` CLI flag with `choices=["y_loss", "y_value"]`, defaulting to
  `y_loss`. This is the clearest evidence of intended use: downstream
  regression/ranking code is written generically against "the target
  column" and a caller picks whichever sign convention matches their
  training framework's convention (minimize a cost vs. maximize a value),
  without needing to negate the column themselves.
- No code path in the audited repository treats the two columns as
  carrying different information, using different horizons, or being
  computed by different code paths — both come from the same generation
  step, differing only by sign.

## Assessment

The redundancy is real (they are not independent measurements) but it is
not accidental duplication: it exists to serve two conventions that
coexist in the caching/ML literature without forcing every downstream user
to remember and correctly apply a sign flip:

- **Minimization interfaces**: "loss", "cost", "regret" framings (common
  in optimization/decision-theory presentations, and in this repository's
  own target-discriminativeness terminology — "regret", "miss cost").
- **Maximization interfaces**: "value", "utility", "reward" framings
  (common in value-function/RL-adjacent presentations, and convenient
  when a downstream user wants `argmax` rather than `argmin` for
  best-candidate selection).

## Recommendation: **B — present one as canonical, the other as a documented convenience alias**

- Canonical, primary-exposition quantity: **`y_loss`** (the finite-horizon
  counterfactual miss cost). It is the more directly interpretable
  quantity (a count of extra misses), it is what the schema's own
  description privileges, and it is the CLI default in the existing
  baseline runner.
- `y_value` should be introduced once, explicitly, as `y_value = -y_loss`,
  described as a convenience alias for maximization-style formulations,
  and then the manuscript should use `y_loss` consistently in prose and
  in all reported statistics, switching to `y_value` only where a specific
  baseline or equation is more naturally stated as a maximization (and
  saying so at that point).
- Do not present both as if they might diverge, and do not report the same
  statistic twice under both names (e.g., do not report both a mean
  `y_loss` and a mean `y_value` table — one is the negation of the other
  and doubling the tables adds no information; this is the "duplicating a
  result in both a table and a figure without a reason" failure mode
  named in `PE_FIGURE_TABLE_PLAN.md`, applied to the schema-narrative
  level rather than to figures).

## Explicitly out of scope for this task

**Do not break released schema compatibility.** Both columns remain in the
schema and the public release unchanged; this recommendation governs
manuscript *presentation* only, not the data contract. `--target
y_value` remains a supported, documented convenience option in code; the
manuscript simply should not spend narrative space presenting it as a
second, independent result.
