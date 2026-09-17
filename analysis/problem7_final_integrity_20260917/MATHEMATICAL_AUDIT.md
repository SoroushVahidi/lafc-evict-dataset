# Problem 7 Phase 6: mathematical / definition audit

## Equations audited

### `sections/04_label_generation.tex` (the core label definition)

1. `L_{t,H}^pi(c) = #{tau in (t, t+H] : r_tau misses in the induced trajectory}`
   - A cardinality of a set of misses -> nonnegative by construction. **NONE.**
   - Domain: c ranges over C_t = S_t^- (resident objects at eviction time);
     |C_t| = capacity. Correctly stated as counted in objects, with an
     explicit disclaimer that object sizes are not modeled. **NONE.**
2. `y_value = -y_loss` -- consistent sign-flip, and the text is explicit that
   only one of the two is ever used as "the" statistic in any given sentence
   (checked: no sentence in the manuscript reports the same number under both
   names). **NONE.**
3. `C_t^* = argmin_{c in C_t} L_{t,H}^pi(c)` -- correct: with a loss/cost
   framing, the optimal set is the argmin, not argmax. **NONE.**
4. `Delta_{t,H}^pi(c) = L_{t,H}^pi(c) - min_{c'} L_{t,H}^pi(c')` -- nonnegative
   by construction (loss minus its own minimum), zero exactly for members of
   `C_t^*`. This is the quantity later called "regret." **NONE.**

### Random-optimal probability / expected random regret (defined in prose,
Section 8, not as a displayed equation)

- "a uniform-random guess already lands in the optimal set X% of the time"
  is consistent with `random_optimal_probability = |C_t^*| / |C_t|` averaged
  (decision-weighted) over decisions -- reproduced exactly from
  `headline_random_optimal_decomposition.csv` (Phase 5). **NONE.**
- "expected regret" is consistent with the decision-weighted mean of
  `Delta_{t,H}^pi(c)` over a uniform draw of `c in C_t`, i.e.
  `mean_c Delta(c)`, which is `>= 0` and `= 0` exactly for all-tied decisions
  (`|C_t^*| = |C_t|`) -- matches the manuscript's own statement that the
  all-tied group contributes zero regret. **NONE.**

### Monotonicity claim (Problem 4 / abstract / Section 8)

"this separation strengthens, monotonically for every decision tested, as
the horizon grows from 16 to 128" is a literal per-decision claim, not a
population-average claim. Verified against
`matched_monotonicity_micro_summary.csv`:
`adjacent_all_nondecreasing_fraction = 1.0` over all 787,762 matched
decisions -- the claim is exactly as strong as, and no stronger than, what
the data supports (informativeness is monotone per decision; this does not
imply ties are eliminated, and the manuscript does not claim that). **NONE.**

### Correlation claims (Section 8c/8d)

All correlation values checked are Pearson correlations over `n=10`
family x capacity cells, correctly labeled as `n=10` and "exploratory"
throughout. One issue found and fixed (see below).

## Issues found

| # | Location | Issue | Severity | Resolution |
|---|---|---|---|---|
| 1 | `sections/08d_mechanistic.tex:19-20` (pre-fix) | `r=-0.83` (hit-rate vs. discriminativeness) reported with the same confidence as `r=0.90` (hit-rate vs. closed-loop gap), but independent LOFO recomputation this pass shows the two are not equally robust: the `r=-0.83` pairing drops to `r=-0.69` when metacdn is excluded and its exact family-permutation `p=0.117` fails a nominal 0.05 threshold, while the `r=0.90` pairing stays strongly positive (`0.83`-`0.98`) under every exclusion. This is a case of wording (implicit equal confidence) stronger than the evidence, not an arithmetic error -- the `r=-0.83`/`r=0.90` values themselves are correct. | MODERATE | Fixed: added an explicit LOFO/permutation caveat sentence distinguishing the two pairings; new verification artifact `outputs/correlation_robustness_recheck.json`. |

No FATAL or unresolved MAJOR mathematical issues were found. No equation
confuses physical decision / decision-horizon instance / candidate row /
pairwise row; each is used consistently with its schema definition in
Section 5.
