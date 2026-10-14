# XAUUSD: M1 Reaction-First Structural Entry Research

**Date:** 2026-10-14. **Status:** Exploratory only; **no validated strategy meeting user's criteria**. Uses all 760,337 original XAUUSD bid M1 candles, not only the previously extracted hindsight winners. Source archive: `research/15M ATR/XAUUSD_Manual_Strategy_Research_Git_Import.zip`; independent as-of feature bank: `research/parameter_bank/condition_bank_m5.csv`.

## What this research changes

Previous 26 and adaptive-rule studies primarily used market entries after M5 triggers, with fixed ATR stops. Here we test M1 **liquidity sweep, local pivot, engulfing, active FVG / Fibonacci** events. Risk is sized to the preceding 5/10 minutes' actual structural low/high plus 0.10×known M5 ATR, or to 1×M5 ATR. All signals use completed candles only, orders can only execute in 06:00–20:00 `Asia/Jerusalem` time, and positions close after 120 elapsed minutes at the latest (when the data feed permits it). Within a single OHLC candle, SL is assumed to trigger before TP.

We test **17 identifiable base signal families** (18 specified, one empty under the conditions), five context gates (none, M15-aligned, H1-aligned, weekly premium/discount, active H1 FVG), three stop types, 3R/4R/6R targets and two managers (fixed and BE after +1.5R) = **1,530 nonempty market-entry variants**. Some are redundant; 1,530 is not an independent hypothesis count. We then test **240 pending-limit variants**, consisting of five promising family types, four context gates, a 5-minute structural stop, 35% or 60% of signal candle total-range retracement, TP 3/4/6R, fixed vs BE after +1.5R.

**Fee proxy:** $0.35 in XAUUSD quote-price units deducted per trade, *not* $0.35 cash per account/trade. **Stress test:** 0.70 and 1.00 XAUUSD price units. Bid-only source means true ask/quotes, spreads, slippage, and broker-specific commissions are NOT independently observed.

## Pre-existing data cannot reveal causality by itself

The 2,091 and 4,584 ZigZag reversal catalogs locate the extrema of successful *future-confirmed* movements. Entering at those extrema by hindsight would introduce lookahead bias. Accordingly, all results here are from signals detected at the time from the entire M1 archive, successful or unsuccessful. Observed correlation with sweep/FVG is not proof of order-flow cause.

## Important result: no qualified live-trading setup

No configuration achieved **+1R per trade with daily coverage** across training and subsequent periods. None of the 1,530 market-entry variants with >=50/20/35 trades in the three chronological splits was positive in all three. The top train-selected liquidity-grab examples deteriorated substantially in later review. The limit-entry study had only one configuration positive in each split, and it had negligible +0.021R on 60 later trades with low daily coverage and high cost sensitivity. The 2026Q2–Q3 period was REUSED by prior explorations and is **NOT a fresh blind holdout**.

### Candidate to understand, NOT to trade with real money

**PDH/PDL sweep-reclaim + H1 directional EMA alignment + 35% candle-retrace pending limit + structural 5-minute SL + fixed TP 4R**:

1. Previous *completed Israel calendar day* high PDH and low PDL are known at the start of day.
2. **LONG condition:** completed M1 candle's **low < PDL**, **close > PDL**, and previous M1 close **>= PDL**; H1 trend is **EMA20 > EMA50** from the previously completed H1 candle. SHORT is mirrored: high > PDH, close < PDH, previous close <= PDH and H1 EMA20 < EMA50.
3. After the signal M1 candle **closes**, place a long limit at `signal_close - 0.35*(signal_high-signal_low)` (short `+0.35*range`). Order is good for the next **six M1 candles** only. If not filled, **cancel**. Execute no entries outside 06:00 <= Israel local time < 20:00 or on weekends.
4. **LONG SL**: lowest low of the five M1 candles ending with the signal candle **minus 0.10×M5 ATR14** known at that time; SHORT SL is symmetrical. Reject entry if original stop-distance is under **$0.65 in XAUUSD price units** or above **6×ATR**. IMPORTANT: the program's risk guard (>=0.65) is *not* account-dollar risk. Size contracts/lots separately for desired account-dollar risk.
5. **TP** is at +4R; no BE or trailing for this variant; one active trade at once; exit after at most 120 minutes. Bid OHLC assumed SL-before-TP within same minute. Fee proxy: −0.35/stop_distance R per completed trade.

