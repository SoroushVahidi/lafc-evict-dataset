# Ethics and Limitations

## Scientific limitations

- The default `v1` label is finite-horizon and continuation-policy-specific.
- The main label uses LRU continuation after forcing a candidate eviction.
- A finite-horizon counterfactual label is not equivalent to a global optimal control target.
- Performance on these labels does not by itself prove online deployment quality.

## Data limitations

- Upstream trace families may reflect different domains, logging practices, sampling procedures, and preprocessing assumptions.
- Some trace families may contain operational or behavioral patterns that should not be redistributed without review.
- A public release may include only a subset of the internally generated dataset families.

## Privacy and legal considerations

- Do not assume raw or processed trace redistribution is allowed.
- CitiBike and Brightkite require explicit license and privacy review before redistribution decisions.
- Derived benchmark rows may still require provenance and license documentation if they were generated from restricted sources.

## Benchmark interpretation

- Pairwise and decision views are derived tasks, not new measurements from upstream providers.
- Report results with the label definition, horizon, capacity, and release profile clearly stated.
