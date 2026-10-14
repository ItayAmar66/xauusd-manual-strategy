# 5M ATR — XAUUSD, 4×ATR(14) movement research

**Definition:** A move from an extreme low to a subsequent extreme high, or vice versa, whose absolute price displacement is **at least 4 × M5 ATR(14) measured at the origin**. For example, ATR = $5 ⇒ minimum $20. M5 candles from M1 OHLC, Wilder ATR14; only the **previously completed** 5-minute candle's ATR is known at a minute timestamp.

## Preliminary independently reproducible results

| Metric | Result |
|---|---:|
| Source M1 candles | 760,337 |
| M5 candles | 152,070 |
| Detected zigzag legs | **4,584** |
| LONG / SHORT | 2,292 / 2,292 |
| Minimum recorded ATR multiple | 4.002870883831058 |
| Historical legs with same-minute endpoints / unknown intrabar sequence | 291 |
| Nonzero leg duration 1–120 minutes | 2,504 |
| Leg duration >120 minutes | 1,789 |
| Trading weekdays with nonzero range | 449 |
| Days with a new leg origin | **447 (99.55%)** |
| Days without a new leg origin | **2** |
| No-origin days | 2026-01-01; 2026-09-25 (partial data) |
| London session origins (fixed UTC+3 09:00–12:00) | 482 |
| New York session origins (fixed UTC+3 16:30–18:30) | 454 |
| Asia origins (02:00–08:00 fixed UTC+3) | 1,268 |
| Other origins | 2,380 |
| Strict temporal overlap among consecutive detected legs | 0 |

## Methodology and limitations

This is a new **alternating hindsight ZigZag segmentation**, not a byte-for-byte replication of the original 15M leg detector: original extraction algorithm was not preserved with the 15M data. The comparison of **4,584** with **2,091** therefore mixes timeframe, threshold AND segmentation implementation. Do not attribute count differences to ATR timeframe alone.

At an extremum, we maintain the latest high or low until a price reversal of at least 4× the ATR at the extremum is observed; then the extremum is frozen as a historical pivot. The **pivot is not knowable in real time until the reversal has already occurred**. Intraminute high-versus-low ordering is unknowable from M1 OHLC; 291 zero-minute legs are explicitly flagged. ATR excludes the current, unclosed M5 bar. Partial days/market shutdown candles and low-ATR conditions can affect event counts.

A historical event origin in London or NY does **not** prove that an entry signal appeared during that window. A 120-minute execution cap must be applied **from causal entry time**, not from the retrospective origin. No success rate or profit estimate is claimed.

## Files

- `build.py`: deterministic generation from the **archived M1 CSV** in `../15M ATR/XAUUSD_Manual_Strategy_Research_Git_Import.zip`
- `XAUUSD_Reversal_Legs_4ATR_M5.csv`: generated 4,584-event catalog
- `daily_coverage.csv`: per-day bars, ranges and origins
- `summary.json`: machine-readable summary

**Status:** Full 15M-style zone-interaction mapping (FVG / liquidity 42-category ranking and 77-context conditions) is **not yet reproduced** for these new 5M events. Prior 15M zone counts must not be reused. To obtain a genuinely comparable research package, rerun the full feature extraction against the new `event_id` and origin times.

The output generator includes assertions of key totals, so unexpected differences between environments fail loudly rather than silently changing the study.
