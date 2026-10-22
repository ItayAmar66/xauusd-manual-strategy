# XAUUSD — Ten 1-minute trading playbooks for regime rotation

**Status: hypotheses / executable specification drafts — NOT backtested or validated.** Created 2026-10-22.

## Objective

Ten diverse, discretionary-but-codifiable XAUUSD **M1 execution** strategies. A future experiment will test whether selecting and rotating among them using information available at the time improves net performance against fixed playbooks and an unfiltered baseline. The historical 15M/5M reversal-leg labels are *not* entry signals and must not be used to pick trades after the fact.

### Common conventions

- Entries only **06:00–20:00 in actual Asia/Jerusalem timezone**, including DST. Open trades may continue later; initial comparative test has a 120-minute maximum hold.
- Price input: M1 bid OHLC; M5/M15/H1/H4 context from **completed** candles only. A `confirmed pivot (L=2,R=2)` becomes known only *two candles after* the extremum, and not at the extremum itself.
- Long setup described throughout; short = exact opposite unless specifically noted.
- **M1 bullish FVG**: for three consecutive *closed* M1 candles C1,C2,C3, C3.low > C1.high; bearish FVG: C3.high < C1.low. Gap is valid only once C3 closes. Inversion: close **fully beyond the far edge** of the previously formed gap, then retest from the opposite side.
- **Sweep**: confirmed price breach of a level established earlier, followed by an M1 close back through that same level within a predeclared deadline. A mere price touch is *not* a sweep.
- **MSS/CHOCH/BOS**: close beyond an earlier confirmed swing (not simply a wick), from a structurally significant swing, with precise pivot rules fixed **before the backtest**.
- **Displacement candidate**: closed M1 body larger than 1.5× median absolute M1 body of the prior 20 completed bars. This is an experimental definition, not a proven threshold.
- All stops are **structure-based**, beyond the relevant previously known sweep, swing, retest, FVG or breaker extreme plus an execution buffer. An ATR-based comparison is optional, not mandatory.
- First comparable target test: fixed **2R and 3R**, with targets filtered for opposing known liquidity. Risk, realistic spread/slippage and both same-bar hit orders must be accounted for. **No rule is asserted to have 50% WR or +1R expectancy.**
- Multiple playbooks may identify the *same underlying setup*. De-duplicate signals before interpreting strategy diversification.

## Ten distinct playbooks

### 01 — User's Original Breaker + CHOCH + paired-origin-liquidity Sweep + FVG

**Regime hypothesis:** structured reversal after a meaningful liquidity grab. **Research baseline:** preserve the user's original rules separately from other methods.

1. Track independent bullish and bearish active structures. A bullish structure break is valid only when a candle closes above a swing high whose formation subsequently caused the relevant swing low (mirror for bearish).
2. Pair each such break with its **own** origin liquidity low; wait for that specific liquidity to be swept. Maintain multiple structures simultaneously; new structures must not overwrite older unexpired ones.
3. Breaker = the latest opposite confirmed pivot between structure break and sweep. A *full M1 candle body* must break through the breaker level; require the relevant FVG linking sweep extreme to the entry sequence.
4. **Entry:** close of full-body breaker confirmation, or next M1 open in executable backtest. **SL:** final sweep extreme. **TP variant A:** 3R fixed (Original Baseline). **TP variant B:** opposing liquidity objective capped at 5R (separate original WR variant).
5. Both sides require deterministic conflict priority and time-expiry rules. Do **not** silently replace this with generic CHOCH.

### 02 — AMD / PO3 manipulation **iFVG** reversal

**Regime hypothesis:** completed accumulation box, failed directional manipulation, distribution opposite sweep.

1. Freeze an accumulation box using only a completed predeclared window (initial candidate: previous 30 M1 candles, optionally 60); do not redraw boundaries after a sweep.
2. **Manipulation:** M1 breaches below frozen box low, then closes back inside within 15 closed M1 bars (long). During manipulation, a bearish M1 FVG formed earlier.
3. **Inversion:** an M1 candle closes above the **upper far boundary** of that bearish FVG. It has now become bullish iFVG.
4. **Entry:** first subsequent retest of inverted gap midpoint / close after a rejection, tested separately. **SL:** lowest manipulation wick. **Targets:** opposing accumulation boundary and 2R/3R candidate.
5. Variation only if preregistered: no-iFVG box-boundary retest *as a separate strategy variant*, not mislabeled as AMD+iFVG.

