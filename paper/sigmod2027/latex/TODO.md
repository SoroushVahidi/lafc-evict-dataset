# LaTeX Draft TODO

## Highest priority

- Add formal notation for the counterfactual label.
- Add the benchmark overview figure.
- Add the artifact layout figure.
- Tighten the generated metadata-backed tables so they fit the SIGMOD page budget cleanly.
- Decide how prominently to present the current light pairwise sanity baselines versus holding richer baselines for the next draft.

## Anonymity checks

- Re-scan all manuscript text for names, affiliations, URLs, and repository identities.
- Keep acknowledgments out of the submission draft.
- Avoid public preprint citations in the anonymous version.

## Technical dependencies

- Full real-release validation still pending.
- Anonymous artifact packaging still pending.
- Metadata-backed statistics tables are now available from `paper/sigmod2027/technical/extract_metadata_tables.py`.
- Candidate-row label-distribution statistics are still pending because they require a candidate-row scan or additional precomputed metadata.
- Baseline experiment plans and runner stubs now exist under `paper/sigmod2027/technical/` and `scripts/sigmod2027/`.
- Feature-based pairwise baselines are still blocked on a candidate-row feature join or an augmented pairwise export.

## Editing priorities

- Tighten the introduction and related-work sections to fit the 12-page SIGMOD limit without losing the benchmark differentiation.
- Move long schema descriptions to appendix if needed.
- Keep release-engineering detail concise in the main text.
- Decide which of the generated characterization tables stay in the main paper versus appendix.

## Metadata-backed tables now available

- Dataset scale: manifest-backed, with full validation explicitly marked pending.
- Split counts: manifest-backed candidate-row counts.
- Decision breakdowns by family, capacity, horizon, and split: decision-view-backed.
- Candidate-count statistics: decision-view-backed overall and per family.
- Tie and regret summaries: decision-view-backed.
- Pairwise sample balance and label distribution: pairwise-sample-backed.
- Artifact layout table: release-relative and manuscript-safe.

## Still pending for characterization

- Candidate-row `y_loss` distribution summaries.
- Candidate-row `y_value` distribution summaries.
- Any per-family row-level label histograms or quantiles that require candidate-row scanning.

## Baseline status

- Pairwise sample first:
  shipped sample supports light sanity baselines now, and current results are recorded under `paper/sigmod2027/results/baselines/pairwise/`.
- Value regression:
  planning stub exists, but full-scale candidate-row execution belongs on Wolverine.
- Best-candidate prediction:
  planning stub exists, but full-scale candidate-row execution belongs on Wolverine.

## Remaining benchmark-task risks

- Pairwise sample is highly tie-heavy, so the paper must state clearly whether pairwise evaluation is over all rows or over the non-tie subset.
- The shipped pairwise sample lacks candidate-side feature columns, which blocks LRU-derived and predictor-derived pairwise baselines unless a feature join is added.
- Full real-release validation is still pending, so all current benchmark numbers must remain explicitly metadata-backed or view-backed rather than fully certified.
- The majority non-tie baseline looks artificially strong on train and validation because the non-tie subset is highly imbalanced; that must be framed as a sanity check, not a meaningful learned result.

## Related-work verification

- Verify whether `DRL-Clusters` has any archival systems paper worth citing; otherwise leave it out.
- Decide whether `HR-Cache` stays in the main related-work section or becomes a short secondary mention.
- Keep `KVP / Learning to Evict from Key-Value Cache` out unless the paper explicitly expands to KV-cache-specific literature.
- If any cloud/block-storage trace family claim is added, replace the broad phrase with exact dataset citations.

## Missing or deferred BibTeX work

- Add additional unbiased-ranking references only if the ranking subsection needs more depth after page budgeting.
- Add a concrete citation for any benchmark-governance or dataset-documentation framing paper only if it becomes necessary.

## Related-work claims needing explicit source confirmation

- ``To our knowledge'' claim about the absence of prior public caching datasets with per-candidate finite-horizon counterfactual eviction labels at this scale.
- Any claim about whether a prior learned-caching paper releases data, code, or only policy results.
- Any future comparison that names an exact ``state-of-the-art'' learned caching policy beyond the currently verified set.

## Essential before abstract submission

- Classical caching citations: Belady, LIRS, ARC, CLOCK-Pro, GreedyDual-Size, TinyLFU/W-TinyLFU.
- Learned caching citations: RL-Cache, ALPS, Feedforward Neural Networks for Caching.
- Benchmark and trace citations: Twemcache trace analysis, UMass Trace Repository, YCSB, OLTP-Bench, JOB.
- Ranking/counterfactual anchors: CRM, contextual-bandit OPE, unbiased LTR, Liu survey, LETOR, Yahoo! LTR.

## Can wait until the full-paper deadline

- Optional HR-Cache inclusion.
- Optional Narita et al. counterfactual-learning citation if the counterfactual-learning subsection grows.
- Any KV-cache, LLM-cache, or broader edge-caching expansion.
