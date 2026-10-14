# XAUUSD Adaptive Bank — Statistical Condition Ablation & Rolling Selection

**Research date:** 2026-10-14. **Universe:** 760,337 XAUUSD M1 bid candles, Jan 2025 to Sep 2026, with 75,264 eligible completed M5 signal timestamps (Israel 06:00–19:59, DST-aware). **Status:** exploratory, **NO validated profitable trading strategy**.

**Primary principle:** The historical 2,091 (3×ATR M15) and 4,584 (4×ATR M5) winning price-leg catalogs contain examples of *where* reversals occurred. They do **not** identify real-time causes, do not cover failed signals, and **ARE NOT** used to trigger a trade. All signal/failure denominators in this experiment come from the full M1 feed and 43 real-time/as-of context features in `../condition_bank_m5.csv`.

## Scope — 348 ablations

Four M5 base triggers: `rejection`, `engulfing`, 12-bar close breakout, and candle-body direction. Each was retested using 29 contextual gates (including `NONE`) × three predeclared managers = **4×29×3 = 348 tests**. Includes the user's proposed dimensions: prior day/week sweeps, multi-week Premium/Discount, H1 confirmed 0.618–0.786 Fibonacci, HTF EMA trend alignment/countertrend, H1/H4/M15/M5 active FVG zones, prior 15-minute countermove, displacement, and selected multi-layer AND/OR conditions.

**Execution:** completed M5 signal candle, market entry at NEXT available continuous M1 open between 06:00 and 20:00 Israeli time, one position at a time, conservative same-candle SL-before-TP, 120-minute maximum on recorded data, stop = 1.5× contemporaneous M5 ATR14, TP=4R or 5R. Management: fixed4, BE after +1.5R with 4R TP, or +0.5R ladder after +1R with 5R TP. Assumed friction of **$0.35 in XAUUSD price units** per round trip. This is only a working cost proxy, not broker-specific live fill quality. No pyramiding. No future 3ATR/4ATR winners are used as signals.

## Key result: adding more confirmations is not automatically an edge

**348 combinations, NONE achieved +1R per trade in either the original development sample or the previously reused Apr–Sep 2026 review.** Among candidates with ≥100 development trades and ≥60 reused-review trades:

- Only **3/348** had an arithmetic average above zero in both development and reused-review samples under *gap-close proxy* handling; an additional **worst-case -1R stress for unobserved feed gaps** can change marginal cases.
- **Zero** showed positive average R in all FIVE chronological subperiods (2025H1, 2025H2, 2026Q1, 2026Q2, 2026Q3).
- Choosing the **best filter and manager from DEVELOPMENT only**, separately for each of four triggers, gave **negative** reused-review expectancy in every case: `rejection` −0.0614R, `engulfing` −0.0044R, `breakout12` −0.0078R, `body` −0.0701R.
- A rolling expanding-window selection (train on previous regimes; evaluate in next) gave aggregate **−0.05184R per trade across 10,723 entries** from 16 held-forward trigger×period tests, all four trigger families negative. Results are based on the same finite historical archive and were already exposed to previous research. They are NOT a fresh blind test.

### Tempting but unstable subset effects

`engulfing + aligned M15 trend + active M15 FVG`, fixed 4R: development −0.091R (695 trades), reused review +0.133R (252 trades). The seeming +0.160R per-trade improvement in review relative to the *unfiltered* engulfing model does not replicate in development. Filtering also changes trade timing and opportunity count, so this difference is **not a randomized causal effect**.

`engulfing + M15/H1 trend alignment`, BE at 1.5R with 4R TP, after worst-case feed-gap stress: reused-review +0.0458R over 460 entries, **weekly block-bootstrap exploratory 95% interval −0.093R to +0.188R**. This combination was among those selected after inspecting many variants; this interval does not correct for multiple comparisons and does not establish an edge.

## Additional test: adaptive ML selector of parameter combinations

Beyond rigid AND/OR recipes, `statistical_selector.py` explores a **50-feature** tree-based regression model (43 live boolean indicators + ATR, direction, time and trigger identity) predicting hypothetical fixed-4R net outcomes for eligible candidates, including losers.

