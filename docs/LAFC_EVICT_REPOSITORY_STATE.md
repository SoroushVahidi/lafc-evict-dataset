# LAFC-Evict Repository State

Audit date: 2026-09-15.

## Canonical State

- Canonical branch: `master`
- Canonical master SHA at this audit: `3553d2eaa46c9671aebd81e560ba10d65ad62db8`
- Remote: `origin`
- Repository: `SoroushVahidi/lafc-evict-dataset`
- Paper: LAFC-Evict: A Large-Scale Counterfactual Benchmark for Learned Cache Eviction
- Canonical manuscript PDF: `paper/performance_evaluation/latex/LAFC-Evict_A_Large-Scale_Counterfactual_Benchmark_for_Learned_Cache_Eviction.pdf`
- LaTeX source entry point: `paper/performance_evaluation/latex/main.tex`
- Manuscript status: integrated into `master`, validated to build successfully at 45 pages.

The manuscript commit `d48a1450b1054eb74463e6c420fd200d6c50ab70` is in
`master`. The provenance commits
`eb0304ac4831104120312343df6268ea4a3381a9` and
`148d9f97934e1512a78f52010011b1ecd82af2dc` are also in `master`.

## Public Release Scope

The current public derived-data package is v0.3 and is wiki2018-only. The
Performance Evaluation manuscript evaluates a five-family scientific corpus,
but Alibaba Block, MetaCDN, MetaKV, and Twemcache generated rows are not
claimed as publicly downloadable release rows. Public release and DOI details
are tracked in `docs/LAFC_EVICT_PUBLICATION_STATE.md` and
`publication/LAFC_EVICT_PUBLICATION_STATE.json`.

## Provenance Terminology

- Reader-facing workload name: Alibaba Block / `alibaba-block`.
- Historical internal reproducibility key: `cloudphysics`.
- The internal key may remain in code, manifests, evidence paths, and explicit
  historical-key disclosures only.
- Provenance and license details are in `THIRD_PARTY_DATA.md`,
  `dataset_card/LICENSE_DATA.md`, and `manifests/source_family_registry.yaml`.

## Integrated Evidence

Major validated evidence currently represented on `master` includes:

- Performance Evaluation manuscript and canonical PDF.
- Closed-loop/offline linkage evidence and Figure 4 linkage redesign.
- Pairwise held-out baseline results used by the manuscript.
- Continuation-sensitivity pilot/full-study artifacts.
- Compact validated full-population MRU-continuation census summaries under
  `analysis/continuation_policy_mru_population_census_20260914/validated/`.
- Publication-state and provenance/license corrections for public release
  scope.

## Branch And Worktree Notes

Retain these active/evidence branches until Query 3 makes an explicit cleanup
decision:

- `analysis/continuation-mru-census-validation-20260915`: contains unique MRU
  population census validation and reproducibility scripts not fully reachable
  from `master`.
- `experiment/continuation-mru-population-census-20260914`: contains the MRU
  population census harness commit and has a dirty worktree with raw local
  census output.
- `manuscript/performance-evaluation-template-20260913`: contains two older
  manuscript-template/acknowledgment commits not reachable from `master`;
  investigate before deletion.

The dirty worktree
`.claude/worktrees/continuation-mru-population-census-20260914` must be
preserved. It contains local-only raw census logs and chunk outputs:

- `analysis/continuation_policy_mru_population_census_20260914/logs/`
- `analysis/continuation_policy_mru_population_census_20260914/outputs/20260914T042528Z_1a29e773a113/`

Do not delete, move, clean, stash, compress, or modify those files without a
separate evidence-retention decision. The compact validated summaries are on
`master`, but the raw chunk set is local-only and large.

## Cleanup Deferred To Query 3

Most clean branches/worktrees whose tips are ancestors of `master` are cleanup
candidates, including the completed Performance Evaluation manuscript worktree
and branch, temporary integration worktrees/branches, completed closed-loop and
continuation sensitivity branches, older SIGMOD branches, and local backup
branches. Query 3 should verify each candidate again before deleting any local
or remote branch or removing any worktree.

No branch, worktree, generated file, or raw evidence artifact was deleted during
this repository-state audit.
