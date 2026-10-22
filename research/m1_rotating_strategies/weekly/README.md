# XAUUSD M1 — Weekly Strategy Rotation (Research)

**Created 2026-10-22. Status: historical exploratory research, **not** a live trading system.**

## Hypothesis from user

At the end of each completed trading week, identify which of ten M1 playbooks performed best on that week. **If the previous week's leader is the currently traded strategy, continue. If another wins, switch on the following Monday.** Compare this one-week rule against other historical windows (2, 3, 4, 8 weeks) and against using the top two strategies together with no overlapping trades.

**Key point:** The decision for week `2026-08-17` uses ONLY results ending in or before `2026-08-14`; never Monday-Friday results of the week being traded.

## Source and data limitations

- Input: `../two_day/all_ten_strategy_trades.csv` (26,999 paper backtest trades across 10 playbook implementations, `2025-01-02`–`2026-09-24`). The last calendar week `2026-09-21` is incomplete and excluded; the first partial week is also excluded.
- **81 fully comparable evaluation weeks: 2025-03-03 through 2026-09-14.** This common start allows all policies to use an 8-week observation window. Training period 2025, reused reviews Jan–Mar 2026 and Apr–Sep 2026.
- All models have pre-existing entries constrained to **06:00–20:00 Asia/Jerusalem**, target 3R for **nine simplified M1 proxy implementations**; outcomes include assumed `$0.35` in XAUUSD price movement equivalent per trade, M1 OHLC stop-first convention and 120-minute maximum holding period.
- **Critical: `01_original_CHoCH_breaker_FVG_ARCHIVE` is an older trade dataset whose payoff is not a uniform 3R test; it cannot validly be scored as a 3R model.** `04_Unicorn_overlap_proxy` had only 27 trades over the full source. Eight-model sensitivity tests omit both. The remaining nine playbooks are simplified executable **proxies**, not exact reproductions of every ICT rule. The origin-liquidity pairing in the user's real strategy still requires full causal implementation/audit. Results must not be treated as proof of live profitability.
- Each week's score relies on **shadow outcomes of all 10 strategies**. In future live/paper workflow, you must record all ten sets of signals and hypothetical paper executions, even during weeks when a strategy is inactive, or the ranking will be based on missing information.
- Price data are bid OHLC, not broker bid/ask ticks; costs/slippage are approximated. The 2026 period has already been repeatedly consulted in past research, so **not** untouched out-of-sample.

## Exact weekly winner model

1. Start of week: Monday before 06:00 Israel local time. Compute each strategy's **completed prior week's sum of net R** from shadow trades, excluding current week.
2. If the previous week contains any trades, choose its **highest-total-R strategy**, not the best win rate of a few isolated trades. This does not require the model to have made money (the winner can be the least bad); `min_trades=1` is deliberate for the user's exact initial hypothesis.
3. If this is the current strategy: **hold**. If different: **switch this Monday**, trade only its M1 entries over that week, and complete a trade before opening the next (no overlapping positions).
4. If that model emits no signals on a trading day, **do not invent a fallback**.
5. Never use the outcomes of the upcoming week to select it. Weekly decisions and trade logs are persisted.

**Observed transition:** The prior week's leader was also the following week's leader in just **9 of 81 weeks (11.1%)** on the ten-model data. The comparable eight-proxy diagnostic also gives 9/81. This descriptive percentage is not a universal probability: sparse models and nonuniform opportunity rates influence the winner rankings.

### Period performance (net R / filled trade)

| Selection | 2025 (development) | Jan–Mar 2026 (reused) | Apr–Sep 2026 (reused) | Coverage of final 122 complete market days |
|---|---:|---:|---:|---:|
| **Previous 1-week winner**, exact user rule | −0.158 | −0.152 | **−0.078** (992 fills) | 112/122 = 91.8% |
| 4-week risk-shrunken return, one model | −0.092 | −0.178 | −0.035 (545) | 109/122 = 89.3% |
| 4-week risk-shrunken return, top two | −0.045 | −0.161 | −0.004 (1,096) | 122/122 = 100% |
| 8-week risk-shrunken return, one model | −0.092 | −0.129 | **+0.083** (610) | 115/122 = 94.3% |
| **Train-2025-selected** policy: 8wk mean, >=12 trades, inertia 0.15, top2 | −0.011 | −0.123 | **−0.002** (876) | 120/122 = 98.4% |
| First signal among all 10, no selection | −0.102 | −0.160 | −0.042 (2,088) | 122/122 = 100% |

