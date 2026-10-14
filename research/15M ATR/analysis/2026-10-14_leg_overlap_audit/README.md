# Independent time-overlap audit — canonical 2,091 historical legs

**Scope:** `primary/XAUUSD_Phase1_Reversal_Legs_3ATR_M15.csv`, January 2025 to September 2026. Time stamps `origin_datetime_utc` and `end_datetime_utc`.

## Results

| Test | Result |
|---|---:|
| Unique events | 2,091 / 2,091 |
| **Strictly overlapping event intervals** | **0** |
| Consecutive sorted event pairs with shared boundary timestamp | 1,998 / 2,090 |
| Consecutive sorted event pairs with a positive gap | 92 / 2,090 |
| Shared-boundary pairs with equal end/origin PRICE | 1,992 |
| Exact duplicate start/end intervals | 0 |
| Zero-duration event intervals | 26 |
| Negative-duration intervals | 0 |

Overlap definition: two event intervals overlap strictly if `max(start_A,start_B) < min(end_A,end_B)`. Sharing one boundary time point is **not** a positive-duration overlap. To verify *all* pairs, sort by start time and check that no start lies before the greatest end of any earlier event.

**Conclusion:** All 2,091 entries are *non-overlapping as positive-duration UTC intervals*, but 1,998 consecutive pairs *touch at their timestamps*. Of those, only 1,992 share exactly the same price. This does not imply independent samples: shared pivots, common candles, overlapping context features and chronological dependence remain.

**26 zero-duration entries** have `qa_flag=INTRABAR_SEQUENCE_AMBIGUOUS`, with start and end on the same minute. Their intrabar price sequence cannot be established from M1 OHLC data alone. They are retained in the canonical source but should be flagged/excluded for execution testing, unless tick data resolves them.

This audit **does not prove** that physical reaction zones (price ranges, FVGs, liquidity levels), feature windows, or candles never overlap. It only addresses the start-to-end time intervals of the *historically labeled 3ATR movements*. Any assertion about zone-level overlap requires explicit zone price boundaries, validity times and a separate audit.

## Reproduction

Run `python audit_leg_overlap.py` from this directory once original source CSV is extracted to the paths in `FILE_MANIFEST.csv`. The script asserts the counts, prints a summary and writes `zero_duration_26.csv`.
