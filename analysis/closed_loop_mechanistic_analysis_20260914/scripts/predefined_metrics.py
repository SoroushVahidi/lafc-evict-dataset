"""Predefined metric set for the trace-only mechanistic analysis.

This list is written and frozen BEFORE any result is interpreted (per the
task's explicit instruction not to compute dozens of arbitrary metrics and
select only favorable ones afterward). Every metric below is computed for
EVERY one of the 5 families identically; none is added or dropped after
seeing which cells look interesting.

Per-family, per-scored-window-set metrics (capacity-independent unless noted):

  1. scored_window_request_count       -- window request count.
  2. unique_objects_in_window          -- distinct item_ids within the window.
  3. unique_over_request_ratio         -- (2) / (1).
  4. compulsory_fraction               -- fraction of window requests whose
                                          item has NEVER appeared before,
                                          anywhere earlier in the full
                                          50,000-request trace (not just
                                          within the window).
  5. repeated_fraction                 -- 1 - (4).
  6. top1pct_share, top5pct_share,
     top10pct_share                    -- fraction of window requests
                                          accounted for by the most
                                          frequent 1%/5%/10% of distinct
                                          items in the window.
  7. shannon_entropy_bits,
     normalized_entropy                -- entropy of the in-window item
                                          frequency distribution; normalized
                                          entropy = entropy / log2(unique
                                          objects), in [0,1], 1 = uniform.
  8. reuse distance summary (median, mean, p10/p25/p75/p90) over all
     in-window requests that ARE reuses (item seen at least once before,
     anywhere in the full trace) -- computed via reuse_distance.py.
  9. reuse_within_32_fraction,
     reuse_within_128_fraction,
     reuse_beyond_128_fraction         -- fraction of in-window REUSE events
                                          (denominator = reuse events, not
                                          all window requests) with stack
                                          distance <=32, <=128, >128.
  10. working_set_size_32, _128        -- number of distinct items among the
                                          most recent 32/128 requests,
                                          averaged over the window (a
                                          capacity-scale, policy-independent
                                          locality proxy).
  11. longest_novel_streak             -- longest run of consecutive
                                          compulsory (first-ever) references
                                          within the window ("scan-like"
                                          stretch, explicitly defined,
                                          policy-independent).
  12. pre_window_history_requests      -- number of full-trace requests
                                          before the window's first index
                                          (0 for MetaKV; large for others).
  13. cache_could_plausibly_be_warm    -- boolean: pre_window_history >= the
                                          larger analyzed capacity (128).

Cold-start-specific metrics (all 5 families, for comparability; MetaKV is
the only family with pre_window_history_requests == 0, so these numbers
are directly informative there and act as controls elsewhere):

  14. max_possible_hits_in_first_32,
      max_possible_hits_in_first_128   -- under an UNBOUNDED cache starting
                                          empty at the window's first
                                          request: the number of the first
                                          32/128 window requests that are
                                          repeats of an earlier request
                                          WITHIN that same 32/128-request
                                          prefix. This is a hard upper bound
                                          on possible hits for ANY
                                          eviction policy over that prefix,
                                          not a policy outcome.
  15. first_repeat_position            -- 0-indexed position, within the
                                          window, of the first request whose
                                          item already occurred earlier in
                                          the window (None if none in the
                                          window).
  16. unique_count_after_n             -- distinct-item count after the
                                          first 32/64/128/256/512/1024
                                          window requests (a cumulative
                                          locality-growth curve).
  17. quarter_repeated_fraction        -- repeated_fraction computed
                                          separately for each quarter of the
                                          window (early-vs-late locality
                                          comparison), using "repeated" in
                                          the same full-trace-history sense
                                          as (4)/(5).

No other metric is computed. Metrics 1-13 answer the general
cross-workload characterization; 14-17 answer the cold-start-specific
question. All are policy-independent (no cache, no eviction, no hit/miss
decision under any actual policy).
"""

METRIC_NAMES_WINDOW_LEVEL = [
    "scored_window_request_count", "unique_objects_in_window", "unique_over_request_ratio",
    "compulsory_fraction", "repeated_fraction",
    "top1pct_share", "top5pct_share", "top10pct_share",
    "shannon_entropy_bits", "normalized_entropy",
    "reuse_distance_median", "reuse_distance_mean", "reuse_distance_p10",
    "reuse_distance_p25", "reuse_distance_p75", "reuse_distance_p90",
    "reuse_within_32_fraction", "reuse_within_128_fraction", "reuse_beyond_128_fraction",
    "working_set_size_32_mean", "working_set_size_128_mean",
    "longest_novel_streak",
    "pre_window_history_requests", "cache_could_plausibly_be_warm",
]

METRIC_NAMES_COLD_START = [
    "max_possible_hits_in_first_32", "max_possible_hits_in_first_128",
    "first_repeat_position",
] + [f"unique_count_after_{n}" for n in (32, 64, 128, 256, 512, 1024)] + [
    f"quarter{q}_repeated_fraction" for q in (1, 2, 3, 4)
]
