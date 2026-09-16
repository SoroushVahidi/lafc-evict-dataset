PE venue-compliance audit, results-independent pass
===================================================

Audit date: 2026-09-16

Sources checked:

- Elsevier / ScienceDirect, Performance Evaluation Guide for Authors:
  https://www.sciencedirect.com/journal/performance-evaluation/publish/guide-for-authors
- Elsevier, ScienceDirect journal issues page for Performance Evaluation:
  https://www.sciencedirect.com/journal/performance-evaluation/issues
- Elsevier, generative-AI policy for journals / writing process:
  https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals
- Elsevier, graphical abstracts guidance:
  https://www.elsevier.com/researcher/author/tools-and-resources/graphical-abstract
- Recent Performance Evaluation article pages sampled through ScienceDirect/ACM
  metadata: Volume 171 / March 2026 articles including "Improving
  nonpreemptive multiserver job scheduling with quickswap",
  "A control-theoretic perspective on BBR/CUBIC congestion-control
  competition", and "Revenue management for parallel services with fully
  observable queues and heterogeneous customers".

Requirements observed:

- Article structure: title, author metadata, abstract, keywords, numbered
  sections, figures/tables with captions, acknowledgments, declarations,
  data availability, funding, CRediT where applicable, AI-use declaration,
  appendices if needed, references.
- Abstract: concise, factual, self-contained, able to stand alone; avoid
  undefined abbreviations and avoid citations unless unavoidable.
- Keywords: required; current manuscript provides four keywords.
- References/citations: numbered Elsevier style via `elsarticle-num`.
- Highlights: journal guide indicates Highlights are mandatory; manuscript
  keeps `highlights.tex` as a separate upload source with five <=85-character
  bullets.
- Graphical abstract: treated as optional/encouraged in Elsevier general
  guidance; no journal-specific formal requirement found in the accessible
  guide content.
- Data/code availability: current manuscript distinguishes public repository,
  code license, dataset release license, and upstream trace governance.
- AI-use disclosure: current manuscript includes the required declaration
  immediately before references, matching Elsevier placement guidance.
- Figures/tables: cited in text, numbered, captioned, submitted as editable
  LaTeX/table source or included figures; no table is an image.
- Formal page/word limit: NONE_FOUND. No formal Performance Evaluation page
  or word limit was found in the current guide content accessible during this
  audit. The manuscript should not invent one.

Recent-paper style observations:

- Performance Evaluation papers use conventional technical sections rather
  than checklist-style artifact prose.
- Mathematical papers and systems/performance papers number displayed
  equations that are part of the argument.
- Experimental papers keep figures/tables close to first discussion and use
  concise captions that explain the statistic being plotted or tabulated.
- Related work is typically integrated near the end or after technical
  sections for article-length papers, with citations grouped by contribution
  rather than as long undifferentiated lists.

Wulver acknowledgment (checked, not added):

- The manuscript's own provenance record for the Tier-1 closed-loop evidence
  (analysis/closed_loop_tier1_evidence_20260914/run/20260914T023445Z_8a4cd32402a1/provenance.json)
  records hostname "al-khwarizmi", a local workstation, and no provenance
  record anywhere in the repository for any result currently reported in this
  manuscript names Wulver. Adding a Wulver acknowledgment now would therefore
  be an inaccurate statement about the present manuscript's evidence base.
  No acknowledgment was added; this should be revisited once the long-horizon
  H=32/64/128 campaign (which does run on Wulver) is integrated into the
  paper, at which point the acknowledgment would become accurate.

Result:

- Venue-compliance posture: PASS after this pass, subject to final editorial
  verification in Elsevier's submission system.
- No results from the active long-horizon or learned-policy computations were
  used.
