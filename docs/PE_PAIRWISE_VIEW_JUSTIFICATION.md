# Why a Pairwise Derived View, and Its Provenance Status

Status: PARTIALLY_COMPLETE prior to this task. The provenance facts were
already documented (`analysis/pairwise_provenance_repair_20260913/`,
summarized in the prior handoff Section 7); no document previously stated
the *scientific rationale* for the pairwise view's existence, which is the
part this task adds.

## Reviewer question

*Why is a pairwise derived view useful if candidate losses (`y_loss`)
already induce a total ordering (with ties) over candidates within a
decision?*

## Answer: it is a derived task view, not a new label source

The pairwise view adds **no new ground-truth information**. Every pairwise
preference label in it is computed directly from the same candidate-level
`y_loss` values already present in the candidate view (see
`PE_WORKED_EXAMPLE.md` Section 8 for a concrete, checkable derivation). A
manuscript must state this explicitly and not imply the pairwise sample was
independently measured.

Given that, the pairwise view is still useful, for four separable reasons:

1. **Learning-to-rank / pairwise-loss algorithms.** A large family of
   ranking methods (RankNet-style pairwise losses, pairwise logistic
   regression, pairwise SVM formulations) is naturally expressed over pairs
   rather than over an absolute regression target. Exposing a pre-built
   pairwise sample lets a researcher use these methods directly on the
   released data without re-deriving pairs from the candidate view
   themselves — a convenience, not a new capability.
2. **Direct preference classification.** Some methods (and some evaluation
   protocols) are stated as binary or three-way preference classifiers
   ("is A better, worse, or tied with B") rather than as value regressors.
   The pairwise view is the natural interface for training or evaluating
   such a classifier without requiring it to also learn to regress
   `y_loss` correctly in absolute terms.
3. **Tie-aware pair construction.** Because the target is substantially
   tied in aggregate (`PE_CLAIM_EVIDENCE_LEDGER.md` C1: all-tied fraction
   0.677), naive pair construction (e.g., "for every pair, whichever has
   lower loss wins") silently discards or mislabels tied pairs unless the
   tie case is handled explicitly. The released pairwise view encodes tie
   as a first-class label value (see the worked example's (A, C) row), so
   downstream users inherit a tie-correct pair sample rather than each
   re-implementing tie handling independently and potentially
   inconsistently.
4. **Diagnostic analysis of preference reversals.** A pairwise
   representation makes certain diagnostics cheap to compute directly on
   the released artifact — e.g., the continuation-policy-sensitivity
   study's "strict reversal fraction" metric (`PE_CLAIM_EVIDENCE_LEDGER.md`
   C10) is naturally a pairwise-reversal count. Having the pairwise view
   pre-built is convenient for this kind of analysis even when the
   researcher is not training a pairwise model at all.

None of these four reasons requires or implies that the pairwise view
carries information beyond what `y_loss` already encodes at the candidate
level. The manuscript's methodology section should state the derivation
relationship first (Section 5/Section 8 of the worked example) and the four
motivations second, in that order, to avoid implying novelty in the data.

## Provenance issue: canonical regenerated sample vs. historical stale shipped sample

Already established in `analysis/pairwise_provenance_repair_20260913/`
(re-verified, not re-derived, for this task):

| | Historical shipped sample | Canonical regenerated sample |
|---|---:|---:|
| File | `release/lafc-evict-v0.1-open-current-contract-preserved/data/pairwise_sample/pairwise_sample.parquet` | `analysis/pairwise_provenance_repair_20260913/artifacts/pairwise_sample_regenerated_canonical.parquet` |
| a_better | 6,134 | 60,673 |
| b_better | 113,898 | 61,065 |
| tie | 879,968 | 878,262 |
| SHA256 | (historical, noncanonical) | `1d770c6999ac999673b46805a6ca173e24b116793b35405d2d211cae7b9eda02` |

Root cause (already documented, verified consistent again for this task):
the historical decision-selection hash used a six-column key; the canonical
pipeline uses a nine-column key. The historical sample's near-total
imbalance toward `b_better` (113,898 vs. 6,134) versus the canonical
sample's near-balance (61,065 vs. 60,673) is itself strong internal
evidence the historical sample was built from a different, non-canonical
decision selection, not just resampled noise.

**Does the intended PE manuscript need an artifact repair before
submission, or can it simply cite the canonical regenerated sample?**

Assessment: **the manuscript can use the canonical regenerated sample's
provenance and statistics directly; no further artifact repair is required
for the manuscript itself.** The regenerated parquet is already durably
tracked in Git (`analysis/pairwise_provenance_repair_20260913/artifacts/`,
11,367,843 bytes, `TRACKED_IN_GIT`), its SHA256 is fixed and citable, and
the regeneration script (`analysis/pairwise_provenance_repair_20260913/scripts/regenerate_pairwise_v2.py`)
is documented. What remains outstanding is a **separate, non-manuscript**
artifact/release decision: whether to promote the regenerated sample into
the *public* release (replacing the historical stale one there). That
promotion decision was explicitly deferred in the prior handoff ("do not
promote this analysis sample into a public release without a separate
release decision") and remains deferred by this task — it is a release
action, not a manuscript-preparation action, and this task does not
perform it. The manuscript's artifact/reproducibility section should state
plainly that the analysis in the paper uses the canonical regenerated
sample (citing its SHA256) and that the public release's pairwise artifact
is being brought into alignment with it as a separate, tracked release
task.
