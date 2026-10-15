# XAUUSD Reaction → M1 confirmation → Entry: ATR vs structural stops

**Research date:** 2026-10-15. **Status: NOT ready for live trading.** This study directly tests the user's hypothesis: a known intraday reaction area, then an *observable M1 confirmation*, then entry at the next candle with 2R or 3R target and a structural stop or one complete-candle ATR14 from M5/M15.

## Objective and core distinctions

- It is possible to identify a historical price extreme *after the fact* without being able to trade at that price. This study generates **all past and failed** candidate levels via the earlier causal `../structural_v2/signal_inventory.csv`; it **never enters at known future winners' optimal extremes** from the 2,091 M15 or 4,584 M5 movement catalogs.
- **50% win rate at +3R vs −1R = +1R gross expectancy**. In real trading fees, spreads, slippage, time exits and partial closes reduce expectancy. A net +1R requires better than 50% effective full-win rate unless other win/loss sizes improve it. At a 2R target and −1R loss, the 50% gross mean is only +0.5R.
- All entries from 06:00 inclusive to 20:00 exclusive in *Asia/Jerusalem*, actual DST; maximum 120 minutes. This study tests multiple subsets of that range.
- OHLC BID rather than true execution quotes; flat assumed all-in friction **$0.35 XAUUSD price movement**, with **$0.70** sensitivity. Stop is resolved first if both stop/TP hit same M1 candle; no unrealistic next-bar lookahead.

## Dataset and test inventory

- **760,337** raw M1 candles; same archived ZIP as the original research.
- **124,751** candidate historical zone interactions (D1/W1/Asia/15m–120m sweeps, structural retests and M5/M15/H1/H4 FVG contacts). As-of candidates from `structural_v2` and not selected from future winners.
- **228,908** M1-confirmed signal candidates after checking five independently observable trigger patterns in the 1–6 minutes after a zone event.
- **9,505** first-stage strategy versions, using only direct-next-open entry, fixed TP at 2R/3R and 3 alternative stops.
- **144** second-stage order/exit-management versions chosen from 18 2025-ranked entry recipes; options: next open vs 5-minute midpoint limit, fixed / BE at 1R / BE at 1.5R / half-R trailing after 1R.
- Backtest decisions are causal, but selecting from thousands of combinations creates substantial **multiple-testing / overfitting** risk. 2026 data have been reused in prior conversations and are **NOT a fresh untouched test**. A separate broker-aware forward paper-trading validation is necessary.

## M1 entry confirmation choices

The zone event is observed at minute `i` after its close; no trade yet. Within minutes `i+1` through `i+6`, find the **first** completed M1 bar satisfying the direction-specific confirmation, while the structural invalidation price has NOT been crossed.

1. **RESPONSE_WICK_BREAK:** M1 closes beyond the whole original reaction candle's wick, in the intended direction.
2. **BODY_ENGULF:** The next M1 candle's body fully engulfs the immediately previous body in the trade direction.
3. **MICRO_BOS3:** M1 closes beyond the highest/lowest price of the **three M1 candles preceding the reaction**, in the intended direction.
4. **TWO_CANDLE_PUSH:** Two consecutive closes progress in the intended direction, with the confirmation candle's body also directional.
5. **M1_FVG_DISPLACEMENT:** A three-candle imbalance is formed by the completed M1 confirmation candle and it also closes beyond the prior candle's extreme.

The order can enter no earlier than the **next** M1 open. Pending limits expire after five minutes and never fill after 20:00.

## SL and trade management

- **STRUCT:** Original zone/reaction's structural invalidation beyond the sweep extreme or FVG boundary.
- **M5_ATR1:** One M5 ATR(14) from next candle's open. Wilder ATR from only completed M5 candles (risk distance changes trade by trade).
- **M15_ATR1:** One M15 ATR(14) from next candle's open, computed only from completed M15 candles.
- The ATR alternatives here are **not a fixed-dollar stop**; they use locally measured volatility. As requested, no single fixed stop-dollar distance is forced across trades.
- Stops below $0.65 risk in XAUUSD price units are excluded as spread/fees would dominate. Values above $70 are also excluded as potential data anomalies. (This changes opportunity count and must be reported.)
- TP 2R or 3R, time out at 120 minutes; pessimistic stop-first same-minute hit. Trailing changes apply only after the closing of a minute and affect future minutes.

