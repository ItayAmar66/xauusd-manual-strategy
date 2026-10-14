# Proof-of-concept playbooks — exploratory only

All examples are symmetric LONG/SHORT. Signal M5 closes, entry at next available M1 open 06:00–20:00 Asia/Jerusalem. The 16 playbooks are **illustrative building blocks, not approved trading rules**.

Baseline comparison uses common parameters: **1.5 × completed M5 ATR14 initial SL, fixed 4R TP, 120-minute max hold, assumed $0.35 roundtrip cost in XAUUSD price units**.

| Playbook | Train trades | Train R/trade | Reused Apr–Sep 2026 trades | Reused R/trade | Reused daily coverage |
|---|---:|---:|---:|---:|---:|
| R10_day_sweep_M15trend | 178 | +0.007 | 57 | +0.140 | 16.7% |
| C04_M15FVG_trend_engulf | 695 | -0.091 | 252 | +0.138 | 88.1% |
| R04_H1_fib_M15_trend | 173 | -0.000 | 74 | +0.087 | 41.3% |
| C02_H1trend_M5FVG | 1818 | -0.020 | 699 | +0.033 | 96.0% |
| C05_adaptive_trend | 2782 | -0.064 | 1013 | +0.010 | 100.0% |
| C01_3TF_trend_breakout | 789 | +0.031 | 268 | -0.010 | 63.5% |
| C03_H1_fib_trend | 257 | -0.210 | 95 | -0.042 | 41.3% |
| R08_HTF_zone_FVG_rejection | 1849 | -0.079 | 866 | -0.053 | 100.0% |
| R07_weighted_reversal | 1398 | -0.128 | 605 | -0.055 | 99.2% |
| R05_H1FVG_prior_15m_counter | 1556 | -0.083 | 613 | -0.070 | 96.8% |
| R06_H4FVG_weekly_zone | 713 | -0.008 | 460 | -0.128 | 75.4% |
| R02_daily_sweep_M15FVG | 442 | -0.049 | 129 | -0.138 | 47.6% |
| R01_PDL_weekly_discount | 374 | -0.164 | 136 | -0.153 | 42.1% |
| C06_H4H1_M15FVG_displace | 238 | -0.085 | 83 | -0.161 | 42.1% |
| R09_weekly_extreme_RSI | 254 | -0.119 | 88 | -0.250 | 35.7% |
| R03_week_sweep_H1FVG | 85 | -0.291 | 44 | -0.524 | 15.9% |

## Every recipe definition

### R01_PDL_weekly_discount
Reversal: previous-day low sweep/reclaim within previous 60m + last-4-week discount + M5 bullish rejection (short mirror).

### R02_daily_sweep_M15FVG
Reversal: previous-day sweep/reclaim + active M15 FVG intersection + M5 directional close.

### R03_week_sweep_H1FVG
Reversal: previous-week sweep/reclaim + active H1 FVG + rejection.

### R04_H1_fib_M15_trend
Retracement: confirmed H1 0.618–0.786 fib zone + M15 trend agreement + M5 rejection.

### R05_H1FVG_prior_15m_counter
Reversal: active H1 FVG touch + completed M5 15m counter-move + M5 rejection.

### R06_H4FVG_weekly_zone
Reversal: H4 FVG + weekly premium/discount + M5 rejection.

### R07_weighted_reversal
Adaptive: >=2 of weekly half, daily sweep, H1 FVG, H1 fib + M5 rejection.

### R08_HTF_zone_FVG_rejection
Flexible: >=1 of weekly half or day sweep AND >=1 of H1/H4/M15 FVG AND M5 rejection.

### C01_3TF_trend_breakout
Continuation: H4+H1+M15 EMA20/50 aligned + 12×M5 high/low breakout.

### C02_H1trend_M5FVG
Continuation: H1/M15 trend + M5 FVG touch + directional M5 body.

### C03_H1_fib_trend
Continuation: confirmed H1 Fib retracement + H1 trend + M5 rejection.

### C04_M15FVG_trend_engulf
Continuation: M15 trend + active M15 FVG touch + M5 engulfing.

### C05_adaptive_trend
Adaptive continuation: >=1 H4/H1 trend, >=1 M15/M5 trend, M5 breakout or rejection.

### R09_weekly_extreme_RSI
Reversal: outer 20% of preceding 4 completed weeks range + M5 RSI14 extreme + rejection.

### R10_day_sweep_M15trend
Reversal/momentum: prior-day sweep/reclaim in previous hour + M15 trend alignment + M5 directional body.

### C06_H4H1_M15FVG_displace
Continuation: H4+H1 trend + M15 FVG + most-recent closed M15 displacement + M5 directional body.

## Critical limitations

**The April–September 2026 period has already been used in previous strategy research, and is NOT an independent unseen holdout.** These are descriptive exploratory outcomes, not proof of a strategy edge. No prototype has validated +1R/trade. Train 2025-01–2026-03; later review 2026-04–2026-09.

Do not sort by recent-period profit and then report it as unbiased performance. No genuine forward out-of-sample testing has been performed for these new composite rules.

Bid-only OHLC feed; friction assumption $0.35 in price; M1 SL/TP collision resolved STOP first; no tick order, partial fills, spread or actual broker costs. Data gaps can force exit after 120 minutes; exceptions must be excluded/resolved before any live deployment.

Entry/exit manager variants in `composite_prototypes_96.csv`, full trade logs in `prototype_trade_log.csv`.
