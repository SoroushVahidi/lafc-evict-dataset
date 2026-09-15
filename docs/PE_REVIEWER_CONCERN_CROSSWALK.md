# Reviewer Concern Crosswalk (Performance Evaluation submission)

Status: **RE-AUDITED 2026-09-15** against the current manuscript at
`manuscript/pe-evidence-restructure-20260914` (HEAD `ac63bd7` plus the
final-audit fixes committed alongside this update). This supersedes the
2026-09-14 version of this document, which explicitly flagged itself as
stale pending exactly this re-audit ("A full re-audit of this table
against the current manuscript state is recommended before submission").

Classification scheme (per the PE final submission audit):
- **CLOSED** — resolved with no remaining scope caveat needed in the text.
- **CLOSED_WITH_SCOPE_LIMITATION** — resolved, and the manuscript
  correctly states the scope/limitation rather than overclaiming.
- **PARTIALLY_CLOSED** — evidence exists and the core concern is met, but
  a nice-to-have manuscript-side improvement remains (not submission-blocking).
- **STILL_OPEN** — not resolved.

| # | Concern | Classification | Evidence / manuscript location | Remaining action |
|---|---|---|---|---|
| 1 | Contribution clarity / terminology | CLOSED | `sections/01_introduction.tex` states RQ1-RQ5 explicitly and an explicit "the contribution is NOT a new eviction policy" statement; no leftover central-narrative jargon found. | None. |
| 2 | Insufficient meaningful evaluation | CLOSED | Tier-1 closed-loop (230/230 runs) and offline↔closed-loop linkage results are integrated into main text (`sections/08b_closed_loop.tex`, `sections/08c_linkage.tex`), not merely planned. | None. |
| 3 | Target degeneracy | CLOSED_WITH_SCOPE_LIMITATION | Framed throughout as "informative where discriminative, degenerate elsewhere" (`sections/08_characterization.tex`, `sections/09_limitations_ethics.tex` ¶3); wiki2018 negative control explicitly discussed, not hidden. | None. |
| 4 | Offline↔closed-loop validity | CLOSED_WITH_SCOPE_LIMITATION | `sections/08c_linkage.tex` states the bounded finding with the two named exceptions (cloudphysics/cap32, metakv/cap128); no universal-validity claim. | None. |
| 5 | Continuation-policy dependence | CLOSED_WITH_SCOPE_LIMITATION | `sections/09_limitations_ethics.tex` ¶2 and `sections/08e_continuation.tex`/Figure 5 caption both state the exact scope: sampled MRU/random at capacities 32/128 only, full-population MRU census at capacities 32/64/128/256, no population-scale random claim, no arbitrary-continuation-policy claim. | None. |
| 6 | Narrow cache abstraction | CLOSED_WITH_SCOPE_LIMITATION | `sections/09_limitations_ethics.tex` ¶4 states unit-object/count-capacity model, unconditional admission, no byte/latency/dirty-write cost. This is a genuine, non-fixable scope limitation of the benchmark design, not a writing gap. | None (would require new label generation to broaden — out of scope, correctly not attempted). |
| 7 | Worked example | CLOSED | Figure 1 (`figures/figure1_worked_example.pdf`) is included via `\includegraphics` in `sections/02_background.tex` (`\label{fig:worked-example}`), referenced from the Introduction and methodology sections, and covers cache state/candidates/forced eviction/admission/horizon/y_loss/tie/optimal set. Prior "not yet inserted" status in this document was stale. | None (caption itself is terse; the full explanation is in adjacent prose — a caption expansion would be a nice-to-have, not required). |
| 8 | Related work | CLOSED_WITH_SCOPE_LIMITATION | `sections/10_related_work.tex` is a comprehensive 6-subsection restructuring; §10.5 explicitly discloses the cross-domain offline-vs-online literature search is "only partially complete," pointing to `PE_LITERATURE_SEARCH_GAPS.md`. Honest hedging, not overclaiming. | None required for submission (see Phase 6 literature decision below — no additions needed). |
| 9 | Artifact completeness | PARTIALLY_CLOSED | Every evidence artifact (Tier-1, linkage, mechanistic, continuation) is independently gate-validated and byte-verified, and each figure/table cites its generating `analysis/...` path in-text. | No single consolidated "reproducibility map" paragraph exists; a careful reviewer can still trace every number via the in-text paths already given. Nice-to-have, not blocking. |
| 10 | Artifact completeness (release side) | CLOSED_WITH_SCOPE_LIMITATION | Public v0.3 wiki2018-only scope vs. canonical dataset distinction is stated in `sections/06_release_validation.tex`/`09_limitations_ethics.tex`. | None for this manuscript (release-engineering item, not a writing gap). |
| 11 | Pairwise view justification | CLOSED | `sections/02_background.tex` explicitly states the pairwise view introduces no new ground truth; canonical regenerated sample cited by SHA-256 prefix in `sections/07_tasks_baselines.tex` and verified (live hash matches) against the tracked artifact — no stale historical sample is cited. | None. |
| 12 | y_loss/y_value redundancy | CLOSED | Canonical `y_loss` + documented alias `y_value = -y_loss` applied consistently in `sections/01_introduction.tex` and `sections/07_tasks_baselines.tex`. | None. |
| 13 | Figures/tables | CLOSED | All 5 figures and 10 tables exist, are built from cited source artifacts, and are `\input`/`\includegraphics`'d into the manuscript. `\ref{}` cross-references were added in the final audit for the two main tables that previously lacked one (`tab:tier1-closed-loop`, `tab:linkage-continuation-summary`). | None. |
| 14 | Citation correctness | CLOSED | 0 undefined citations (independently re-verified against `refs.bib`); LeCaR "Wendy A. Martinez" confirmed correct; one bibliography name-consistency fix applied in the final audit (S3-FIFO entry's "Rashmi, K. V." now matches the other 4 entries by the same author, was "Vinayak, Rashmi"). | None. |

## Summary counts (2026-09-15 re-audit)

Across the 14 rows: **CLOSED = 7** (#1, #2, #7, #11, #12, #13, #14), **CLOSED_WITH_SCOPE_LIMITATION = 6** (#3, #4, #5, #6, #8, #10), **PARTIALLY_CLOSED = 1** (#9), **STILL_OPEN = 0**.

No prior SIGMOD reviewer concern remains STILL_OPEN. The one PARTIALLY_CLOSED item (artifact completeness / consolidated reproducibility narrative) is a documentation nicety, not a submission blocker, since every number in the manuscript already carries an in-text pointer to its generating `analysis/` artifact.
