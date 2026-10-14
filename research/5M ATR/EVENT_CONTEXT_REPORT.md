# Event-by-event context audit — XAUUSD 5M ATR(14) ×4

**Events:** 4,584 historical, retrospectively selected ZigZag legs. **Source:** 760,337 XAUUSD M1 bid OHLC candles and the original 188k+ FVG lifecycle table stored in `research/15M ATR/XAUUSD_Manual_Strategy_Research_Git_Import.zip`.

## Core question and answer

For each labeled leg, what measurable conditions were present **at the retrospectively identified origin**? The full table `all_4584_event_context.csv` contains one row per event and its individual flags, levels, trend and FVG conditions; `possible_explanation_labels` is a machine-generated list of candidates, **not an established cause**.

We cannot establish "exactly what caused the move" from OHLC alone. Multiple drivers, unknown order flow, and selection of origins only after the move can all lead to spurious associations. Crucially, origin-point price extrema **are not trade signals known in real time**.

## Initial summary, all 4,584 events

| Observable feature | Events | Percent |
|---|---:|---:|
| New extreme beyond past 5 M1 bars at the leg origin | 4,110 | 89.66% |
| New extreme beyond past 15 M1 bars | 4,030 | 87.91% |
| New extreme beyond past 60 M1 bars | 3,821 | 83.36% |
| Prior 15-minute M1 close-to-close movement opposite to future leg direction | 3,893 | 84.93% |
| M5 five-bar trend opposite to future leg | 3,469 | 75.68% |
| M15 five-bar trend opposite to future leg | 3,117 | 68.00% |
| H1 five-bar trend opposite to future leg | 2,273 | 49.59% |
| H4 five-bar trend opposite to future leg | 2,344 | 51.13% |
| At/beyond prior day's relevant high (for SHORT) or low (for LONG) | 1,858 | 40.53% |
| At/beyond prior week's relevant high or low | 1,005 | 21.92% |
| At/beyond prior month's relevant high or low | 841 | 18.35% |
| Active bearish M15 FVG containing origin price | 1,086 | 23.69% |
| Active bullish M1 FVG containing origin price | 1,051 | 22.93% |
| Active bearish M1 FVG containing origin price | 1,003 | 21.88% |
| No match among candidate flags summarized in `possible_explanation_labels` | 29 | 0.63% |
| Zero-duration, intraminute ambiguous movement | 291 | 6.35% |

**All 12 FVG groups and all 4,584 event records** are in the machine-readable data. Most events have multiple candidate conditions (mean **4.88** per event); do not infer causation from frequency.

## Exact definitions and safeguards

- **New extreme**: at the leg origin, origin price beyond the maximum/minimum of the preceding 5, 15 or 60 *completed* M1 candles, excluding the origin candle. Likely biased high by retrospective ZigZag pivot selection.
- **Previous day/week/month**: extrema of the previous complete UTC+3 calendar day/week/month group in M1 OHLC. Breach of this stored level at the future pivot. **No reclaim, retracement or causal sweep was required**. Week boundaries fixed Monday UTC+3; all date grouping fixed UTC+3. Not identical to broker session-based daily candles.
- **Opposite preceding movement**: differences of completed M1 closes before pivot, compared to the future leg's direction. It is *not* a predictive forecast of reversal.
- **M5/M15/H1/H4/D1 trend5**: sign of previous completed TF candle's close vs the close five candles earlier. Data for the currently forming higher-timeframe bar is excluded via `shift(1)`.
- **FVG at origin**: `available_at <= origin < invalidated_at` and `level_low <= origin_price <= level_high`; groups indicate timeframe and BULL/BEAR. Multiple can coexist and percentages are not exclusive. This is not evidence of limit order execution or confirmed reaction at FVG.
- **ATR**: 14-period Wilder smoothing over M5 OHLC true range, measured at historical extreme using the previously completed M5 ATR, with a >=4 ATR leg threshold.
- **291 ambiguous events**: same-minute extrema from M1 OHLC; future intraminute order cannot be recovered without ticks. Exclude for tradability/backtests.
- All candidate labels are observational associations, **not verified causes**. Features describing the extreme at an event origin can only be known as 'the pivot' **after** the reversal is observed.

## Files

- `enrich_events.py`: reproducible generation from the ZIP and the 4,584 leg catalog.
- `all_4584_event_context.csv`: complete per-leg parameter columns and candidate-label string.
- `event_context_ranked.csv`: group counts/percentages.
- `event_context_summary.json`: machine-readable totals.
- `.github/workflows/enrich-5m-atr.yml`: automatic generation and commit when the extraction code changes.

## Key limitations and next step

Frequency conditional on a **historically successful movement** cannot establish effectiveness. To answer "what makes the market react" or select entries, sample **all** times the same signals were present, including failures, and compare P(4ATR within 120 minutes | signal), drawdown, time-to-move, and out-of-sample robustness. In-session setup filters (London 09–12 and NY 16:30–18:30 fixed UTC+3) must use detection timestamps **not** retrospective origin timestamps.

**Research status:** descriptive feature annotation only. No trading signal or performance inference is validated.