| Chronological split | Filled trades | Net WR | Net mean/trade | Days with entries | Total R | Max DD in R | Longest nonwinning streak |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2025 development | 111 | 27.93% | +0.0645R | 57 | +7.157R | −14.365R | 8 |
| 2026 Q1 (previously inspected validation) | 23 | 43.48% | +0.8613R | 13 | +19.810R | −4.273R | 4 |
| 2026 Q2–Q3 reused review | 60 | 23.33% | **+0.0211R** | **25** | +1.269R | −14.577R | 10 |

On later 60 trades, weekly-block resampling over **18 calendar weeks** yields unadjusted exploratory 95% CI on the mean of about **−0.394R to +0.499R**. Also, the purported +0.0211R is reduced to **−0.1396R** if the assumed price-unit round-trip cost doubles to $0.70, and to **−0.2775R** at $1.00. There is **no credible positive expected return at realistic unknown costs**. It triggers on only about 20% of market days during Q2–Q3, far below the requested at-least-one-trade-per-day objective.

**Selection disclosure:** This concrete example was highlighted after inspecting the broader exploratory results and 2026, and is **NOT** prespecified or objectively validated. The name in the machine-generated code should be interpreted as an *exploratory* candidate. Neither training nor reused review is truly unexposed to strategy-selection effects.

## Other findings

- The *best* fixed-target setup seen in Q2–Q3 reused review among market-entry variants (H1 Fibonacci 0.618–0.786 reaction, M15 directional filter, 1×ATR stop, TP6R, no BE) had **+0.125R on 168 trades** and **59% day coverage** there but was **−0.171R across 349 2025 development trades**. Do **not** present as consistently profitable.
- The most favorable 2025 train-selected daily liquidity-grab strategy with delayed three-bar breakout and H1 FVG had +0.153R in development (174 trades), −0.045R in 2026 Q1 and −0.407R in 2026 Q2–Q3.
- The strongest early-2026 result is **not predictive** of later conditions: the 23-trade limit-entry candidate reached +0.861R in Q1 but only +0.021R in Q2–Q3. Typical structural stop was about **$2.89 XAUUSD price distance** on the latter subset; high costs are a substantial fraction of 1R.

## Next genuinely useful tests

1. Measure signal-to-pivot latency; **post-sweep displacement and breaker retest** instead of instant 1m reclaim. Use micro swings confirmed without future candles, iFVG formed and invalidated only when observed, and compare 1/2/3-candle confirmation latency.
2. For each candidate setup, explicitly log **all losing activations**, MFE/MAE during first 120 min, whether setup arrived when target room was >=3–6R before opposite liquidity. Test stop=structural swing vs FVG and target=next known HTF level with RR floor.
3. Establish separate untouched forward data (after Sep 2026) or true prospective simulated trades. All current 2025–Sep 2026 data has already been mined in many variants. Even the confidence intervals above do not adjust for multiple comparisons.
4. Rebuild with bid/ask tick quotes, verified spread/commission and fills before risking capital.

## Files and reproduction

- `research.py`: end-to-end full-market scan, 1,530 market-order variants, per-family training selection and logs.
- `limit_retest.py`: 240 limit variants and detailed 194-trade *candidate* trade log.
- `all_variants.csv`, `train_selected_by_family.csv`, `train_selected_trade_logs.csv` — market entry results.
- `limit_all_variants.csv`, `limit_train_selected.csv` — pending-order results.
- `candidate_PD_H1_limit_trade_log.csv`, `candidate_PD_H1_summary.json`, `candidate_cost_robustness.json` — executable rule, trade-by-trade SL and TP, drawdown, cost sensitivity.
- `summary.json`, `limit_summary.json` — QA metadata and experiment counts.

To reproduce in GitHub Actions: use archived M1 CSV and existing 43-parameter bank. Run `python research.py`, then `python limit_retest.py` from this folder (Python 3.11; pandas/numpy/numba). GitHub Actions checks counts and commits generated result files.