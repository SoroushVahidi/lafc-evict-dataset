# Differentiation Matrix

Legend: `yes`, `no`, `partial`

| Prior work | raw traces | cache policy | learned policy | labeled eviction decisions | per-candidate counterfactual labels | finite-horizon loss/value | pairwise / ranking task | reusable benchmark artifact | public code / data | difference from LAFC-Evict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Belady 1966 | no | yes | no | no | no | no | no | no | no | Foundational optimal replacement analysis, not a benchmark release |
| LIRS | no | yes | no | no | no | no | no | no | no | Algorithmic baseline only |
| ARC | no | yes | no | no | no | no | no | no | partial | Adaptive heuristic policy, not a labeled dataset |
| CLOCK-Pro | no | yes | no | no | no | no | no | no | partial | Practical replacement policy, not a reusable benchmark |
| GreedyDual-Size | no | yes | no | no | no | no | no | no | no | Cost/size-aware policy paper, not supervised benchmark data |
| TinyLFU / W-TinyLFU | no | yes | no | no | no | no | no | no | partial | Admission and software-cache management, but no candidate labels |
| RL-Cache | no | yes | yes | no | no | no | no | no | partial | Learned cache-admission policy, not public eviction supervision |
| ALPS | no | yes | yes | no | no | no | no | no | partial | Lightweight learned replacement policy, not benchmark artifact |
| Feedforward Neural Networks for Caching | no | yes | yes | no | no | no | no | no | partial | Learned policy comparison, not released supervision data |
| HR-Cache | no | yes | yes | no | no | no | no | no | partial | Edge caching policy framework, not decision-aligned benchmark release |
| Twemcache trace papers | yes | no | no | no | no | no | no | partial | yes | Public workload traces and analysis, but no per-candidate labels |
| UMass Trace Repository | yes | no | no | no | no | no | no | partial | yes | Repository of traces, not an eviction-label benchmark |
| YCSB | synthetic / workload generator | no | no | no | no | no | no | yes | yes | Benchmark workload generator, not labeled cache decisions |
| OLTP-Bench | workload / benchmark suite | no | no | no | no | no | no | yes | yes | Reusable DB benchmark, not cache-eviction supervision |
| Join Order Benchmark | query benchmark | no | no | no | no | no | partial | yes | yes | Strong benchmark framing example, but not a cache-label dataset |
| LETOR | no | no | no | no | no | no | yes | yes | yes | Ranking benchmark, not cache decision supervision |
| Yahoo! LTR Challenge | no | no | no | no | no | no | yes | yes | yes | Public ranking challenge, not eviction-labeled data |
| Counterfactual risk minimization / OPE / unbiased LTR | no | no | no | partial | no | no | yes | no | partial | Supplies learning principles, not a cache benchmark artifact |
| LAFC-Evict | trace-derived | no | no | yes | yes | yes | yes | yes | pending final public hosting | Decision-aligned benchmark with candidate, decision, and pairwise task views |
