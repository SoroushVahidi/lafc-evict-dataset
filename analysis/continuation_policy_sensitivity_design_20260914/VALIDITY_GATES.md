# Validity Gates for the Future Continuation-Policy Sensitivity Experiment

No experiment may launch until every gate below is defined in executable
form; this document specifies them, it does not implement or run them.

## Blocking gate (checked first, before anything else)

- **LRU reproduction gate** (see `DESIGN.md` Section 11): the extended
  `_choose_victim(..., policy="lru")` code path must reproduce the
  canonical generator's `_simulate_lru_misses` output exactly on an audit
  sample, or via the aggregate cross-check against
  `phase8_lru_mru_stratified.csv` described there. **If this fails, stop —
  do not proceed to MRU/random comparisons.**

## Provenance gates

- Source trace SHA256 for every family matches the values already recorded
  in the Tier-1 harness (`fedb3d31...`, `7301f02e...`, `4c229e84...`,
  `62df2706...`, `3813084b...` for cloudphysics/metacdn/metakv/twemcache/
  wiki2018 respectively) — reused, not re-derived, from already-verified
  provenance.
- Exact sampled decision IDs (`trace, capacity, request_index`) and the
  sampling RNG seed are recorded and committed *before* any
  alternative-continuation computation runs on them.
- Secondary-repo commit/branch and dirty-status recorded at run time,
  exactly as the Tier-1 harness's `simulator_provenance()` already does —
  reuse that pattern rather than inventing a new one.

## Mechanics gates

- Forced-candidate state (the `after` list) is identical in composition
  across every continuation-policy comparison for the same decision — only
  the continuation rule differs, nothing else about the forced state.
- Horizon is identical across compared continuations for the same decision.
- No candidate is silently omitted from a decision's candidate set between
  continuation-policy runs.
- No accidental modification of the canonical prefix-generation logic
  (which must remain hardcoded LRU, exactly as released) — verified by a
  diff-based check that `evict_value_wulver_v1.py` is untouched.

## Numerical gates

- No NaN, infinite, or negative loss/regret values anywhere in the output.
- `hits + misses` (equivalently, requests accounted for) is internally
  consistent with the horizon length for every rollout.
- Deterministic continuations (LRU, MRU) reproduce identical output on a
  repeated run of the same decision.
- Random continuation, same seed, reproduces identical output on a
  repeated run (seed reproducibility).

## Execution/output gates

- No run directory is silently overwritten (reuse the Tier-1 harness's
  immutable-run-directory + explicit-resume pattern).
- Every output row is unambiguously `complete` or `failed` — no
  ambiguous/partial status silently treated as complete (reuse the
  Tier-1 harness's JSONL append-only + status-field pattern).
- Full provenance (Section above) is written before the run state is
  reported as valid.
- Exact SHA256 of every output file is recorded in a manifest, following
  the same pattern as `analysis/closed_loop_tier1_evidence_20260914/EVIDENCE_MANIFEST.json`.

## Statistical-design gates (checked against DESIGN.md, not invented ad hoc)

- Sampling stratification variables are computed from LRU-only information
  (verified by inspecting the sampling code for any read of an
  alternative-continuation output before sampling is finalized).
- The pre-registered ROBUST/CONDITIONALLY_ROBUST/SENSITIVE/INCONCLUSIVE
  thresholds (`DESIGN.md` Section 3) are not edited after data collection
  begins — a hash of the thresholds section should be recorded at design-
  freeze time for auditability.
- The 4 stratified reporting views (`DESIGN.md` Section 7) are all
  produced for every primary metric — a report presenting only the
  pooled/unstratified number is treated as incomplete, not as a valid
  result.

## Correctness pilot (see `DESIGN.md` Section 10 for cells/decision counts)

Purpose: verify semantics, reproduce LRU labels, detect that MRU/random
substitution runs without error, validate the seed-count rule, and get a
real timing number — explicitly **not** for scientific claims. The pilot's
own summary statistics must be labeled `PILOT — NOT A SCIENTIFIC RESULT` in
any output it produces, to prevent accidental promotion.
