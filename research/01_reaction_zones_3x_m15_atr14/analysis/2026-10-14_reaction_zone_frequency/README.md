# Frequency of reaction-zone interactions — 2,091 events

**Period:** 2025-01 through 2026-09 (historical XAUUSD M1 event catalog). **Threshold:** observed move of at least 3 × M15 ATR(14). This sample is selected *by future observed movement*, so results express **P(zone present | successful historical move)**, not P(success | zone), not entry accuracy.

## Dataset and precise calculation

Denominator: 2,091 unique `event_id` values from `primary/XAUUSD_Phase1_Reversal_Legs_3ATR_M15.csv`.

Sources:
- `context/XAUUSD_Liquidity_Interactions.csv` contains [event_id, family, level, state, price, distance_atr]. Deduplicate on event_id + family + level + state. All 30 observed liquidity labels included.
- `context/XAUUSD_ACTIVE_FVG_at_Origins.csv` contains [event_id, tf, direction, formation_bar, available_at, level_low, level_high, invalidated_at]. Deduplicate on event_id + tf + direction. All 12 tf/direction labels included.

Compute `events = count(distinct event_id)`; `percent = events/2091*100`. Combinations and multiple categories per event can overlap; sums do not equal 100%. `SWEEP_RECLAIM` is nested in `SWEEP` categories, not additional independent occurrences.

**Audit:** the 42 event counts here were independently recomputed from the two underlying CSV sources and matched all 42 entries in the previous `XAUUSD_Clean_Groups_Percentages.csv` catalog (42/42). `qa_flag`: 26/2,091 events have `INTRABAR_SEQUENCE_AMBIGUOUS`; retained, not silently removed.

## Complete ranked catalog — all 42 observed zone/interaction types

| Rank | Family | Pattern | Events | % of 2,091 |
|---:|---|---|---:|---:|
| 1 | CALENDAR | PDH_SWEEP | 648 | 30.99% |
| 2 | CALENDAR | PMH_SWEEP | 644 | 30.80% |
| 3 | CALENDAR | PWH_SWEEP | 602 | 28.79% |
| 4 | CALENDAR | PDH_SWEEP_RECLAIM | 509 | 24.34% |
| 5 | SESSION | ASIA_LOW_SWEEP | 496 | 23.72% |
| 6 | CALENDAR | PDL_SWEEP | 482 | 23.05% |
| 7 | SESSION | ASIA_HIGH_SWEEP | 479 | 22.91% |
| 8 | ACTIVE_FVG | M1_BULL | 454 | 21.71% |
| 9 | ACTIVE_FVG | M15_BEAR | 437 | 20.90% |
| 10 | CALENDAR | PDL_SWEEP_RECLAIM | 437 | 20.90% |
| 11 | ACTIVE_FVG | M1_BEAR | 432 | 20.66% |
| 12 | ACTIVE_FVG | M15_BULL | 412 | 19.70% |
| 13 | ACTIVE_FVG | H4_BEAR | 404 | 19.32% |
| 14 | ACTIVE_FVG | M5_BEAR | 394 | 18.84% |
| 15 | ACTIVE_FVG | M5_BULL | 394 | 18.84% |
| 16 | ACTIVE_FVG | H1_BULL | 380 | 18.17% |
| 17 | ACTIVE_FVG | H1_BEAR | 371 | 17.74% |
| 18 | SESSION | ASIA_HIGH_SWEEP_RECLAIM | 364 | 17.41% |
| 19 | SESSION | ASIA_LOW_SWEEP_RECLAIM | 342 | 16.36% |
| 20 | ACTIVE_FVG | H4_BULL | 339 | 16.21% |
| 21 | ACTIVE_FVG | D1_BULL | 324 | 15.49% |
| 22 | SESSION | LONDON_LOW_SWEEP | 318 | 15.21% |
| 23 | SESSION | LONDON_HIGH_SWEEP | 272 | 13.01% |
| 24 | ACTIVE_FVG | D1_BEAR | 259 | 12.39% |
| 25 | CALENDAR | PWL_SWEEP | 231 | 11.05% |
| 26 | SESSION | LONDON_HIGH_SWEEP_RECLAIM | 231 | 11.05% |
| 27 | SESSION | LONDON_LOW_SWEEP_RECLAIM | 220 | 10.52% |
| 28 | CALENDAR | PWH_SWEEP_RECLAIM | 145 | 6.93% |
| 29 | CALENDAR | PWL_SWEEP_RECLAIM | 142 | 6.79% |
| 30 | CALENDAR | PML_SWEEP | 106 | 5.07% |
| 31 | CALENDAR | PMH_SWEEP_RECLAIM | 33 | 1.58% |
| 32 | CALENDAR | PML_SWEEP_RECLAIM | 20 | 0.96% |
| 33 | SESSION | NY_LOW_SWEEP | 19 | 0.91% |
| 34 | SESSION | NY_HIGH_SWEEP | 8 | 0.38% |
| 35 | CALENDAR | PDH_TOUCH | 3 | 0.14% |
| 36 | SESSION | NY_LOW_SWEEP_RECLAIM | 3 | 0.14% |
| 37 | SESSION | LONDON_HIGH_TOUCH | 2 | 0.10% |
| 38 | SESSION | NY_HIGH_SWEEP_RECLAIM | 2 | 0.10% |
| 39 | CALENDAR | PDL_TOUCH | 1 | 0.05% |
| 40 | CALENDAR | PWH_TOUCH | 1 | 0.05% |
| 41 | SESSION | ASIA_LOW_TOUCH | 1 | 0.05% |
| 42 | SESSION | NY_LOW_TOUCH | 1 | 0.05% |

## What this does **not** show

- A frequently appearing zone is NOT proven to predict price reversals. We have no denominator of *all touches and all failed moves* here.
- Active FVG means an FVG active at/near the recorded origin; it is not necessarily a confirmed touch or an execution-quality fill.
- Calendar and session levels are sometimes sweep/touch/reclaim event labels; their definitions must be reproduced before using them as live causal signals.
- The 26 bar-order-ambiguous event flags warrant separate robustness checks.

## Next research phase

Rebuild the market-wide denominator of **all** candidate liquidity sweeps and FVG interactions from the full 760,337 M1 candles, including events that did *not* lead to a 3 ATR move. Measure reaction lift, adverse excursion, time-to-3ATR, risk, and true live-time signal availability. Split train/holdout chronologically and include costs. Until then this is a frequency study, not a tradable strategy.

## Reproduction

Run `reproduce_zone_frequency.py` from repo root once the 14 source CSVs are extracted to the manifest paths. The script asserts that every one of the 42 source category counts matches the output.
