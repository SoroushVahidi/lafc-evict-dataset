# Cover Letter Draft — Performance Evaluation Submission

Status: DRAFT for the author's review before use. Do not send. Placeholders
in `[ ]` require the author to fill in or confirm (submission date,
editor name if known, journal-specific portal fields).

---

Dear Editor,

Please consider our manuscript, "LAFC-Evict: A Large-Scale Counterfactual
Benchmark for Learned Cache Eviction," for publication in *Performance
Evaluation* as a full-length original research article.

This paper studies how to construct and evaluate counterfactual
supervision for cache-eviction decisions -- a per-decision,
per-candidate, finite-horizon counterfactual miss-cost label computed
from real cache traces -- and asks five evaluation-methodology questions
about it: whether the resulting target is actually discriminative between
candidates and where it degenerates; whether the offline candidate
ranking corresponds to actual closed-loop cache performance; how that
correspondence depends on workload, capacity, and horizon; how sensitive
the resulting labels are to the continuation-policy assumption used to
construct them; and what this implies for practitioners deciding when to
trust offline supervision in place of, or alongside, closed-loop
evaluation.

We believe this work is a good fit for *Performance Evaluation*: the
central contribution is a measurement and evaluation methodology --
including a production-derived closed-loop evaluation across five trace
families, two cache capacities, and multiple policies, and a
pre-registered continuation-policy robustness study -- rather than a new
eviction policy or a purely dataset-release contribution. The released
benchmark artifact exists to support this evaluation methodology and to
let other researchers reuse and extend it; it is not itself the paper's
central argument.

Every quantitative claim in the manuscript is traced to an independently
validated, gate-checked evidence artifact, and we have been deliberately
conservative about scope: we report continuation-policy robustness with
its exact tested scope (sampled MRU/random continuation at two
capacities; a separate full-population census for MRU continuation at
four capacities) rather than as a general robustness claim, and we
identify and mechanistically explain a workload for which the offline
target is fully degenerate rather than omitting it.

This manuscript is not under review, and has not been published, at any
other journal or conference. We wish to disclose that a related manuscript,
currently under consideration at *Knowledge-Based Systems*, focuses on the
design and closed-loop evaluation of a learned cache-eviction model/policy. The
present *Performance Evaluation* manuscript instead focuses on the LAFC-Evict
counterfactual dataset and evaluation benchmark, including target
characterization, degeneracy, horizon/capacity sensitivity, continuation
robustness, offline–closed-loop correspondence, expanded comparator
robustness, and release methodology. The two works share some underlying
caching infrastructure and counterfactual-label concepts, and the related
submission is disclosed for editorial consideration to ensure complete
transparency.

Thank you for considering our manuscript. We look forward to your
response.

Sincerely,

Soroush Vahidi
New Jersey Institute of Technology
sv96@njit.edu

---

## Notes for the author (remove before submission)

- This draft intentionally avoids exaggerated novelty language ("first,"
  "unprecedented") consistent with the manuscript's own claim-strength
  discipline.
- The bracketed paragraph about prior submission history is a factual
  question only the author can answer accurately; most journals'
  submission systems ask this directly as a form question rather than
  requiring it in the letter itself -- keep or delete this paragraph
  depending on what the Editorial Manager submission form actually asks.
- Confirm whether *Performance Evaluation* requires a cover letter at all
  before submission (see `docs/PE_SUBMISSION_REQUIREMENTS_20260915.md`,
  "Cover letter" row -- this could not be confirmed via a first-party
  Elsevier page fetch in this audit and should be re-checked directly on
  ScienceDirect).
