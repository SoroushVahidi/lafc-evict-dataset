# Problem 6 Phase 5: repetition audit

For each repeated idea: every occurrence found, and the PRIMARY/SECONDARY/
REMOVE decision applied in the rewrite.

## 1. Headline tie statistics (0.9912 random-optimal / 0.6766 all-tied / 0.0 unique-winner)
Occurrences: Abstract, Introduction, Section 8 (twice, aggregate + interpretation),
Section 9 Limitations (item 4), Section 11 Conclusion.
- PRIMARY: Section 8 ("The uncomfortable aggregate facts, stated first").
- SECONDARY (one clause, no re-derivation): Abstract, Introduction, Conclusion.
- REDUCED: Limitations item 4 (was a near-full restatement; cut to a
  cross-reference plus the one sentence that adds a genuinely new
  scope point, "no result claims this generalizes beyond the audited
  population").

## 2. wiki2018 is a fully degenerate negative control (zero reuse events)
Occurrences: Benchmark Design, Section 8 (twice), Section 8b, Section 8d
(the actual deductive proof), Section 8f, Section 9 Limitations.
- PRIMARY: Section 8d ("causally established" deductive proof — this is the
  only place the *mechanism* is proved, everywhere else just asserts the
  fact).
- SECONDARY: Benchmark Design (one clause, first mention), Section 8
  (one clause), Section 8b (one clause, needed for the closed-loop number).
- REMOVED: the repeated re-explanation of *why* in Section 8f and the
  second mention in Section 9 Limitations; both now cross-reference 8d.

## 3. metakv/cap128 is the one closed-loop exception to LRU dominance
Occurrences: Section 8b (twice within the section), 8c, 8d (the
investigation), 8f, Section 9 Limitations.
- PRIMARY: Section 8d (the actual investigation of candidate causes).
- SECONDARY: Section 8b (where the number is first reported).
- REDUCED: 8c's restatement condensed to a clause; 8f's and Limitations'
  mentions condensed to a clause pointing at 8d.

## 4. "The offline label is not a substitute for closed-loop evaluation" / benchmark scope
Occurrences: Introduction, Section 8f, Section 9b Discussion, Section 9
Limitations (item 1), Section 11 Conclusion.
- PRIMARY: Section 8f (practical implications is the natural home for this
  guidance).
- SECONDARY: Introduction (one sentence, sets reader expectation early),
  Conclusion (one clause).
- REMOVED: Section 9b Discussion's version, which added no new evidence
  over 8f; Section 9b is compressed rather than restating this.

## 5. LRU-continuation caveat / continuation-policy robustness scope
Occurrences: Label Generation, Release Validation, Section 8e (the
evidence), Section 8f, Section 9b Discussion, Section 9 Limitations (item
3), Section 11 Conclusion.
- PRIMARY: Section 8e (the actual evidence).
- SECONDARY: Label Generation (one clause, states the modeling choice),
  Conclusion (one clause).
- REMOVED/CONDENSED: Release Validation's "two label sources must not be
  conflated" box is folded into one sentence; Section 9b's restatement is
  cut; Limitations keeps only the scope boundary not already stated (no
  claim beyond MRU/random at the tested capacities).

## 6. "Every number traces to a validated, gate-checked artifact"
Occurrences: Introduction, Section 3b, Section 6 (twice), Section 11
Conclusion (implied).
- PRIMARY: Section 6 (Release Validation), where the actual gates are listed.
- SECONDARY: Introduction (one sentence, reproducibility claim upfront).
- REMOVED: Section 3b's restatement of the same claim in different words;
  replaced with a one-line pointer to Section 6.

## 7. Five workload families / dataset row counts
Occurrences: Abstract, Introduction, Benchmark Design, Section 7, Data
availability (front matter).
- PRIMARY: Benchmark Design (where families are introduced) and Data
  availability (where exact release counts belong).
- SECONDARY: Abstract, Introduction (family count only, no row counts).
- No further action needed — these are short, load-bearing mentions, not
  re-explanations.

## 8. "Not a new eviction policy" / scope-of-contribution disclaimer
Occurrences: Introduction, Section 10 (Related Work, "Positioning"), Section
11 Conclusion.
- PRIMARY: Section 10 (this is where the full positioning argument belongs).
- SECONDARY: Introduction (one sentence, up front).
- REMOVED: Conclusion's restatement folded into the synthesis sentence
  instead of repeated as its own claim.

## 9. Unit-object / count-based capacity abstraction caveat
Occurrences: Benchmark Design, Label Generation, Section 9 Limitations
(item 5).
- PRIMARY: Benchmark Design (states the scope boundary once, explicitly).
- SECONDARY: Limitations (one sentence expanding on consequences).
- Label Generation's parenthetical is redundant with Benchmark Design and
  is trimmed to a cross-reference.

## Net effect
Three sections absorbed almost all of the cuts without losing evidence:
Section 9b (Discussion) is compressed by roughly half, Section 9
(Limitations) loses two fully-restated paragraphs (kept as one-line
cross-references), and Section 11 (Conclusion) no longer re-lists every
number from the Abstract/Introduction — it synthesizes instead. No
evidence, caveat, or number is deleted; only the *n*-th restatement of an
already-established fact is cut, per Phase 5's PRIMARY/SECONDARY/REMOVE
rule.
