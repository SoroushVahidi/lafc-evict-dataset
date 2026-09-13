# Validity Gates And Stop Rules

No production experiment should start until these gates are checked.

## Global Gates

- Confirm the LAFC-Evict production branch/worktree is clean except intended output files.
- Confirm frozen pilot source commit `983d7d0204645660e7b683ed30298677c2b42ccf` remains accessible.
- Confirm Augmented-caching source path and processed traces exist.
- Record Augmented-caching commit and dirty status before execution.
- Record SHA256 hashes for every processed trace used.
- Confirm every processed trace has exactly 50,000 requests before any policy metrics are accepted.
- Confirm scored windows are derived from encoded split provenance and match the released decision-view chunk/split assignments.
- Confirm every policy in a family/capacity cell uses identical scored windows.
- Confirm unscored requests affect cache state but do not enter scored metrics.
- Confirm hits + misses = scored_requests for every output row.
- Confirm no NaN, infinite, missing, or negative metric values.
- Confirm no premature truncation: every run must process the full 50,000-request trace.
- Confirm result files include command/provenance records before committing.

## Family Gates

| Family | Gate |
| --- | --- |
| cloudphysics | Use test windows only for primary claims; stop if chunks 4,5 are unavailable or trace length differs. |
| metacdn | Do not call results test-window evidence; learned policy is blocked for production claims. |
| metakv | Use test chunk 0 only with explicit no-leading-warmup caveat; stop if the design silently substitutes validation chunks. |
| twemcache | Use test chunks 8,10 only; compare against frozen pilot cap32 where applicable. |
| wiki2018 | Include as negative/control case; stop if offline all-tie status is not shown next to closed-loop results. |

## Learned-Policy Gates

Block evict_value_v1 for a cell if any of the following hold:

- No nonempty test chunks exist for that family.
- The scored interval overlaps validation chunks used for model selection.
- Model artifact hash differs from `0c9e8a48066f8bb80bfab31b023c9785ca5b955f408d50c18008dbcc314ea61b`.
- Model load fails.
- Feature-column schema differs from the artifact's expected feature list.
- The run falls back to the lightweight scorer instead of artifact mode.
- scikit-learn version warnings are not recorded in provenance.
- Any scored row has NaN or invalid diagnostics.

Allowed learned-policy classifications:

- `LEARNED_POLICY_SAFE_TEST`: nonempty test chunks and split isolation are documented.
- `VALIDATION_ONLY`: only validation-window evidence is available; do not use for learned-policy production claims.
- `BLOCKED_LEAKAGE_RISK`: validation/model-selection overlap or missing test isolation prevents interpretation.
- `UNKNOWN_PROVENANCE`: model/data provenance cannot establish isolation.

Current classification:

| Family | Classification |
| --- | --- |
| cloudphysics | LEARNED_POLICY_SAFE_TEST |
| metacdn | BLOCKED_LEAKAGE_RISK |
| metakv | LEARNED_POLICY_SAFE_TEST |
| twemcache | LEARNED_POLICY_SAFE_TEST |
| wiki2018 | LEARNED_POLICY_SAFE_TEST |

## Analysis Stop Rules

Stop and report before interpreting results if:

- a scored interval is empty unexpectedly
- any family has inconsistent scored request counts across policies
- any policy processes fewer than 50,000 total requests
- random seed set differs from 0..19
- duplicate deterministic checks fail
- the production script changes simulator or policy source code
- MetaCDN is mislabeled as test-window evidence
- any result text calls these windows an unseen trace
- a learned-policy run is attempted before Tier 1 outputs are validated and explicitly approved
