# LAFC-Evict Tier-1 Closed-Loop Production Harness

This directory implements the execution harness for the **approved** Tier-1
production closed-loop evaluation. It was created on branch
`experiment/closed-loop-tier1-harness-20260913`, forked from the canonical
handoff commit `d37d084b45bcb76550364c68784fc1a40abbd496`
(`polish/final-handoff-20260914`).

**As of this commit, Tier 1 has NOT been launched.** This directory contains
a validated, tested implementation and a `--preflight` mode that passes, but
no production run has been executed and no scientific result exists here.
See "Exact future launch procedure" below for what a later, explicitly
approved launch looks like.

## Relationship to the frozen pilot

The frozen closed-loop pilot (`analysis/closed_loop_pilot_20260913/`,
branch `experiment/closed-loop-pilot-20260913` @ `983d7d0`) evaluated
MetaCDN and Twemcache at capacity 32 only, with LRU/MRU/random/SIEVE and
`evict_value_v1` where leakage-safe. Its script
(`analysis/closed_loop_pilot_20260913/scripts/run_pilot.py`) is the direct
precedent this harness generalizes: the LRU/SIEVE imports, the MRU/random
pilot-local policy classes, the trace-loading and window-scoring functions,
and the random-seed aggregation math are all carried forward faithfully
(see `scripts/tier1_core.py` docstrings for exactly where). The frozen pilot
itself is **not modified** by this work.

## Relationship to the approved production design

Every family, capacity, policy, seed, window, and classification value in
this harness is copied verbatim from the checked-in, approved design at
`analysis/closed_loop_production_design_20260913/` (`DESIGN.md`, `MATRIX.md`,
`VALIDITY_GATES.md`, `RUNTIME_ESTIMATE.md`), frozen on
`experiment/closed-loop-production-design-20260913` @ `adc7c64`. That
directory is **not modified** by this work. If the design changes in the
future, `scripts/tier1_core.py`'s constants must be updated to match
explicitly -- this harness does not reinterpret or improvise the design.

## The exact 230-run Tier-1 matrix

- **Families**: cloudphysics, metacdn, metakv, twemcache, wiki2018
- **Capacities**: 32, 128
- **Policies**: LRU, MRU, random, SIEVE
- **Random seeds**: 0 through 19 inclusive (random policy only)
- **Cells**: 5 families x 2 capacities = 10 (family, capacity) cells
- **Deterministic runs**: 3 deterministic policies (LRU, MRU, SIEVE) x 10 cells = 30
- **Random runs**: 20 seeds x 10 cells = 200
- **Total**: **230 closed-loop replay executions**

Offline horizons H=4, H=8, H=16 are **not** additional executions. They are
pre-existing offline label variants (already computed and frozen in
`analysis/sigmod_target_discriminativeness_20260913/`) that Tier-1 results
are compared against descriptively, per family/capacity cell. H=16 is the
primary offline comparison (used by the pilot); H=4/H=8/H=16 are all used as
secondary comparisons.

`tier1_core.assert_plan_valid()` programmatically asserts this exact
composition (230 total, exact family/capacity/policy/seed sets, no
duplicate keys, exactly one deterministic run and exactly 20 random-seeded
runs per cell) every time a plan is built, both in `--preflight` and at the
start of `--run`.

## Split terminology

Per the canonical handoff and production design, scored evidence windows are
always described as **"temporally held-out test window(s)"**, or, for
MetaCDN, explicitly as **validation-window evidence**. They are never
described as "held-out traces" and never as "an unseen trace" -- every
scored window is a slice of the same continuous 50,000-request trace used
end-to-end for cache-state evolution, not an independently sourced trace.

