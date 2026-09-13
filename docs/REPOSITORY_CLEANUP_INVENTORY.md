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
| `sigmod-placeholder-cleanup-20260629` | branch | Historical manuscript cleanup branch; review before deleting. |
| `sigmod-table-layout-pass-20260629` | branch | Historical table-layout branch; review before deleting. |
| Other historical SIGMOD branches | branch | Keep unless a future audit demonstrates preservation and low risk. |

## Completed Cleanup

Completed during Query 3 on 2026-09-13.

| Item | Action | Verification |
|---|---|---|
| `/home/soroush/projects/lafc-evict-dataset/repo/.claude/worktrees/agent-a667cf3501eaf0ea3` | Removed worktree | Worktree was clean; introduced Performance Evaluation paths are preserved in `manuscript/performance-evaluation-template-20260913` at `471b3c4`, which also contains later acknowledgments/funding updates. |
| `worktree-agent-a667cf3501eaf0ea3` | Deleted local branch | Historical Elsevier source at `3cbcb88`; superseded by the manuscript branch above; no remote branch observed. |
| `/home/soroush/projects/lafc-evict-dataset/repo/.claude/worktrees/closed-loop-feasibility-20260913` | Removed worktree | Worktree was clean; `analysis/closed_loop_feasibility_20260913/` content matches preserved integrated lineage. |
| `worktree-closed-loop-feasibility-20260913` | Deleted local branch | Side feasibility branch at `34e9dcc`; content preserved in `integration/closed-loop-feasibility-20260913` at `a85fe5e` and descendants. |
| `/home/soroush/projects/lafc-evict-dataset/repo/.claude/worktrees/closed-loop-pilot-integration` | Removed worktree | Redundant clean checkout of `integration/closed-loop-feasibility-20260913`; branch preserved. |
| `publication/.env.example.azure-cleanup-backup-20260903-213025` | Deleted untracked file | Byte-identical to tracked `publication/.env.example`; no unique configuration preserved there. |
| Primary checkout generated caches | Deleted ignored cache/build metadata | Removed `.pytest_cache/`, `.ruff_cache/`, Python `__pycache__/` directories, and `src/lafc_evict_dataset.egg-info/`; release/report payloads were left untouched. |

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

Query 3 completed the safe cleanup items above. Remaining recommendations:

1. Do not remove additional historical branches without a fresh preservation
   audit.
2. Preserve the tracked canonical pairwise artifact as analysis evidence; do
   not promote it into a public release without a separate release decision.
3. Prepare a final validation pass over branch/worktree cleanliness in Query 4.