- 114,704 direction-specific historical candidate signals before removing same-time conflicts and overlapping active positions.
- **Train 2025H1**, choose one risk/coverage threshold using **2025H2**, then refit on data through 2026Q1 before reviewing Apr–Sep 2026.
- Actual 2025H2 threshold-selection evaluation on the model trained on 2025H1: **−0.0468R** (1,406 trades). **Do not confuse this with the +0.128R shown by the subsequent refitted model on its IN-SAMPLE 2025H2 data.**
- Reused 2026Q2 review: 702 entries, **−0.0628R**, 100% calendar coverage.
- Reused 2026Q3 review: 745 entries, **−0.0929R**, 100% coverage.
- Therefore **the adaptive weighting model does NOT meet the +1R objective**. High daily coverage alone is not positive expectancy.

## Time/data QA

M1 candles can be absent (holiday/market pauses). A position open during a feed break cannot have an accurately inferred market fill. `ablation.py` closes it at the last observed close with `gap_proxy`; 437 such proxy exits are counted **across all 348 repeated scenario runs** (not 437 independent real trades). Also reports the hypothetical conservative sensitivity assigning **−1R plus fees** to these outcomes. After this correction all exit durations are ≤120 minutes in observed bars. The standalone ML outcome exercise uses −1R stress for such cases. Neither proxy provides real tick execution certainty. Features are evaluated after **closed candles**; higher-timeframe pivots are not retroactively available before their confirmation.

## File guide

| Filename | Purpose |
|---|---|
| `ablation.py` | Reproduce 348 causal-time signal/manager tests including gap sensitivity |
| `all_348_ablations.csv` | Full train, prior-period, reused-review metrics for all 348 variants |
| `fixed4_all_116_filters.csv` | Fixed4 apples-to-apples filter leaderboard (4×29) |
| `train_selected_four.csv` | One filter/manager per trigger chosen using training data only |
| `walkforward.py` | Four sequential expanding-window comparisons per trigger |
| `rolling_16_train_before_test_folds.csv` | Which filter was selected at each historical time boundary and results next window |
| `rolling_trigger_summary.csv`, `stability_summary.json` | Aggregated robustness findings |
| `statistical_selector.py` | Adaptive regression model for context scoring; decision threshold based on past only |
| `ml_threshold_validation_2025H2.csv` | The actually out-of-training threshold selection test |
| `ml_selector_period_results.csv`, `ml_selector_trade_log.csv` | Model and uninformed baseline comparisons, executed trade outcomes |
| `bootstrap.py`, `three_positive_variants_bootstrap.csv` | Unadjusted posthoc weekly-cluster uncertainty for marginal best variants |
| `summary.json`, `ml_summary.json` | Key machine-readable methods and aggregate QA |

## What we can and cannot conclude

We can reliably say the **tested rules/filters/management settings did not show a persistent advantage** in this historical sample. We CANNOT say no successful strategy is possible, nor that the original reaction labels reveal what *caused* a move. Statistical comparisons selected from the same archive are exploratory and have multiple-testing risk. The 2026 April–September review period was seen repeatedly in prior research; it is **not a virgin holdout**. Confidence intervals calculated for posthoc selected winners are optimistic and not selection-adjusted. Bid-only OHLC, synthetic fees, intrabar sequencing, stop gaps and session-dependent spreads limit live conclusions.

## Scientifically justified next branch

1. Build **failure-aware 120-minute opportunity labels** (MFE, MAE, earliest causal signal, time to 1R/2R/3R/4R and stop hit), including all candidates and skipped signals, not hindsight ZigZag origin marks.
2. Evaluate **incremental conditional value** of each filter and pair: *same trigger, same risk and costs, same trading calendar*, report sample shrinkage and week-cluster intervals. Avoid including three correlated indicators as independent 'confirmations'.
3. Design regime-aware decisions with prespecified bounded complexity, penalize variable selection, and freeze definitions before obtaining a genuinely **new future sample/paper-trading period**. Target ≥1 trade each active market day only if return/risk results justify it; do not force low-quality entries.
4. Run independent tick/quote and cost/spread sensitivity before considering capital deployment.

**Run locally or through GitHub Actions**: From repo root, with dependencies pandas, numpy, numba and scikit-learn, execute `python 'research/parameter_bank/ablation/ablation.py'`, then `walkforward.py`, `statistical_selector.py`, `bootstrap.py`. The workflow commits all output tables; it never reuses the historical winning-leg labels to choose trade entries.
**Reproducibility note:** A local rerun and GitHub Actions run gave slightly different gradient-boosting regression scores because the scientific Python dependency/runtime environments are not identical. The 348 deterministic rule tests and rolling tests agreed. Numbers quoted above use the verified committed GitHub Actions results. Freeze the exact numerical dependency versions before any pre-registered out-of-sample test.