| Family | Scored split | Windows | Classification (informational; Tier 1 runs no learned policy) |
|---|---|---|---|
| cloudphysics | test | `[16384,20479]`, `[20480,24575]` | `LEARNED_POLICY_SAFE_TEST` |
| metacdn | **validation** (no test chunks exist) | `[0,4095]`, `[24576,32767]`, `[36864,45055]` | `BLOCKED_LEAKAGE_RISK` |
| metakv | test (first-window/no-leading-warmup caveat) | `[0,4095]` | `LEARNED_POLICY_SAFE_TEST` |
| twemcache | test | `[32768,36863]`, `[40960,45055]` | `LEARNED_POLICY_SAFE_TEST` |
| wiki2018 | test (offline-degenerate control) | `[24576,28671]` | `LEARNED_POLICY_SAFE_TEST` (learned-policy evaluation deferred) |

### Why MetaCDN is validation-window evidence, not test evidence

MetaCDN has **no test-split chunks at all** at these capacities. Its scored
windows are validation chunks, which is the only available proxy for
held-out evidence for this family -- but those same validation chunks
participated in learned-policy model selection historically, so any
learned-policy claim on them would be circular. Tier 1 itself runs no
learned policy anywhere, so this does not block Tier-1 execution; it only
means MetaCDN's Tier-1 result must always be reported and labeled as
validation-window evidence, never as test-window evidence, in any downstream
analysis or manuscript text.

### Why wiki2018 is a negative/offline-degenerate control

Prior offline audit (`analysis/sigmod_target_discriminativeness_20260913/`)
found wiki2018 completely non-discriminative under the current finite-horizon
target: all candidates tied, zero random regret, no unique winner, in every
capacity/horizon cell. Including it in Tier 1 tests whether closed-loop
policy separation also vanishes (supporting the offline-degeneracy
diagnosis) or whether policies separate substantially in closed loop despite
offline degeneracy (exposing a limitation of the finite-horizon labels or
their state distribution). Either outcome is scientifically informative;
this is why the design explicitly includes it rather than dropping it as
uninteresting.

## Policies and seeds

- **LRU**, **SIEVE**: imported directly from the clean, committed simulator
  implementation (`/home/soroush/projects/augmented-caching/repo/src/lafc/policies/{lru,sieve}.py`).
  Deterministic; no seed.
