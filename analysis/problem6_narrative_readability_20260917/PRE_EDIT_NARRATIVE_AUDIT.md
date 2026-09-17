# Problem 6 Phase 1: pre-edit narrative audit

Date: 2026-09-17. Read in full: `main.tex` (front matter, abstract, end
declarations) and all 20 `sections/*.tex` files, beginning to end, before any
edit.

For each section: why it exists, the question it answers, what new
information the reader gets, and whether that information is repeated
elsewhere.

| # | Section | Why it exists | Question answered | New info for reader | Repeated elsewhere? |
|---|---|---|---|---|---|
| - | Abstract | Entry point | What is this paper's whole argument? | Everything, compressed | Yes — restates almost verbatim in Intro and Conclusion |
| 1 | Introduction | Frame the problem and contribution | Why does counterfactual eviction supervision matter, and what does this paper claim? | Problem statement, 5 RQs, contribution scope | RQ answers restated near-verbatim from abstract; restated again in Conclusion |
| 2 | Background / Worked Example | Ground terminology before formalism | What is one eviction decision, concretely? | Worked numeric example (candidates, `y_loss`, a tie) | Good — this is the only place the worked example lives |
| 3 | Benchmark Design | State the abstraction and design requirements | What is a trace/cache state/decision, and what does the release cover? | Formal abstraction, 5 families, scope boundary (unit-object, unconditional admission) | wiki2018-is-a-control-workload claim repeated 4+ more times later |
| 3b | Experimental Methodology | Consolidate protocol once | What scope/caveats apply to every later result? | Capacities/horizons per analysis, split terms, metric definitions | Some of this (MetaCDN validation-window, MetaKV cold-start) is re-explained again in Limitations and Discussion |
| 4 | Label Generation | Formal definition of `y_loss` | What exactly is the label, mathematically? | Formula, `y_loss`/`y_value` duality, scope statement | The "not offline-optimal, finite-horizon, continuation-tied" scope statement is repeated in Limitations and Conclusion |
| 5 | Schema and Views | Document release columns | What columns exist in the released files? | Column names, decision/pairwise view definitions | Reads as a data dictionary; column names are barely used again — the most report-like section in the paper |
| 6 | Release Validation | Document the release pipeline/QA | Was the released artifact validated? | Pipeline steps, validation checklist, provenance caveat | The "every number traces to a validated artifact" claim is repeated in 3b, 7, and Conclusion |
| 7 | Tasks and Baselines | Define benchmark tasks; report baselines | What can you do with this data, and how weak/strong are simple baselines? | 4 task definitions, feature-degeneracy finding, 3 baseline results | Feature-degeneracy paragraph is release-audit prose (schema-repair narrative) more than a scientific result |
| 8 | Characterization (RQ1) | Answer RQ1 | Is the target discriminative? | 0.9912/0.68/0.0 headline stats, per-family variation, matched-horizon result, informativeness-stratified separation | The 0.9912/0.68 numbers already appear in the Abstract and Introduction; restated again in Limitations and Conclusion |
| 8b | Closed-Loop (RQ2 pt.1) | Report actual policy replay | How do real policies perform? | Tier-1 table, "LRU best in 9/10", expanded ARC/LIRS/S3-FIFO subsection | The "LRU no longer wins outright" correction is stated three times within this one section |
| 8c | Linkage (RQ2 pt.2 / RQ3) | Compare offline vs.\ closed-loop orderings | Does the offline ranking predict closed-loop behavior? | Concordance/correlation numbers, two discordant cells | metakv/cap128 exception restated (already named in 8b) |
| 8d | Mechanistic (RQ3 pt.2) | Explain *why* discriminativeness varies | What trace property drives the pattern? | Capacity-scale-reuse correlation, wiki2018 deductive proof, metakv/twemcache case studies | This is the single best place for the wiki2018 and metakv explanations; every other section should point here instead of re-explaining |
| 8e | Continuation (RQ4) | Robustness to continuation-policy choice | Do the labels depend on assuming LRU continuation? | Sampled + population MRU/random robustness numbers | Restated in Discussion, Limitations, Conclusion |
| 8f | Practical Implications (RQ5) | Practitioner guidance | When should the offline signal be trusted? | Synthesis rules of thumb | Substantial overlap with Discussion (9b) and Limitations (9) — three consecutive synthesis sections |
| 9b | Discussion | High-level synthesis | What did the evaluation add beyond the surface itself? | Little that is new; mostly re-summarizes 8/8c/8d/8e | Heavily overlaps 8f and 9 |
| 9 | Limitations | Scope and caveats | What should a reader NOT conclude? | 8 numbered caveats | Several caveats (wiki2018, tie fraction, continuation scope) restate earlier sections in full rather than cross-referencing |
| 10 | Related Work | Position against prior work | What's actually new here? | Citation landscape, explicit non-claims | Reasonably tight already |
| 11 | Conclusion | Synthesize | What did the paper establish, and what's next? | Should be synthesis only | Re-lists all 5 RQ answers with numbers already given 2-3 times earlier — the most redundant section in the paper |
| 12 | AI-use disclosure | Policy-mandated | — | — | N/A (mandated declaration, out of scope for rewrite) |
| 13 | Appendix tables | Move schema tables out of main text | — | — | Already correctly placed outside main narrative |

## Top findings (drive Phases 2-9)

1. **Report-like sections**: 05 (Schema/Views) and 06 (Release Validation) are
   the clearest cases of documentation-style prose in the main narrative —
   column names, pipeline steps, and validation checklists with little
   scientific argument. 07's feature-degeneracy paragraph is also
   audit-report prose.
2. **Three consecutive synthesis sections** (8f Practical Implications, 9b
   Discussion, 9 Limitations) say overlapping things from slightly different
   angles. This is very likely the direct cause of the "reads like a report"
   / "repetition and excessive length" feedback.
3. **The same 3-4 headline facts are repeated 4-6 times each** across
   Abstract, Introduction, Characterization, Limitations, and Conclusion:
   the 0.9912/0.68/0.0 triple, wiki2018's degeneracy, the metakv/cap128
   exception, and the LRU-continuation caveat. See `REPETITION_AUDIT.md`.
4. **AI-like prose patterns** recur throughout: heavy use of "X, not Y"
   antithesis pairs, "This is not a claim that..." hedges, sentences whose
   grammatical subject is an abstraction ("This label has two
   consequences...", "These boundaries are central to..."), and a vague
   umbrella noun ("supervision surface" / "evaluation surface" / "label
   surface") used as if it were one defined term. See Phase 7 edits.
5. **Terminology is mostly already sound**: the worked example correctly
   precedes formal notation (Section 2 already does what a SIGMOD reviewer
   asked for), and most jargon is defined at first use. The main terminology
   problem is redundant near-synonyms for "the dataset/benchmark" rather
   than undefined jargon. See `TERMINOLOGY_AUDIT.csv`.
6. **No missing worked example** — Phase 10's requirement is already met by
   Section 2; this audit does not recommend adding a second one.
