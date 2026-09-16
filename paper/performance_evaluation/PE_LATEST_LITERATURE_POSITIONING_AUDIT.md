# PE Latest-Literature Positioning Audit (2026-09-16)

Scope: a focused literature-positioning pass on the Performance Evaluation
manuscript (`paper/performance_evaluation/latex/`), branch
`manuscript/pe-long-horizon-integration-20260916`. Goal: make the boundary
between LAFC-Evict and the closest 2021-2026 caching literature unmistakable
to a skeptical reviewer, without turning the paper into a survey and without
touching any scientific result.

## Starting point

Before this pass, `sections/10_related_work.tex` already contained a
carefully constructed positioning (evidently from an earlier session's work,
cross-referenced against `docs/PE_LITERATURE_SEARCH_GAPS.md`, which is dated
2026-09-14 and pre-dates several citations already present in the current
`refs.bib`): a dedicated "Positioning LAFC-Evict" subsection, an explicit
Cache-Coliseum distinction, an explicit HALP distinction, and a clean
disclaimer immediately followed by a positive contribution claim. A search
for dangerous novelty language (`first`, `novel`, `unique`, `unprecedented`,
`unlike previous`, `no prior work`, `state-of-the-art`, `comprehensive`,
`fundamentally different`, `the only`) across every section found no
overclaiming usage — all matches were either ordinal/idiomatic ("grounded in
a concrete example first") or precise technical findings ("no audited
decision has a strict unique winner"). This pass therefore made targeted
additions rather than a rewrite.

## Searches performed (this pass)

- `Cache-Coliseum OptiSys-ZJU benchmark learning-augmented caching Guard
  NeurIPS 2025` — confirmed via WebSearch that Cache-Coliseum was introduced
  by the same author group as the Guard/NeurIPS-2025 paper
  (`chen2025guard`), evaluated in that paper on BrightKite, Citi Bike, and
  SPEC CPU2006. This *validates* the manuscript's existing bundled citation
  `\cite{chen2025guard,cachecoliseumrepo}` for the sentence "Cache-Coliseum
  is a NeurIPS 2025 benchmark..." — it is not a citation error, contrary to
  an initial concern that prompted the search.
- `"Towards Optimal Robustness in Learning-Augmented Paging" arXiv 2606.01342`
  and a follow-up `... ICML 2026 proceedings PMLR` search, plus a direct
  `WebFetch` of `https://arxiv.org/abs/2606.01342` — confirmed exact title,
  full 5-author list (Peng Chen, Hailiang Zhao, Xueyan Tang, Yixuan Wang,
  Shuiguang Deng — the same group as `chen2025guard` minus one co-author),
  and that the paper's own arXiv "Comments" field states "ICML 2026". No
  independent PMLR volume/page record was located, so the manuscript cites
  the arXiv preprint (`chen2026robustpaging`), not a conference version with
  fabricated volume/page numbers, per the task's own instruction to omit
  unverified conference metadata.
- Direct `WebFetch` of the USENIX FAST '25 3L-Cache presentation page and
  the arXiv 3L-Cache summary already in the bib — confirmed 3L-Cache's
  specific contribution (efficient training-data collection, bidirectional
  sampling, parameter auto-tuning; ~61% CPU-cost reduction vs. HALP, ~95%
  vs. LRB) to write an accurate, non-inferred one-sentence distinction.
- Direct `WebFetch` of the LAH/S4-FIFO arXiv page (`arxiv.org/abs/2608.27975`,
  already cited as `xia2026lah`) — confirmed LAH learns cache-level
  parameters of a static heuristic (S3-FIFO, as S4-FIFO) via an asynchronous
  control-plane/data-plane split, distinct from per-object scoring, to write
  an accurate one-sentence distinction.

## Changes made

1. `refs.bib`: added `chen2026robustpaging` (arXiv:2606.01342), cited as a
   plain arXiv preprint (matching the existing house style for
   `yang2023mat`) — no conference proceedings metadata was fabricated.
2. `sections/10_related_work.tex`:
   - One new sentence distinguishing 3L-Cache from LAFC-Evict within the
     "Learned and Adaptive Cache Replacement" subsection (low-overhead
     per-object learned policy vs. reusable supervision artifact).
   - One new sentence distinguishing LAH/S4-FIFO from LAFC-Evict within
     "Heuristics and Learning-Augmented Caching" (cache-level parameter
     learning with control/data-plane split vs. no proposed controller at
     any granularity).
   - One new sentence adding `chen2026robustpaging` to the
     learning-augmented-theory cluster, stating precisely that LAFC-Evict
     supplies no robustness/competitive-ratio guarantee and asks a
     complementary question instead.
   - Cache-Coliseum and HALP distinctions were left untouched (already
     precise and well-supported).

## Comparison table: not added

A compact closest-work comparison table was evaluated (per the requesting
task's own "evaluate rather than blindly add" framing) and **not added**.
Reasoning: the manuscript's Related Work already carries the same
information as targeted, source-verified prose sentences immediately next
to each closest work, which the five-question reviewer self-test below shows
is independently sufficient; the document is float-dense enough that earlier
polish passes already fought table/figure drift with multiple explicit
`\clearpage` interventions (see comments in `main.tex`), and a new table
would add float-placement risk for a benefit the prose already delivers.

## Reviewer self-test (five questions, answerable from Introduction +
Related Work alone)

1. **Is this another cache eviction policy?** No — stated directly in the
   Introduction ("The contribution of this paper is not a new eviction
   policy") and restated in the Positioning subsection and Conclusion.
2. **How is it different from HALP?** HALP's preference signal is generated
   and consumed online by a deployed policy; LAFC-Evict's pairwise view is a
   static reformatting of already-materialized, model-agnostic finite-horizon
   labels (existing text, unchanged).
3. **How is it different from 3L-Cache/S4-FIFO?** 3L-Cache is a low-overhead
   per-object learned eviction policy; LAH/S4-FIFO learns cache-level
   heuristic parameters with a control/data-plane split. LAFC-Evict proposes
   no controller at either granularity — it exposes the counterfactual
   supervision such controllers could train or evaluate against (new text,
   this pass).
4. **How is it different from Cache-Coliseum?** Cache-Coliseum benchmarks
   algorithms against each other; LAFC-Evict supplies the labels an algorithm
   would train or evaluate against (existing text, unchanged, now
   corroborated as accurate by this pass's verification).
5. **How is it different from learning-augmented paging robustness work
   (Guard, the 2026 optimal-robustness result)?** That work supplies
   competitive-ratio/robustness guarantees for how an algorithm should use
   predictions; LAFC-Evict supplies no such guarantee and instead asks how
   reusable per-decision supervision can be constructed and characterized —
   a complementary, not competing, question (new text for the 2026 paper,
   this pass; Guard/Cache-Coliseum framing pre-existing).

All five are answerable within Introduction + Related Work without searching
the rest of the manuscript.

## What was explicitly not changed

No scientific numbers, H16/H32/H64/H128 results, closed-loop evidence,
`alibaba-block`/`cloudphysics` terminology, LFU claims, or manuscript
sections outside `sections/10_related_work.tex` and `refs.bib` were touched.
The active learned closed-loop Slurm campaign (jobs 1291048/1291049/1291050)
was not queried, referenced, or used in any way in this pass.

## Build/QA

`latexmk -pdf` succeeded with no errors and no new undefined/multiply-defined
references. Page count grew from 48 to 49 (the four new sentences plus one
new bibliography entry). Pages 34-37 (Related Work, Positioning, Conclusion)
and 48 (bibliography entry 42) were rendered to PNG and visually inspected:
clean justification, no clipping, no orphaned headings, correct arXiv-style
bibliography rendering matching the existing `yang2023mat` entry's format.
Every `\cite{...}` command in the manuscript was scanned for citation
density: none carries more than 4 distinct keys, satisfying the ≤4-distinct-
references-per-sentence rule.
