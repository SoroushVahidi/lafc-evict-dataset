# Problem 7 Phase 10: literature freshness check

Two targeted WebSearch queries (2026-09-17), scoped to material that would
change the paper's novelty/positioning statement, not an open-ended survey.

Query 1: "learned cache eviction replacement policy 2026 SOSP OSDI VLDB
SIGMOD benchmark"
Query 2: "cache replacement policy benchmark 2025 2026 new algorithm S3-FIFO
successor"

## Papers found and classified

| Paper | Venue/date | Classification | Reason |
|---|---|---|---|
| LearnedCache (eBPF perceptron, Linux page cache) | arXiv 2026-05 | NOT_RELEVANT | Systems/throughput contribution (eBPF integration), not a labeled-supervision benchmark; does not compete with LAFC-Evict's claimed artifact type |
| Demystifying and Improving Lazy Promotion in Cache Eviction | VLDB (recent) | OPTIONAL | Extended/journal treatment of the concept already correctly cited via its original HotOS'23 source (`yang2023lazypromotion`); not required for correctness |
| DynamicAdaptiveClimb | arXiv 2025-11 | NOT_RELEVANT | Adaptive resizing policy, not benchmark/supervision-construction work |
| Clock2Q+ | arXiv 2025-11 | NOT_RELEVANT | New replacement algorithm; would only matter if LAFC-Evict claimed to survey all modern policies, which it explicitly does not |
| SL-Cache | DASFAA 2026 | NOT_RELEVANT | New learned-eviction algorithm, not a benchmark/supervision contribution |
| Which Eviction Policy Should an LLM Cache Use? (arXiv 2608.20280) | arXiv 2026-08 | OPTIONAL (checked in detail) | Systematic multi-policy comparison, topically closest in spirit, but the object of study is semantic/embedding-similarity LLM response caches, a different domain from LAFC-Evict's byte/object-level trace-driven eviction; abstract confirmed via search (CLEVER framework, FIFO/LRU/LFU/ARC/GDSF/SISO compared on query-embedding caches) |
| Learning-Augmented Heuristics (arXiv 2608.27975) | arXiv 2026-08 | OPTIONAL | Learned-heuristic eviction contribution, already covered by the existing learning-augmented-caching related-work cluster (`lykouris2021mladvice` et al.) |
| Mobius, EEvA, 3L-Cache (already cited as `zhou2025threelcache`) | various 2024-2026 | NOT_RELEVANT / ALREADY_CITED | Throughput/latency-engineering or already-cited learned policies |

## MUST_CITE additions
None. No paper found would make the current novelty/positioning statement
in `sections/10_related_work.tex` ("Positioning \lafc") materially
misleading if omitted -- that section already explicitly disclaims being
the first benchmark, first learned-caching work, or first preference-
learning approach, and cites Cache-Coliseum (NeurIPS 2025) as the closest
prior benchmark.

## SHOULD_CITE additions
None applied. `berger2018foopfoo`, `fedchenko2018fnncache`, and
`kirilin2020rlcache` were already present in `refs.bib` but uncited; they
are caching-relevant but their omission does not weaken any claim (see
BIBLIOGRAPHY_AUDIT.csv) given the already-extensive 12+-policy related-work
citation cluster. Removed as unused entries rather than newly cited, since
adding them now would be citation-list padding without a specific claim
they are needed to support (violates Phase 11's anti-padding rule).

## Novelty wording
Not changed -- already precise and appropriately hedged (see
CLAIM_LEDGER.csv C22 and the Wording-Strength spot-check in the final
report).
