# Citation Metadata Audit

Status: PARTIALLY_COMPLETE prior to this task. The prior handoff
(Section 16) already listed known cautions (Parrot, Park, Cache-Coliseum
authorship/venue needing checks) but had not performed a structured
per-entry audit or a live authoritative-source verification of any entry.
This task performs both for the entries actually cited, and fixes one
confirmed error.

Source audited: `paper/performance_evaluation/latex/refs.bib` (44 entries,
copied from `manuscript/performance-evaluation-template-20260913` @
`471b3c4`, identical to `paper/sigmod2027/latex/refs.bib`).

**Update (2026-09-14, literature-positioning follow-on task):** 6 new
entries added after a full `PE_LITERATURE_CITATION_COVERAGE_AUDIT` pass
identified them as verified-real, on-topic, and missing (see that audit's
`TARGET_REFERENCE_TABLE`). `refs.bib` now has 50 entries. Every new entry
was independently verified against an authoritative primary source before
being added (USENIX presentation pages, arXiv abstract pages, and the
Crossref API for the one journal entry) — see `PE_LITERATURE_SEARCH_GAPS.md`
for the exact sources checked per entry. `paper/sigmod2027/latex/refs.bib`
was intentionally left untouched (that track's own literature pass is out
of this task's scope), so the two `refs.bib` files are no longer
byte-identical; this is a deliberate divergence, not an oversight.

## Citation-key hygiene

- Cited keys (from all 20 section `.tex` files, `\cite*{...}` scan): 48
  (42 pre-existing + 6 newly added, all 6 of which are cited at least once).
- Bib entries: 50.
- **Undefined citations** (cited, no bib entry): 0 (confirmed by a clean
  `latexmk` build with zero `[?]` markers in the compiled PDF — see
  `TEMPLATE_MIGRATION_REPORT.md`-style build notes in the manuscript-
  rewrite commit for the toolchain used).
- **Uncited bib entries** (in bib, never cited): still 2 —
  `kirilin2020rlcache` (RL-Cache) and `narita2019efficient`. Decision this
  task: **leave both bibliography-only, do not cite or remove.**
  `kirilin2020rlcache` covers cache *admission* for CDN caching, not
  eviction/replacement — the manuscript's scope (candidate-level eviction
  labels) does not have a natural place to cite it without stretching the
  claim; removing it was judged unnecessary since an unused `.bib` entry is
  a minor cleanliness issue, not a correctness one, and removal carries a
  small, unforced risk of affecting some other future manuscript variant
  that might reuse this file. `narita2019efficient` (counterfactual
  bandit learning) was already flagged as uncited before this task and is
  unchanged; same reasoning applies. Both remain open items for a future
  submission-readiness pass, not blockers.
- No duplicate citation keys found (each `@type{key,` key is unique,
  including the 6 new keys: `xia2026lah`, `song2023halp`,
  `qiu2026hitratio`, `wong2024baleen`, `yang2023lazypromotion`,
  `berg2020cachelib`).
- No malformed entries found (every entry has balanced braces, a closing
  `}` on its own line, and the required fields for its type — checked by
  visual inspection of all 50 entries, and confirmed indirectly by the
  clean `latexmk`/BibTeX build in this task).

## Recency (cache-replacement / learned-caching relevant entries only, by year, after this task's additions)

- 2023: 5 (`yang2023mat`, `yang2023s3fifo`, `yang2023glcache`,
  `song2023halp`, `yang2023lazypromotion`)
- 2024: 4 (`zhang2024sieve`, `torabi2024hrcache`, `shahout2024alps`,
  `wong2024baleen`)
- 2025: 1 (`zhou2025threelcache`)
- 2026: 2 (`xia2026lah`, `qiu2026hitratio`)
- Newest cited relevant paper: `xia2026lah` (OSDI '26, July 2026),
  closely followed by `qiu2026hitratio` (*Queueing Systems*, April 2026).
  Before this task, the newest was `zhou2025threelcache` (FAST '25,
  February 2025) — the state-of-the-art discussion no longer stops a full
  cycle behind the manuscript's own writing date.

## Fixed in this task

### `vietri2018lecar` (LeCaR) — INCORRECT, FIXED

- Before: `author = {Vietri, Giuseppe and Rodriguez, Liana V. and
  Martinez, William A. and Lyons, Steven and Liu, Jason and Rangaswami,
  Raju and Zhao, Ming and Narasimhan, Giri}`
- Authoritative source checked (live, this task): the USENIX HotStorage
  '18 conference page,
  https://www.usenix.org/conference/hotstorage18/presentation/vietri
  (confirmed via two independent web searches), lists the author as
  **"Wendy A. Martinez"**, not "William A. Martinez", and lists the final
  two authors as **Narasimhan, Giri and Zhao, Ming** (Narasimhan before
  Zhao), not Zhao before Narasimhan.
- After (applied to `refs.bib` in this task): `author = {Vietri, Giuseppe
  and Rodriguez, Liana V. and Martinez, Wendy A. and Lyons, Steven and
  Liu, Jason and Rangaswami, Raju and Narasimhan, Giri and Zhao, Ming}`
- This is a deterministic metadata correction against a live authoritative
  source, not an experiment or a regeneration of any scientific artifact —
  permitted under this task's constraints.

## Needs external verification (not changed in this task — no
authoritative source was checked live for these; flagged per the prior
handoff's own to-do list, not re-verified here due to time budget)

- `liu2020parrot` (Parrot / imitation learning cache replacement, ICML
  2020): current entry lists first author as "Liu, Evan"; the paper is
  commonly cited as "Evan Zheran Liu" — the given-name completeness should
  be checked against the official ICML/PMLR page before submission.
- `song2020lrb` (LRB, NSDI 20): entry looks complete and internally
  consistent (ISBN, address, month, publisher all present) but was not
  independently re-checked against the NSDI proceedings page in this task.
- `yang2023glcache` (GL-Cache, FAST 23) and `zhou2025threelcache`
  (3L-Cache, FAST 25): both entries look complete and well-formed (ISBN,
  address, month, publisher, DOI-equivalent URL) — appear to already have
  been corrected since the prior handoff flagged them as "needing
  re-check"; not independently re-verified live in this task.
- `libcachesim` and `cachedataset` (`@misc`, author `{cacheMon}`, GitHub
  URLs, "Accessed 2026-07-03"): software/dataset citations with an
  organizational rather than personal author, which is acceptable style
  for a GitHub-hosted tool but should be double-checked against the
  repositories' own citation guidance (a CITATION.cff file, if present)
  before submission.

## High-priority missing references (confirmed still absent, matching the
prior handoff's list — re-confirmed by direct grep of the 44 entries in
this task, not newly discovered)

- Cache-Coliseum (NeurIPS 2025 associated paper)
- "Learning Caching Policies with Subsampling"
- DAgger (Ross, Gordon, Bagnell — imitation learning; relevant since Parrot
  and the design docs' own continuation-policy discussion reference
  DAgger-style reasoning)
- Park (RL for systems platform)
- QD-LP / "FIFO Can Be Better than LRU"

None of these were added in this task — see `PE_LITERATURE_SEARCH_GAPS.md`
for what a full search for each would need to verify before citing.

## Positioning note

No entry was found for direct Performance-Evaluation-journal-venue prior
work on counterfactual/offline supervision for cache eviction specifically
— this is consistent with the manuscript's own restrained novelty framing
("to the best of our knowledge") and does not by itself indicate a missing
citation; see `PE_LITERATURE_SEARCH_GAPS.md` for the categories still
requiring a full search pass.