## Training-only selected candidate, with full disclosure

**30M_SWEEP + MICRO_BOS3 + H1/M15/H4 alignment, 15:00–18:00 Jerusalem, next-open entry, 1× closed M15 ATR14 stop, fixed TP 3R.**

| Interval | Trades | Net Win Rate | Average R net @ fee $0.35 | Avg R @ fee $0.70 | 95% unadjusted week-block bootstrap interval |
|---|---:|---:|---:|---:|---:|
| Jan–Jun 2025 (selection) | 59 | 47.46% | +0.39797R | +0.32186R | [−0.050, +0.863] |
| Jul–Dec 2025 (selection) | 74 | 39.19% | +0.32592R | +0.26530R | [−0.044, +0.720] |
| Jan–Mar 2026 (reused research) | 41 | 48.78% | +0.34442R | +0.31414R | [−0.164, +0.792] |
| Apr–Sep 2026 (reused research) | 79 | 30.38% | **−0.02166R** | **−0.05811R** | [−0.341, +0.346] |

Overall 253 trades. For the chosen configuration: **57 hit full +3R**, **140 hit stop**, **56 exited at 120-minute horizon**, 0 data-gap exits, and no trade went beyond 120 minutes. Earlier gains are **not a reliable estimate of future profitability**. No 2025 strategy (at least 100 training trades) in the 9,505 phase-1 trials had ≥50% win rate with 3R.

### Does *waiting for M1 confirmation* add value?

Hold constant the **30M sweep**, HTF H1/M15/H4 alignment, time 15–18, M15 ATR stop and 3R TP. Compare two executable alternatives:

| Interval | Directly after sweep: n / avg net R | Only after M1 MICRO_BOS3: n / avg net R |
|---|---|---|
| Jan–Jun 2025 | 153 / +0.176R | 59 / +0.398R |
| Jul–Dec 2025 | 187 / **−0.046R** | 74 / +0.326R |
| Jan–Mar 2026 | 92 / +0.219R | 41 / +0.344R |
| Apr–Sep 2026 (reused) | 128 / **+0.175R** | 79 / **−0.022R** |

This is the precise finding relevant to the trader's hypothesis: **confirmation may improve some periods but worsen others**. Neither method is proven to yield the target >50% successful 3R trades after fees. The confirmation selection trades only 94/259 eligible days in 2025 and 77/190 in 2026, **far below the 1-trade-every-day requirement**.

## Required independent validation before trading

1. **Use a new, untouched, chronologically later tick/ask-bid dataset** with the actual broker's spread/commission/slippage and timestamp DST treatment.
2. Freeze the chosen recipe and code *before* evaluation, avoid further rule selection using this data and correctly handle pending-order fill sequencing.
3. Check at least ~200+ genuinely independent live/paper signals as achievable; even then uncertainty may remain substantial.
4. For ≥1 trade/day, combine complementary setups only if the final merged portfolio meets profit, risk, drawdown and coverage targets **without adding losing backup trades**.

## Reproduce on GitHub

- `research.py`: loads `../15M ATR/XAUUSD_Manual_Strategy_Research_Git_Import.zip` and `../structural_v2/signal_inventory.csv`, generates raw M1-confirmed setups, screens 9,505 combinations and 144 management variants, selects ONLY on 2025.
- `diagnostics.py`: baseline same-zone immediate entry vs M1-confirmed entry, chronology-preserving period reports, daily coverage and unadjusted week-block bootstrap intervals.
- `confirmed_entry_inventory.csv`: each M1 confirmation record (228,908 rows).
- `phase1_all_strategies.csv`: every one of 9,505 screening results.
- `phase2_selected_144_variants.csv`: additional management/limit tests.
- `train_selected_18.csv`, `train_only_top12.csv`: selection and ranking audit.
- `train_chosen_trade_log.csv`: **all 253 entries including dates, entry/SL/TP and exit**.
- `immediate_vs_confirmed_by_period.csv`, `daily_coverage_comparison.csv`: no cherry-picked comparison.
- `summary.json`, `diagnostic_summary.json`: fixed-count QA.

**Research outcome:** A reproducible strategy *candidate* was identified, but there is **no validated +1R net/trade strategy meeting the daily frequency requirement**, and it would be misleading to claim otherwise.