# XAUUSD M1 | Exact 3R / 50% hit rate | Decision plan and negative validation result

**Date:** 2026-10-22. **Status:** No strategy satisfying the requested 3R full-target hit rate of at least 50% **and** a minimum of one executed trade on every eligible market day has been validated. Do NOT deploy the tested selector as a funded/live trading system.

## Requested acceptance conditions

1. **All wins must hit the full 3R target**, not merely close positive. Use realistic spread/commission/slippage. A time expiry may be logged as a separate partial outcome, not silently counted as a TP.
2. **≥50% full 3R hits** on a genuinely new, untouched test period. Report uncertainty. **50% at +3R/-1R = +1R before fees**, not +1R net. Given average assumed transaction cost of 0.20R, a pure +3/-1 trade requires at least 55% success to average +1R net. Real time-outs/gaps alter this exact threshold.
3. **≥1 filled trade per eligible day** between 06:00–20:00 Asia/Jerusalem for entry. No future events selected in same day. Open trades may finish after 20:00 but max 120 minutes in comparable simulation. If an eligible day has no valid trading signal, record this explicitly; never invent a compulsory trade and call the target satisfied.
4. Position sizing uses **structure-derived stop**, beyond sweep/pivot/breaker/FVG invalidation with spread/execution buffer; compare an ATR stop only as a declared alternative and never choose a stop retrospectively.
5. Proof must hold at least in successive walk-forward months, stress costs, and final blinded forward paper/live-simulation sample. **Do not optimize on 2026Q2/Q3**; it has been reused across previous research.

## Exact findings of this increment

**Candidate universe:** 760,337 original XAUUSD M1 bid candles and 25,843 already logged executions from **nine simplified trade models**, excluding the archival custom-strategy log because its execution/payoff conventions are different. There are 449 eligible weekdays in the broader prior set, but only 446 days where any pre-existing candidate reached 3R even with perfect hindsight (NOT an executable selector). Source: `research/m1_rotating_strategies/two_day/all_ten_strategy_trades.csv` and the original archived tape in `research/15M ATR`.

**Reproducible causal model experiment:** `repro_from_market_tape.py` derives all features from candles **closed before the M1 entry open**. One shallow gradient-boosted tree and one regularized logistic classifier were fit exclusively on **Jan–Jun 2025** outcomes. Threshold/model chosen exclusively on **Jul–Dec 2025**, requiring ≥25 eligible first-in-day trades and ≥25% coverage. Select earliest score-qualified signal each day, no later-same-day hindsight. Assess **Jan–Mar 2026** and reused **Apr–Sep 2026**. A model can at most classify the *proxy* entries' recorded outcomes; it cannot optimize entries not in the candidate list.

### Verified in local run — canonical Github automation may yield minor rounding differences

| Evaluation period | Earliest-qualified filled trades | Eligible candidate days | Full 3R hit % | Average net R |
|---|---:|---:|---:|---:|
| Jan–Jun 2025 (model fit; non-holdout) | 126 | 126 | 45.24% | +0.639 |
| Jul–Dec 2025 (selector choice; non-holdout) | 129 | 131 | 27.13% | −0.038 |
| Jan–Mar 2026 (subsequent test) | 50 | 63 | 26.00% | −0.104 |
| Apr–Sep 2026 (previously reused review period) | 123 | 126 | 26.83% | −0.085 |

**Best validation-only selector**: shallow HistGradientBoostingClassifier with a 0.25 predicted full-TP-hit threshold. It failed the 50% win rate target in both 2026 segments and failed 100% coverage. Note the artificially strong **in-sample fit** to Jan–Jun 2025. Among all April–September candidates, the top decile by this model reached only ~23.2% full 3R hits (base ~21.2%). This is why we do not choose a strategy based on impressive in-sample rankings.

