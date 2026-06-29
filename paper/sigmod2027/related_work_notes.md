# Related Work Notes

These are categories to search and cite later, not final bibliography entries.

## 1. Cache replacement and eviction policies

- Classical policies:
  LRU, LFU, ARC, CLOCK variants, Belady-inspired approximations.
- Trace-driven empirical studies of replacement behavior.
- Evaluation criteria used in cache-policy papers.

## 2. Learned caching and learning-augmented caching

- Learned eviction policies.
- Predictor-assisted caching.
- Learning-augmented online algorithms.
- Offline-to-online evaluation gaps in learned systems.

Questions to answer:

- How do prior papers define supervision?
- Do they release data?
- Do they evaluate across multiple trace families and capacities?

## 3. Counterfactual supervision and offline policy evaluation

- Counterfactual labels for decision making.
- Offline evaluation for combinatorial or structured decisions.
- Pairwise preference supervision versus value regression.
- Regret-oriented evaluation methods.

Questions to answer:

- What is novel about decision-aligned candidate supervision here?
- How should the paper distinguish finite-horizon counterfactual labels from global optimality claims?

## 4. Systems benchmarks and workload characterization

- Benchmark construction in systems and data management.
- Workload characterization methodologies.
- Dataset papers that emphasize composition analysis and reuse guidelines.

Questions to answer:

- What makes a systems benchmark trustworthy?
- Which validation and artifact practices are expected in SIGMOD benchmark papers?

## 5. Dataset and benchmark papers in data management and systems

- SIGMOD, VLDB, NSDI, OSDI, MLSys, and related benchmark/data papers.
- Experiment & Analysis papers that emphasize empirical comparability.
- Artifact and reproducibility papers in systems venues.

Questions to answer:

- How do successful benchmark papers balance dataset description against experimental results?
- What is the right level of release-engineering detail in the main paper?

## 6. Trace-driven cache evaluation

- Public trace repositories used for cache studies.
- CDN, KV-store, storage, and pageview-derived trace families.
- Caveats around mixing heterogeneous workloads into one benchmark.

Questions to answer:

- How should the paper justify cross-family heterogeneity?
- What prior work exists on trace-family transfer or cross-workload generalization?
