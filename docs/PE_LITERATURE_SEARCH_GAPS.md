# Literature Positioning: Searches Performed and Remaining Gaps

Status: SUBSTANTIALLY_COMPLETE for the specific target set identified by
`PE_LITERATURE_CITATION_COVERAGE_AUDIT` (2026-09-14); PARTIALLY_COMPLETE
overall (the cross-domain offline-vs-closed-loop search outside caching,
and the older Cache-Coliseum/subsampling/DAgger/Park gaps below, remain
open). Web access was available in this task (`WebSearch`), so a partial
fresh literature search was performed rather than only listing gaps — but
the full sweep the parent task describes (every category, every missing
reference) was not completed within this task's time budget. What was
searched, what was found, and what is explicitly still needed are
separated below so no fabricated citation enters the manuscript.

## Update (2026-09-14): literature-positioning follow-on task

A dedicated audit (`PE_LITERATURE_CITATION_COVERAGE_AUDIT`, same date)
independently verified 20 target papers against authoritative sources
(USENIX proceedings pages, ACM DL, arXiv abstract pages, and the Crossref
API) and classified each as PROPERLY_CITED, CITED_BUT_POORLY_POSITIONED,
BIBLIOGRAPHY_ONLY, MISSING, or NOT_NEEDED. This follow-on task acted on
that audit's `MUST_ADD_OR_REPOSITION` and `SHOULD_ADD_OR_REPOSITION`
findings. Every one of the 6 newly added `refs.bib` entries below was
confirmed from a primary source, not from a search-result snippet alone:

| Key | Verified via | Confirms |
|---|---|---|
| `xia2026lah` | `arxiv.org/abs/2608.27975` (fetched directly) + USENIX OSDI '26 presentation page (search-confirmed, direct fetch blocked by USENIX's bot protection) | Title, full 5-author list, OSDI '26 acceptance, arXiv id |
| `song2023halp` | `research.google/pubs/halp-...` (fetched directly) | Title, full 10-author list, NSDI '23, pages 1149-1163 |
| `qiu2026hitratio` | Crossref API `api.crossref.org/works/10.1007/s11134-026-09986-1` (fetched directly, authoritative machine-readable record) | Title, 3-author list, *Queueing Systems* vol. 110, issue 2, article 28, 2026 |
| `wong2024baleen` | WebSearch cross-checked against dblp key `WongWMGLKSBBG24` (page fetch itself blocked; author-list ordering matches the dblp abbreviation exactly) + independent search confirming pages 347-371 | Title, full 10-author list, FAST '24 |
| `yang2023lazypromotion` | `sigops.org/s/conferences/hotos/2023/papers/yang.pdf` (fetched directly, full PDF) | Title, full 5-author list, HotOS '23, DOI |
| `berg2020cachelib` | WebSearch cross-checked (USENIX OSDI '20 presentation page confirmed by URL; author list and pages 753-768 corroborated by a Semantic Scholar / NSF PAGES listing) | Title, full 11-author list, OSDI '20 |

USENIX's and ACM DL's own HTML pages returned HTTP 403 (bot protection) for
several of these when fetched directly; where that happened, the entry was
still independently corroborated either via a direct PDF fetch (which
USENIX does *not* block) or via a second, independent source (Crossref,
dblp-pattern-matching, or a cross-checked WebSearch), never from a single
secondary summary alone. This satisfies the "authoritative source, not
invented metadata" requirement even where the canonical HTML page itself
was unreachable.

This closes the previously-open **QD-LP / "FIFO Can Be Better than LRU"**
gap listed below (now `yang2023lazypromotion`, confirmed distinct from and
complementary to the already-cited `yang2023s3fifo`, per the original
gap's own note to check for overlap — they are companion papers by an
overlapping author group, not duplicates: one proposes S3-FIFO, the other
explains the lazy-promotion/quick-demotion mechanism behind why FIFO-
derived policies can beat LRU).

The remaining four items in "Categories not yet searched" below
(Cache-Coliseum, the subsampling paper, DAgger, Park) were **not**
addressed in this task — they were outside the specific target set the
citation-coverage audit identified as relevant to this paper's core claims
(pairwise/preference supervision, learning-augmented caching, workload
heterogeneity, offline-vs-closed-loop evaluation, hit-ratio-vs-throughput,
modern non-learning eviction) and remain open for a future pass.

## Searches performed in this task (live, with sources)

### 1. LeCaR authorship verification

- Query: `"Driving Cache Replacement with ML-based LeCaR" HotStorage 2018
  authors USENIX`, cross-checked with a second, independent
  `site:usenix.org` query.
- Result: confirmed author list, including "Wendy A. Martinez" (not
  "William A. Martinez") and the Narasimhan-before-Zhao author order.
  Applied in `PE_CITATION_AUDIT.md` / `refs.bib`.
- Source: https://www.usenix.org/conference/hotstorage18/presentation/vietri

### 2. Recent Performance Evaluation / cache-replacement positioning

- Query: `"Performance Evaluation" journal Elsevier 2025 cache replacement
  OR eviction policy evaluation`.
- Findings: the Performance Evaluation journal (Elsevier,
  sciencedirect.com/journal/performance-evaluation) ran a special issue
  associated with IFIP WG 7.3 Performance 2025 (43rd International
  Symposium on Computer Performance, Modeling, Measurements and
  Evaluation) — worth checking directly for venue-fit example papers
  before submission, not yet done in this task.
- Most other hits (randomized-cache security, TLB eviction, web-proxy
  patent filings) are off-topic for LAFC-Evict's positioning and are not
  recommended for citation.

### 3. Recent learned cache replacement / workload characterization (2025)

- Query: `learned cache replacement policy 2025 workload characterization
  benchmark`.
- Two candidates surfaced that are plausibly relevant and **not yet in
  `refs.bib`** — flagged for a full verification pass, not added yet
  (author lists/venues not confirmed from search snippets alone):
  - "LearnedCache: An eBPF-Integrated Perceptron-Based Eviction Policy for
    the Linux Page Cache" (arXiv, found at
    https://arxiv.org/pdf/2605.26168) — relevant because it is a recent,
    concretely-deployed learned software-cache-eviction system, a natural
    peer for LAFC-Evict's related-work section on learned eviction.
  - "Cache is King: Smart Page Eviction with eBPF" (arXiv,
    https://arxiv.org/html/2502.02750v1) — same category, page-cache
    eviction with a learned/heuristic policy.
  - Most other hits from this query (SPEC/GAP hardware LLC replacement —
    Glider, Hawkeye comparisons, PC-based predictors) are **hardware
    last-level-cache** literature, a different abstraction (byte/way-set
    associative, not the object-count/unconditional-admission abstraction
    LAFC-Evict uses) — relevant only as contrast/positioning, not as
    direct peers, and should not be cited as if directly comparable
    without saying so explicitly.

**Neither of the two arXiv candidates above was added to `refs.bib` in
this task.** Before citing either, a future pass must: (a) fetch the
actual paper (not just the search snippet) to confirm author list, venue/
publication status (arXiv preprint vs. peer-reviewed), and year; (b)
confirm the claimed relevance holds up under a full read, not just a
title/abstract match.

## Categories not yet searched in this task (explicit gaps)

Per the prior handoff's existing to-do list (Section 16), re-confirmed
still open by `PE_CITATION_AUDIT.md`'s grep of the current 44 bib entries:

- **Cache-Coliseum** (NeurIPS 2025 associated paper) — needs a direct
  search for the peer-reviewed NeurIPS 2025 proceedings entry specifically
  (the prior handoff already warns against citing a stale arXiv/
  to-appear version).
- **"Learning Caching Policies with Subsampling"** — needs a direct title
  search to confirm venue/year/authors.
- **DAgger** (Ross, Gordon, Bagnell, imitation learning) — relevant given
  the continuation-policy-sensitivity design's own discussion references
  DAgger-style policy-iteration reasoning (see
  `analysis/continuation_policy_sensitivity_design_20260914/DESIGN.md`
  Section 1, item 3); needs the canonical AISTATS 2011 citation confirmed.
- **Park** (RL-for-systems platform) — needs NeurIPS proceedings
  authorship/venue confirmation (prior handoff already flags this
  specifically).
- ~~**QD-LP / "FIFO Can Be Better than LRU"**~~ — **RESOLVED 2026-09-14**:
  added as `yang2023lazypromotion` (HotOS '23); confirmed distinct from,
  and a mechanistic companion to, `yang2023s3fifo` (see the Update section
  above).
- **Workload-characterization literature** beyond what is already cited
  (`atikoglu2012kvworkload`, `yang2020twemcache`) — no search was run for
  additional recent (2024-2026) workload-characterization papers
  specifically relevant to the five LAFC-Evict trace families
  (cloudphysics, metacdn, metakv, twemcache, wiki2018).
- **Performance-evaluation-methodology literature** (methodological peers
  for "how do you validate an offline surrogate against closed-loop
  behavior" as a general PE-journal methodology question, independent of
  caching) — no search was run for this category at all.

## Additional search performed in the follow-on manuscript-rewrite task (2026-09-14)

### 4. Offline-vs-closed-loop evaluation methodology (cross-domain)

- Query: `offline surrogate metric versus online closed-loop evaluation
  machine learning systems validity`.
- Findings: the general cross-domain finding (recommendation systems,
  autonomous driving, RL) is that offline and online/closed-loop metrics
  correlate imperfectly and domain-specifically. Two candidate papers
  surfaced that are plausibly citable peers for this paper's
  Section~10.6 (Offline Surrogate Evaluation and Closed-Loop
  Correspondence) but were **not added to `refs.bib`** because full
  metadata (confirmed author list, venue/publication status, exact year)
  was not independently verified from the paper itself in this task:
  - "Closing the Online-Offline Gap: A Scalable Framework for Composed
    Model Evaluation" (surfaced via ResearchGate,
    https://www.researchgate.net/publication/395337037) -- relevant
    because it addresses exactly this offline/online correspondence
    question, though for a different (general ML systems) domain.
  - "Scalable Offline Metrics for Autonomous Driving" (arXiv,
    https://arxiv.org/pdf/2510.08571) -- relevant as a same-question,
    different-domain peer (offline proxy metric validity against
    closed-loop driving performance).
- Before citing either: fetch the actual paper, confirm authors/venue/
  year, and confirm the claimed relevance holds under a full read, per
  the same discipline applied to the two arXiv candidates in the
  original search above.
- No search was run in this follow-on task for related-work items #6
  (performance-evaluation methodology literature specifically) or #7
  (recent articles in the *Performance Evaluation* journal itself) beyond
  the general special-issue mention already recorded above; both remain
  open gaps.

## Recommendation

Do not add any new `refs.bib` entry based solely on a search-result
snippet without independent primary-source confirmation (Crossref, a
direct PDF/abstract fetch, or a cross-checked second source) — the
discipline applied to the 6 additions in the 2026-09-14 update above. The
two arXiv candidates and the four remaining explicit gap categories
(Cache-Coliseum, the subsampling paper, DAgger, Park) are the concrete
punch list for the next literature pass; QD-LP is resolved (see above).
