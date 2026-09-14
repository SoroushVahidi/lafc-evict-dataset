# LAFC-Evict Current Project Status and Handoff

> **SUPERSEDED as of 2026-09-14.** This document predates the Tier-1
> closed-loop evaluation, the offline/closed-loop linkage analysis, the
> mechanistic analysis, and the full continuation-policy-sensitivity study.
> Read `docs/CURRENT_PROJECT_STATUS_AND_HANDOFF_20260914B.md` first. This
> document is kept, unmodified below this notice, because its release/
> publication history (Sections 1, 4, 15-17) remains accurate and because
> manuscript/scientific content must never be discarded.

This is the canonical starting point for a future LAFC-Evict agent. It records
the current scientific, manuscript, release, and cleanup state after the
closed-loop pilot was frozen and the production closed-loop evaluation was
designed.

## 1. Canonical Repository State

Repository: `SoroushVahidi/lafc-evict-dataset`

Canonical scientific handoff branch: `polish/final-handoff-20260914`

Base lineage: `experiment/closed-loop-production-design-20260913` at
`adc7c64311d54b1fca927baf0bbaca57e179cca8`

Important lineage:

```text
master/fbbeedb
  ->
analysis/sigmod-target-discriminativeness-20260913 / 76d562f
  ->
integration/closed-loop-feasibility-20260913 / a85fe5e
  ->
experiment/closed-loop-pilot-20260913 / 983d7d0
  ->
experiment/closed-loop-production-design-20260913 / adc7c64
  ->
polish/final-handoff-20260914 / this document's commit
```

Separately, the Performance Evaluation manuscript is intentionally maintained
on its own branch:

```text
76d562f
  ->
Performance Evaluation template reconciliation / 91bd814
  ->
manuscript/performance-evaluation-template-20260913 / 471b3c4
```

`master` remains the historical/default publication base at
`fbbeedb02ffedf571cf6a08a9a7418467d857cea`. Do not treat `master` as the
latest scientific state.

The Performance Evaluation manuscript branch remains separate at
`manuscript/performance-evaluation-template-20260913`, HEAD
`471b3c43031d5ab08b98a5ccd26cc48cab687182`. Do not merge it into the final
polish branch without an explicit integration plan.

Current relevant worktrees after Query 3 cleanup:

- `/home/soroush/projects/lafc-evict-dataset/repo`:
  `analysis/sigmod-target-discriminativeness-20260913`
- `/home/soroush/projects/lafc-evict-dataset/repo/.claude/worktrees/final-handoff-20260914`:
  `polish/final-handoff-20260914`
- `/home/soroush/projects/lafc-evict-dataset/repo/.claude/worktrees/closed-loop-production-design-20260913`:
  `experiment/closed-loop-production-design-20260913`
- `/home/soroush/projects/lafc-evict-dataset/repo/.claude/worktrees/closed-loop-pilot-20260913`:
  `experiment/closed-loop-pilot-20260913`
- `/home/soroush/projects/lafc-evict-dataset/repo/.claude/worktrees/manuscript-pe-template-20260913`:
  `manuscript/performance-evaluation-template-20260913`

Removed during Query 3 after clean/preservation checks:

- worktree and local branch `worktree-agent-a667cf3501eaf0ea3`
- worktree and local branch `worktree-closed-loop-feasibility-20260913`
- redundant worktree `closed-loop-pilot-integration`

The provenance branch `integration/closed-loop-feasibility-20260913` was kept.

## 2. What LAFC-Evict Is

LAFC-Evict provides a reusable supervised decision surface between raw cache
traces and closed-loop cache-policy evaluation. It materializes per-decision,
per-candidate finite-horizon counterfactual eviction outcomes so researchers
can train, compare, and diagnose learning objectives without independently
reconstructing the same supervision from raw traces.

These labels are finite-horizon and continuation-policy-dependent. LAFC-Evict
complements rather than replaces closed-loop policy evaluation.

When novelty is discussed, use restrained language such as "to the best of our
knowledge." Do not claim absolute novelty.

## 3. Canonical Scientific Dataset

The canonical SIGMOD-scale scientific dataset is internal scientific evidence,
not the current public payload.

Families:

- `cloudphysics`
- `metacdn`
- `metakv`
- `twemcache`
- `wiki2018`

Candidate rows: `277,995,072`

Decisions: `2,363,286`

Capacities: `32`, `64`, `128`, `256`

Horizons: `4`, `8`, `16`

