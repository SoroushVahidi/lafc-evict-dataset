# Closed-Loop Cache-Policy Evaluation Feasibility Audit (2026-09-13)

Scope: read-only inspection and planning only. No experiments launched, no
Wulver jobs submitted, no labels regenerated, no canonical generated data
modified, no manuscript edited, no public artifact touched.

Motivation: the strongest unresolved SIGMOD criticism (Reviewer #2, #4) is
that the benchmark evaluates a forced eviction followed by LRU continuation,
not a deployed policy's repeated victim choices. This audit determines
whether a genuine closed-loop replay experiment is feasible today, and if
so, designs (without running) a minimal pilot and a production experiment.

Files:

- `REPORT.md` — full findings, organized by the 12 requested phases, ending
  in the structured `LAFC_EVICT_CLOSED_LOOP_FEASIBILITY_REPORT` block.
- `outputs/component_inventory.json` — machine-readable inventory of
  repositories, branches, commits, and file paths for every simulator/policy/
  training component found.

Repositories inspected (read-only):

- `SoroushVahidi/lafc-evict-dataset` — local: `/home/soroush/projects/lafc-evict-dataset/repo`
- `SoroushVahidi/Augmented-caching` — local: `/home/soroush/projects/augmented-caching/repo`,
  plus three unmerged worktrees (`3l-cache`, `cacheus`, `halp`) under
  `/home/soroush/projects/augmented-caching/worktrees/`

Headline finding: a working, tested, deterministic closed-loop simulator
already exists in `Augmented-caching` (`src/lafc/simulator/`, `src/lafc/policies/`,
`src/lafc/runner/run_policy.py`), LRU and SIEVE are ready to run today, and the
exact raw/processed request traces for all five released families
(cloudphysics, metacdn, metakv, twemcache, wiki2018 — 50,000 requests each)
are present locally in the simulator's native input format. This materially
changes the feasibility picture: closed-loop replay is cheap (local,
minutes) compared to the multi-hour Wulver-scale offline label-generation
jobs already run for this project.
