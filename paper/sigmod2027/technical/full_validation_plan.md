# Full Validation Plan

## Status

This command is intentionally recorded here for later execution only. It has not been run as part of the current paper-packaging work.

## Deferred command

```bash
python scripts/validate_real_release.py \
  --release-root release/lafc-evict-v0.1-open-current-contract-preserved
```

## Why deferred

- The user explicitly prohibited running full real-release validation in the current phase.
- The manuscript should therefore describe full validation as pending.
- No release or paper claim should state that the preserved open release has fully passed end-to-end validation until this command completes successfully.

## When to run

- only after explicit approval,
- after manuscript wording is ready to absorb either a pass or a failure,
- before any final public release or camera-ready artifact claims.
