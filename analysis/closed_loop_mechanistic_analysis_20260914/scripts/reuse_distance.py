"""Trace-only LRU stack-distance (reuse-distance) computation.

This is NOT a cache-policy simulation: it never allocates a cache, never
decides a hit/miss for any specific capacity, and never runs any of the
policy classes in the augmented-caching simulator. It computes a single,
long-established, purely trace-derived statistic (Mattson et al. 1970;
Bennett & Kruskal 1975): for each reference to an item that has been seen
before, the number of *distinct* items referenced since that item's
previous reference (exclusive of the item itself). This is the classic
"stack distance" / "LRU distance" used to characterize locality in a
trace, independent of any particular cache size -- a capacity only enters
later, when the caller thresholds the resulting distance values (e.g.
"fraction of reuses with distance <= 32").

Two independent implementations are provided:

- `stack_distances_fenwick`: O(n log n) via a Fenwick (Binary Indexed) tree
  of "active last-access markers" indexed by trace position. This is the
  one used for all real traces (n=50,000), since it is fast enough to run
  on the full trace in well under a second.
- `stack_distances_bruteforce`: O(n * average-gap) direct backward scan,
  counting distinct items between consecutive references. Used only for
  cross-checking correctness on short sequences (see tests/ and
  independent_recheck.py) -- far too slow to run on a full 50,000-request
  trace, and not needed there since it and the Fenwick version are proven
  to agree on smaller inputs.

A reference's stack distance is `None` if the item has never appeared
before in the sequence (a "compulsory" / first-occurrence reference).
"""
from __future__ import annotations

from typing import List, Optional, Sequence


class _Fenwick:
    def __init__(self, n: int) -> None:
        self.n = n
        self.tree = [0] * (n + 1)

    def update(self, i: int, delta: int) -> None:
        i += 1  # 1-indexed internally
        while i <= self.n:
            self.tree[i] += delta
            i += i & (-i)

    def prefix_sum(self, i: int) -> int:
        # sum of [0, i] inclusive, 0-indexed input
        i += 1
        s = 0
        while i > 0:
            s += self.tree[i]
            i -= i & (-i)
        return s

    def range_sum(self, lo: int, hi: int) -> int:
        # inclusive [lo, hi], 0-indexed; empty range if lo > hi
        if lo > hi:
            return 0
        if lo == 0:
            return self.prefix_sum(hi)
        return self.prefix_sum(hi) - self.prefix_sum(lo - 1)


def stack_distances_fenwick(item_ids: Sequence[str]) -> List[Optional[int]]:
    n = len(item_ids)
    fw = _Fenwick(n)
    last_pos: dict = {}
    distances: List[Optional[int]] = [None] * n
    for i, item in enumerate(item_ids):
        if item in last_pos:
            old_p = last_pos[item]
            distances[i] = fw.range_sum(old_p + 1, i - 1)
            fw.update(old_p, -1)
        else:
            distances[i] = None
        fw.update(i, 1)
        last_pos[item] = i
    return distances


def stack_distances_bruteforce(item_ids: Sequence[str]) -> List[Optional[int]]:
    n = len(item_ids)
    last_pos: dict = {}
    distances: List[Optional[int]] = [None] * n
    for i, item in enumerate(item_ids):
        if item in last_pos:
            old_p = last_pos[item]
            distances[i] = len(set(item_ids[old_p + 1 : i]))
        else:
            distances[i] = None
        last_pos[item] = i
    return distances
