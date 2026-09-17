# Problem 6 Phase 14: blind-reader test

Answered using ONLY the revised manuscript (post-rewrite). Each answer
cites the section(s) it comes from.

**Q1. What problem motivates LAFC-Evict?**
PASS. Abstract + Introduction, para 1: papers that predict which candidate
to evict typically derive their own labels from raw traces with different
traces/definitions/protocols, so a reported improvement is often not
attributable to the policy alone. LAFC-Evict removes that variable by
computing a common, reusable label.

**Q2. What is one physical eviction decision?**
PASS. Section 2 (Background and a Worked Example), "A worked eviction
decision": a full cache holding A, B, C; a miss on D forces evicting one of
A/B/C; those three are the candidate victims for that decision. Concrete,
numbered, precedes any formalism.

**Q3. What does y\_loss measure?**
PASS. Section 2 (worked example: "if this candidate, and no other, had
been evicted... how many of those requests would miss") and Section 4
(formal definition, the counted-miss formula). Both precede any aggregate
statistic.

**Q4. Why are there so many ties?**
PARTIAL PASS. Section 8 states the fact (67.7% all-tied) and Section 8d
explains the *mechanism for one family* (wiki2018: zero reuse events makes
ties a mathematical certainty) and gives *contributing factors* for other
families (capacity-scale reuse, Section 8d's locality correlation). The
manuscript does not claim a single universal cause of ties across all
families — correctly, since none exists — but a first-time reader may need
to read both Section 8 and Section 8d together to get the full picture
rather than finding it in one place. Acceptable given the actual science
(there is no single-sentence causal answer to give), but flagged as a
residual readability item.

**Q5. Does high random-optimal probability mean the benchmark is useless?**
PASS. Explicitly answered no, in the Abstract ("but an informativeness-
stratified analysis shows the benchmark is conditionally, not uniformly,
discriminative") and in Section 8 ("Interpretation" subsection and the
"headline random-optimal probability is also less catastrophic than it
sounds" paragraph), with the supporting mechanism (99.1% is dominated by
decisions where alternatives are exactly/nearly equivalent, not by failure
to find real regimes).

**Q6. What does expected random regret measure?**
PASS. Section 8, "Does informativeness translate into method separation?":
given as an explicit formula (mean loss across candidates minus the
minimum), in misses, zero for all-tied decisions.

**Q7. What happens as horizon increases?**
PASS. Abstract, Introduction (RQ3), and Section 8 (matched-population
paragraph): informativeness rises monotonically for every one of 787,762
matched decisions from H=16 to H=128, but more than half remain all-tied
even at H=128 — stated as both directions (rises, but does not eliminate
degeneracy), not just one.

**Q8. How sensitive are labels to continuation policy?**
PASS. Introduction (RQ4) and Section 8e give both the sampled-scale and
full-population-scale numbers (Jaccard overlap, cross-continuation regret)
and state the exact tested scope (MRU and random, capacities as evaluated)
without overclaiming beyond it.

**Q9. Do offline benchmark differences correspond to closed-loop policy differences?**
PASS. Introduction (RQ2) and Section 8c: agree in most, not all, regimes
where the offline signal is non-trivial, with two specific discordant
cells named and investigated in Section 8d, not hidden.

**Q10. What did the expanded ARC/LIRS/S3-FIFO experiment change?**
PASS. Abstract, Section 8b (subsection "Robustness to an Expanded
Comparator Set"): LRU no longer wins outright in nearly every cell once
compared against a broader set (4/10 vs. 9/10), but the offline-
discriminativeness/closed-loop-spread correlation is essentially
unchanged (r=0.96 vs. r=0.96) — stated as a correction to an earlier,
narrower reading, not hidden or minimized.

**Q11. What is the benchmark useful for?**
PASS. Section 8f (Practical Implications) gives concrete conditions (low
all-tied mass, high trace-derived LRU hit rate) for when the offline signal
can be trusted, and the Conclusion restates this as "a reproducible way to
ask whether a candidate-level eviction signal is informative before
building a policy around it."

**Q12. What should it NOT be used to claim?**
PASS. Stated in multiple places consistently: not a new eviction policy
(Introduction, Related Work "Positioning," Conclusion), not evidence that
a learned selector improves real cache performance without closed-loop
validation (Abstract, Conclusion), not a claim beyond the tested
capacities/horizons/continuation policies (Limitations).

## Summary
11/12 full PASS, 1/12 PARTIAL PASS (Q4 — the ties question has two answers
in two places because the underlying science genuinely has no single
unifying cause; this is a scientific fact, not a readability defect to
paper over, so it is reported rather than "fixed").
