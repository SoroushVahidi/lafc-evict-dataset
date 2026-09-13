# LAFC-Evict Repository Cleanup Inventory

This inventory records cleanup candidates for a later task. Do not delete
branches, worktrees, or artifacts based on this file without a fresh validation
pass.

## Keep / Active

| Item | Type | Current role |
|---|---|---|
| `master` | branch | Historical/default publication base at `fbbeedb`; keep as the public-repository baseline, but do not treat as latest scientific state. |
| `analysis/sigmod-target-discriminativeness-20260913` | branch | Target-discriminativeness audit and pairwise provenance repair line, HEAD `76d562f`. |
| `experiment/closed-loop-pilot-20260913` | branch | Frozen closed-loop pilot evidence, HEAD `983d7d0`. |
| `experiment/closed-loop-production-design-20260913` | branch | Designed production closed-loop matrix, HEAD `adc7c64`. |
| `polish/final-handoff-20260914` | branch | Canonical final-polish handoff branch created from `adc7c64`. |
| `manuscript/performance-evaluation-template-20260913` | branch | Separate Elsevier Performance Evaluation manuscript branch, HEAD `471b3c4`. |
| `release/aws-open-data-v0.3-freeze-20260912` | branch | Preserved AWS release documentation improvements, synced with remote at `4d63b01`. |

## Keep / Frozen Provenance

| Item | Type | Current role |
|---|---|---|
| `integration/closed-loop-feasibility-20260913` | branch | Integration step between target audit and pilot, HEAD `a85fe5e`. |
| `sigmod-final-polish-text-fixes` | branch | Historical SIGMOD text-polish branch; remote exists. |
| `sigmod-integrate-corrected-query3-results` | branch | Historical SIGMOD result-integration branch; remote exists. |
| `sigmod-manuscript-integrate-feature-pairwise` | branch | Historical anonymous-submission/manuscript branch. |
| `sigmod-related-work-pass-20260629` | branch | Historical related-work pass; remote exists. |
| `wulver-feature-pairwise-baseline-20260701` | remote branch | Historical feature-based pairwise baseline evidence. |
| `wulver-fix-pairwise-bestcandidate-20260701` | remote branch | Historical pairwise orientation and baseline reconciliation evidence. |

## Cleanup Candidate, But Do Not Delete Yet

These were identified as likely superseded by later preserved lineage. Confirm
no unique needed content before removal.

| Item | Type | Reason |
|---|---|---|
| `worktree-agent-a667cf3501eaf0ea3` | branch/worktree | Historical Elsevier source at `3cbcb88`; superseded by `manuscript/performance-evaluation-template-20260913`. |
| `worktree-closed-loop-feasibility-20260913` | branch/worktree | Side feasibility branch at `34e9dcc`; later integrated in `integration/closed-loop-feasibility-20260913` and descendants. |
| `/home/soroush/projects/lafc-evict-dataset/repo/.claude/worktrees/closed-loop-pilot-integration` | worktree | Clean integration worktree; content appears preserved by pilot/design lineage. |
| `sigmod-placeholder-cleanup-20260629` | branch | Historical manuscript cleanup branch; review before deleting. |
| `sigmod-table-layout-pass-20260629` | branch | Historical table-layout branch; review before deleting. |

## Manual-Review Cleanup Candidate

| Path | Status | Recommendation |
|---|---|---|
| `publication/.env.example.azure-cleanup-backup-20260903-213025` | Untracked in the primary checkout | Manual-review cleanup candidate. Do not commit or delete automatically. |

## Do Not Touch

- Dirty augmented-caching worktrees in `/home/soroush/projects/augmented-caching/repo/.claude/worktrees/`.
- The secondary repository `/home/soroush/projects/augmented-caching/repo` unless a future task explicitly authorizes it.
- Frozen scientific artifacts under:
  - `analysis/sigmod_target_discriminativeness_20260913/`
  - `analysis/pairwise_provenance_repair_20260913/`
  - `analysis/closed_loop_pilot_20260913/`
  - `analysis/closed_loop_production_design_20260913/`
- The Performance Evaluation manuscript branch and PDF during cleanup unless a manuscript-specific task authorizes edits.
- Any raw traces, model binaries, local caches, external-host payloads, AWS/Hugging Face/Zenodo state, or temporary session logs without an explicit preservation/deletion decision.

## Branch Graph Summary

```text
master/fbbeedb
  ->
analysis lineage / 76d562f
  ->
closed-loop feasibility integration / a85fe5e
  ->
closed-loop pilot / 983d7d0
  ->
production design / adc7c64
  ->
final polish / polish/final-handoff-20260914
```

Separate manuscript line:

```text
76d562f
  ->
Performance Evaluation template reconciliation
  ->
471b3c4 manuscript state
```

## Query 3 Cleanup Preparation

Recommended next cleanup/organization actions, after review:

1. Validate that superseded worktrees have no unique uncommitted content.
2. Decide durable handling for the regenerated pairwise Parquet currently under
   `/tmp`.
3. Re-check public-release docs for any remaining stale historical wording that
   lacks a current-status pointer.
4. Prepare a final validation pass over branch/worktree cleanliness before any
   optional branch/worktree removal.