### 03 — ICT 2022: external liquidity raid → M1 MSS displacement → fresh FVG

**Regime hypothesis:** directional reversal with strong shift in delivery.

1. Sweep a previously closed session/day high or low (not arbitrary recent five-bar high).
2. An M1 candle closes across last **confirmed** counter-direction swing with displacement.
3. A *new* same-direction three-candle M1 FVG completes **after** the sweep/MSS.
4. **Entry:** first return to the new gap's 50% point. **SL:** the raid extreme. **TP:** opposing liquidity and fixed 2R/3R comparison.
5. Distinction from #02: uses newly created **normal** FVG after MSS, not inverted gap from the manipulation phase.

### 04 — Unicorn: **Breaker × FVG overlapping price zone**

**Regime hypothesis:** reversal at overlapping structural invalidation zone.

1. Confirm an M1 swing liquidity sweep followed by a directional structure break. An earlier opposite-side order block / pivot zone must be **broken** and thus become a breaker.
2. The displacement move creates an M1 FVG in the new direction whose price interval overlaps the breaker interval.
3. Define overlap exactly: `[max(low_bounds),min(high_bounds)]`; require positive width and no prior mitigation of the entry zone.
4. **Entry:** first return to midpoint of the intersection. **SL:** relevant breaker/sweep outer extreme (predeclare variant). **TP:** opposite internal/external liquidity; compare 2R/3R.
5. Distinction: the **overlap** is required. FVG merely adjacent to breaker does not count.

### 05 — H1 FVG reaction + M1 rejection / swing break

**Regime hypothesis:** higher-timeframe price-zone reversal.

1. An H1 FVG must have completed and remained uninvalidated before touch. Price first returns to this H1 zone.
2. On M1 wait for a rejection candle closing back out of the zone, *then* close beyond high of the rejection candle or an earlier confirmed micro swing.
3. **Entry:** next M1 open after the confirmation. **SL:** low of the touch/rejection excursion. **TP:** next known M15/H1 liquidity target; test 2R/3R.
4. Distinction: the zone comes from **H1**, not an accumulation manipulation or structural overlap.

### 06 — M5 impulse, OTE 0.618–0.786 retracement + M1 reversal

**Regime hypothesis:** orderly trend pullback.

1. A completed M5 impulse breaks a previously confirmed M5 swing in the direction of higher-timeframe trend.
2. Freeze the impulse endpoints **when known**. Calculate 61.8%–78.6% corrective zone only from those prior endpoints; no moving Fibonacci to a future better anchor.
3. Price retraces into this frozen zone; M1 forms a micro-MSS with a close beyond last confirmed opposite pivot.
4. **Entry:** next M1 open or first retest of new M1 FVG. **SL:** correction swing extreme. **TP:** prior impulse high and/or 2R/3R.
5. Distinction: deep **continuation retracement**, not liquidity reversal.

### 07 — Completed Asian-range raid + M1 reclamation

**Regime hypothesis:** transition from quiet session range to London expansion/reversal.

1. Freeze the full preceding **00:00–05:59 local Israel** Asia candidate range at 06:00; do not use later candles to define it.
2. M1 price sweeps one range boundary then closes inside within 10 M1 bars; a confirming bullish M1 candle closes over high of the reclaim candle (for long).
3. **Entry:** next M1 open; alternative entry first retest of reclaim level *separate parameter*. **SL:** Asia sweep extreme. **TP:** other side of Asia box, 2R/3R.
4. Distinction from #02: a **specific session-frozen range** and simple reclaim confirmation, **iFVG not required**.

### 08 — Trend continuation: M5/H1 bias + M1 pullback to fresh FVG

**Regime hypothesis:** persistent directional trend rather than reversal.

