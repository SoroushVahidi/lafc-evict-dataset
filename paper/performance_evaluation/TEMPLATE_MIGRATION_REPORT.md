# LAFC-Evict: SIGMOD -> Performance Evaluation (Elsevier) template migration report

Date: 2026-09-13
Task type: mechanical template/format migration only (no scientific content changes)

## 0. Environment-blocker history (attempts 1-2) and resolution (attempt 3, this session)

Attempts 1 and 2 at this task hit a sandbox misconfiguration: the session was
permanently isolated to an unrelated concurrent worktree
(`closed-loop-pilot-20260913`) regardless of `EnterWorktree` calls, so no
mutating tool could write into the intended target worktree. The full
mechanical migration content was nonetheless authored and staged at
`/tmp/lafc_pe_migration_20260913/paper/performance_evaluation/` on the host,
with nothing committed and no compile/visual-inspection step possible from
that `/tmp` location (relative figure/`\input` paths only resolve correctly
inside a real `paper/` tree).

**This session (attempt 3)** was launched with `isolation: worktree`, which
provided a proper dedicated git worktree
(`.claude/worktrees/agent-a667cf3501eaf0ea3`, branch
`worktree-agent-a667cf3501eaf0ea3`) from the start -- confirmed via `pwd`,
`git branch --show-current`, and `git status` before any other action. The
sandbox issue from attempts 1-2 did not recur. Per the task's reuse
instructions, the attempt-2 staged tree at
`/tmp/lafc_pe_migration_20260913/paper/performance_evaluation/` was read in
full, spot-checked against the SIGMOD source (byte-identical `diff` on all
10 "unchanged" section files, all 8 table files, and `refs.bib`; targeted
`diff` review of `main.tex` and the two mechanically-edited section files
confirmed every hunk matches the documented mechanical changes and nothing
else), found sound, copied into this worktree at
`paper/performance_evaluation/`, then compiled and visually inspected from
here (Sections 11-12 below). No content was rewritten in this pass; this
section and Sections 11-14 were updated to reflect the successful
copy/compile/inspect/commit that attempts 1-2 could not perform.

