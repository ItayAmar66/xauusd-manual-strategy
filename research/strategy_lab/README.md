# XAUUSD strategy discovery — 26 families × 45 implementations (1,170 tests)

**Status: RESEARCH ONLY — no validated +1R/trade strategy found.**

All signals are formed on completed M5 candles and executed no earlier than the following M1 open. Trading window uses **Asia/Jerusalem 06:00–20:00 (exclusive)**, including real daylight-saving changes. Max holding time 120 minutes from entry. Market data are XAUUSD BID candles, January 2025–September 2026. Market days with at least 200 active/available M1 bars and positive intraday range: **446** (320 train and 126 holdout).

**No selection on holdout:** each strategy family tests 5 stop distances × 9 management options = 45 candidates using training data only, then locks best family variant. Reports present the locked variant's once-only holdout results. Selecting or combining based on holdout after viewing it will invalidate its status as independent test and require a fresh later period.

## Method and execution assumptions

- Stop distances 0.75, 1.0, 1.5, 2.0, 2.5 × Wilder M5 ATR14 at completed signal bar, using exact M1 exits.
- **Execution time exception:** 25 trades across all 45,009 selected-variant trades (16 in holdout) exceeded 120 elapsed minutes because quote data stopped during exchange closures or gaps. The simulator filled them at the next available M1 open; these gaps make the nominal 120-minute holding cap **not fully executable**. Per-strategy audit is in selected_26_robustness.csv.
- Exit management: fixed 3R/4R/5R/8R, break-even after +1.5R or +2R, 1R ladders, 0.5R ladders. Stop only changes for the subsequent M1 bar.
- If both SL and TP in the same M1 candle, assume the SL hit first. Gap-through stops fill at gap open when worse. Trades may remain open after 20:00 but no new entries outside time window.
- Assumed fixed roundtrip execution friction: **$0.35 price per XAUUSD** base, **$0.70** stress. No true order book, commission tier, or broker tick data; live returns could differ.
- Hindsight 2,091 and 4,584 leg catalogs were **not** used to generate entry times, eliminating that source of direct future label leakage.
- Independent comparison period is **2026-04-01 to 2026-09-24**; training is 2025-01-01 to 2026-03-31.
- Bootstrap CI resamples holdout trading days 1000 times; it may understate regime and interday dependency risk.
- CAVEAT: strategy families were brainstormed after reviewing earlier market data, so multiple-testing / research-selection effects still exist. The holdout must be treated as spent after this report.

## Critical conclusion

**No strategy achieved ≥ +1.00R mean per trade in independent holdout.** The 120-minute cap could not actually be met in 25 trades with market-data gaps, so no model is yet operationally validated.

[QA: trades held beyond 120 minutes](QA_over120min_trades.csv) explicitly lists all such exceptions. Having a signal every trading day is possible with time-based daily entries, but that method did not achieve the required expectancy. Entries should NOT be deployed just because the signal has high historical coverage or the favorable return multiple is 4R/8R.

## Complete leaderboard — lock variants before holdout