This must be distinguished from the currently public wiki2018-only v0.3
release.

## 4. Current Public Release

Public version: `v0.3`

Public family: `wiki2018` only

This is a public/reproducibility release and must not be described as
equivalent to the five-family canonical scientific dataset.

Hugging Face: repository documentation reports v0.3 published at revision
`2113cc4d1edee57275d769d8760da77ed67c875d`.

AWS Open Data:

- Bucket: `lafc-evict-open-data`
- Region: `us-west-2`
- Payload: `v0.3`, `wiki2018` only
- Objects: `18`
- Size: approximately `106.1 MiB`
- License: `CC0-1.0`
- Anonymous public download: previously verified `PASS`
- AWS Open Data Registry PR: `#3335`
- Fork branch: `add-lafc-evict-dataset`
- Known PR head: `e12ac8f90714daf2bc88987725cc2a48b916cd59`
- Registry status: awaiting AWS/Open Data Registry maintainer activity unless
  later local documentation proves otherwise

AWS sponsorship: AWS Open Data Sponsorship Program, up to `600 GB` hosted for
two years beginning `2026-08-18`.

Zenodo:

- Current documented DOI-backed release: `v0.2`
- Version DOI: `10.5281/zenodo.21895844`
- Concept DOI: `10.5281/zenodo.21895843`
- v0.3 Zenodo DOI: not documented as minted

If repository documentation contains inconsistent explanations for why v0.3
was not minted on Zenodo, preserve the most recent verified repository state
and explicitly mark the contradiction rather than inventing a reconciliation.

## 5. Critical Public-Release Caveat

`wiki2018` is completely non-discriminative under the current finite-horizon
target in the audited canonical construction.

It exhibits:

- all candidates tied
- zero random regret
- no unique winner

Therefore, the public wiki2018-only v0.3 release must not be presented as
representative of the discriminative behavior of the full five-family
scientific dataset.

It remains useful as:

- a reproducibility/public preview
- a schema/example release
- an intentionally informative negative/control case

Do not describe wiki2018-only v0.3 as a strong supervised-learning benchmark by
itself under the present target.

## 6. Target-Discriminativeness Audit

Artifact: `analysis/sigmod_target_discriminativeness_20260913/`

Important results:

- candidate rows: `277,995,072`
- decisions: `2,363,286`
- decision-weighted random-optimal probability: `0.9912418754543462`
- decision-weighted random mean regret: `0.008826200441884731`
- all-tied fraction: `0.676601985540472`
- unique-winner fraction: `0.0`
- classification: `B = CONDITIONALLY DISCRIMINATIVE`

Interpretation:

- supervision is highly tie-dominated in aggregate
- discriminativeness is strongly workload/capacity/horizon dependent
- MetaCDN and Twemcache capacity 32, especially H=16, provide substantially
  more useful signal
- wiki2018 is fully degenerate

Avoid claiming uniform discriminativeness.

## 7. Pairwise Provenance

Artifact: `analysis/pairwise_provenance_repair_20260913/`

Historical shipped sample:
`release/lafc-evict-v0.1-open-current-contract-preserved/data/pairwise_sample/pairwise_sample.parquet`

Historical/stale counts:

- `a_better = 6,134`
- `b_better = 113,898`
- `tie = 879,968`

Correct regenerated sample counts:

- `a_better = 60,673`
- `b_better = 61,065`
- `tie = 878,262`

Correct regenerated SHA256:
`1d770c6999ac999673b46805a6ca173e24b116793b35405d2d211cae7b9eda02`

Root cause: the historical decision-selection hash used a six-column key; the
canonical selection later uses the nine-column key.

Current state:

- old shipped sample is historical/noncanonical
- regenerated sample is canonical with respect to current decision selection
- regenerated parquet is durably preserved as tracked Git analysis evidence

Durable path:
`analysis/pairwise_provenance_repair_20260913/artifacts/pairwise_sample_regenerated_canonical.parquet`

Durable size: `11,367,843` bytes

Storage mode: `TRACKED_IN_GIT`

The temporary source path used during repair was:
`/tmp/claude-1000/-home-soroush/8a66210e-4d63-4b01-b3ba-10065c25f134/scratchpad/pairwise_repair/generated/pairwise_sample.parquet`

The regeneration script exists at
`analysis/pairwise_provenance_repair_20260913/scripts/regenerate_pairwise_v2.py`
and is documented in the pairwise repair report. The durable artifact manifest
is `analysis/pairwise_provenance_repair_20260913/ARTIFACT_MANIFEST.md`.

