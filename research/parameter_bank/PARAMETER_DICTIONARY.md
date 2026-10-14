# Parameter bank — named fields and market-wide frequency

Counts represent **completed M5 decision points 06:00–20:00 local time**, not 3×ATR or 4×ATR retrospectively successful legs. Signals can overlap.

| Family | Feature ID | Bars with feature | % of 75,264 |
|---|---|---:|---:|
| Context | `m15_up` | 42,576 | 56.57% |
| Context | `m15_down` | 32,688 | 43.43% |
| Context | `h1_up` | 42,960 | 57.08% |
| Context | `h1_down` | 32,304 | 42.92% |
| Context | `h4_up` | 47,208 | 62.72% |
| Context | `h4_down` | 28,056 | 37.28% |
| Context | `m15_displacement` | 5,466 | 7.26% |
| Context | `weekly_premium` | 45,892 | 60.97% |
| Context | `weekly_discount` | 26,515 | 35.23% |
| Context | `weekly_rangetop20` | 26,106 | 34.69% |
| Context | `weekly_rangebottom20` | 8,028 | 10.67% |
| Context | `m5_up` | 40,265 | 53.50% |
| Context | `m5_down` | 34,999 | 46.50% |
| M5 trigger | `m5_body_bull` | 37,751 | 50.16% |
| M5 trigger | `m5_body_bear` | 37,023 | 49.19% |
| M5 trigger | `m5_rejection_bull` | 12,934 | 17.18% |
| M5 trigger | `m5_rejection_bear` | 11,953 | 15.88% |
| M5 trigger | `m5_engulf_bull` | 3,845 | 5.11% |
| M5 trigger | `m5_engulf_bear` | 3,705 | 4.92% |
| M5 trigger | `m5_rsi_oversold` | 6,678 | 8.87% |
| M5 trigger | `m5_rsi_overbought` | 8,710 | 11.57% |
| M5 trigger | `m5_breakup` | 4,022 | 5.34% |
| M5 trigger | `m5_breakdown` | 3,471 | 4.61% |
| Liquidity | `pdl_sweep_reclaim` | 985 | 1.31% |
| Liquidity | `pdh_sweep_reclaim` | 1,101 | 1.46% |
| Liquidity | `pwl_sweep_reclaim` | 486 | 0.65% |
| Liquidity | `pwh_sweep_reclaim` | 418 | 0.56% |
| Liquidity | `pdl_sweep_reclaim_last60m` | 5,803 | 7.71% |
| Liquidity | `pdh_sweep_reclaim_last60m` | 6,432 | 8.55% |
| Liquidity | `pwl_sweep_reclaim_last60m` | 2,694 | 3.58% |
| Liquidity | `pwh_sweep_reclaim_last60m` | 2,532 | 3.36% |
| M5 trigger | `prior_15m_down` | 36,510 | 48.51% |
| M5 trigger | `prior_15m_up` | 38,342 | 50.94% |
| Fibonacci | `fib_h1_bull_618_786` | 3,181 | 4.23% |
| Fibonacci | `fib_h1_bear_618_786` | 3,622 | 4.81% |
| FVG | `fvg_touch_H1_BEAR` | 17,248 | 22.92% |
| FVG | `fvg_touch_H1_BULL` | 18,210 | 24.19% |
| FVG | `fvg_touch_H4_BEAR` | 16,595 | 22.05% |
| FVG | `fvg_touch_H4_BULL` | 13,563 | 18.02% |
| FVG | `fvg_touch_M15_BEAR` | 24,336 | 32.33% |
| FVG | `fvg_touch_M15_BULL` | 22,268 | 29.59% |
| FVG | `fvg_touch_M5_BEAR` | 26,204 | 34.82% |
| FVG | `fvg_touch_M5_BULL` | 27,141 | 36.06% |

## Detailed calculations and caution
- Previous-day sweep/reclaim: M5 wick beyond the prior **trading-day** high/low and M5 close back through the level; `_last60m` means this happened in the previous 12 completed M5 bars, including the signal bar. Previous week analogous, Israeli weeks ending Sunday.
- Weekly premium/discount: above/below the midpoint of last four **fully completed Israel calendar weeks** (not the current week's final high/low). Outer 20% of this historic four-week range also provided.
- H1 swing fib: last confirmed H1 swing highs/lows with 2 completed H1 bars on each side; pivot confirmation is delayed 2 hours. Only the most recent two opposite confirmed pivots define the impulse; 0.618–0.786 area requires current price within that zone. This is NOT a verified ICT structural swing and is NOT proof of untouched 0.5.
- M15/H1/H4 trend: EMA20 greater/less than EMA50 on latest **completed** HTF candle. EMA trend and directional confirmation are highly correlated and must not be counted as independent evidence.
- FVG: lifecycle table from canonical archive; zone's `available_at` strictly precedes the signal M5 close and `invalidated_at` is later. Zone range overlaps current completed M5 candle's high-low, which does not prove a clean tradable bounce, and can introduce same-bar sequencing ambiguity.
- M5 rejection, engulfing, breakout and RSI14 are defined exactly in `build_bank.py` and use only completed bars.
- The M1 execution price is the **next M1 open** following M5 signal close, not a lookahead pivot low/high.
- Missing or incomplete bars and ambiguous OHLC order require tick verification for deployment.
