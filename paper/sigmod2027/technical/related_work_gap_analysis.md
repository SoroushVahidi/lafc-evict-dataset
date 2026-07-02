# Related Work Gap Analysis

## Purpose

This note records the cautious artifact-positioning update made while the Wolverine result jobs were running. It is intentionally narrower than a full literature survey: the goal is to sharpen the manuscript's taxonomy and novelty wording without adding unverified bibliography metadata.

## External investigation summary integrated cautiously

- Existing cache artifacts often provide raw traces, workload studies, simulators, oracle-like features, or learned eviction frameworks.
- PARROT is relevant as a learned replacement and Belady-imitation reference point, but not as a released static dataset of per-candidate finite-horizon counterfactual labels.
- MAT is relevant as a learned eviction framework with low overhead, but not as a public candidate-label dataset.
- S3-FIFO and SIEVE are relevant modern policy artifacts, but they remain algorithm/evaluation endpoints rather than supervised benchmark releases.
- Learning-augmented caching theory papers by Lykouris/Vassilvitskii and Wei are relevant because they separate predictive advice from online policy behavior, but they do not release reusable eviction-label datasets.
- The manuscript should position LAFC-Evict as complementary to trace, simulator, and policy artifacts rather than as replacing them.

## What was integrated into the manuscript

The related-work section in `paper/sigmod2027/latex/sections/10_related_work.tex` was reorganized into a clearer taxonomy:

1. trace datasets, workload studies, and benchmark surfaces
2. learned eviction and imitation learning
3. modern eviction policies
4. learning-augmented caching and predictive advice
5. benchmark and dataset positioning

The manuscript now states explicitly that:

- existing trace libraries and simulators provide the substrate for cache evaluation;
- \lafc\ packages a different layer of supervision, namely per-decision, per-candidate finite-horizon counterfactual labels plus decision and pairwise views;
- the artifact is meant to complement traces, simulators, and policy papers;
- the novelty wording is cautious and uses "to our knowledge" rather than absolute claims.

## Citations already present and reused

- `liu2020parrot`
- `yang2023mat`
- `yang2023s3fifo`
- `zhang2024sieve`
- `jiang2002lirs`
- `megiddo2003arc`
- `jiang2005clockpro`
- `einziger2017tinylfu`
- `einziger2018wtinylfu`
- `lykouris2021mladvice`
- `wei2020learningaugcache`
- `umasstracerepo`
- `atikoglu2012kvworkload`
- `yang2020twemcache`
- `cooper2010ycsb`
- `difallah2013oltpbench`
- `leis2018job`
- `swaminathan2015crm`
- `li2011offlinecb`
- `joachims2017unbiasedltr`
- `liu2009ltr`
- `qin2010letor`
- `chapelle2011yahoo`
- `saito2020pairwise`

## Citations added

- None. The manuscript revision strengthened positioning through taxonomy and wording changes only.

## Citations deferred because metadata or artifact status still needs verification

- `cacheMon` / `cache_dataset`
- `libCacheSim`
- `ChampSim` / CRC-2 traces
- `CacheQuery`
- `Thesios`
- `QD-LP` / "FIFO can be Better than LRU: the Power of Lazy Promotion and Quick Demotion"
- `LRB` ("Learning Relaxed Belady")
- `LHD` ("Learning Cache Replacement with Cacheus" is `rodriguez2021cacheus`, already cited; `LHD` refers to the separate "Least Hit Density" replacement policy)
- `GL-Cache`
- `FOO` / `PFOO` (approximate-Belady offline algorithms)

These names came from the external investigation, but this repo does not currently contain verified BibTeX metadata for them in `paper/sigmod2027/latex/refs.bib` or a corresponding verified reference-audit entry. They should be added only after a separate metadata pass against authoritative sources.

## Comparison table decision

- Main-paper comparison table: deferred.
- Reason: the current manuscript already has a tight 12-page SIGMOD budget, and the prose taxonomy plus the existing internal files `related_work/differentiation_matrix.md` and `related_work/taxonomy_table.md` already capture the comparison logic.

## Recommended cautious novelty wording

Recommended sentence for the main paper:

> Existing trace libraries and simulators provide the substrate for cache evaluation, and some public artifacts expose oracle-style features or procedural oracle policies. To our knowledge, however, we are not aware of a public cache-eviction artifact that releases reusable candidate-level finite-horizon counterfactual supervision together with decision-level and pairwise task views at this scale.

Recommended shorter variant:

> \lafc\ complements existing traces, simulators, and policy artifacts by releasing a reusable supervision layer rather than another eviction rule.
