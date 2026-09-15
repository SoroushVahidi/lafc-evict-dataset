# Performance Evaluation (Elsevier) submission-requirements audit

Date compiled: 2026-09-15
Journal: *Performance Evaluation* (Elsevier), ISSN 0166-5316 (print) / 1872-745X (online)
Primary source: ScienceDirect "Guide for authors" for Performance Evaluation —
`https://www.sciencedirect.com/journal/performance-evaluation/publish/guide-for-authors`
(the canonical `elsevier.com/journals/.../guide-for-authors` URL 301-redirects to this
ScienceDirect page). **Caveat on sourcing**: direct `WebFetch` of this page returns
HTTP 403 (bot/CAPTCHA gate) in this environment, both directly and via a reader proxy.
The figures below were obtained via targeted web searches whose results quote/paraphrase
this exact guide-for-authors page (search-engine-indexed snippets of the live page,
cross-checked against Elsevier's general policy pages for consistency). This matches
what the prior `TEMPLATE_MIGRATION_REPORT.md` audit (2026-09-13) in this same repo found
via the same method. **Recommendation: before final submission, a human should log in to
ScienceDirect directly (or via institutional access) and re-verify every row below
against the live page**, since none of this was confirmed via a first-party page fetch
in this session.

## Requirements table

| Requirement | Current Official Guidance (with source URL) | Current Manuscript Status | Action Needed |
|---|---|---|---|
| Scope fit | "Performance Evaluation... aims to present a balanced view of the entire field of performance evaluation," covering modeling, measurement, and evaluation of performance aspects of computing and communication systems; audience = academics, industrial researchers, performance engineers, network managers, system designers. [Guide for authors](https://www.sciencedirect.com/journal/performance-evaluation/publish/guide-for-authors); [journal home](https://www.sciencedirect.com/journal/performance-evaluation) | See separate scope-fit assessment below | See scope-fit section |
| Article types | Standard Elsevier "Your Paper, Your Way" categories apply; search evidence indicates this journal accepts full-length original research articles and short communications ("short, self-contained articles on ongoing research, or reporting interesting, possibly tentative, ideas, or comments on previously published research"); some listings also reference tutorials/surveys as a historical submission type for this journal. [Guide for authors](https://www.sciencedirect.com/journal/performance-evaluation/publish/guide-for-authors) | Manuscript is written as a full-length original research article (`main.tex`, no short-communication markers) | Confirm "full length article" is the intended submission category in Editorial Manager at submission time; no change needed to manuscript type |
| Manuscript format / LaTeX class | elsarticle.cls (Elsevier's own class) is the recommended/required LaTeX class; column layout (`1p`/`3p`) is a documentclass option, not journal-mandated in the retrieved snippets — no explicit page limit surfaced. [Guide for authors](https://www.sciencedirect.com/journal/performance-evaluation/publish/guide-for-authors); [Elsevier LaTeX instructions](https://www.elsevier.com/researcher/author/policies-and-guidelines/latex-instructions) | `main.tex` line 21: `\documentclass[preprint,12pt]{elsarticle}` — uses the `preprint` (1-column, non-typeset "review" style) option, not a `1p`/`3p` production option | Verify whether `preprint` is acceptable for initial submission (it usually is — Elsevier typically only requires `1p`/`3p`/`5p` at production/proof stage) or switch to `1p,12pt` or `3p,12pt` per current guide-for-authors LaTeX instructions before submission |
| Word/page limits | No explicit page/word cap surfaced for full-length articles in the retrieved snippets (unlike the abstract, which does have a stated limit — see below); short communications are explicitly a shorter format. [Guide for authors](https://www.sciencedirect.com/journal/performance-evaluation/publish/guide-for-authors) | N/A — not checked against a numeric limit | Re-verify directly on the live guide page; no evidence of a hard limit being violated |
| Abstract | Guide-for-authors snippet: "The abstract must not exceed 250 words," stating purpose, principal results, and major conclusions; not structured (no mandated subheadings). [Guide for authors](https://www.sciencedirect.com/journal/performance-evaluation/publish/guide-for-authors) | `main.tex` lines 69–112: abstract is long (roughly 480–520 words by rough count) and organized as a running RQ-by-RQ narrative | **Action needed**: abstract very likely exceeds the 250-word limit and must be substantially shortened/condensed before submission |
| Highlights | "Highlights are mandatory... 3 to 5 bullet points, each a maximum of 85 characters, including spaces," submitted as a separate file, capturing the novelty of the study. [Guide for authors](https://www.sciencedirect.com/journal/performance-evaluation/publish/guide-for-authors) | `latex/highlights.tex` exists with exactly 5 `\item` bullets. Character counts (incl. spaces): (1) 76, (2) 75, (3) 61, (4) 74, (5) 62 — all appear to fit under 85, but should be re-counted precisely (e.g., `y\_loss` LaTeX-escape characters need to be excluded/converted when measuring the plain-text length actually uploaded) | Recount exact plain-text character length of each bullet after stripping LaTeX escaping (`\_`, `R2` math, etc.); confirm file will be uploaded as the separate "Highlights" item type per the file's own header note, not left inside the main PDF only |
| Graphical abstract | Guide/general Elsevier graphical-abstract guidance gives technical specs (image ≥1328×531 px at 300 dpi or proportionally larger, readable at 5×13 cm; TIFF/EPS/PDF/MS-Office preferred; AI-generated artwork not permitted) but is described generically rather than confirmed as strictly mandatory for this specific journal in the retrieved snippets. [Guide for authors](https://www.sciencedirect.com/journal/performance-evaluation/publish/guide-for-authors); [Elsevier graphical abstract guidance](https://www.elsevier.com/researcher/author/tools-and-resources/graphical-abstract) | No graphical abstract file exists anywhere under `paper/performance_evaluation/latex/` (confirmed by directory search; only `TEMPLATE_MIGRATION_REPORT.md` mentions it was considered and deliberately not produced) | Decide whether to produce one; since mandatoriness for this specific journal is unconfirmed, treat as **recommended but not confirmed-required** — verify on live page, and produce one if optional-but-encouraged, given the paper already has pipeline/architecture figures that could be adapted |
| Keywords | Standard Elsevier guidance surfaced for this journal: maximum of 6 keywords immediately after the abstract, American spelling, avoid generic/plural terms and terms already in the title; no controlled vocabulary (e.g., no ACM CCS or MSC requirement) noted. [Guide for authors](https://www.sciencedirect.com/journal/performance-evaluation/publish/guide-for-authors) | `main.tex` lines 118–120: 4 keywords ("learned cache eviction", "benchmark datasets", "counterfactual supervision", "cache replacement") | Within the ≤6 limit — compliant; optionally add 1–2 more (e.g., "closed-loop evaluation", "workload characterization") to better signal PE's performance-evaluation angle |
| Author declarations (CRediT, competing interest) | Elsevier mandates a CRediT authorship contribution statement (14 standard roles) and a Declaration of Competing Interest for all research articles. [CRediT policy](https://www.elsevier.com/researcher/author/policies-and-guidelines/credit-author-statement); guide for authors reiterates both are required at submission | `main.tex` has both sections: CRediT statement (line 170–173, filled in for sole author) and "Declaration of competing interest" (line 152–159) which is explicitly left as a `\relax` TODO placeholder | **Action needed**: fill in the actual competing-interest declaration (even if it is the standard "the author declares no competing financial interests" boilerplate) before submission — currently unfilled |
| Data availability statement | Elsevier requires (or strongly requests) a "Data availability" statement describing where underlying data can be accessed. [Elsevier data statement guidance](https://www.elsevier.com/researcher/author/tools-and-resources/research-data/data-statement) | `main.tex` lines 161–165: present, links to GitHub repo and Zenodo DOI, but carries an explicit TODO to confirm final hosting/DOI status before submission | Resolve the open TODO — confirm the Zenodo DOI is finalized/versioned (not a placeholder) and that public hosting is actually live before submission |
| Source file requirements | Elsevier LaTeX instructions require elsarticle.cls, the relevant `.bst`, and all figures/tables at the same folder level as `main.tex` in the final submission bundle (no nested subfolders) for the production system, though many submission portals tolerate a zipped multi-folder structure at initial submission. [Elsevier LaTeX instructions](https://www.elsevier.com/researcher/author/policies-and-guidelines/latex-instructions) | Current layout uses `latex/sections/*.tex`, `latex/tables/*.tex`, `latex/figures/`, i.e., nested subfolders, per `main.tex`'s `\input{sections/...}` calls | Flatten (or prepare a flattened copy) of all `.tex`/`.bib`/figure files into one folder for the final Editorial Manager source upload, per standard Elsevier packaging requirements — not necessarily needed for initial draft review but should be planned for pre-submission packaging |
| Figure formats | Standard Elsevier accepted formats: TIFF, EPS, PDF, JPEG (halftones), or MS Office-native for line art; vector formats preferred for line drawings. [Elsevier general artwork guidelines, cross-referenced from graphical abstract page] | `latex/figures/` directory exists; formats not individually verified in this pass | Verify each figure file extension against accepted formats before final packaging (not done in this pass — recommend a follow-up figure-format check) |
| Reference/citation style | `elsarticle-num` (numbered, IEEE-style numeric citations) is confirmed for this journal. [Guide for authors](https://www.sciencedirect.com/journal/performance-evaluation/publish/guide-for-authors) | `main.tex` line 179: `\bibliographystyle{elsarticle-num}` | Compliant — no action needed |
| Supplementary material | Elsevier's standard policy allows supplementary material (data, code, video) to be submitted alongside the article and linked from the published version; no PE-specific restriction surfaced. | Not explicitly packaged as "Supplementary Material" in the submission tree; the dataset itself is externally hosted (GitHub/Zenodo) and referenced via the Data Availability statement rather than uploaded as Elsevier supplementary material | Decide whether any files (e.g., extended tables, worked-example appendix material) should instead be submitted as formal Elsevier supplementary material vs. kept as an appendix section (`13_appendix_release_tables.tex`) — no hard requirement found either way |
| Cover letter | Not confirmed specific to this journal in the retrieved snippets; general Elsevier practice is that a cover letter is typically optional but recommended, submitted as a separate file during Editorial Manager submission. | No cover letter draft found anywhere under `docs/` (confirmed by recursive search) | Draft a cover letter before submission as a precaution, since most Elsevier journals accept/expect one even when not strictly mandatory — verify exact requirement on the live guide page |
| Submission system | Editorial Manager is Elsevier's standard portal; general Elsevier submission-process documentation (not a PE-specific page) confirms this is the default across the portfolio, and no evidence surfaced of Performance Evaluation being an exception. [Elsevier submission process](https://www.elsevier.com/researcher/author/submit-your-paper/submit-and-revise) | N/A (pre-submission) | No manuscript action; note Editorial Manager as the target portal when submitting |
| Anonymization / peer-review type | Search evidence indicates Performance Evaluation uses **single-anonymized** review (author identities visible to reviewers; reviewer identities hidden from authors) — i.e., NOT double-blind. [Guide for authors](https://www.sciencedirect.com/journal/performance-evaluation/publish/guide-for-authors) | `main.tex` already carries real author name/affiliation/email (lines 60–67), consistent with single-anonymized (non-double-blind) review, and a template note explicitly documents this decision | Compliant as currently drafted — no anonymization of the manuscript is needed; re-verify "single-anonymized" wording on the live page before relying on it, since this was not confirmed via first-party fetch |

## Journal scope-fit assessment

**Classification: ACCEPTABLE_FIT** (not STRONG_FIT; not BORDERLINE/POOR_FIT either).

Reasoning, based on `sections/01_introduction.tex`, `sections/09b_discussion.tex`, and
`sections/10_related_work.tex`:

- **Evaluation methodology is central, not incidental.** The introduction frames the
  paper explicitly around five research questions (RQ1–RQ5) about discriminativeness,
  offline/closed-loop correspondence, workload/capacity/horizon dependence, and
  continuation-policy robustness — this is a measurement/evaluation-methodology paper,
  not a systems-design or pure-ML paper. This is squarely in PE's wheelhouse.
- **Workload characterization is genuinely central.** RQ1 and RQ3 are explicitly about
  how discriminativeness and offline/closed-loop agreement vary by workload, capacity,
  and horizon, including a "negative control" workload (wiki2018) that is mechanistically
  explained rather than discarded. This is a strong PE-style contribution.
- **Measurement/simulation methodology is rigorous and foregrounded**, with a
  production-scale closed-loop evaluation (LRU/MRU/random/SIEVE across 5 families × 2
  capacities × 20 seeds) and a pre-registered robustness study — both hallmarks of the
  kind of empirical rigor PE reviewers expect.
- **Results emphasize performance behavior** (miss cost, policy ordering agreement,
  closed-loop miss ratio) rather than model architecture or training procedure, which
  fits PE's audience of performance engineers and system designers.
- **Artifact framing is explicitly subordinated.** The introduction states directly:
  "release construction, schema, and validation... support the evaluation methodology in
  this paper... but are not the paper's central argument," and the discussion section
  frames the release as an enabler ("What LAFC-Evict enables") rather than the point of
  the paper. This is the single most important framing correctness already present.
- **Why not STRONG_FIT**: (1) the related-work section (`10_related_work.tex`) still
  spends substantial space positioning against ML/learned-caching and benchmark/dataset
  literature (LETOR, YCSB-style benchmark framing, "reusable table," "static benchmark
  surface") — language and comparison set that reads more naturally in an ML-systems or
  benchmarks venue than in PE's own core citation community (queueing theory, workload
  characterization, capacity planning, stochastic performance modeling). PE reviewers may
  read the positioning-heavy related work as evidence the paper's primary audience is
  the learned-caching/ML community, with PE as a secondary target. (2) The paper's title
  itself ("...Counterfactual Benchmark...") foregrounds "benchmark" before "evaluation,"
  which is a framing signal working against, not for, PE fit, even though the body text
  correctly subordinates the artifact.

**Exact framing fix needed to move to STRONG_FIT**: (a) revise the title to foreground
the evaluation-methodology contribution ahead of the benchmark/dataset noun — e.g.,
something like "Evaluating Counterfactual Supervision for Cache Eviction: A Large-Scale
Measurement Study" — with "LAFC-Evict" retained as the artifact's name rather than the
paper's primary descriptor; (b) trim `10_related_work.tex`'s benchmark/ML-dataset
positioning (LETOR/Yahoo LTR comparison, "reusable table" framing) to a shorter
paragraph, and correspondingly expand comparison to PE-adjacent performance-evaluation
methodology literature (offline-vs-closed-loop validity work already cited via Qiu et
al. is a good anchor — more work in that vein, plus classical trace-driven simulation
methodology literature, would strengthen this); (c) ensure the abstract (once shortened
to meet the 250-word cap) leads with the evaluation-methodology finding rather than the
dataset scale numbers (277,995,072 candidate rows currently appears prominently).

## Files referenced

- `/home/soroush/projects/lafc-evict-dataset/repo/.claude/worktrees/pe-evidence-restructure-20260914/paper/performance_evaluation/latex/main.tex`
- `/home/soroush/projects/lafc-evict-dataset/repo/.claude/worktrees/pe-evidence-restructure-20260914/paper/performance_evaluation/latex/highlights.tex`
- `/home/soroush/projects/lafc-evict-dataset/repo/.claude/worktrees/pe-evidence-restructure-20260914/paper/performance_evaluation/latex/sections/01_introduction.tex`
- `/home/soroush/projects/lafc-evict-dataset/repo/.claude/worktrees/pe-evidence-restructure-20260914/paper/performance_evaluation/latex/sections/09b_discussion.tex`
- `/home/soroush/projects/lafc-evict-dataset/repo/.claude/worktrees/pe-evidence-restructure-20260914/paper/performance_evaluation/latex/sections/10_related_work.tex`
- `/home/soroush/projects/lafc-evict-dataset/repo/.claude/worktrees/pe-evidence-restructure-20260914/paper/performance_evaluation/TEMPLATE_MIGRATION_REPORT.md` (prior partial audit, cross-checked for consistency)
- No graphical abstract file found under `paper/performance_evaluation/latex/`
- No cover letter draft found under `docs/`
