# A Worked Cache-Eviction Decision Example

Status: NOT_PRESENT prior to this task (repository-wide search found no
existing worked example of this kind; SIGMOD reviewers repeatedly asked for
one — see `analysis/closed_loop_offline_linkage_20260914/REVIEWER_ISSUE_MATRIX.md`
item #7, "NOT_ADDRESSED" until now). This document is self-contained,
uses only toy objects A-G, and every number below can be checked by hand.

This example is written for a reader who has not seen the dataset schema.
It uses plain vocabulary: request, cache miss, eviction decision, candidate
victim, future requests, counterfactual miss cost, optimal candidate set.

## 1. Setup

Cache capacity: 3 objects (unit-sized; count-capacity abstraction).

Immediately before the decision, the cache holds three objects, ordered
from least-recently-used to most-recently-used:

```
LRU end                      MRU end
[ A ]        [ B ]        [ C ]
```

## 2. The eviction decision

A request arrives for object **D**, which is not in the cache: a **cache
miss**. The cache is full, so admitting D requires evicting exactly one
resident object. The three resident objects — A, B, C — are the
**candidate victims** for this decision.

## 3. The future window and the continuation policy

We look ahead **H = 3 future requests**, which turn out to be:

```
B, E, F
```

To score each candidate victim, we ask: *if this particular candidate (and
no other) had been evicted right now, and D admitted, how many of the next
H requests would miss?* After the forced eviction, the cache continues to
evict under a **continuation policy** — here, plain LRU, the canonical
choice used throughout the dataset (see `PE_CLAIM_EVIDENCE_LEDGER.md`,
cross-cutting caveats, and the continuation-policy-sensitivity result for
what happens if this assumption is relaxed). This gives three counterfactual
worlds, one per candidate, that are simulated independently and compared.

## 4. The three counterfactual worlds

**World A (evict A):** state after evicting A and admitting D:
`[B, C, D]` (LRU end to MRU end).

| Step | Request | Resident before | Outcome | Resident after (LRU->MRU) |
|---|---|---|---|---|
| 1 | B | B,C,D | **HIT** | C,D,B |
| 2 | E | C,D,B | MISS (evict C) | D,B,E |
| 3 | F | D,B,E | MISS (evict D) | B,E,F |

Misses in window: 2 (E, F). **y_loss(A) = 2.**

**World B (evict B):** state after evicting B and admitting D:
`[A, C, D]`.

| Step | Request | Resident before | Outcome | Resident after (LRU->MRU) |
|---|---|---|---|---|
| 1 | B | A,C,D | MISS (evict A; B is gone, it was just evicted) | C,D,B |
| 2 | E | C,D,B | MISS (evict C) | D,B,E |
| 3 | F | D,B,E | MISS (evict D) | B,E,F |

Misses in window: 3 (B, E, F). **y_loss(B) = 3.**

**World C (evict C):** state after evicting C and admitting D:
`[A, B, D]`.

| Step | Request | Resident before | Outcome | Resident after (LRU->MRU) |
|---|---|---|---|---|
| 1 | B | A,B,D | **HIT** | A,D,B |
| 2 | E | A,D,B | MISS (evict A) | D,B,E |
| 3 | F | D,B,E | MISS (evict D) | B,E,F |

Misses in window: 2 (E, F). **y_loss(C) = 2.**

All three worlds converge to the same resident set `[B, E, F]` after step 3
— an incidental feature of this small example, not a general property.

## 5. Candidate-level labels

`y_value` is defined as `-y_loss` (see `PE_YLOSS_YVALUE_DECISION.md` for
why the dataset schema stores both).

| Candidate | y_loss (counterfactual miss cost) | y_value | Optimal? |
|---|---:|---:|---|
| A | 2 | -2 | yes |
| B | 3 | -3 | no |
| C | 2 | -2 | yes |

**Optimal candidate set = {A, C}.** This decision has **no unique winner**:
A and C cost exactly the same in the future window (neither is needed again
before the window ends), while evicting B is strictly worse (B is needed
again immediately). A method that scores "the" single correct answer as A
and marks C wrong would be penalizing a candidate that is, by the same
counterfactual measure, equally correct. This is exactly why the dataset
reports an **optimal candidate set** per decision rather than a single
label, and why aggregate statistics distinguish "all candidates tied"
(every candidate equally good or bad) from "some candidates tied at the
optimum, others strictly worse" (this example) from "a unique winner"
(none of the three cases here).

## 6. Decision-level view

One row summarizing the whole decision:

| decision_id | resident_before | requested | candidates | H | continuation_policy | optimal_candidate_set | num_candidates | all_tied | unique_winner |
|---|---|---|---|---|---|---|---:|---|---|
| toy-1 | {A,B,C} | D | {A,B,C} | 3 | LRU | {A,C} | 3 | false | false |

## 7. Candidate-level view

One row per (decision, candidate) — this is the primary supervised table:

| decision_id | candidate | y_loss | y_value | is_optimal |
|---|---|---:|---:|---|
| toy-1 | A | 2 | -2 | true |
| toy-1 | B | 3 | -3 | false |
| toy-1 | C | 2 | -2 | true |

## 8. Pairwise derived view

For every unordered pair of candidates within the decision, the pairwise
view derives a preference label directly from the candidate-level y_loss
values already computed above — it introduces **no new ground-truth
information** (see `PE_PAIRWISE_VIEW_JUSTIFICATION.md`):

| Pair | y_loss(first) vs y_loss(second) | Label |
|---|---|---|
| (A, B) | 2 < 3 | A preferred |
| (A, C) | 2 = 2 | tie |
| (B, C) | 3 > 2 | C preferred |

The (A, C) pair is a tied pair — a direct, row-level echo of Section 5's
optimal-set tie, and the reason tie-aware pairwise construction matters:
naively excluding all tied pairs would discard this pair rather than
recording it as a genuine tie.

## 9. Proposed manuscript figure (Figure 1)

No image-generation tooling is required; this is a hand-drawable vector
figure (e.g., TikZ or a simple illustrator diagram):

- **Layout**: three horizontal rows, one per candidate world (A, B, C, in
  that order), each row showing 4 small cache-state boxes (3 slots each)
  left to right: "after decision", "after request B", "after request E",
  "after request F". Slots are labeled with the resident object; the slot
  that just changed is highlighted.
- **Between consecutive boxes**: a small arrow labeled with the requested
  object and annotated "hit" (green check) or "miss" (red cross).
- **Right of each row**: the row's final `y_loss` value in bold.
- **Below the three rows**: a compact summary strip showing the
  candidate-level table (Section 7) and the optimal set `{A, C}`
  highlighted.
- **Caption** should state explicitly that A and C tie and why, since this
  is the figure's main pedagogical point (per the instruction not to pick
  an example that accidentally implies every decision has a unique
  winner).