| Strategy | Selected risk ×ATR | Manager | Train trades | Train avg R | Holdout trades | Holdout avg R | Holdout Win% | Holdout days with a trade |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| [23_M15_FVG_revisit](strategies/23_M15_FVG_revisit.md) | 2.50 | be1p5_tp4 | 569 | -0.047 | 213 | **0.050** | 41.8% | 110/126 |
| [24_Daily_0610_trend](strategies/24_Daily_0610_trend.md) | 2.00 | ladder1_tp5 | 320 | 0.066 | 126 | **0.035** | 45.2% | 126/126 |
| [09_Prior_day_breakout](strategies/09_Prior_day_breakout.md) | 1.50 | fixed3 | 522 | -0.004 | 173 | **0.015** | 34.7% | 78/126 |
| [13_RSI30_70_reclaim](strategies/13_RSI30_70_reclaim.md) | 2.00 | ladder0p5_tp4 | 1206 | -0.064 | 439 | **0.003** | 41.2% | 124/126 |
| [15_RSI50_EMA_trend](strategies/15_RSI50_EMA_trend.md) | 1.50 | ladder1_tp5 | 2266 | 0.002 | 898 | **-0.015** | 29.0% | 126/126 |
| [19_Inside_bar_breakout](strategies/19_Inside_bar_breakout.md) | 1.50 | fixed8 | 2083 | -0.003 | 842 | **-0.016** | 33.5% | 126/126 |
| [02_EMA20_50_cross](strategies/02_EMA20_50_cross.md) | 1.00 | fixed8 | 1053 | -0.042 | 409 | **-0.019** | 24.2% | 123/126 |
| [21_MACD_signal_cross](strategies/21_MACD_signal_cross.md) | 1.50 | be2_tp8 | 1768 | -0.008 | 666 | **-0.024** | 28.7% | 126/126 |
| [16_Bollinger_reentry](strategies/16_Bollinger_reentry.md) | 1.00 | fixed3 | 2900 | -0.019 | 1117 | **-0.029** | 28.7% | 126/126 |
| [04_EMA50_pullback](strategies/04_EMA50_pullback.md) | 2.50 | ladder1_tp5 | 1304 | 0.013 | 507 | **-0.031** | 36.7% | 125/126 |
| [08_Donchian36_sweep_fade](strategies/08_Donchian36_sweep_fade.md) | 1.50 | be2_tp8 | 1683 | 0.004 | 645 | **-0.033** | 32.6% | 126/126 |
| [07_Donchian12_sweep_fade](strategies/07_Donchian12_sweep_fade.md) | 2.00 | fixed8 | 2088 | 0.002 | 818 | **-0.035** | 40.3% | 126/126 |
| [18_ATR_displacement_trend](strategies/18_ATR_displacement_trend.md) | 2.50 | ladder1_tp5 | 614 | 0.049 | 253 | **-0.036** | 33.2% | 121/126 |
| [03_EMA20_pullback](strategies/03_EMA20_pullback.md) | 2.50 | ladder0p5_tp4 | 1574 | -0.036 | 609 | **-0.046** | 40.6% | 126/126 |
| [06_Donchian36_breakout](strategies/06_Donchian36_breakout.md) | 2.00 | be1p5_tp4 | 1563 | -0.046 | 597 | **-0.050** | 32.2% | 126/126 |
| [22_M5_FVG_revisit](strategies/22_M5_FVG_revisit.md) | 2.50 | fixed4 | 1090 | 0.007 | 445 | **-0.056** | 40.4% | 125/126 |
| [01_EMA9_21_cross](strategies/01_EMA9_21_cross.md) | 1.50 | fixed8 | 1918 | -0.049 | 747 | **-0.059** | 31.1% | 126/126 |
| [17_Bollinger_breakout](strategies/17_Bollinger_breakout.md) | 2.00 | ladder0p5_tp4 | 2037 | -0.042 | 786 | **-0.059** | 36.4% | 126/126 |
| [05_Donchian12_breakout](strategies/05_Donchian12_breakout.md) | 2.50 | ladder0p5_tp4 | 2471 | -0.065 | 945 | **-0.068** | 37.8% | 126/126 |
| [14_RSI20_80_reclaim](strategies/14_RSI20_80_reclaim.md) | 1.00 | fixed8 | 242 | 0.147 | 85 | **-0.074** | 24.7% | 56/126 |
| [10_Prior_day_sweep_fade](strategies/10_Prior_day_sweep_fade.md) | 2.50 | fixed3 | 413 | 0.015 | 147 | **-0.120** | 39.5% | 76/126 |
| [12_Asia_range_sweep_fade](strategies/12_Asia_range_sweep_fade.md) | 1.00 | ladder0p5_tp4 | 623 | -0.132 | 255 | **-0.152** | 30.2% | 92/126 |
| [25_Opening_hour_breakout](strategies/25_Opening_hour_breakout.md) | 1.50 | ladder0p5_tp4 | 846 | 0.057 | 337 | **-0.157** | 29.4% | 126/126 |
| [11_Asia_range_breakout](strategies/11_Asia_range_breakout.md) | 1.00 | be2_tp5 | 591 | 0.147 | 235 | **-0.158** | 19.1% | 100/126 |
| [20_Engulf_extreme20](strategies/20_Engulf_extreme20.md) | 2.00 | ladder0p5_tp4 | 358 | 0.075 | 159 | **-0.161** | 32.7% | 92/126 |
| [26_RSI_extreme_fade](strategies/26_RSI_extreme_fade.md) | 1.50 | be2_tp8 | 343 | -0.092 | 111 | **-0.308** | 26.1% | 64/126 |

## Read the data

- [LEADERBOARD_holdout.csv](LEADERBOARD_holdout.csv) includes cost sensitivity and 95% CI.
- [all_1170_variants.csv](all_1170_variants.csv) includes ALL 1,170 trials with both train/holdout diagnostic columns; do not select variants by comparing holdout returns.
- [selected_26_strategies.csv](selected_26_strategies.csv) contains best train-only variant per family.
- [selected_26_robustness.csv](selected_26_robustness.csv) shows sampling uncertainty, time/stop/TP exits, and cost sensitivity.
- [all_selected_trades.csv](all_selected_trades.csv) contains each trade's entry/exit UTC and Israeli time, direction, R result, price stop distance, exit reason, and selected management.
- [backtest.py](backtest.py), [reports.py](reports.py): full reproducible test implementation, expected to run from original 15M ATR ZIP in the same GitHub repo.

**Next step:** fix strategy deficiencies using training only in a NEW dataset period; test live-paper forward data and broker-realistic spreads. Do not treat small +0.02R samples as statistical edge.
