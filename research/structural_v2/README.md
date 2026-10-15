# XAUUSD structural stops, causal entries, and four-strategy coverage study

**Status: NOT READY FOR LIVE TRADING. No validated +1R/trade strategy has been found.**

Date: 2026-10-15. Historical XAUUSD BID M1 from January 2025 to 25 September 2026 (760,337 OHLC minute bars). Time zone for trade eligibility: `Asia/Jerusalem` with actual DST; entries strictly **06:00 inclusive to 20:00 exclusive**. Positions may remain open for at most 120 minutes, subject to data gaps; no automatic entries after 20:00.

This study deliberately never consults the catalog of 4,584 successful M5 legs or 2,091 M15 legs to select entries. Both successful and failed setups are included. The question is whether a structural trade rule is profitable, not whether winning reversals have recognizable antecedents.

## 1. Scope and implementation

- 21 structural setup families: previous day/week/Asia and rolling 15/30/60/120-minute **sweep + reclaim**; the same sweeps followed by **a confirmed M1 break of the prior microstructure** within 12 minutes; a close beyond 15/30/60-minute boundaries followed by optional price improvement; and **M5/M15/H1/H4 active FVG touches/rejections**.
- **36,192** executable parameter combinations: 9 context filters, 4 session windows, 4 entry executions (next M1 open, limit at half signal candle, limit at broken/reclaimed level, limit at one-third signal candle body), 3 profit targets (3R/5R/8R) and 4 exits (fixed target, BE after 1.5R, 1R ladder, trailing structural five-bar pivot). Filters with fewer than 15 raw signals were not evaluated.
- **220,638** unique structural entry *candidates* before historical fills and filters, time-stamped at the next M1 after a fully closed signal candle. These are **not** 220,638 trades.
- Stop comes **exclusively from chart structure**, never a predefined ATR multiple: (1) below the swept wick or above the swept high with a 0.10 XAUUSD price buffer, (2) outside the last 10 M1 bar swing for breakout/continuation, or (3) outside the FVG / rejection candle. Minimum price risk of $0.65 is just an execution viability filter. Position quantity can be determined independently from desired fixed monetary risk.
- Exits are simulated using raw M1 bid OHLC and stop-first handling whenever both stop and target occur inside the same minute. No advantage is assigned from future price paths; intra-minute price sequence is not actually observed.
- Cost assumption $0.35 in XAUUSD price units per completed trade (not observed broker spread or slips). Further $0.70 stress case; gaps and poor fills need real tick/quote verification before deployment.
- Daily/week levels are from completed local Israel day/week. Asia range: completed 00:00–06:00 local hours. H1/M15/H4 EMA20 vs EMA50 filters require **completed** timeframe bars. Historical FVG availability/invalidation timestamps are checked as-of signal time.
- Non-overlapping positions tested with a chronological portfolio simulator; at most one pending limit order open, then one position.

## 2. Full 36,192-variant scan — selection discipline

Periods:
1. 2025 H1 (development): 2025-01-01 through 2025-06-30.
2. 2025 H2 (development/validation for composite selection): 2025-07-01 through 2025-12-31.
3. 2026 Q1 (forward chronological test, **but previously seen in other project research**).
4. 2026 Apr–Sep (**reused review**, not untouched test).

The script publishes: all tested variants, results in each period, a deliberately narrow first-half-2025-only selection per family, exploratory top-100 2025 rank, and complete trade logs. Scanning tens of thousands of versions means even seemingly stable four-quarter winners can arise by chance. **Selecting winners using any 2026 result invalidates 2026 as an out-of-sample test**.

### An interesting but retrospective candidate: 30-minute structure-break limit

**Long:** M1 candle CLOSES beyond the previous 30 *completed* M1 highs; M15/H1 EMA20 > EMA50 on last closed candles; local entry time 15:00–18:00; place Buy Limit at `(2 * signal_M1_open + signal_M1_close) / 3`, capped at next available open so the order does not cross unfavorably; cancel if not filled within 15 minutes. Stop is below the lower of last 10 *completed* M1 lows and signal candle low minus 0.10 XAUUSD; no fixed ATR risk distance. Target 8R. No breakeven on this version; exit after up to 120 minutes. SHORT symmetrical.

| Period | R/trade (after $0.35 assumed cost) | Actual fills | Weekly-block exploratory bootstrap 95% interval |
|---|---:|---:|---|
| 2025 H1 | +0.071 | 155 | [-0.231, +0.437] |
| 2025 H2 | +0.168 | 159 | [-0.123, +0.497] |
| 2026 Q1 | **-0.053** | 95 | [-0.393, +0.311] |
| 2026 Apr–Sep | +0.280 | 137 | [+0.026, +0.572] |

**Important:** This candidate was singled out after inspecting the search across all four periods. The confidence bounds are **NOT corrected for 36,192 multiple comparisons**. Positive post-hoc CI in one period does not demonstrate future tradable expectancy. Mean +1R was **not attained**. The two alt entry/TP recipes and every fill are in `posthoc_BOS30_candidate_*`.

### A portfolio selected using 2025 data only