**Earlier complementary local experiment:** An independently built 24-feature dataset with two other score models selected an online classifier based on Jul–Dec 2025. That selector reached **34/126 full 3R winners = 27.0%** in Apr–Sep 2026, mean net −0.035R. Those input features were from an earlier local experiment and are **not** the reproducible model in this directory; therefore they are reported for cross-check context only.

**Important data limitation:** The nine candidate algorithms are **proxies** (AMD+iFVG, ICT 2022, H1 FVG reaction, OTE, Unicorn, etc.), not a complete faithful implementation of every named setup. The user's own original breaker/paired-liquidity rules **must be validated separately**, not replaced with a proxy. Same-minute stop and target are interpreted conservatively, using bid OHLC and an assumed 0.35 XAUUSD price-unit cost instead of real broker fills. Samples are correlated. Observed model lift does NOT prove predictive power or future profitability.

## Concrete experimental manual playbook — not validated as profitable

Four separate entry families to code faithfully, test independently and potentially combine only **after** validation:

1. **AMD manipulation → iFVG:** freeze accumulation range; sweep and reclaim it; identify a bearish FVG formed before long iFVG inversion; confirm close above far FVG edge; first return to the inverted gap; stop below manipulation low; fixed full TP 3R.
2. **User's original BOS/CHOCH → paired origin-liquidity sweep → confirmed breaker + FVG:** preserve *independent concurrent* structures and exact originating swing relationship; full body breaker confirmation; enter next open or separately tested retest; stop at final sweep extreme; full TP 3R.
3. **External PDH/PDL raid → M1 displaced MSS → new FVG → retest:** entry at first return to midpoint; stop at raid extreme; TP 3R.
4. **Trend continuation → M1 FVG pullback:** H1/M5 completed-bar alignment, fresh impulse M1 FVG, first touch and close back through its boundary or an M1 pivot; stop behind last pullback swing; TP 3R.

**Daily discretionary execution:** Before trading, freeze PDH/PDL, Asia high/low, completed H1/H4 FVGs, H1/M5 swing context. Watch for one of the four **fully defined**, not approximated setups. No entry outside 06:00–20:00 Israeli time. If multiple setups refer to the same liquidity move, take just one predeclared priority. Set SL based on scenario invalidation *before* sizing; target 3R net of reasonable execution friction when testing; check no major news/slippage caveats; log confirmed or absent signals every day. Start only with simulation/paper trading; the 50%+ goal has **not** been met.

### Gate for considering live deployment

- First implement and visually audit ≥30 random trades **and ≥30 failed signals per family** versus M1 charts; no retrospective pivots or future completed H1/FVG data.
- Lock four strategy specs, no in-sample tuning on later test periods; use truly **new chronological data** after historical fit. Record the first eligible signal each day and skip days with no valid setup, reporting coverage honestly.
- **Full TP3 hit rate ≥50% and daily coverage 100%** on untouched observations; demonstrate after-cost expectancy and its lower weekly-block uncertainty bound. If exact 50% hit rate is achieved but mean after-cost R is <1, **the +1R-net goal has not been met**.
- Risk management until verified: paper only; if later deployed use small risk per trade, a fixed *money* risk ceiling and structural *price* stop; one exposure at a time, daily loss kill switch, no averaging losers to force a win.

## Files

- `repro_from_market_tape.py`: regenerates lagged features and both classifiers solely from existing public repo inputs. Requires numpy 2.3.5, pandas 2.2.3, scikit-learn 1.8.0.
- `discrimination_by_period.csv`: probability ranking quality vs actual full target hits.
- `causal_online_gate_56_results.csv`: daily-first execution and threshold comparisons across historical splits.
- `selected_online_trades.csv`: every historical selection from the model chosen in 2025.
- `summary.json`: metadata, validation regime and selected parameters.

### Why selection overfit is particularly dangerous here

A huge hyperparameter search can produce a visually impressive result even for strategies without durable profitability. The PBO/CSCV research by Bailey et al. explains why an untouched prospective period is essential: https://scholarworks.wmich.edu/math_pubs/42/ . This study is **exploratory**, not statistical proof of any trading edge.