Do not promote this analysis sample into a public release without a separate
release decision.

## 8. Predictor Feature Issue

Audited canonical data has:

`candidate_is_predictor_victim == candidate_is_lru_victim`

throughout the audited canonical data.

Predictor/bucket/confidence-related features include constant or placeholder
fields.

Status: unresolved upstream/data-generation issue.

References:

- `analysis/sigmod_target_discriminativeness_20260913/`
- `analysis/pairwise_provenance_repair_20260913/`

Future manuscript claims involving predictor fields must be cautious.

## 9. Frozen Closed-Loop Pilot

Branch: `experiment/closed-loop-pilot-20260913`

Commit: `983d7d0204645660e7b683ed30298677c2b42ccf`

Artifacts: `analysis/closed_loop_pilot_20260913/`

Classification: `B = MIXED`

Central finding:

MetaCDN cap32:

- offline H=16: `LRU > random > MRU`
- closed-loop: `LRU > random > MRU`

Twemcache cap32:

- offline H=16: `LRU > random > MRU`
- closed-loop: `LRU > random > MRU`

Closed-loop numbers:

| Family | Policy | Misses | Difference vs LRU |
|---|---:|---:|---:|
| MetaCDN | LRU | 11,861 | reference |
| MetaCDN | random mean | 12,499.15 | +5.38% |
| MetaCDN | MRU | 17,479 | +47.37% |
| MetaCDN | SIEVE | 11,957 | +0.81% |
| MetaCDN | evict_value_v1 | blocked | leakage risk |
| Twemcache | LRU | 6,153 | reference |
| Twemcache | evict_value_v1 | 6,315 | +2.63% |
| Twemcache | random mean | 6,410.90 | +4.19% |
| Twemcache | SIEVE | 6,674 | +8.47% |
| Twemcache | MRU | 7,822 | +27.12% |

Interpretation:

- policy separation is meaningful
- offline ordering agrees with closed-loop ordering for LRU/random/MRU in both
  pilot families
- current evidence supports that the offline supervision contains information
  associated with actual policy behavior
- evidence is not sufficient for a universal offline-to-closed-loop claim
- current learned model does not beat LRU
- MetaCDN learned evaluation remains blocked because no independent test chunks
  exist

Split wording:

- MetaCDN: validation-window evidence
- Twemcache: temporally held-out test-window evidence

Do not describe either as a separately held-out raw trace.

## 10. Production Closed-Loop Design

Branch: `experiment/closed-loop-production-design-20260913`

Commit: `adc7c64311d54b1fca927baf0bbaca57e179cca8`

Artifacts: `analysis/closed_loop_production_design_20260913/`

Status: designed, not run.

Tier 1:

- families: `cloudphysics`, `metacdn`, `metakv`, `twemcache`, `wiki2018`
- capacities: `32`, `128`
- policies: `LRU`, `MRU`, `random`, `SIEVE`
- random seeds: `0..19`
- offline comparison: H=16 primary; H=4, H=8, H=16 secondary

Tier 2:

- reuse frozen Twemcache cap32 learned-policy result
- potentially add cloudphysics cap32 `evict_value_v1` only after Tier-1
  validation and explicit approval

No other expensive learned-policy cell is currently approved.

## 11. Production Research Questions

RQ-CL1: Do offline LRU/random/MRU rankings agree with closed-loop miss
rankings?

RQ-CL2: Does offline regret-gap strength track closed-loop miss-gap magnitude?

RQ-CL3: How does agreement vary by workload and capacity?

RQ-CL4: Which H in {4, 8, 16} is most aligned with closed-loop behavior?

RQ-CL5: Can `evict_value_v1` produce competitive closed-loop behavior on
leakage-safe temporal test windows?

RQ-CL6: What happens on offline-degenerate `wiki2018`?

## 12. Continuation-Policy Sensitivity

Status: not run.

This is a different question from closed-loop evaluation.

Closed-loop replay asks: how does a deployed policy behave while inducing its
own cache-state trajectory?

Continuation-policy sensitivity asks: how do the counterfactual labels
themselves change if the continuation policy after a forced eviction changes?

These must not be conflated. A separate continuation-policy sensitivity
experiment remains necessary.

## 13. Current Hypothesis Map