- **MRU**, **random**: do not exist in the simulator repository. Per the
  approved design ("carrying pilot-local adapter in the production analysis
  script, not by editing simulator code"), both are carried forward
  faithfully from the frozen pilot script into
  `tier1_core.build_local_policy_classes()`, with no behavioral changes.
  MRU is deterministic; random is seeded (`random.Random(seed)` fresh per
  execution, seeds 0..19).
- **evict_value_v1 is categorically out of scope for Tier 1.** See "Scope
  boundaries" below.

## Outputs

Each production run writes to its own immutable directory
`outputs/<RUN_ID>/` (never reused or overwritten; `RUN_ID` is an ISO-like
UTC timestamp plus a short LAFC-Evict commit hash), containing:

- `run_results.jsonl` -- one JSON line per completed/failed execution,
  appended durably as the run progresses (the resume/durability substrate).
- `run_results.csv` -- the same raw per-execution rows in CSV form, written
  once at the end. Every raw random-seed row is preserved individually;
  nothing is averaged away at the raw layer.
- `summary.csv` -- per (family, capacity, policy) aggregates, relative to
  LRU. Deterministic policies are single rows; the random policy is
  aggregated across its (up to 20) seeds into mean / standard deviation /
  min / max / 95%-CI half-width / n_seeds, matching the frozen pilot's
  aggregation formula exactly.
- `sanity_checks.json` -- the full programmatic validity-gate evaluation
  (see below) plus completion counts.
- `provenance.json` -- see "Provenance" below.
- `run_manifest.json` -- overall run_valid flag, completion counts, and
  SHA256 + byte size of every other output file, for tamper-evident
  after-the-fact auditing.
- `tier1_run.log` -- persistent stdout+file log of the run (see "Logging").

`outputs/` and `logs/` both carry a `.gitignore` (`*` except `.gitkeep`/
`.gitignore` itself) so that no generated scientific result is ever
accidentally committed to this repository; a real production run's outputs
must be committed (or otherwise preserved) as a deliberate, separate,
explicit decision, exactly as the frozen pilot's outputs were.

## Provenance

`provenance.json` captures, at run start and again at run end:

- **LAFC-Evict**: repository path, branch, HEAD SHA, `git status --short`,
  and the SHA256 of the harness script itself (`tier1_core.py`).
- **Simulator repository** (augmented-caching): expected vs. actual branch
  and HEAD, the full `git status --porcelain` (recorded, never acted on --
  this repository is intentionally, pre-existingly dirty overall), the
  per-file clean/dirty status and SHA256 of every one of the 7 files Tier 1
  actually imports, the names and (where readable) SHA256 of every untracked
  file, and the full tracked working-tree diff saved to a durable file
  alongside its own SHA256 and byte count. **A run is refused at start if
  any Tier-1 dependency file is not clean relative to the expected HEAD;
  general repository dirtiness elsewhere is recorded but never itself a
  rejection reason, and this harness never cleans, resets, stashes, or
  commits anything in that repository.**
- **Inputs**: absolute trace path, SHA256 (verified against the value
  transcribed from `DESIGN.md`), file size, split/window definitions, and
  evidence label, per family. **A run is refused at start if any trace's
  SHA256 does not match the value recorded in the approved design.**
- **Experiment**: the complete 230-execution plan, command line, Python
  version/platform/hostname/user/PID, resume/retry-failed flags, and
  start/end timestamps.
- **Result artifacts**: SHA256 and byte size of every output file, recorded
  in `run_manifest.json` after completion.

This closes the two provenance gaps a prior read-only audit of this project
found in the frozen pilot: (1) the pilot recovered no stdout/stderr log --
this harness always writes a persistent `tier1_run.log`; (2) the pilot could
only record a coarse dirty/clean flag for the simulator repository at
"freeze inspection" time, not the exact working-tree state at actual runtime
-- this harness saves the full tracked diff and untracked-file inventory at
the moment each run actually starts.

## Resume semantics

Tier 1 is small (230 executions, each a few tens of milliseconds to a few
seconds), so this harness deliberately does not build a distributed or
transactional execution engine -- durability is a single append-only JSONL
file (`run_results.jsonl`), one line per completed or failed execution,
flushed and `fsync`'d on every append.

- **Without `--resume`**: the target run directory must be new/empty. A
  non-empty existing directory is refused outright (`FileExistsError` from
  `new_run_dir`, or a `RuntimeError` from `run_production` if rows already
  exist in a directory passed explicitly via `--run-dir` without
  `--resume`).
- **With `--resume`**: run_keys already recorded as `complete` are skipped.
  Run_keys recorded as `failed` are **also skipped by default** -- a failed
  execution stays failed and visible; it is never silently retried just
  because `--resume` was passed.
- **With `--resume --retry-failed`**: previously `failed` run_keys become
  eligible to run again (an explicit, separate decision). `complete` keys
  are still skipped.
- A malformed or truncated JSONL line (e.g. from an interrupted write) is
  detected and ignored -- never treated as a complete result -- and reported
  as a warning; the line before it (if well-formed) is unaffected.
- If a run_key appears more than once in the file (e.g. a failed attempt
  followed by a successful retry), the **last** well-formed row for that key
  wins when the file is loaded.

## Validation semantics

`--validate --run-dir PATH` re-checks a completed (or partial) run directory
against every programmatic gate below, without re-executing anything. A run
is only ever reported `run_valid: true` if **every** gate passes **and**
all 230 planned executions are present with `status == "complete"` --
never on a partial run, and never merely because a script exited with
status 0.

Programmatic gates (`tier1_core.evaluate_gates`, translated from
`VALIDITY_GATES.md`):

- exact plan composition (230 executions; exact families/capacities/
  policies/seeds; no duplicate keys)
- no learned policy present anywhere in the results
- every result key is one of the planned keys
- every row has a recognizable status (`complete` or `failed`)
- scored windows match the authoritative matrix, and are identical across
  every policy within a given family/capacity cell
- `hits + misses == scored_requests` for every complete row
- no negative counts anywhere
- no NaN/Inf in any numeric output
- miss ratios in `[0, 1]`
- exactly one result per deterministic policy per cell
- exactly seeds 0..19 for the random policy per cell, when present
- failed rows are recorded and visible (not silently dropped)
- all 230 planned executions present with status `complete`

## Scope boundaries

This harness contains **no code path that can construct or invoke a
learned policy**. `tier1_core.assert_no_learned_policy()` is applied,
independently, at plan-build time, plan-validation time, and individual
policy-construction/execution time. `tier1_core.build_policy("evict_value_v1")`
raises immediately. Note: `lafc.runner.run_policy` (a required Tier-1
dependency -- it defines the `run_policy()` function every execution calls)
unconditionally imports `EvictValueV1Policy` and even constructs one default
instance into its own internal registry as an unavoidable module-import
side effect; that instance is never invoked with real data, and Tier 1's own
code path never reads from that registry -- it always passes a policy object
this module constructed itself directly into `run_policy(policy, requests,
pages, capacity)`. See the `NOTE` in `tier1_core._import_simulator_modules`
for the full explanation.

**Tier 2 (the gated `evict_value_v1` learned-policy demonstration) and
continuation-policy sensitivity are explicitly out of scope for this
harness and for Tier 1 generally.** Nothing here launches, prepares, or
partially implements either. Per the approved design, Tier 2 may only be
considered after Tier-1 results are validated and explicitly approved, and
continuation-policy sensitivity is a separate experiment entirely (it asks
how the *counterfactual labels themselves* would change under a different
continuation policy after a forced eviction -- a different question from
closed-loop replay, which this harness performs).

## Exact future launch procedure

**Not executed by this implementation task.** For a future, explicitly
approved launch:

```sh
tmux new-session -d -s lafc-tier1-<YYYYMMDD> \
  'cd /home/soroush/projects/lafc-evict-dataset/repo/.claude/worktrees/closed-loop-tier1-harness-20260913/analysis/closed_loop_production_tier1_20260913 && \
   python3 scripts/run_tier1.py --run 2>&1 | tee -a logs/tier1_run_$(date -u +%Y%m%dT%H%M%SZ).log'
```

- **tmux session name**: `lafc-tier1-<YYYYMMDD>`
- **Log path**: `logs/tier1_run_<UTC timestamp>.log` (the harness also
  writes its own `outputs/<RUN_ID>/tier1_run.log` independently; the tee
  above additionally captures the launcher shell's own stdout for a future
  agent inspecting from tmux)
- **Expected output directory**: `outputs/<RUN_ID>/` (created fresh by
  `run_production`, printed to stdout/log at start)
- **Progress inspection**: `tmux capture-pane -pt lafc-tier1-<YYYYMMDD> | tail -n 40`,
  or `wc -l outputs/<RUN_ID>/run_results.jsonl` (should climb toward 230)
- **Log tail**: `tail -n 100 -f outputs/<RUN_ID>/tier1_run.log`
- **Resuming an interrupted run**:
  `python3 scripts/run_tier1.py --run --run-dir outputs/<RUN_ID> --resume`
  (add `--retry-failed` only as an explicit, separate decision)
- **Validating a completed run**:
  `python3 scripts/run_tier1.py --validate --run-dir outputs/<RUN_ID>`

Per the operational rule for long-running scientific jobs: launch once in
the named tmux session with a persistent log, observe for approximately 3
minutes, confirm the process is alive and progressing with no immediate
error/OOM/missing-file failure, then detach without waiting for completion,
and never silently restart a failed job. `RUNTIME_ESTIMATE.md` estimates the
full 230-run Tier-1 matrix completes locally in well under 5 minutes, so a
3-minute observation window will likely span most or all of the run in
practice -- but detach rather than wait, since actual runtime could differ.

## Running the non-production checks yourself

```sh
cd analysis/closed_loop_production_tier1_20260913
python3 -m pytest tests/ -v          # unit + synthetic tests (no real trace I/O for execution)
python3 scripts/run_tier1.py --preflight   # non-destructive; reads real trace files only to verify SHA256
```

Neither command executes a real closed-loop replay against the production
matrix.
