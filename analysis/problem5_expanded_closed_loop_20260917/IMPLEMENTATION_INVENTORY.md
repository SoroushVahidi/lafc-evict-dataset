# Problem 5 Phase 1: implementation inventory

Date: 2026-09-17

## Existing Tier-1 harness and protocol

The exact production closed-loop protocol the manuscript reports (Table
`tab:tier1-closed-loop`, Section 8b) is implemented at:

- `analysis/closed_loop_production_tier1_20260913/scripts/tier1_core.py`
  (reachable at commit `8a4cd32402a1c053af5db17c26cf05ee88842d8c`, present
  unmodified in the current worktree; its originating branch
  `experiment/closed-loop-tier1-harness-20260913` was deleted after merge but
  the commit is reachable from `master`/this branch).
- Frozen production evidence:
  `analysis/closed_loop_tier1_evidence_20260914/` (`EVIDENCE_MANIFEST.json`,
  run id `20260914T023445Z_8a4cd32402a1`).

Protocol facts confirmed by reading `tier1_core.py` directly (not assumed):

- 5 families x 2 capacities (32, 128) x {LRU, MRU, SIEVE, random x20 seeds}
  = 230 executions.
- Policy interface: `lafc.policies.base.BasePolicy` (`reset(capacity, pages)`,
  `on_request(request) -> CacheEvent`), driven by
  `lafc.runner.run_policy.run_policy(policy, requests, pages, capacity)` in
  the `augmented-caching` simulator repo.
- Unit-object semantics: `build_requests_from_lists` assigns every page a
  weight of exactly `1.0`; capacity is a page *count*, not a byte budget.
- Simulator dependency files are gated to an exact expected commit
  (`chore/repository-polish` @ `ceb36705b59d0d16db55d0fc0bfb63a5c7a2a6a1`);
  this branch/commit still exists in `augmented-caching`.
- MRU and random are *not* in the simulator repo; by design (per
  `DESIGN.md`, quoted in `tier1_core.py`) they are carried as harness-local
  `BasePolicy` subclasses in the analysis script, not added to simulator
  `src/`. Problem 5 follows the same convention for the new policies below,
  so the simulator's gated dependency files stay byte-identical.
- Scored windows/capacities/families are exact, hardcoded, and independently
  self-checked against `MATRIX.md` in `run_preflight()`.

## Candidate policy search

Searched both repositories (`augmented-caching`, all worktrees; `lafc-evict-dataset`)
for existing implementations, and checked for an installable reference
library.

| Policy | Existing impl? | Source/provenance | License | Unit-object compatible | Unconditional-admission compatible | Deterministic | Already tested | Practical cost |
|---|---|---|---|---|---|---|---|---|
| ARC | NO in-repo | `libcachesim` (`cacheMon/libCacheSim-python`, PyPI `libcachesim==0.3.5`, C core via pybind11) | GPL-3.0-or-later | Yes (`obj_size=1`) | Yes (no admissioner set -> always admits) | Yes | Upstream project has its own test suite; independently smoke/cross-checked here (Phase 3) | Low: thin wrapper, `.get(req)` per-request API matches `on_request` exactly |
| LIRS | NO in-repo | `libcachesim` | GPL-3.0-or-later | Yes | Yes | Yes | Same as above | Low |
| S3-FIFO | NO in-repo | `libcachesim` (same project that published the S3-FIFO paper/algorithm; cited in the manuscript already as `zhang2024sieve`'s sibling work) | GPL-3.0-or-later | Yes | Yes (default ratios `small_size_ratio=0.1`, `ghost_size_ratio=0.9`, `move_to_main_threshold=2`, i.e. paper defaults, no tuning) | Yes | Same as above | Low |
| W-TinyLFU | NO in-repo | `libcachesim` (`WTinyLFU` class: built-in TinyLFU admission sketch + segmented-LRU main cache, fully bundled, no separate admission wiring needed) | GPL-3.0-or-later | Yes | Bundled admission is part of the algorithm's own design, not an ad hoc addition | Yes | Same as above | Low |
| LFU | YES | `augmented-caching` `src/lafc/policies/lfu.py` (`LFUPolicy`), added for the PE Tier-2/learned closed-loop work, has passing regression tests (`tests/test_lfu.py`, 2026-09-16 gate-fix pass) | Project's own (matches simulator repo license) | Yes | Yes | Yes | Yes (16/16 relevant tests passed 2026-09-16) | Not selected as a Problem-5 addition: already validated but not part of the pre-registered set (see `COMPARATOR_PROTOCOL.md`) -- kept as a documented, already-available option if a future problem wants it |
| CLOCK / CLOCK-Pro | NO in-repo | `libcachesim` (`Clock`, `ClockPro` classes exist) | GPL-3.0-or-later | Yes | Yes | Yes | Upstream only | Not selected (see protocol: three FIFO/adaptive/frequency families already give broad, non-redundant coverage; CLOCK is a low-overhead LRU approximation and would add limited new signal beyond LRU+ARC+S3-FIFO in a *small* representative set) |
| TinyLFU (plain, no W-) | NO in-repo | Not exposed as a standalone class in `libcachesim` (`WTinyLFU` bundles it with an SLRU main cache) | n/a | n/a | n/a | n/a | n/a | Not applicable: W-TinyLFU is the form this library validates and exposes |

## libCacheSim decision

`libcachesim` (PyPI `libcachesim==0.3.5`, upstream `cacheMon/libCacheSim` /
`cacheMon/libCacheSim-python`) is a maintained, published reference
simulator from the same research lineage as SIEVE (`zhang2024sieve`,
already cited and used as a Tier-1 policy in this manuscript) and S3-FIFO.
It exposes `ARC`, `LIRS`, `S3FIFO`, `WTinyLFU`, `Clock`, `ClockPro`, `LFU`,
`FIFO`, `Random`, and others as direct Python classes with a per-request
`get(req) -> bool` method -- i.e. exactly the stateful, one-request-at-a-time
interface `BasePolicy.on_request` needs, with no batch-only trace-replay
API forcing a redesign of the harness. License is GPL-3.0-or-later: used
here only as an evaluation dependency invoked by an analysis script (not
statically linked into or redistributed as part of a combined proprietary
work), which is standard practice for reproducible research code and
consistent with this manuscript's own use of the SIEVE reference algorithm.

Decision: reuse `libcachesim`'s ARC, LIRS, and S3-FIFO as the three primary
additions, plus W-TinyLFU as the optional fourth (admission semantics are
fully bundled in the library's own `WTinyLFU` class, so no ad hoc admission
wiring is needed to make it "fair" under this protocol). Do not reimplement
these from scratch: reimplementing ARC/LIRS/S3-FIFO/W-TinyLFU correctly from
their papers would be strictly higher-risk (silent correctness bugs) for zero
scientific benefit over reusing the reference implementation from the field's
own dominant simulator, which is separately smoke- and cross-validated in
Phase 3 rather than trusted blindly.
