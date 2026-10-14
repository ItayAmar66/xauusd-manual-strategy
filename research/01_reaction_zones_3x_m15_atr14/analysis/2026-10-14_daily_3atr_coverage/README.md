# Daily occurrence of 3×M15 ATR(14) reversal legs

Period: XAUUSD M1 bid candle archive from 2025-01-01 00:00 UTC to 2026-09-24 23:58 UTC, converted to fixed UTC+3 event date convention. Original reversal-leg catalog: 2,091 records.

## Denominator

Count each fixed UTC+3 **Monday–Friday** date with M1 data whose daily high minus daily low is strictly positive. This excludes artificial flat holiday bars, Saturday and Sunday remnants.

- 449 weekday dates with nonzero intraday range.
- 440 dates with >=1 newly **originating** 3×M15 ATR14 reversal leg.
- 9 dates with no leg origin = **2.004454%**.
- 440/449 = **97.995546%** with a new leg start.

## Days without a NEW leg origin

| Date UTC+3 | M1 bars | Observed daily range USD | Does an earlier leg overlap the calendar day? |
|---|---:|---:|---|
| 2025-01-28 | 1,440 | 30.137 | Yes |
| 2025-04-22 | 180 | 21.150 | No — incomplete daily coverage |
| 2025-06-27 | 1,440 | 72.220 | Yes |
| 2025-07-04 | 1,199 | 21.560 | Yes |
| 2026-01-01 | 1,319 | 21.363 | Yes |
| 2026-01-02 | 1,440 | 92.310 | Yes |
| 2026-02-06 | 1,440 | 316.543 | Yes |
| 2026-06-26 | 1,440 | 113.160 | Yes |
| 2026-09-25 | 179 | 10.690 | No — incomplete daily coverage |

## Second interpretation: Any interval of an existing leg present

Count a date as covered if any strictly positive-length interval [origin_datetime_utc, end_datetime_utc] overlaps that UTC+3 calendar date, even if the leg began the preceding day.

- **447/449 = 99.554566%** of sampled market dates had an existing labeled 3 ATR leg ongoing for some part of the day.
- **2/449 = 0.445434%** had no overlap with a labeled leg; both were partial-data days (2025-04-22 and 2026-09-25).

**Interpretation caveat:** A historically labeled leg crossing midnight is NOT a newly available entry setup for that day. For entry-frequency goals, use 440/449, not 447/449.

The event catalog is retrospectively segmented and may miss legs on partial-data boundaries; these counts do **not** establish an executable daily trade opportunity or 3 ATR move within each individual day.

To reproduce, run `reproduce_daily_coverage.py` after extracting original canonical CSVs into `primary/` and `raw/`.
