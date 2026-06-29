# Reference Audit

This audit is intentionally strict. Metadata was checked against primary or authoritative sources where possible, prioritizing ACM DL, USENIX, IEEE Xplore, DBLP, Springer, arXiv, official conference proceedings, and official project or repository pages.

## Status legend

- `MUST_CITE_VERIFIED`
- `USEFUL_VERIFIED`
- `BACKGROUND_ONLY`
- `VERIFY_BEFORE_USE`
- `PROBABLY_EXCLUDE`
- `NON_ARCHIVAL_OR_BLOG`
- `DUPLICATE_OR_REDUNDANT`

## Candidate audit

| Candidate reference | Recommended work to cite | Status | Verification basis | Notes |
| --- | --- | --- | --- | --- |
| Belady MIN | Belady, “A study of replacement algorithms for a virtual-storage computer” (IBM Systems Journal, 1966) | MUST_CITE_VERIFIED | IBM / ACM DOI / DBLP | Foundational optimal-lookahead reference for replacement. |
| LIRS | Jiang and Zhang, SIGMETRICS 2002 | MUST_CITE_VERIFIED | ACM DL / DBLP | Canonical recency-based replacement improvement. |
| ARC | Megiddo and Modha, FAST 2003 | MUST_CITE_VERIFIED | USENIX / DBLP | Core adaptive replacement baseline. |
| CLOCK-Pro | Jiang, Chen, and Zhang, USENIX ATC 2005 | MUST_CITE_VERIFIED | USENIX / DBLP | Standard CLOCK-family improvement. |
| GreedyDual-Size | Cao and Irani, USITS 1997 | MUST_CITE_VERIFIED | USENIX / DBLP | Important cost/size-aware caching reference. |
| TinyLFU | Einziger, Friedman, and Manes, ACM TOS 2017 | MUST_CITE_VERIFIED | ACM DL / DBLP | Key modern admission-policy reference. |
| W-TinyLFU | Einziger et al., Middleware 2018 (“Adaptive Software Cache Management”) | MUST_CITE_VERIFIED | ACM DL / DBLP | Practical software-cache evolution of TinyLFU; cite the Middleware paper rather than folklore descriptions. |
| RL-Cache | Kirilin et al., IEEE JSAC 2020 | MUST_CITE_VERIFIED | IEEE Xplore / DBLP | Strong learned caching reference for content delivery. |
| ALPS | Shahout and Friedman, OPODIS 2024 | MUST_CITE_VERIFIED | Dagstuhl / DBLP | Verified and relevant as a lightweight learned cache-management policy. |
| Feedforward Neural Networks for Caching | Fedchenko, Neglia, and Ribeiro, SIGMETRICS PER 2018 | MUST_CITE_VERIFIED | ACM DL / DBLP / arXiv | Useful because it questions whether heavier neural models are actually necessary. |
| HR-Cache | Torabi, Khazaei, and Litoiu, ICPE 2024 | USEFUL_VERIFIED | ACM DL / DBLP / arXiv | Verified and relevant, but edge-content focus makes it secondary to RL-Cache and ALPS. |
| KVP / Learning to Evict from Key-Value Cache | Moschella, Manduchi, and Sener, arXiv/OpenReview 2026 | PROBABLY_EXCLUDE | arXiv / OpenReview | Verified as a 2026 LLM KV-cache paper, but likely out of scope for the first SIGMOD draft unless a KV-cache subsection is added. |
| Google preference-learning blog | Google Research blog post | NON_ARCHIVAL_OR_BLOG | Official blog page only | Can motivate pairwise preference ideas internally, but should not be used as a final scholarly citation. |
| DRL-Clusters | uncertain | VERIFY_BEFORE_USE | no stable verified archival citation established in this pass | Do not cite unless a precise archival paper and metadata are identified. |
| Twitter cache-trace / Twemcache | Yang, Yue, and Rashmi, OSDI 2020; optionally Atikoglu et al., SIGMETRICS 2012 | MUST_CITE_VERIFIED | USENIX / DBLP | Prefer the OSDI trace-analysis paper over a GitHub repository citation in the manuscript. |
| UMass Trace Repository | official repository website | MUST_CITE_VERIFIED | official repository page | Not a traditional paper, but an important public-trace resource for benchmark positioning. |
| cloud / block storage cache datasets | exact citation depends on which dataset is discussed | VERIFY_BEFORE_USE | only broad category identified | Too vague as stated; cite concrete datasets only after naming them. |
| YCSB | Cooper et al., SoCC 2010 | MUST_CITE_VERIFIED | ACM / DBLP | Canonical systems benchmark reference. |
| OLTP-Bench | Difallah et al., PVLDB 2013 | MUST_CITE_VERIFIED | PVLDB / DBLP | Strong benchmark-paper comparison point. |
| Join Order Benchmark | Leis et al., VLDB Journal 2018 | MUST_CITE_VERIFIED | Springer / DBLP | Strong data-management benchmark comparison point. |
| Narita et al. counterfactual learning from bandit feedback | Narita, Yasui, and Yata, AAAI 2019 | USEFUL_VERIFIED | AAAI / DBLP | Useful for counterfactual-learning context, but not the first counterfactual-risk reference to cite. |
| deterministic logging / bandit feedback | Swaminathan and Joachims 2015; Li et al. 2011 | DUPLICATE_OR_REDUNDANT | ICML / WSDM / DBLP | Treat as a topic label, not a separate citation item. |
| contextual bandit OPE | Li et al., WSDM 2011 | MUST_CITE_VERIFIED | ACM DL / DBLP / arXiv | Strong offline-evaluation reference. |
| unbiased learning-to-rank | Joachims, Swaminathan, and Schnabel, WSDM 2017; optionally Ai et al., SIGIR 2018 | MUST_CITE_VERIFIED | ACM DL / DBLP | Natural bridge from counterfactual feedback to ranking tasks. |
| Liu learning-to-rank survey | Liu, Foundations and Trends 2009 | MUST_CITE_VERIFIED | ACM DL / DBLP | Standard survey anchor. |
| LETOR | Qin et al., Information Retrieval 2010 | MUST_CITE_VERIFIED | Springer / DBLP | Important benchmark-paper comparison point. |
| Yahoo LTR challenge | Chapelle, Chang, and Liu, JMLR Workshop and Conference Proceedings 2011 | MUST_CITE_VERIFIED | JMLR / DBLP | Strong public ranking-benchmark reference. |
| pairwise LTR | Liu 2009; Saito 2020 if pairwise debiasing is discussed | BACKGROUND_ONLY | survey / ICTIR / DBLP | A concept rather than one indispensable reference. |
| NeurIPS Datasets and Benchmarks guidance | workshop/call/blog-style framing | PROBABLY_EXCLUDE | not central to SIGMOD benchmark positioning | Use only for internal framing, not as a main related-work citation. |
| RULER / OASST2 | none for current draft | PROBABLY_EXCLUDE | outside current benchmark scope | Only relevant if the KV-cache paper is brought in. |

## Immediate manuscript guidance

- The first related-work pass should cite the verified classical caching, learned caching, benchmark, and ranking/counterfactual references.
- Do not cite blogs, Medium posts, Papers with Code, SciSpace, or GitHub repositories as final scholarly references in the paper.
- Keep KVP, DRL-Clusters, and generic cloud/block-storage dataset claims out of the current LaTeX draft unless they are verified and become necessary.