**Toolchain note:** this host's `latexmk` on `PATH`
(`~/.local/bin/latexmk`) is a thin shim around `tectonic`, not real
`latexmk`/TeX Live `latexmk`. `elsarticle.cls` and the `elsarticle-num.bst`
bibliography style were **not** present in the base TeX Live install and had
to be installed via `sudo apt-get install -y texlive-publishers` (Ubuntu's
package containing Elsevier's `elsarticle` bundle) before compilation
succeeded -- see Section 11.

## 1. Source manuscript

- Source: `paper/sigmod2027/latex/main.tex` + `paper/sigmod2027/latex/sections/*.tex` +
  `paper/sigmod2027/latex/tables/*.tex` + `paper/sigmod2027/latex/refs.bib` +
  `paper/64BDAA68-CBD4-4E8E-800B-467D62C0D9DE.png` (pipeline figure).
- Last commit touching `paper/sigmod2027/` (`git log -1 -- paper/sigmod2027/`,
  run in this session): `1e6796aacdd320887ea3a905d15bfa1e64cb5745`
  ("Polish SIGMOD related work with latest cache references", 2026-07-03).
  (Attempt 2's report cited the then-current worktree HEAD,
  `76d562f9...`, as an upper bound since `git log` could not be run under
  that attempt's sandbox blocker; this session re-ran the actual query.)
- `paper/sigmod2027/` was **not modified** in any way.

## 2. Target journal / publisher

- Journal: **Performance Evaluation** (Elsevier, ISSN 0166-5316)
- Publisher: Elsevier

## 3. Official guidance consulted (2026-09-13)

- ScienceDirect "Guide for authors" listing for Performance Evaluation:
  `https://www.sciencedirect.com/journal/performance-evaluation/publish/guide-for-authors`
  (direct fetch returned HTTP 403; content below obtained via web search
  snippets of this exact page, cross-checked against Elsevier's general
  LaTeX/policy pages)
  - LaTeX class: **elsarticle.cls** (Elsevier's own class, recommended).
  - Bibliography style: **elsarticle-num**.
  - **Highlights are mandatory**: 3-5 bullet points, max 85 characters
    (incl. spaces) each, capturing study novelty.
  - Graphical abstract: described generically (dimensions, format) but not
    stated as mandatory for this specific journal in the retrieved snippet.
- Elsevier "LaTeX instructions for authors":
  `https://www.elsevier.com/researcher/author/policies-and-guidelines/latex-instructions`
  - Confirms elsarticle.cls is current ("The Elsevier article class helps
    you to format the frontmatter... part of the elsarticle package").
  - Bibliography style is journal-specific; check each journal's guide.
  - All submission files/figures/bib/style files must sit at the same
    folder level (no subfolders) for the final Elsevier submission bundle
    (noted as a TODO for final submission packaging; this template keeps a
    `sections/`/`tables/` subfolder layout matching the SIGMOD source for
    now, see "Remaining template TODOs").
- Elsevier CRediT author statement policy:
  `https://www.elsevier.com/researcher/author/policies-and-guidelines/credit-author-statement`
  - Lists the 14 standard CRediT roles used to build the CRediT statement in
    `main.tex`.
- Elsevier data statement guidance:
  `https://www.elsevier.com/researcher/author/tools-and-resources/research-data/data-statement`
- Elsevier declaration-of-interest / competing-interest guidance (Elsevier
  Declaration Tool, `https://declarations.elsevier.com/`, and
  `https://www.elsevier.support/publishing/answer/what-are-conflict-of-interest-statements-funding-source-declarations-author-agreementsdeclarations-and-permission-notes`).
- Elsevier graphical abstract guidance:
  `https://www.elsevier.com/researcher/author/tools-and-resources/graphical-abstract`
  (dimensions: min 1328x531 px at 300 dpi; TIFF/EPS/PDF/MS-Office preferred;
  described as increasingly requested, not universally mandatory).
- Elsevier generative-AI-in-writing disclosure policy (policy updated
  2026-06): `https://www.elsevier.com/about/policies/publishing-ethics/the-use-of-ai-and-ai-assisted-writing-technologies-in-scientific-writing`
  - Mandatory disclosure statement, in a section titled **"Declaration of
    Generative AI and AI-assisted technologies in the writing process"**,
    placed immediately before the References list. AI tools must not be
    listed as authors.

## 4. LaTeX class / bibliography style chosen

- `\documentclass[preprint,12pt]{elsarticle}` (elsarticle.cls, "preprint"
  layout option -- single column, suitable for an initial-submission/working
  PDF; the journal's production system will apply final Elsevier typesetting
  after acceptance).
- `\bibliographystyle{elsarticle-num}` with the existing `refs.bib` unchanged.

## 5. New manuscript tree created (now committed at `paper/performance_evaluation/` in this worktree; originally staged at `/tmp/lafc_pe_migration_20260913/` by attempt 2, see Section 0)

```
paper/performance_evaluation/
  TEMPLATE_MIGRATION_REPORT.md      (this file)
  TODO_SIGMOD_REVISIONS.md          (deferred citation-issue notes)
  latex/
    main.tex
    highlights.tex                 (separate file; NOT \input by main.tex -- see file header)
    refs.bib                        (byte-identical copy of the SIGMOD .bib)
    sections/
      01_introduction.tex           (unchanged)
      02_background.tex             (unchanged)
      03_benchmark_design.tex       (figure* -> figure, \Description removed, see Section 6)
      04_label_generation.tex       (unchanged)
      05_schema_views.tex           (unchanged)
      06_release_validation.tex     (unchanged)
      07_tasks_baselines.tex        (unchanged)
      08_characterization.tex       (unchanged)
      09_limitations_ethics.tex     (unchanged)
      10_related_work.tex           (unchanged)
      11_conclusion.tex             (unchanged)
      12_ai_use_disclosure.tex      (heading retitled to Elsevier's mandated
                                      wording; body text unchanged)
    tables/
      table_dataset_scale.tex             (unchanged)
      table_split_counts.tex              (unchanged)
      table_artifact_layout.tex           (unchanged)
      table_pairwise_sample_stats.tex     (unchanged)
      table_pairwise_feature_baselines.tex(unchanged)
      table_decision_breakdown.tex        (unchanged)
      table_candidate_count_stats.tex     (unchanged)
      table_regret_tie_stats.tex          (unchanged)
```

The figure (`64BDAA68-CBD4-4E8E-800B-467D62C0D9DE.png`) is **referenced**,
not copied: `sections/03_benchmark_design.tex` points at
`../../64BDAA68-CBD4-4E8E-800B-467D62C0D9DE.png`, i.e. the original file
under `paper/` (one level up from both `sigmod2027/latex/` and
`performance_evaluation/latex/`, so the same relative path works from
either tree). This avoids a binary duplicate/possible drift and keeps a
single source of truth; the task brief explicitly allows "figures/tables
copied or referenced."

## 6. Mechanical changes made (format only)

1. **Document class**: `\documentclass[sigconf,anonymous,nonacm]{acmart}` ->
   `\documentclass[preprint,12pt]{elsarticle}` + `\journal{Performance
   Evaluation}`.
2. **Removed ACM-only frontmatter macros** (no elsarticle equivalent, purely
   ACM production metadata): `\settopmatter{printacmref=false}`,
   `\renewcommand\footnotetextcopyrightpermission{...}`, `\pagestyle{plain}`,
   `\acmConference[]{}{}{}`, `\acmBooktitle{}`, `\acmPrice{}`, `\acmDOI{}`,
   `\acmISBN{}`.
3. **Removed ACM CCS concepts** (`\ccsdesc[500]{...}`, `\ccsdesc[300]{...}`)
   -- no direct Elsevier/elsarticle equivalent; keywords are preserved.
4. **Author/affiliation**: `\author{Anonymous Authors}` (SIGMOD
   double-blind placeholder) replaced with real author/affiliation metadata
   from the repository's own `CITATION.cff` (Soroush Vahidi, New Jersey
   Institute of Technology; corresponding email `sv96@njit.edu`, matching
   the session's known user identity). No author metadata was invented --
   `CITATION.cff` is the only in-repo source of truth for this, and it lists
   exactly one author, so no co-authors were assumed or added.
5. **Title**: dropped the SIGMOD/VLDB "Experiments & Analysis" track-label
   suffix (`\texorpdfstring{[Experiments \& Analysis]}{...}`) as a
   venue-specific submission-track label inapplicable outside that track --
   this is a formatting/venue artifact, not a scientific title change. Core
   title text is otherwise unchanged.
6. **Abstract, keywords**: copied verbatim; `\begin{keyword}...\end{keyword}`
   (elsarticle syntax with `\sep`) replaces ACM's `\keywords{...}`.
7. **Frontmatter wrapping**: title/author/affiliation/abstract/keywords
   wrapped in elsarticle's `\begin{frontmatter}...\end{frontmatter}`;
   `\maketitle` removed (elsarticle's frontmatter environment renders it).
8. **Figure environment** (`sections/03_benchmark_design.tex`): ACM's
   two-column-only `figure*` environment changed to plain `figure` (single
   column is elsarticle's default preprint layout; `figure*` is only valid
   under a twocolumn class option and would be an undefined environment
   otherwise). ACM's accessibility macro `\Description{...}` (alt-text for
   ACM's production pipeline; not defined by elsarticle) was removed from
   the compiled output but its text is preserved verbatim as a LaTeX comment
   in the same file for future accessibility reuse. Caption, label, and
   image content are unchanged.
9. **Bibliography**: `\bibliographystyle{ACM-Reference-Format}` ->
   `\bibliographystyle{elsarticle-num}`; `refs.bib` copied byte-for-byte,
   zero entries added, removed, or edited.
10. **AI-use disclosure section** (`sections/12_ai_use_disclosure.tex`):
    heading changed from `\section*{Use of Generative AI Tools}` to
    Elsevier's mandated `\section*{Declaration of Generative AI and
    AI-assisted technologies in the writing process}`. Body text is
    unchanged. Placement (immediately before the bibliography) already
    matched Elsevier's "immediately before References" requirement.
11. **New end-of-manuscript declarations added** to `main.tex` (Elsevier
    requirements with no ACM analogue -- see Section 7 for what is/isn't
    filled in): Declaration of competing interest, Data availability,
    Funding, CRediT authorship contribution statement.
    A non-declaration Acknowledgments section was subsequently added before
    these declarations using verified advisor and research-support
    information supplied for this Performance Evaluation manuscript.
12. **New `highlights.tex`** added (mandatory per journal guide; kept as a
    separate un-\input'd file matching Elsevier's separate-file submission
    workflow for Highlights; see its header comment).

No section body prose, equation, table content/numbers, or bibliography
entry text was altered anywhere in this migration.

## 7. End-matter status

| End-matter item | Status |
|---|---|
| Acknowledgments | **Filled in** with verified advisor and support acknowledgments: Prof. Ioannis (Yiannis) Koutis; Google Cloud Research Credits Program; Cohere Labs Catalyst Grant Program (`$1,000` in API credits); CloudRift AI Builder Grant (1,000 credits); and AWS Open Data Sponsorship Program hosting support (up to 600 GB for two years). |
| Declaration of competing interest | **TODO placeholder** (source comment only, nothing fabricated, nothing visible in rendered PDF). No competing-interest info exists anywhere in the source manuscript/repo metadata. |
| Data availability | **Filled in** with factual, already-public repo metadata (GitHub repo URL + Zenodo concept DOI + CC0-1.0 license, all sourced from `CITATION.cff`), with a TODO comment to reconfirm final hosting/DOI status at actual submission time (mirroring a caveat the manuscript itself already states in Section~6/`release-validation`). |
| Funding | **Filled in** with verified computing/API-credit support from Google Cloud Research Credits Program, Cohere Labs Catalyst Grant Program (`$1,000` in API credits), and CloudRift AI Builder Grant (1,000 credits), plus AWS Open Data Sponsorship Program public dataset hosting support (up to 600 GB for two years). |
| CRediT authorship contribution statement | **Filled in** with a standard sole-author default (all roles attributed to Soroush Vahidi, the only author in `CITATION.cff`), flagged in a source comment as auto-generated and requiring author confirmation before submission. |
| AI-assisted-writing disclosure | **Filled in** -- reused the SIGMOD manuscript's existing, already-accurate AI-use disclosure text under Elsevier's mandated section title. |

## 8. Highlights / Graphical Abstract

- **Highlights: required** for this journal per the guide-for-authors
  snippet retrieved. `paper/performance_evaluation/latex/highlights.tex`
  contains 5 bullets (all <= 85 characters), each derived directly and
  conservatively from existing abstract/results sentences with no new
  claims:
  1. "LAFC-Evict is a benchmark for decision-aligned cache-eviction supervision." (74 chars)
  2. "Each row is one candidate victim's finite-horizon counterfactual y_loss label." (78 chars)
  3. "Open release covers 278M candidate rows across five trace families." (67 chars)
  4. "A linear value-regression baseline is intentionally weak (test R2 0.0026)." (74 chars)
  5. "Logistic pairwise baseline reaches 0.9660 accuracy on non-tie samples." (70 chars)
- **Graphical abstract: not confirmed mandatory** for this specific journal
  from the guidance retrieved (only Highlights were explicitly stated as
  mandatory; the graphical-abstract page describes growing adoption and
  technical specs but not a hard requirement for Performance Evaluation
  specifically). Per the task's own instruction ("don't invent one if
  optional and not asked for"), **no graphical abstract file was created**.
  If the author later decides to submit one, the existing pipeline figure
  (`64BDAA68-CBD4-4E8E-800B-467D62C0D9DE.png`) is a reasonable starting
  point since it already visually summarizes the pipeline/contribution, but
  turning it into a proper graphical abstract (correct aspect ratio/DPI,
  "designed to appeal to an interdisciplinary audience") is a design task,
  not a mechanical one, and was intentionally left undone here.

## 9. Content-preservation audit (source SIGMOD vs. new template)

| Item | SIGMOD source | PE template | Match |
|---|---|---|---|
| Numbered sections | 11 (`\section{...}`) | 11 | Yes |
| Unnumbered sections | 1 (AI-use disclosure) | 1 (retitled per Elsevier policy) + 4 new Elsevier-required declaration sections (competing interest, data availability, funding, CRediT) | Content sections match 1:1; declaration sections are new administrative additions required by the target venue, not scientific content |
| Figures | 1 (`fig:pipeline`) | 1 (same file, referenced not copied) | Yes |
| Tables | 10 (`tab:dataset-scale`, `tab:split-counts`, `tab:schema-summary`, `tab:artifact-layout`, `tab:pairwise-sample-stats`, `tab:pairwise-feature-baselines`, `tab:task-definitions`, `tab:decision-breakdown`, `tab:candidate-count-stats`, `tab:label-selection-summary`) | 10, identical labels/captions/numbers | Yes |
| Bibliography entries | 44 (`refs.bib`) | 44, byte-identical file | Yes |
| Algorithms (`algorithm`/`algorithmic` envs) | 0 | 0 | Yes (none in source) |
| Appendices | 0 (`\appendix` not used) | 0 | Yes (none in source) |
| Equations | 3 displayed equations (`L_{t,H}^\pi(c)` definition, `C_t^\star` argmin, `\Delta_{t,H}^\pi(c)` regret) in Section 4 | Same 3, verbatim | Yes |
| Substantive text changes | -- | **Zero.** All prose, numbers, claims, captions, and equation content are copied verbatim. Only class-specific wrapper macros, the figure environment name, the AI-disclosure heading, and the title's track-label suffix were touched, all documented in Section 6 above. | -- |

## 10. Bibliography

`refs.bib` was copied unchanged (44 entries, same as source). Bibliography
style switched from `ACM-Reference-Format` to `elsarticle-num` only. See
`TODO_SIGMOD_REVISIONS.md` for a possible author-name issue noticed in the
`vietri2018lecar` entry ("Martinez, William A." vs. likely correct "Martinez,
Wendy A.") and one unused bib entry (`narita2019efficient`) -- neither was
fixed here per the task's explicit "no citation-content cleanup" scope.

## 11. Compile status

**PASS**, run from this worktree (`agent-a667cf3501eaf0ea3`):

```sh
sudo apt-get install -y texlive-publishers   # provides elsarticle.cls, elsarticle-num.bst (one-time)
cd paper/performance_evaluation/latex
latexmk -pdf -interaction=nonstopmode -halt-on-error -output-directory=/tmp/pe_build main.tex
```

Notes:
- `elsarticle.cls` / `elsarticle-num.bst` were not present in the base
  TeX Live install on this host and were installed via the `texlive-publishers`
  Ubuntu package (contains Elsevier's `elsarticle` bundle). `kpsewhich
  elsarticle.cls` / `elsarticle-num.bst` confirmed presence afterwards.
- This host's `latexmk` shim (`~/.local/bin/latexmk`) wraps `tectonic`, which
  does not honor `-output-directory=`/`-halt-on-error` the way real
  `latexmk` does (it only recognizes its own `-outdir=` flag); the compiled
  `main.pdf` therefore landed in `paper/performance_evaluation/latex/`
  alongside the sources (the same convention already used by the committed
  `paper/sigmod2027/latex/main.pdf`), not in `/tmp/pe_build`. Result:
  `paper/performance_evaluation/latex/main.pdf`, 27 pages, 1.3 MB after
  the acknowledgments/funding-support update, built
  cleanly through TeX + BibTeX + a second TeX pass (tectonic's internal
  engine sequence) with exit code 0.
- Confirmed via `pdftotext`/`pdfinfo`: correct title/author metadata, zero
  `[?]` undefined-citation markers, bibliography numbering runs to `[42]`
  (identical max citation index as the already-compiled
  `paper/sigmod2027/latex/main.pdf`), confirming citation-level parity with
  the frozen SIGMOD PDF.

**Unresolved (harmless) warnings:**
- 3 `Overfull \hbox` warnings (main.tex:84 in the output routine;
  `05_schema_views.tex:5`; `07_tasks_baselines.tex:14`, worst case
  ~44pt too wide) -- minor single-column line-width overflows from
  `preprint,12pt` layout being narrower than ACM's two-column layout; content
  unaffected, cosmetic only.
- Several `Underfull \hbox (badness ...)` warnings inside `main.bbl`
  (bibliography entries with long URLs/DOIs) -- standard `elsarticle-num`
  bibliography line-breaking, harmless.

## 12. Visual inspection

**PASS.** Performed by rendering all 26 pages to PNG (`pdftoppm -r 100`) and
reading them, plus full-text extraction (`pdftotext -layout`) for targeted
checks. Verified:
- **Frontmatter** (page 1): title, `Soroush Vahidi` with NJIT affiliation and
  corresponding-author email, abstract, keywords -- all render correctly in
  `elsarticle`'s single-column preprint style; running footer correctly
  reads "Preprint submitted to Performance Evaluation" with today's date.
- **Section hierarchy**: numbered sections 1-11 render in order with correct
  numbering; no stray ACM/SIGMOD headers.
- **Figure** (page 6): the pipeline diagram renders at full text width with
  its caption and label intact, single-column (`figure`, not `figure*`).
- **Tables**: spot-checked Table 1 (dataset scale), Table 4 (release-package
  layout, page 10) -- render with `booktabs` rules identical to the SIGMOD
  originals.
- **Equations** (page 8): the three displayed equations (loss-label
  definition, `C_t^\star` argmin, regret `\Delta`) render correctly with
  proper numbering/spacing.
- **Citations/bibliography**: in-text citations resolve (no `[?]`); reference
  list renders in `elsarticle-num` numeric style, ending at `[42]`, matching
  the SIGMOD PDF's citation count exactly.
- **Acknowledgments/declarations** (pages 20-21): "Acknowledgments" and
  "Funding" render with verified support text (Section 7). "Declaration of
  competing interest" remains an intentionally unfilled `\relax`-only TODO
  placeholder with no visible stray text. "Data availability" and "CRediT
  authorship contribution statement" render with their intended body text.
  The "Declaration of Generative AI..." section (page 21) immediately
  precedes "References", per Elsevier's placement requirement.
- **No ACM/SIGMOD branding or anonymous-review artifacts**: full-text search
  for "ACM", "anonymous", "SIGMOD", "double-blind", "CCS concept" across the
  whole PDF returns only legitimate bibliography entries citing papers
  published at ACM-sponsored venues (e.g., "Proceedings of the ACM...") --
  no leftover ACM production macros, conference metadata, or review-process
  artifacts.

## 13. Scientific / reviewer-driven changes explicitly deferred (NOT done here)

- No SIGMOD reviewer feedback was applied (none was in scope).
- The possible `vietri2018lecar` author-name issue (`TODO_SIGMOD_REVISIONS.md`).
- The unused `narita2019efficient` bib entry (`TODO_SIGMOD_REVISIONS.md`).
- Any closed-loop cache-policy pilot results (that experiment is unrelated,
  running in a different worktree, and was not touched or referenced).
- No new results, numbers, figures, or claims were added anywhere.

## 14. Remaining template TODOs

- ~~Copy the staged tree from `/tmp/lafc_pe_migration_20260913/` into the real
  worktree, compile, visually inspect, and commit~~ -- **done in this
  session** (Section 0, 11, 12).
- Consider adding a small `\vspace` / comment-out for the currently-empty
  `\section*{Declaration of competing interest}` heading once its real
  content is known, purely to avoid a bold heading with no body paragraph
  (Section 12) -- cosmetic only, not required for a working draft.
- Fill in "Declaration of competing interest" before submission (currently a
  TODO placeholder, nothing visible in the PDF).
- Confirm the CRediT statement and data-availability wording before
  submission (both flagged with source comments).
- Confirm co-author list / ORCID / grant numbers are complete (only
  `CITATION.cff`'s single author was available).
- Decide on `\documentclass[preprint,12pt]{elsarticle}` vs. `[review]` (line
  numbers) vs. no options, per the author's preferred draft/review workflow.
- Elsevier's final submission bundle wants all files at the same folder
  level (no subfolders); this template keeps the SIGMOD source's
  `sections/`/`tables/` subfolder layout for now, which is fine for
  authoring/compiling but should be flattened (or the multi-file
  `.tex`/`.bib`/figure bundle assembled per Elsevier's exact submission
  instructions) at actual submission time.
- Decide whether to produce a Graphical Abstract (optional per guidance
  retrieved; not created here, see Section 8).
- Resolve the two `TODO_SIGMOD_REVISIONS.md` items in a separate, explicitly
  scientific/citation-focused pass.