**Selection mechanism:** 300 combinations (`5 lookbacks × 5 scores × 3 sample minimums × 2 inertia values × 2 top counts`). The `TRAIN_SELECTED` policy was chosen by **2025 only**, maximizing mean R with a sample-size penalty and a >=120 fill floor, and subsequently checked on 2026. It did **not** exhibit a consistently positive advantage. The 8-week positive late-2026 number was discovered during exploratory comparisons and was **negative in prior regimes**. It is not a verified edge or reason to start live trading.

### Filter sensitivity and rarity controls

Since the source's original-archive model has different profit-taking and the Unicorn proxy hardly trades, repeat selection with **eight other M1 proxies only**:

| Eight comparable proxy models | Apr–Sep 2026 fills | Mean net R | Days traded |
|---|---:|---:|---:|
| Previous 1-week winner (R sum) | 982 | −0.066 | 91.0% |
| Previous 1-week, shrunken avg R, >=4 fills | 760 | +0.040 | 91.8% |
| Previous 4 weeks, shrunken avg R, >=4 fills | 657 | −0.027 | 90.2% |
| Previous 8 weeks, shrunken avg R, >=4 fills | 836 | +0.070 | 95.9% |
| Previous 8 weeks, top 2 strategies | 1,468 | +0.003 | 100% |

The isolated positive periods are **post-hoc** and must not be interpreted as robust. No policy approaches +1R net. More models does not ensure better results.

### User's previous >=50% WR at 3R requirement

Also tested a stricter weekly gate: previous week's paper strategy must have positive sum R **and hit full 3R on at least 50% of trades**; compare going flat versus retaining incumbent if no model qualifies. That strict gate is seldom met:

- With **minimum four trades in one week** and **go-flat**, 2025 gave **−0.411R** across 79 trades; Apr–Sep 2026 gave **+0.422R** on **29 fills in only 10/122 days (8.2%)**. Not a viable daily coverage solution; high variance.
- With **minimum four trades and keep incumbent**, Apr–Sep 2026 gave **+0.054R** on 454 trades covering 86.1% of days, but was **−0.251R in 2025** and **−0.356R in 2026Q1**. No stable advantage.

## How to interpret the weekly results

- **Same-week winning strategy = hindsight oracle, never tradeable.** The actual weekly rotation uses the *previous* week.
- **Previous-week winner persistence is weak.** Switching 70 times in 80 comparable weekly transitions is itself evidence of rank instability.
- Smoother 8-week scores can look better in a favorable market period but fall short during other regimes. Statistical uncertainty and multiple testing mean choosing that period after the fact is not validation.
- A fair future test should freeze strategy rules and rotation before **new data after 2026-09-25**, run all strategy paper shadows daily (including inactive models), use real bid/ask costs and no retrospective optimization. If selection is changed based on this week's feedback, start a new untouched validation period.

## Reproducible evidence files

- `weekly_rotation.py`: full source and selection rules.
- `shadow_weekly_strategy_scoreboard.csv`: net R, fill count and 3R hit rate for each source playbook by past completed week.
- `exact_user_rule_weekly_switches.csv` and `exact_user_rule_trades.csv`: chosen strategy **before each week** and all paper fills under exact weekly-winner model.
- `all_300_weekly_rotation_policy_scores.csv`: fixed parameter sweep by historical period, including no-trade days, max drawdown and 3R hit rates.
- `weekly_rotation_comparison.csv`, `train_selected_weekly_switch_decisions.csv`, `train_selected_rotation_trade_log.csv`: baselines and train-only-selected policy.
- `strict_50pct_3R_weekly_gate.csv`: 50%-hit 3R weekly filter and hold/flat comparisons.
- `exclude_archive_and_rare_sensitivity.csv`: robustness removing archival nonuniform-payoff strategy and sparse Unicorn proxy.
- `week_to_next_week_winner_persistence.csv`, `eight_model_winner_persistence.csv`: test if performance has any next-week persistence.
- `bootstrap_weekly_paired_comparison.csv`: exploratory week-resampling confidence ranges on extra cumulative R, not familywise-corrected.

**Conclusion:** Weekly rotation is a sensible hypothesis to test, but the simplest rule (last week's winner) **failed** here, and longer windows did not produce a consistently validated profitable strategy. These are historical proxy trades, not forecasts or broker-executable signals.
**Canonical rebuild:** The GitHub Actions run uses the committed prior-source trade-log snapshot. The developer's local snapshot differs by 35 bytes (a few floating-point net-R values), which can alter close policy rankings and borderline first-signal fills. The GitHub run selected **8W mean + 12-minimum + 0.15 switching margin + top two** on 2025. All headline values here use committed CI-generated tables; do not mix the local snapshot's policy winner with these data.