Four distinct candidate families were chosen by pre-2026 metrics, one each: previous-day sweep; London 15-minute structural breakout; New York 30-minute structural breakout; New York M15-FVG touch. Per-family configuration is specified exactly in `portfolio_4_2025_selected.json`. All signals are globally serialized: **not four simultaneous portfolios**.

| Period | Trading days with >=1 filled entry / eligible | Trades | Net R per trade | Max drawdown (R) | Stress avg R, $0.70 cost |
|---|---:|---:|---:|---:|---:|
| 2025 H1 | 123 / 126 (97.6%) | 596 | +0.150 | -30.45 | +0.019 |
| 2025 H2 | 127 / 131 (96.9%) | 655 | +0.101 | -38.11 | -0.017 |
| 2026 Q1 | 62 / 63 (98.4%) | 347 | **-0.198** | -94.10 | -0.256 |
| 2026 Apr–Sep | 125 / 126 (99.2%) | 628 | **-0.075** | -96.27 | -0.157 |

**Finding:** Achieves near-daily frequency without a forced daily fallback, but **fails profitability** in 2026. It must not be recommended as live trading. Across four periods coverage is 437/446 eligible market days (98.0%), NOT every single day, and only counts eligible full-data trading days, not all calendar days.

### Why 2026 failed and structural viability sensitivity

Trade-by-trade splits reveal that both the previous-day sweep and M15-FVG legs harmed the 2026 portfolio, while the BOS30 entry family was relatively stronger. This is a descriptive observation **after viewing 2026**, not a license to delete losing components and claim an out-of-sample winner.

A **structural risk-viability gate**, which does not move SL but rejects entries whose true structural distance is too small, was tested on 7 min-risk thresholds × 3 max-risk thresholds (21 combinations). The gate selected **using only 2025 H1/H2** with >=90% coverage and >=100 entries per half-year was `min structural risk $1.00; max $150`. It improved 2026 slightly but remained negative: 2026Q1 about **−0.191R** and Apr–Sep about **−0.053R**. The limit of profitability remains binding even after this treatment.

## 3. Caution about same-bar execution, selection and fees

Data have **BID OHLC only** and no tick ordering. If SL/TP occur inside one bar, SL is assumed first; LIMIT fill and adverse move in the same M1 bar are simulated pessimistically. A quoted stop-market order can fill beyond its stop price during a gap, so futures/CFD execution is broker-dependent. This is an approximation, not a broker-certified execution simulator.

Current gold spot prices and volatility regimes vary greatly between 2025 and 2026. The same physical stop distance or fee in XAUUSD price units may correspond to a dramatically different R drag across samples. Futures vs CFD scaling and commission are unspecified, so all R statistics here use price-based assumptions.

Repeated testing of 2026 in this project means **no untouched 2026 dataset exists anymore**. A verified future pilot must freeze exact rules, obtain a fresh out-of-sample range/tick quote history, and paper trade with actual spreads/slippage.

Reference methodology:
- [QuantConnect: look-ahead bias and bar time frontiers](https://www.quantconnect.com/docs/v2/research-environment/datasets/key-concepts)
- [CMT Association: overfitting and out-of-sample pitfalls](https://cmtassociation.org/technically_speaking/technically-speaking-may-2015/)
- [QuantConnect: stop-market slippage is not bounded by stop price](https://www.quantconnect.com/docs/v1/algorithm-reference/trading-and-orders)

## 4. Files to inspect

| File | What it contains |
|---|---|
| `research.py` | Complete causal M1 feature generation and 36k structural-variant backtest engine |
| `signal_inventory.csv` | Every timestamped M1 structural candidate and all direction/context columns |
| `all_structural_variants.csv` | Complete results of 36,192 parameter tests and all four time regimes |
| `train_selected_family.csv` | Each family's H1-2025-selected management, then other periods |
| `top100_exploratory_2025.csv` | Development-era best variants (not independently validated) |
| `train_selected_trade_log.csv` | Individual fills for the family-selected variants |
| `portfolio_test.py` | Exact globally serial four-component portfolio backtest |
| `portfolio_4_2025_selected.json` | Full configs of four recipes picked using 2025 only |
| `portfolio_4_2025_selected_trade_log.csv` | All 2,226 portfolio executions with initial market structure stops |
| `portfolio_4_period_report.csv` | Period metrics, total/average R, coverage, fees, drawdowns |
| `risk_gate.py` | Min/max structural stop DISTANCE viability gate (doesn't move stop) |
| `structural_stop_viability_gates.csv` | 21 viability gates × four regimes |
| `risk_gate_2025_selected.json` | Gate selected only on 2025 |
| `candidate_study.py` | Detailed replay and weekly-cluster bootstrap of the exploratory BOS30 limit entry |
| `posthoc_BOS30_candidate_trade_log.csv` | Full fills of two posthoc 30M break/retest variants |
| `posthoc_BOS30_candidate_periods.csv` | Per-period R, drawdown, costs, week-block uncertainty |

**Conclusion:** we have a much more precise mechanical trading idea and a near-daily coverage portfolio. We **have not** found a strategy achieving +1R net average per trade, nor one defensibly profitable through all review periods. No simulation result should be portrayed as a guaranteed result or traded without paper-forward verification.