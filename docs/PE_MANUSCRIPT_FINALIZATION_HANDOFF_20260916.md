# PE Manuscript Finalization Handoff - 2026-09-16

This handoff is the current starting point for the LAFC-Evict Performance
Evaluation manuscript branch. Older handoffs remain useful historical records,
but they predate the final manuscript-finalization branch state below.

## 1. Canonical Manuscript Worktree

- Worktree: `/home/soroush/projects/lafc-evict-dataset/worktrees/pe-learned-closed-loop-integration-20260916`
- Branch: `manuscript/pe-learned-closed-loop-integration-20260916`
- Manuscript snapshot commit:
  `525d3c764c20eadeac01328d3bfb0dd7bf707b06`
- Parent/base before manuscript finalization:
  `8abf686777520c8b04f049229d1d33d5153c443b`
- Remote branch: `origin/manuscript/pe-learned-closed-loop-integration-20260916`
- Expected state after Query 3: clean local worktree, upstream configured, and
  local branch synchronized with the remote branch.
- Do not merge or rebase this branch before the corrected long-horizon
  integration unless a new explicit instruction supersedes this handoff.

## 2. Manuscript State

- Target journal: `Performance Evaluation`.
- Current validation build: passes with a 54-page PDF.
- Undefined references/citations: none observed in final Query 3 validation.
- Known benign warning state: ordinary overfull/underfull diagnostics remain,
  along with repeated `xdvipdfmx` object messages previously diagnosed as
  driver/template-level behavior rather than duplicate LaTeX labels.
- Static QA completed: conflict markers, unfinished manuscript placeholders,
  duplicate Table 9 placement, public-release wording, and unresolved-reference
  checks were reviewed.
- Compression/prose polish completed across the main manuscript.
- Family-aware robustness calibration completed: the metacdn-sensitive
  leave-one-family-out result is now described as a sensitivity limitation, not
  robust confirmation.
- Completed manuscript-finalization work includes
  tie-aware/discriminative-only correction, pairwise subset/caveat correction,
  public-release state reconciliation, Table 9 main-body placement, Figure 3
  visual polish, Figure 6 visual-only polish, prose/compression, `y_loss`
  terminology correction, family-aware correlation calibration, static QA,
  float/page-layout cleanup, and repository/LaTeX hygiene.

## 3. Key Current Scientific Results

- Canonical evaluated scale: 277,995,072 candidate rows and 2,363,286
  decision-horizon rows across five evaluated families.
- Pairwise sample: 1,000,000 sampled pairs; 121,738 non-tie rows and 878,262
  ties.
- Target structure: all-tied fraction 0.6766; unique-winner fraction 0.0.
- Best-candidate selection must be read tie-aware. The primary selector-quality
  view is the discriminative stratum: 764,282 decisions (32.34%). In that
  stratum, the linear best-candidate selector has optimal-selection rate 0.6145
  and mean regret 0.3867, versus uniform-random expected optimal-selection rate
  0.9729 and expected regret 0.0273.
- Pairwise non-tie feature baseline: test accuracy 0.7078 with Wilson 95% CI
  [0.688, 0.726] on 2,211 held-out non-tie rows. The held-out non-tie subset is
  94.98% twemcache/alibaba-block and contains zero metacdn or wiki2018 rows, so
  this is not a cross-family generalization claim.
- Tier-1 closed-loop status: validated 5-family x 2-capacity closed-loop
  evidence for LRU, MRU, random, and SIEVE. LRU is best in 9/10 cells; metakv
  capacity 128 is the one cell where SIEVE and random-mean beat LRU. MRU is
  worst in every non-degenerate cell.
- Frozen learned-model check: one frozen HistGradientBoostingRegressor was
  evaluated under a separate held-out protocol, not Tier-1. It did not
  consistently beat LRU, SIEVE, or random (1 win, 2 wiki2018 ties, 7 losses
  against each); it beat MRU in every non-degenerate cell and beat LFU more
  often than not.

## 4. Public Release State

- Canonical public repository: `github.com/SoroushVahidi/lafc-evict-dataset`.
- Authoritative public/master commit for this handoff:
  `a3de075b90fdcc698e9c0ce0e18138f2044e6f85`.
- Hugging Face: `https://huggingface.co/datasets/SoroushVahidi/lafc-evict`,
  v0.3 revision `2113cc4d1edee57275d769d8760da77ed67c875d`.
- AWS Open Data: bucket `lafc-evict-open-data`, region `us-west-2`, hosting the
  v0.3 wiki2018-only payload.
- Zenodo: current DOI-backed release is v0.2 only; version DOI
  `10.5281/zenodo.21895844`, concept DOI `10.5281/zenodo.21895843`. No v0.3
  Zenodo version DOI is documented.
