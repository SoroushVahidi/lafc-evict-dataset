# Glossary

Plain-language definitions for terms used throughout this dataset card, the
release documentation, and the AWS Open Data materials. Added 2026-09-12 to
close a documentation-clarity gap raised in SIGMOD 2027 reviewer feedback.

| Term | Meaning |
|---|---|
| Access / request | One item lookup against the simulated cache, replayed in sequence; the basic unit of trace replay. |
| Full-cache miss | An access that misses while the cache is already at its capacity limit, forcing an eviction decision. (A miss with free capacity requires no eviction and is not a decision point.) |
| Decision point / decision | The specific full-cache-miss event at which one resident object must be chosen for eviction. Identified by `decision_id`. |
| Resident victim candidate / candidate row | One row per object currently resident in the cache at a decision point, describing what would happen if that specific object were the one evicted. This is the unit of one published row. |
| Capacity | The number of objects the simulated cache can hold at once (32, 64, or 128 in the public v0.3 release). |
| Horizon | The fixed number of future requests over which a candidate's evicted-outcome label is measured (4 requests throughout v0.3). |
| Continuation policy | The policy assumed to run the cache forward, after a candidate is hypothetically evicted, when computing its label. The public release uses plain LRU continuation. |
| Counterfactual loss / `y_loss` | The number of cache misses over the next `horizon` requests that would occur if this specific candidate were evicted and the cache then continued under the continuation policy — the central supervision label. |
| Decision group | The full set of candidate rows sharing one `decision_id` (all resident objects considered at that decision point). Candidate rows from the same decision group must not be split across a user-constructed train/validation/test partition. |