| Hypothesis | Current state | Interpretation |
|---|---|---|
| H_TARGET | CONDITIONALLY SUPPORTED | Labels are useful in some regimes but highly tie-dominated overall. |
| H_OFFLINE_CLOSED_LOOP | SUPPORTED IN PILOT ONLY | LRU/random/MRU offline ordering agrees with closed-loop ordering on MetaCDN and Twemcache cap32. |
| H_LEARNED_POLICY | NOT SUPPORTED AS SUPERIOR TO LRU | Twemcache learned policy beats random/SIEVE but loses to LRU. MetaCDN is blocked. |
| H_WIKI | NOT SUPPORTED AS A DISCRIMINATIVE SUPERVISED TARGET | Useful negative/control case. |
| H_CONTINUATION | UNKNOWN / NOT TESTED | Requires a separate continuation-policy sensitivity experiment. |
| H_PRACTICAL_USE | PARTIALLY SUPPORTED AND STRENGTHENED BY PILOT | LAFC-Evict is defensible as a reusable offline supervised decision surface complementary to closed-loop evaluation, but stronger production evidence is still required. |
| H_PAIRWISE | OLD SHIPPED SAMPLE NOT CANONICAL | Historical pairwise sample must not be conflated with the canonical regenerated sample. |

## 14. Reviewer-Remediation Status

High-priority remaining issues:

1. Run Tier-1 production closed-loop evaluation.
2. Integrate target-discriminativeness findings honestly.
3. Prevent stale/canonical pairwise-sample conflation.
4. Run or otherwise address continuation-policy sensitivity.
5. Finish practical-use exposition and supervised-decision-surface framing.
6. Complete citation metadata validation.
7. Build a complete code-inclusive reproducibility/artifact package.
8. Integrate new scientific evidence into the Performance Evaluation
   manuscript.

Do not claim these are resolved merely because the experiments are designed.

## 15. Why LAFC-Evict Exists

Existing shared cache resources primarily expose raw request traces, simulation
environments, or runnable policies. Learned eviction systems commonly derive
their own training signals from those traces inside bespoke pipelines.
LAFC-Evict materializes a reusable candidate-level supervision layer so
researchers can train, compare, and diagnose supervised eviction objectives on
the same decisions without independently regenerating the counterfactual
labels.

This layer supports training, comparison, diagnostics, and
target-discriminativeness analysis.

Closed-loop evaluation remains mandatory because eviction is sequential and
policy actions change future cache states.

Avoid absolute novelty claims such as "every group does this" or "no one has
ever released..." Use restrained, source-backed language.

## 16. Related-Work and Citation State

Citation maintenance remains incomplete. Do not edit bibliography metadata
without checking authoritative sources.

High-priority missing or requiring authoritative verification:

- Cache-Coliseum / NeurIPS 2025 associated paper
- Learning Caching Policies with Subsampling
- DAgger
- Park
- QD-LP / FIFO Can Be Better than LRU

Metadata needing re-check:

- LRB
- GL-Cache
- 3L-Cache
- LeCaR
- Parrot
- cache_dataset
- libCacheSim

Known cautions:

- Parrot authorship must be checked against the official ICML/PMLR paper.
- Park authorship and venue must be checked against official NeurIPS
  proceedings.
- Cache-Coliseum should be cited using its actual peer-reviewed NeurIPS 2025
  paper metadata where appropriate, not stale arXiv/to-appear metadata.

## 17. Performance Evaluation Manuscript State

Branch: `manuscript/performance-evaluation-template-20260913`

HEAD: `471b3c43031d5ab08b98a5ccd26cc48cab687182`

PDF: 27 pages

Status:

- Elsevier/elsarticle migration complete
- acknowledgments/funding complete
- scientific reviewer revision not yet incorporated

Acknowledgments include:

- Prof. Ioannis (Yiannis) Koutis
- Google Cloud Research Credits Program, no unsupported amount
- Cohere Labs Catalyst Grant, `$1,000` API credits
- CloudRift AI Builder Grant, `1,000` credits
- AWS Open Data Sponsorship, up to `600 GB` for two years

Major scientific evidence still not incorporated:

- target audit
- pairwise repair
- predictor issue
- wiki2018 degeneracy
- closed-loop pilot
- production results, once run
- continuation limitation
- practical-use reframing
- citation updates

## 18. Exact Next Action

NEXT SCIENTIFIC ACTION:

Run and validate Tier-1 production closed-loop evaluation only.

Do not begin Tier-2 learned-policy expansion before Tier-1 results are
validated.

Do not yet perform the full journal scientific rewrite because production
evidence is still pending.