- Evaluated manuscript families: alibaba-block (historical internal key
  `cloudphysics`), metacdn, metakv, twemcache, and wiki2018.
- Currently hosted public v0.3 subset: wiki2018-derived rows only.
- License distinction: the hosted wiki2018 v0.3 slice is CC0-1.0; twemcache and
  alibaba-block are cleared under CC BY 4.0; metakv and metacdn are cleared
  under Apache License 2.0; brightkite and citibike remain excluded.
- Important nuance: the authoritative public-repo top-level `README.md` still
  contains older wording that says four evaluated families were not yet cleared
  for public release. Newer publication-state docs on `master`, especially
  `docs/LAFC_EVICT_PUBLICATION_STATE.md`, supersede that wording. Do not modify
  public `master` in this manuscript cleanup; reconcile the top-level README in
  a dedicated public-repository change.

## 5. Corrected Long-Horizon Campaign - Pending

- Campaign: `pe_long_horizon_canonical_regen_20260916`.
- Jobs to track before any integration:
  - production: `1291887`
  - validation: `1291888`
  - aggregation: `1291889`
- Scientific branch/worktree: not independently verified in Query 2. Re-check
  local branches/worktrees and current Slurm state before resuming integration.
- Status in this handoff is LAST KNOWN unless freshly checked elsewhere.
- Do not trust superseded H32/H64/H128 scientific results for the final
  manuscript.
- Exact 20/20 H16/H32/H64/H128 decision-key identity must pass first.
- Authoritative recomputation must pass before any manuscript integration.
- Figure 6 currently has visual-only polish but stale scientific data:
  `SAFE_EXISTING_VISUAL_CHANGE_PENDING_DATA_REGENERATION`.
- Keep the visual polish diff for Figure 6, but do not regenerate or update its
  scientific data until the canonical campaign is `COMPLETE_VALID`.
- Table 8, long-horizon prose, and final Figure 6 data integration for corrected
  H32/H64/H128 remains pending.
- Query 2 did not contact Wulver and did not verify current job state. Any job
  completion counts from earlier notes must be treated as LAST KNOWN, not
  current, unless independently rechecked in the future task.

## 6. Protected Content

Do not accidentally revert:

- Tie-aware/discriminative-only best-candidate analysis and Table 9 in the main
  body.
- Pairwise non-tie held-out result, Wilson interval, and workload-composition
  caveat.
- Public five-family evaluation vs hosted wiki2018-only v0.3 distinction.
- Family-specific licensing/public-release language.
- Continuation-scope caveats: sampled MRU/random only at capacities 32/128;
  population-scale evidence only for MRU at capacities 32/64/128/256.
- Family-aware robustness calibration for the metacdn leave-one-family-out
  sensitivity result.
- Mechanistic per-family evidence and Tier-1 closed-loop results.
- Frozen learned-policy closed-loop check and its protocol distinction from
  Tier-1.
- Continuation robustness results and scope caveats.
- Figure 3 annotation/leader-line visual polish.
- Figure 6 visual-only polish, while leaving corrected data integration pending.
- Modern related-work positioning and compression polish.
- Public-release distinction between the evaluated five-family manuscript
  evidence and the currently hosted wiki2018-only v0.3 subset.

## 7. Current Branch State

The manuscript snapshot has been committed as
`525d3c764c20eadeac01328d3bfb0dd7bf707b06`. This handoff document is committed
separately so it can name that exact snapshot. After Query 3 finishes, the
worktree is expected to be clean and synchronized with
`origin/manuscript/pe-learned-closed-loop-integration-20260916`.

## 8. Remaining Steps

1. Re-check Wulver DAG status in a separate task.
2. If all complete, run full canonical identity/metric audit.
3. Integrate corrected H32/H64/H128 values only after `COMPLETE_VALID`.
4. Regenerate Figure 6 with corrected data while preserving visual styling.
5. Update Table 8 and dependent prose.
6. Run a full final build.
7. Run a fresh blind `Performance Evaluation` reviewer pass.
8. Prepare submission packaging.

Separate future public-repository task: reconcile the top-level public README
wording with authoritative publication-state docs.

## 9. Do-Not-Touch Areas

- Wulver jobs or running Slurm state from a manuscript cleanup task.
- Canonical experiment outputs, corrected long-horizon campaign outputs, or raw
  census outputs.
- Authoritative public `master` worktree at
  `/home/soroush/projects/lafc-evict-dataset/repo`.
- Unrelated worktrees and branches listed by `git worktree list`.
- Any raw or generated scientific artifact whose provenance is unclear.
