# XAUUSD 10 × M1 — two-day strategy-rotation gate test

**Exploratory experiment dated 2026-10-22. Not live-ready. No confirmed positive edge.**

## Question

> When a fixed-risk **3R** M1 playbook achieved **≥50% of trades hitting the full +3R TP** over the previous **two completed trading days**, should it be switched on for the *next* market day?

The answer from this first set of implementations is **NO, not by this test**. The effect is statistically noisy and the next-day portfolio expectancy was negative in all reviewed periods.

## Exactly how the gate works

1. Every model runs in **paper/shadow** continuously and records every realized trade. Shadow results are based on completed **M1 bid candles**. A signal at M1 candle close enters at the *next contiguous* M1 open, only between 06:00–20:00 **Asia/Jerusalem**, including DST.
2. Each trade uses a **predefined structural invalidation stop** and a **fixed TP = 3× initial risk**. No ATR multiple is used to place the SL. An independent risk viability condition rejects trades with a calculated stop distance below 0.70 or above 90 XAUUSD price units, rather than moving the stop.
3. At the start of the next eligible trading day, inspect only the prior **two fully completed trading days** (not the two previous calendar dates over weekends). The gate is enabled if there was at least one completed trade **each day**, the combined **full +3R TP hit rate** was **≥50%**, and combined net R was **positive**. An exit before 3R with +0.2R is **not** counted as a win for the gate.
4. Additional checks: A stricter gate requires ≥50% TP hits **on each day individually**, and a sample-size gate requires **at least four prior trades** across the two days.
5. Once eligible, trades following that model are permitted on the next market day only. The selector never sees that day's eventual outcomes before choosing. For the combined portfolio, all original candidate signals are replayed with **one open position maximum**, with a fixed lexicographic tie-breaker for simultaneous signals.
6. Max 120-minute hold from entry. Stop checked first when TP and stop both touch within the same M1 candle. At a candle-feed gap, close at last available candle before the gap; **no false 30-hour holds**. Cost = fixed 0.35 price units per completed trade, assumed, not verified on a specific broker.

## Canonical dataset and reproducibility

- 760,337 original M1 bid candles from January 2025 to September 25, 2026. In GitHub the raw file lives inside `research/15M ATR/XAUUSD_Manual_Strategy_Research_Git_Import.zip`, with the original archived trade signals.
- The archival file's SHA-256 equals the local copy: `29c6f8d7a676400381b57e65d972a457f47d29bc7af2b1cdb7b317d3a5502bce`.
- 10 named rule implementations; **nine of them are simplified, exploratory executable proxies**, not full, precisely certified interpretations of every ICT playbook. The user's original strategy uses an **existing historical signal archive**, not a newly reimplemented and fully causality-audited original algorithm. Treat *all* results as a method proof-of-concept, not validation of the precise 10 discretionary strategies.
- Note especially: H1/M1 FVG usage includes **latest observed gap** but does not fully reconstruct every gap's lifecycle/mitigation. AMD and Unicorn definitions are *proxies*, which substantially limit any conclusion about the true AMD+iFVG method.
- Testing the same 2026 history repeatedly means **2026 is reused review data, not a fresh untouched holdout**. No claim of live edge.

## Portfolio results (fixed +3R targets, costs deducted)

| Market period | Strategy policy | Filled trades | Full 3R TP hit % | Net avg R/trade | Traded days / eligible days |
|---|---|---:|---:|---:|---:|
| 2025 development | All 10, no switching | 4,474 | 19.60% | −0.101R | 257/259 |
| 2025 development | 2-day pooled 50% | 231 | 20.35% | −0.114R | 47/259 |
| 2025 development | ≥50% each day | 98 | 24.49% | +0.028R | 24/259 |
| 2026 Jan–Mar reused | All 10 | 1,252 | 18.85% | −0.113R | 63/64 |
| 2026 Jan–Mar reused | 2-day pooled 50% | 62 | 12.90% | −0.507R | 9/64 |
| 2026 Jan–Mar reused | ≥50% each day | 22 | 9.09% | −0.563R | 3/64 |
| 2026 Apr–Sep reused | All 10 | 2,293 | 19.76% | −0.066R | 126/126 |
| 2026 Apr–Sep reused | 2-day pooled 50% | 110 | 17.27% | −0.234R | 25/126 |
| 2026 Apr–Sep reused | ≥50% each day | 59 | 16.95% | −0.238R | 11/126 |
| 2026 Apr–Sep reused | pooled 50%, min 4 prior trades | 98 | 18.37% | −0.166R | 21/126 |

The 2025 strict 2-day test's small positive expectancy is not evidence of advantage given a reused/repeated experiment and poor results in 2026.

**Mathematical note:** At 50% WR and realized +3R/−1R payoffs, expectancy is +1R **gross**. Real observed payoffs also have timed exits, gap exits, trade costs, and potentially worse than −1R gap/slippage outcomes. The meaningful question is the **next-day realized net expectancy**, *not* whether a paper sample happened to meet the prior 50% threshold.

## Caveats and next iteration

1. Reimplement all 10 fully faithful, version-locked signal/stop/target definitions (especially the user's Original Baseline and AMD iFVG). Then rerun gate logic unchanged.
2. Use market-wide OHLC+spread/quotes or tick data; current bid OHLC with a synthetic 0.35 price friction lacks fill realism.
3. Consider gates based on trailing **expectancy in R**, credible intervals, minimum samples and volatility/regime changes rather than only 2-day win rate. Predeclare gate thresholds before opening fresh data.
4. Separately test sticky states (e.g., enabled until 2 consecutive failed days), rolling 5/10-day profitability and shadow-performance monitoring versus fixed trading models and no-trade control, then require a **genuinely new unseen sample** before live trading.
5. The goal of ≥1 trade/day and +1R net per trade remains **unmet**. Do not force a daily trade merely to satisfy coverage.

## Files

- `rotation_research.py` — ten initial M1 operational models, structural stops, next-minute fills, no-overlap global execution, date-safe 2-day model gating.
- `diagnostics.py` — per-model lift and 5,000-sample trading-day bootstrap.
- `all_ten_strategy_trades.csv` — 26,999 model-shadow fills, with outcomes and gate flags.
- `two_day_eligibility_by_strategy_date.csv` — model-by-date state, always computed from previous two completed market days.
- `rotation_policy_metrics.csv` — time-period statistics for each model and combined portfolio.
- `portfolio_all_trades.csv`, `portfolio_gate_agg_trades.csv`, `portfolio_gate_strict_trades.csv`, `portfolio_gate_min4_trades.csv` — one-position-at-a-time globally replayed portfolios (8,018/403/179/361 full-sample trades).
- `per_strategy_gate_lift.csv` and `calendar_day_bootstrap.csv` — sensitivity and calendar-day outcome intervals (the 2025 bootstrap excludes 2 initial gate-warmup days).
- `QA_summary.json` and `summary.json` — limitations and statistics.

**No historical trade here is investment advice, or proof that a strategy will perform similarly live.**
**Environment precision:** The canonical pinned GitHub Actions rebuild gives 4,474 unfiltered portfolio trades in 2025 (local environment 4,473) and −0.066R average in the latest reused review (local approx −0.065R). Exact 2-day-gated late-period results **match** across environments: 110 trades, −0.234R. See stored CSVs for authoritative GitHub-run values; freeze the full system stack and audit this one-fill discrepancy before any live use.