1. Both completed H1 and M5 candles exhibit rising swing structure / optional EMA20>EMA50; trend condition fixed before scoring.
2. An M1 impulse in that direction creates a fresh FVG; price retraces for first time into the FVG without breaking the local confirmed M1 impulse swing.
3. **Entry:** reclaim of gap midpoint or M1 close above preceding candle high. **SL:** pullback low. **TP:** previous expansion high, 2R/3R.
4. Distinction: **continuation** bias and no external sweep required.

### 09 — Range breakout + retest of formerly defended boundary

**Regime hypothesis:** volatility expansion after compression.

1. Freeze a 30-M1-candle box if its completed-bar range is below a predeclared quantile of historical rolling ranges; do not choose box after breakout.
2. M1 displacement candle closes completely outside box; avoid intra-bar wick-only breaks.
3. **Entry:** first retest of the previously broken boundary, confirmed by close back in breakout direction; no entry if no retest within 15 bars.
4. **SL:** retest excursion extreme or opposite side of breakout candle (predeclared), **TP:** measured range projection and 2R/3R comparison.
5. Distinction: **successful breakout** continuation, not a failed breakout/sweep.

### 10 — BPR: overlapping opposing M1 FVGs + first-touch reversal confirmation

**Regime hypothesis:** choppy-to-directional repricing within an inefficient overlap.

1. A fully formed bearish M1 FVG and a later bullish M1 FVG (or mirrored order) have a positive **overlap** in price, each defined using closed candles.
2. Freeze the intersection after the second FVG closes. Prefer M15/H1 directional context, but keep unfiltered and contextual variants separately.
3. Price returns for **first** touch of shared band; M1 confirmation closes beyond a confirmed micro swing / rejects out of the overlap.
4. **Entry:** next M1 open after confirmation or midpoint limit. **SL:** outer low/high of rejection excursion. **TP:** adjacent opposing liquidity, 2R/3R.
5. Distinction from Unicorn: overlap is between **two opposite FVGs**, **not** between breaker and FVG.

## Rotation research — design only (not performed)

The user's key hypothesis is that the *relative* effectiveness of these models changes across weeks. **Weekly switching is a hypothesis; last week's winner is not necessarily next week's winner.**

Once instructions are agreed:
- Freeze exact signal/stop/management definitions first. Backtest **all 10 playbooks across the same historical tape**, not merely the 2,091 or 4,584 successful pivot legs.
- At each Friday/week close, calculate each model's **causally observable** trailing 10/20/40 trading-day return in R, number of filled trades, net win rate, max drawdown, no-trade days, fee sensitivity and regime context. Use **past-only** data; no contemporaneous week's outcomes for the ranking. Week-by-week walk-forward logs record the selected models *before* Monday.
- Compare: fixed playbook, trade all compatible models with deduplication, weekly-top-2 rotation, weekly regime-based choice, and skip/flat when statistical evidence is weak. Penalize low sample counts and account for changes in strategy ranking.
- All overlapping signals from different models on the **same sweep/leg** require unique scenario IDs; never count the same move as independent evidence.
- For small weekly trade samples, make **no claim of edge** and don't force the one-trade-per-day objective. Use robust shrinkage and conservative empirical confidence intervals before strategy-selection claims.
- Target 50% WR at 1:3 is **+1R gross**, not net after realistic fees. Net +1R requires greater effective gross expectancy. Market-entry candles, limit fill ordering, data gaps and uncertainty should be audited.

## Sources for *definitions*, not evidence of profitability

- AMD/iFVG conceptual trigger: https://fxreplay-webflow.fxreplay.app/strategies/ict-amd-po3-strategy
- ICT 2022 structural model: https://snipercharts.com/learn/strategies/ict-2022
- iFVG inversion definition: https://www.everfunded.com/blog/inversion-fair-value-gap
- Unicorn overlap concept: https://hadalinstruments.com/glossary/ict-unicorn-model/

**Honesty:** The ten strategies are separate candidate rulebooks; no fresh historical backtests have been run as part of defining this library. The adaptive rotation hypothesis has not yet been tested. No win rate or weekly edge is invented.
